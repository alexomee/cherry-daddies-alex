#!/usr/bin/env python3
"""«Беги от меня»: the keys (Moises keys + strings) written out as notes for the GM-800
(wiki/pipelines/part-transcription-guide.md; Alex 2026-11-20: «большая задача на снятие партии клавиш»,
notes and the part itself = the MIDI from the web, sound type / brightness = Roma's concert take,
original stems = reference; nothing played on the GM-800 yet: «пока gm 800 занят делай все что требуется
для записи»).

  P="uv run -q --python 3.12 --with numpy --with scipy --with soundfile --with mido python"
  $P tools/jamzone/prep_begi_ot_menya.py notes     # MIDI + stem corrections -> parts/synths.notes.json
                                                   #   (+ the MIDI as it is -> analysis/.../synths-midi.notes.json)
  $P tools/jamzone/prep_begi_ot_menya.py fx        # the two reverse swells cut from the stems -> parts/pb-fx.wav
  $P tools/jamzone/prep_begi_ot_menya.py plan      # voices, bars, tone candidates, the sweep commands
  $P tools/jamzone/prep_begi_ot_menya.py preview   # A/B page: original / my notes / MIDI as it is / Roma
  gmp record "Беги от меня" "music/songs/Беги от меня/parts/synths.notes.json"   # when the GM-800 is free
  gmp layer  "Беги от меня" "music/songs/Беги от меня/parts/synths.notes.json"   # -> parts/pb-synths.wav

Source of the notes: parts/begi-midifind.mid (midifind.com, C# minor = the record = the band key,
pitch_semitones 0; 124 bpm, ours 125). Bars below = mix.json bars.
MIDI bar -> our bar (every section start lands on its cue):
  MIDI 1-16   -> 1-16, and MIDI 9-16 once more -> 17-24   (our intro is 24 bars, the MIDI's 16)
  MIDI 17-99  -> + 8    (stop 25, kick-bass 27, beat 35, chorus 43, solo 59, stop 67, ... solo 100)
  MIDI 96-99  -> 108-111 once more                         (our second solo is 12 bars, the MIDI's 8)
  MIDI 100-139 -> + 12  (bridge 112, all in 120, chorus 128, solo only 144; the end hit 152 has no keys)

Voices (MIDI track -> what it is; each checked against the stems: tools/part_notes.py --roll, pyin by 16ths,
band envelopes by 64ths of a bar):
  lead      t1 Fantasia, the loud notes (velocity >= 80, picked by their place: the MIDI fades its last two bars
            by velocity): G#4 / B4 / E5 / F#5 -> D#5, five to a bar on the 16ths 0 3 6 10 13. Intro 1-24, solos 59-66, 100-111, 144-151.
  lead_lo   the same an octave down. NOT in the MIDI: in the record the lower octave is the fundamental
            (pyin locks on G#3 B3 E4 F#4), the two octaves are within 3 dB of each other.
  lead_echo t1, the soft notes in between (velocity < 80) = the MIDI author's echo of the lead; in the record they are
            bumps 12 dB under the main notes. Kept as its own voice at -10 dB: a tone with a delay replaces it.
  whistle   t4 Swist: D#5 E5 D#5 E5 D#5 C#5 x C#5 in 8ths. 1-24, 43-66, 84-111, 128-143. As in the MIDI.
  stab      t0 Chord. 43-58, 84-99, 128-143.
  arp       t6 TB303. 76-83, 112-127.
  pad       t2 Pad. 1-24, 59-66, 100-127, 144-151.

Where the record disagrees with the MIDI, the notes follow the record (the MIDI version of these voices is
kept in synths-midi.notes.json for the A/B):
  stab   the record: a fifth stack an octave up, G#4 C#5 G#5 C#6 for three bars and F#4 B4 F#5 B5 on the
         fourth, on the 16ths 0 4 7 10 13 (1, 2, 2.75, 3.5, 4.25). The MIDI: triads C#4 E4 G#4 / B3 E4 G#4 /
         C#4 E4 A4 / B3 D#4 F#4 on 0 6 10 13 (the bass rhythm). No stabs under the solos (the MIDI keeps them
         under the second one).
  arp    the record: ONE figure C#4 D#4 E4 G#3 in 16ths through all bars of 76-83 and 112-127. The MIDI:
         chord arpeggios (G#4 E4 C#4 E4 ...) that change every bar.
  pad    in the record (strings stem) the pad sounds in 1-24, 59-66, 100-127, 144-151; the MIDI also holds it
         through 92-99 and the last chorus 128-143 (there the stem has only a thin high line / nothing).
         Bridge bars 118 and 126: G#sus4 (G#3 C#4 D#4), 119 and 127: G# (G#3 C4 D#4); the MIDI has G# and
         then two single notes F#4, G#4.
  lead   the second pass of «solo only» (148-151) is 5 dB quieter in the record: a level ramp on the notes.
Not notes (stay as cut stems, parts/pb-fx.wav): the reverse swell of a C#m chord into the choruses, beats 3-4
of bars 42 (keys + strings) and 83 (strings).
Not written: the thin high string line of 92-99 (B4 / C#5, -40 dBFS), the MIDI's RollCymb and percussion.
"""
import collections, importlib.util, json, os, subprocess, sys
import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SONG = os.path.join(REPO, "music", "songs", "Беги от меня")
MID = os.path.join(SONG, "parts", "begi-midifind.mid")
PART = os.path.join(SONG, "parts", "synths.notes.json")
FX = os.path.join(SONG, "parts", "pb-fx.wav")
OUT = os.path.join(REPO, "analysis", "gm800-match", "Беги от меня")
ALT = os.path.join(OUT, "synths-midi.notes.json")
PAGE = os.path.join(OUT, "preview-part")
NAMES = "C C# D D# E F F# G G# A A# B".split()
END = 152                                  # bar after the last one with keys
SEGS = [(1, 17, 1), (9, 17, 17), (17, 100, 25), (96, 100, 108), (100, 140, 112)]   # MIDI [mb0, mb1) -> our bar of mb0
PAD_BARS = [(1, 25), (59, 67), (100, 128), (144, 152)]                             # where the record has the pad
STAB_BARS = [(43, 59), (84, 100), (128, 144)]
ARP_BARS = [(76, 84), (112, 128)]
SOLO_END_DB = {147: -2, 148: -5, 149: -5, 150: -5, 151: -5}                        # keys stem, 148-151 against 144-147
ARP_DB = lambda b: 5 if 112 <= b < 120 else 1 if 120 <= b < 128 else 0          # keys stem: 76-83 -27, 112-119 -22, 120-127 -26 dBFS
MAIN = (0, 3, 6, 10, 13)                   # 16ths of the lead's loud notes (velocity >= 80 in the MIDI, attacks in the record)
FX_WINDOWS = [(42.5, 43.0, ("keys", "strings")), (83.5, 84.0, ("strings",))]       # bars [from, to), stems

name = lambda m: f"{NAMES[m % 12]}{m // 12 - 1}"
_solnyshko = None


def shared():
    """spans / dump / synth of prep_solnyshko.py (same file format, same plain synth)."""
    global _solnyshko
    if _solnyshko is None:
        s = importlib.util.spec_from_file_location("prep_solnyshko", os.path.join(os.path.dirname(__file__), "prep_solnyshko.py"))
        _solnyshko = importlib.util.module_from_spec(s); s.loader.exec_module(_solnyshko)
    return _solnyshko


# tone = provisional pick by patch name (nothing has been played on the GM-800 yet); cand = the short list for
# `gmp sweep --tones`; solo = bars where the voice is (almost) alone in keys + strings, for the sweep.
VOICES = {
    "lead":      dict(tone=316, role="lead",  solo=(144, 148), cand=[316, 1024, 1092, 352, 350, 1073, 314, 349, 1019, 980],
                      what="лид, верхняя октава (G#4 B4 E5 F#5→D#5)"),
    "lead_lo":   dict(tone=316, role="lead",  solo=(144, 148), cand=[], what="лид октавой ниже (в записи основная)"),
    "lead_echo": dict(tone=316, role="lead",  solo=(144, 148), cand=[], what="эхо лида, −10 дБ (или дилей тона)"),
    "whistle":   dict(tone=880, role="whistle", solo=(1, 5),   cand=[880, 881, 882, 883, 886, 223, 224, 957, 205],
                      what="«свист» восьмыми D#5 E5 D#5 E5 D#5 C#5 · C#5"),
    "stab":      dict(tone=1024, role="stab", solo=(43, 47),   cand=[1024, 316, 1092, 322, 314, 317, 1019, 352],
                      what="удары припева квинтами, 1 · 2 · 2.75 · 3.5 · 4.25"),
    "arp":       dict(tone=350, role="pluck", solo=(76, 80),   cand=[350, 351, 1089, 1073, 1083, 1078, 354, 680, 676],
                      what="фигура шестнадцатыми C#4 D#4 E4 G#3"),
    "pad":       dict(tone=287, role="pad",   solo=(112, 116), cand=[287, 286, 284, 753, 1011, 275, 264, 285],
                      what="пэд, аккорды по такту"),
}
GAP = {"lead": 0.002, "lead_lo": 0.002, "lead_echo": 0.002, "stab": 0.002, "arp": 0.002}   # 16th-long notes: keep the length


def tracks():
    """{track: [(start beat, beats, pitch, velocity)]}"""
    import mido
    m = mido.MidiFile(MID); tpb = m.ticks_per_beat; out = {}
    for i, tr in enumerate(m.tracks):
        t = 0; on = collections.defaultdict(list); ns = []
        for msg in tr:
            t += msg.time
            if msg.type == "note_on" and msg.velocity > 0:
                on[msg.note].append((t, msg.velocity))
            elif msg.type in ("note_off", "note_on") and on[msg.note]:
                s, v = on[msg.note].pop(0); ns.append((s / tpb, (t - s) / tpb, msg.note, v))
        out[i] = sorted(ns)
    return out


def cut(ns, semi=0, keep=lambda col: True, bars=None, opt=None):
    """A MIDI track through SEGS -> [[our bar, beat, beats, "pitches"(, options)]]; bars = [(from, to)] of ours to keep;
    keep(16th of the bar, 0-15) picks notes by their place in the bar."""
    grp = collections.OrderedDict()
    for mb0, mb1, ours in SEGS:
        for s, d, p, v in ns:
            mb = int(s // 4) + 1; b = ours + mb - mb0
            if mb0 <= mb < mb1 and keep(int(round(s % 4 * 4))) and (bars is None or any(a <= b < e for a, e in bars)):
                grp.setdefault((b, round(s % 4 + 1, 3), round(d, 3)), set()).add(p + semi)
    out = [[b, bt, d, " ".join(name(p) for p in sorted(ps))] for (b, bt, d), ps in grp.items()]
    return [n + [dict(opt)] for n in out] if opt else out


def ramp(notes):
    """The quieter second pass of «solo only», as a gain on the notes."""
    out = []
    for n in notes:
        db = SOLO_END_DB.get(n[0], 0) + (n[4]["gain_db"] if len(n) > 4 else 0)
        out.append(n[:4] + ([{"gain_db": db}] if db else []))
    return out


def build(as_midi=False):
    T = tracks(); V = {}
    main = lambda col: col in MAIN
    V["lead"] = cut(T[1], keep=main)
    if not as_midi:
        V["lead_lo"] = cut(T[1], -12, keep=main)
    V["lead_echo"] = cut(T[1], keep=lambda col: col not in MAIN, opt={"gain_db": -10})
    V["whistle"] = cut(T[4])
    if as_midi:
        V["stab"] = cut(T[0]); V["arp"] = cut(T[6]); V["pad"] = cut(T[2])
    else:
        V = {vn: ramp(ns) for vn, ns in V.items()}
        chord = ["G#4 C#5 G#5 C#6"] * 3 + ["F#4 B4 F#5 B5"]
        V["stab"] = [[b, bt, 0.25, chord[(b - a) % 4]] for a, e in STAB_BARS for b in range(a, e) for bt in (1, 2, 2.75, 3.5, 4.25)]
        V["arp"] = [[b, 1 + q / 4, 0.25, "C#4 D#4 E4 G#3".split()[q % 4]] + ([{"gain_db": ARP_DB(b)}] if ARP_DB(b) else [])
                    for a, e in ARP_BARS for b in range(a, e) for q in range(16)]
        sus = {118: "G#3 C#4 D#4", 126: "G#3 C#4 D#4", 119: "G#3 C4 D#4", 127: "G#3 C4 D#4"}
        V["pad"] = [n for n in cut(T[2], bars=PAD_BARS) if n[0] not in sus] + [[b, 1.0, 4.0, c] for b, c in sus.items()]
    return {vn: dict({"at": [1], "bars": END - 1, "notes": sorted(ns, key=lambda n: (n[0], n[1]))},
                     **({"gap": GAP[vn]} if vn in GAP else {})) for vn, ns in V.items()}


def cmd_notes():
    sh = shared(); V = build()
    takes = [{"voice": vn, "tone": VOICES[vn]["tone"], "base": 33, "bars": sp, "gain_db": 0.0}
             for vn in VOICES for sp in sh.spans(V[vn]["notes"])]
    part = {"_about": "Keys of «Беги от меня» (Moises keys + strings) written out for the GM-800; generated by "
                      "tools/jamzone/prep_begi_ot_menya.py notes (edit there, not here). Notes: the MIDI from midifind "
                      "(parts/begi-midifind.mid) with the record's notes where they differ (stab, arp, pad bars, the lower "
                      "octave of the lead). C# minor = band key, mix.json bars. Tones and gains are provisional: nothing "
                      "has been played on the GM-800 or checked by ear yet (2026-11-20). Which voices Alex plays live is "
                      "not decided: all of them are in the layer for now.",
            "stems": ["keys", "strings"], "voices": V, "layer": {"file": "pb-synths", "takes": takes}}
    sh.dump(part, PART)
    os.makedirs(OUT, exist_ok=True)
    sh.dump({"_about": "The MIDI as it is (only the bar mapping changed): A/B against parts/synths.notes.json",
             "stems": ["keys", "strings"], "voices": build(as_midi=True)}, ALT)
    print(PART)
    for vn, v in V.items():
        print(f"  {vn:9} {len(v['notes']):4} notes  bars " + " ".join(f"{a}-{b - 1}" for a, b in sh.spans(v["notes"])))
    print(f"  layer: {len(takes)} takes, {sum(b - a for t in takes for a, b in [t['bars']])} bars to record")
    print(ALT)


def song_obj():
    load = lambda nm: (lambda s: (lambda m: (s.loader.exec_module(m), m)[1])(importlib.util.module_from_spec(s)))(
        importlib.util.spec_from_file_location(nm, os.path.join(REPO, "tools", nm + ".py")))
    gp = load("gm800_part"); return gp, gp.gmm.Song("Беги от меня")


def cmd_fx():
    """The reverse swells into the choruses, cut from the stems in their windows -> parts/pb-fx.wav (stem frame:
    a "frame": "stem", "derived": true layer of mix.json; pitch_semitones is 0, so no transposing)."""
    import soundfile as sf
    gp, song = song_obj(); out = None; sr = None
    for a, e, stems in FX_WINDOWS:
        for st in stems:
            x, sr = sf.read(song.stem(st), always_2d=True, dtype="float64")
            if out is None:
                out = np.zeros_like(x)
            i0, i1 = int(round(song.t_stem(a) * sr)), int(round(song.t_stem(e) * sr)); f = int(0.01 * sr)
            w = np.ones(i1 - i0); w[:f] = np.linspace(0, 1, f); w[-f:] = np.linspace(1, 0, f)
            out[i0:i1] += x[i0:i1] * w[:, None]
    sf.write(FX, out, sr, subtype="PCM_16")
    print(FX, f"peak {20 * np.log10(np.abs(out).max()):.1f} dBFS")


def cmd_plan():
    sh = shared(); part = json.load(open(PART, encoding="utf-8"))
    rows = {int(r.split("\t")[0]): r.split("\t")[1] for r in open(os.path.join(REPO, "gear", "gm-800", "tones.tsv"), encoding="utf-8")}
    rel = os.path.relpath(PART, REPO)
    for vn, spec in VOICES.items():
        sp = " ".join(f"{a}-{b - 1}" for a, b in sh.spans(part["voices"][vn]["notes"]))
        print(f"\n{vn}: {spec['what']}; такты {sp}; пока тон {spec['tone']} {rows[spec['tone']]}")
        if spec["cand"]:
            print("   кандидаты: " + ", ".join(f"{n} {rows[n]}" for n in spec["cand"]))
            both = "lead,lead_lo" if vn == "lead" else vn
            print(f"   gmp sweep \"Беги от меня\" \"{rel}\" {both} --bars {spec['solo'][0]} {spec['solo'][1]} "
                  f"--role {spec['role']} --tones {','.join(map(str, spec['cand']))}")


HTML = """
<h2>Голоса плейбека</h2>
<div class="wrap"><table>
<tr><th>Голос</th><th>Такты</th><th>Что играет</th><th>Откуда</th></tr>
<tr><td>lead + lead_lo</td><td class="n">1–24, 59–66, 100–111, 144–151</td><td>G#4 / B4 / E5 / F#5→D#5 по такту, пять нот на такт (1 · 1.75 · 2.5 · 3.5 · 4.25), две октавы</td><td>MIDI; нижняя октава по записи</td></tr>
<tr><td>lead_echo</td><td class="n">там же</td><td>тихие повторы между основными нотами, −10 дБ</td><td>MIDI (в записи это эхо)</td></tr>
<tr><td>whistle</td><td class="n">1–24, 43–66, 84–111, 128–143</td><td>D#5 E5 D#5 E5 D#5 C#5 · C#5 восьмыми; седьмая нота G#4 / G#4 / A4 / B4</td><td>MIDI</td></tr>
<tr><td>stab</td><td class="n">43–58, 84–99, 128–143</td><td>G#4 C#5 G#5 C#6 три такта, F#4 B4 F#5 B5 четвёртый; 1 · 2 · 2.75 · 3.5 · 4.25</td><td>запись (в MIDI трезвучия октавой ниже в ритме баса)</td></tr>
<tr><td>arp</td><td class="n">76–83, 112–127</td><td>C#4 D#4 E4 G#3 шестнадцатыми, одна фигура на все такты</td><td>запись (в MIDI арпеджио по аккордам)</td></tr>
<tr><td>pad</td><td class="n">1–24, 59–66, 100–127, 144–151</td><td>C#m · E · A · B→B/F#; бридж F#m · B · C#m · A · F#m · B · G#sus4 · G#</td><td>MIDI; такты и G#sus4 по записи</td></tr>
<tr><td>FX (из стемов)</td><td class="n">42.3–42.4, 83.3–83.4</td><td>обратный свелл аккорда C#m перед припевом</td><td>вырезано из keys/strings</td></tr>
</table></div>
<p class="q">Не выписано: тонкая высокая линия струнных в 92–99 (B4 / C#5, очень тихо). Какой голос ты играешь вживую
(сцена 3), я не знаю: пока в плейбеке все голоса.</p>
"""

# ---- preview without the GM-800: plain synth, render timeline -------------------------------------------------
SR = 44100
#            kind      lowpass decay  level
TIMBRE = {"lead":      ("saw",    5000, 0.10, 1.0), "lead_lo": ("saw", 3500, 0.10, 0.8), "lead_echo": ("saw", 4000, 0.08, 0.9),
          "whistle":   ("organ",  0,    None, 0.5), "stab":    ("saw", 6000, 0.09, 0.5), "arp":       ("square", 1600, 0.07, 0.35),
          "pad":       ("pad",    2200, None, 0.3)}


def render(song, gp, part, voices):
    sh = shared(); n = int(round(song.t_render(END) * SR)) + 2 * SR; out = {}
    for vn in voices:
        buf = np.zeros(n)
        if vn in part["voices"]:
            kind, fc, dec, g = TIMBRE[vn]
            gains = gp.voice_gains(song, part, vn, 1, END)
            for t, m, d in gp.voice_line(song, part, vn, 1, END):
                db = next((x for t0, dd, x in gains if abs(t0 - t) < 1e-6), 0)
                x = sh.synth(kind, fc, dec, 440 * 2 ** ((m - 69) / 12), max(d, 0.03)) * g * 10 ** (db / 20)
                a = int((song.t_render(1) + t) * SR); k = min(len(x), n - a)
                buf[a:a + k] += x[:k]
        out[vn] = buf
    return out


def cmd_preview():
    import soundfile as sf
    gp, song = song_obj(); os.makedirs(PAGE, exist_ok=True)
    n = sf.info(os.path.join(SONG, "auto-render", "all.wav")).frames
    rd = lambda p: sf.read(p, always_2d=True, dtype="float64")[0].mean(1)
    fit = lambda x: np.pad(x, (0, max(0, n - len(x))))[:n]
    seg = lambda x, a, b: x[int(song.t_render(a) * SR):int(song.t_render(b) * SR)]
    rms = lambda x, a, b: np.sqrt((seg(x, a, b) ** 2).mean()) + 1e-12
    off = int(round(song.off * SR))
    at_off = lambda x: fit(np.concatenate([np.zeros(off), x]))
    keys, strings = at_off(rd(song.stem("keys"))), at_off(rd(song.stem("strings")) * 10 ** (3.5 / 20))   # +3.5 as in pb-other
    orig = keys + strings
    mine, alt = json.load(open(PART, encoding="utf-8")), json.load(open(ALT, encoding="utf-8"))
    vm = {k: fit(v) for k, v in render(song, gp, mine, list(VOICES)).items()}
    # level of each voice group from the stems (a balance for this page only; the layer is balanced on the takes)
    g = {}; lead = vm["lead"] + vm["lead_lo"] + vm["lead_echo"]
    left = lambda tot, known: np.sqrt(max(tot ** 2 - known ** 2, (0.25 * tot) ** 2))
    g["pad"] = rms(strings, 112, 120) / rms(vm["pad"], 112, 120)
    g["arp"] = rms(keys, 76, 84) / rms(vm["arp"], 76, 84)
    half = rms(keys, 43, 59) / np.sqrt(2)                     # chorus = stab + whistle, taken as equal halves
    g["whistle"] = half / rms(vm["whistle"], 43, 59); g["stab"] = half / rms(vm["stab"], 43, 59)
    g["lead"] = left(rms(keys, 59, 67), g["whistle"] * rms(vm["whistle"], 59, 67)) / rms(lead, 59, 67)   # solo = lead + whistle
    print("voice gains (dB): " + ", ".join(f"{k} {20 * np.log10(v):+.1f}" for k, v in g.items()))
    grp = {"lead": "lead", "lead_lo": "lead", "lead_echo": "lead", "whistle": "whistle", "stab": "stab", "arp": "arp", "pad": "pad"}
    fx = at_off(rd(FX)) if os.path.exists(FX) else np.zeros(n)
    mix = lambda vs: sum(v * g[grp[k]] for k, v in vs.items())
    va = {k: fit(v) for k, v in render(song, gp, alt, list(VOICES)).items()}
    src = {"orig": orig, "mine": mix(vm) + fx, "midi": mix(va),
           "roma": fit(rd(os.path.join(SONG, "parts", "roma-keys-2810.wav")))}
    src["roma"] *= rms(orig, 9, 17) / rms(src["roma"], 9, 17)
    for a, b, what in ((1, 9, "intro"), (9, 25, "intro+kick"), (43, 59, "chorus"), (59, 67, "solo"), (76, 84, "arp"),
                       (100, 112, "solo 2"), (112, 128, "bridge"), (144, 152, "solo only")):
        print(f"  {what:10} bars {a}-{b - 1}:  orig {20 * np.log10(rms(orig, a, b)):6.1f}  mine {20 * np.log10(rms(src['mine'], a, b)):6.1f}"
              f"  midi {20 * np.log10(rms(src['midi'], a, b)):6.1f}  roma {20 * np.log10(rms(src['roma'], a, b)):6.1f} dBFS")
    ctx = sum(fit(rd(os.path.join(SONG, "auto-render", p))) for p in ("stems/drums.mp3", "stems/vocal.mp3", "pb-bass.mp3"))
    ctx *= rms(orig, 9, 17) / rms(ctx, 9, 17) * 2.0
    peak = max(np.abs(v + ctx).max() for v in src.values())
    for k, v in src.items():
        for tag, x in (("", v), ("-ctx", v + ctx)):
            p = os.path.join(PAGE, f"{k}{tag}.mp3")
            subprocess.run(["ffmpeg", "-v", "quiet", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", "-b:a", "128k", p],
                           input=(x / peak * 0.9).astype(np.float32).tobytes(), check=True)
            print(p)
    cues = [(c["bar"], c["text"]) for c in song.mix["cues"] if str(c.get("beat", 1)) == "1"]
    meta = {"bar": song.bar, "bar1": song.t_render(1), "cues": cues, "dur": n / SR, "ctx": "-ctx",
            "title": "Беги от меня — клавиши нотами для GM-800",
            "sub": "Вся песня. Синтезаторные варианты сыграны простым синтом: здесь проверяются "
                   "<b>ноты и ритм</b>, не звук — звук подберём на GM-800. Переключение сохраняет место.",
            "tracks": [["1", "orig.mp3", "Оригинал", "стемы keys + strings", True],
                       ["2", "mine.mp3", "Мои ноты", "MIDI + правки по записи"],
                       ["3", "midi.mp3", "Как в MIDI", "MIDI без правок"],
                       ["4", "roma.mp3", "Рома, концерт 28.10", "сейчас в плейбеке; ориентир по типу звука", True]],
            "marks": [[1, "лид: добавлена нижняя октава"], [42, "свелл перед припевом (из стема)"],
                      [43, "удары: квинты октавой выше, другой ритм"], [76, "арп: одна фигура C# D# E G#"],
                      [92, "пэда нет (в MIDI есть)"], [100, "соло: без ударов (в MIDI есть)"],
                      [118, "бридж: G#sus4 → G#"], [128, "припев: пэда нет (в MIDI есть)"],
                      [148, "лид тише на 5 дБ"]],
            "html": HTML}
    tpl = open(os.path.join(REPO, "tools", "templates", "part-listen-full.html"), encoding="utf-8").read()
    open(os.path.join(PAGE, "index.html"), "w", encoding="utf-8").write(tpl.replace("/*META*/", json.dumps(meta, ensure_ascii=False)))
    print(os.path.join(PAGE, "index.html"))


if __name__ == "__main__":
    {"notes": cmd_notes, "fx": cmd_fx, "plan": cmd_plan, "preview": cmd_preview}[sys.argv[1]]()
