#!/usr/bin/env python3
"""«Беги от меня»: the keys (Moises keys + strings) written out as notes for the GM-800
(wiki/pipelines/part-transcription-guide.md; Alex 2026-11-20: «большая задача на снятие партии клавиш»,
notes and the part itself = the MIDI from the web, sound type / brightness = Roma's concert take,
original stems = reference; nothing played on the GM-800 yet: «пока gm 800 занят делай все что требуется
для записи»; then «всё в плейбек»: all voices go into the layer, none is played live).

  P="uv run -q --python 3.12 --with numpy --with scipy --with soundfile --with mido python"
  $P tools/jamzone/prep_begi_ot_menya.py notes     # MIDI + stem corrections -> parts/synths.notes.json
                                                   #   (+ the MIDI as it is -> analysis/.../synths-midi.notes.json)
  $P tools/jamzone/prep_begi_ot_menya.py fx        # the two reverse swells cut from the stems -> parts/pb-fx.wav
  $P tools/jamzone/prep_begi_ot_menya.py plan      # voices, bars, candidates: scenes (gmp take) and tones (gmp sweep)
  $P tools/jamzone/prep_begi_ot_menya.py rank      # after the takes: scenes and tones in one ranking against the stems
  $P tools/jamzone/prep_begi_ot_menya.py sound     # the page where Alex picks the sound: best takes of every voice
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
    "lead":      dict(tone=316, role="lead",  solo=(144, 148), cand=[316, 1024, 1092, 352, 350, 1073, 314, 349, 980, 315],
                      what="лид, верхняя октава (G#4 B4 E5 F#5→D#5)"),
    "lead_lo":   dict(tone=316, role="lead",  solo=(144, 148), cand=[], what="лид октавой ниже (в записи основная)"),
    "lead_echo": dict(tone=316, role="lead",  solo=(144, 148), cand=[], what="эхо лида, −10 дБ (или дилей тона)"),
    "whistle":   dict(tone=880, role="whistle", solo=(1, 5),   cand=[880, 881, 882, 883, 886, 223, 224, 957, 205, 213, 167],
                      what="«свист» восьмыми D#5 E5 D#5 E5 D#5 C#5 · C#5"),
    "stab":      dict(tone=1024, role="stab", solo=(43, 47),   cand=[1024, 316, 1092, 322, 314, 317, 1019, 352, 315],
                      what="удары припева квинтами, 1 · 2 · 2.75 · 3.5 · 4.25"),
    "arp":       dict(tone=350, role="pluck", solo=(76, 80),   cand=[350, 351, 1089, 1073, 1083, 1078, 354, 680, 676],
                      what="фигура шестнадцатыми C#4 D#4 E4 G#3"),
    "pad":       dict(tone=287, role="pad",   solo=(112, 116), cand=[287, 286, 284, 753, 1011, 275, 264, 285, 281],
                      what="пэд, аккорды по такту"),
}
# Scenes (presets) first, single ROM tones second (Alex 2026-11-20: «ты по одному тону собрался перебирать? кандидатов из
# пресетов нет?»). Picked from the contents of all 150 scenes of gear/gm-800/livesets/2026-11-17-v3.tsl (tones of every
# part); (scene, parts or None = the whole scene). Slot 50 + N = factory scene N. Scene 3 BEGI OT MENYA is Alex's own
# scene for this song (= factory SWEEP STRINGS at scene level 68): OB Bright Str + Voyager Pad + Aurora Pad.
# Only slots up to 128: gm800_part.py take loads a scene with bank 0, so slot 129+ comes out as slot N - 128 (first run
# 2026-11-20: 130 -> 2, 136 -> 8, 137 -> 9, 144 -> 16, 148 -> 20; those takes were thrown away). The tones of factory
# scenes 80, 86, 87, 94, 98 are in the single-tone lists instead (315, 286, 281, 167, 213, 223).
SCENES = {
    "lead":    [(76, [4]), (114, [2]), (28, [4]), (19, None), (84, None), (101, None), (79, None), (17, [1]), (121, None), (112, None)],
    "whistle": [(116, [3]), (83, None), (8, [1]), (80, [3])],
    "stab":    [(76, [4]), (114, [2]), (121, None), (60, None), (101, None), (23, [4]), (119, None)],
    "arp":     [(84, None), (112, [4]), (19, [2, 4]), (28, [3]), (25, [4]), (93, [4]), (105, None), (87, [1])],
    "pad":     [(3, None), (81, None), (70, None), (57, None), (16, None), (62, None), (91, None), (11, None)],
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
                      "has been played on the GM-800 or checked by ear yet (2026-11-20). Alex 2026-11-20: «всё в плейбек» - "
                      "all seven voices go into the layer, none is played live.",
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


def scene_table():
    """{slot: (name, [(part, tone number, tone name)] of the parts that are on)} from the liveset file (no GM-800)."""
    T = {}
    for r in open(os.path.join(REPO, "gear", "gm-800", "tones.tsv"), encoding="utf-8"):
        c = r.rstrip("\n").split("\t"); T[(int(c[2]), int(c[3]), int(c[4]))] = (int(c[0]), c[1].split("  ")[0])
    h = lambda x: int(x, 16); out = {}
    d = json.load(open(os.path.join(REPO, "gear", "gm-800", "livesets", "2026-11-17-v3.tsl")))
    for i, sc in enumerate(d["data"][0], 1):
        ps = sc["paramSet"]; parts = []
        for q in range(1, 5):
            t = ps[f"User_Scene%ToneSelect({q})"]
            if h(t[4]):
                parts.append((q, *T.get((h(t[0]), h(t[1]), h(t[2]) + 1), (0, "?"))))
        out[i] = ("".join(chr(h(x)) for x in ps["User_Scene%Common"][3:19]).strip(), parts)
    # slot 28 was changed on the unit after that export (2026-11-20, wiki/pipelines/gm-800.md): part 4 = 316 with a 1/8 delay
    out[28] = (out[28][0], [(1, 323, "Moving Reso Poly"), (2, 323, "Moving Reso Poly"), (3, 350, "Saw Seq"), (4, 316, "Trance Syn Poly + дилей 1/8")])
    return out


def cmd_plan():
    sh = shared(); part = json.load(open(PART, encoding="utf-8")); sct = scene_table()
    rows = {int(r.split("\t")[0]): r.split("\t")[1].split("  ")[0] for r in open(os.path.join(REPO, "gear", "gm-800", "tones.tsv"), encoding="utf-8")}
    rel = os.path.relpath(PART, REPO); n_sc = n_t = 0
    for vn, spec in VOICES.items():
        sp = " ".join(f"{a}-{b - 1}" for a, b in sh.spans(part["voices"][vn]["notes"]))
        print(f"\n{vn}: {spec['what']}; такты {sp}; пока тон {spec['tone']} {rows[spec['tone']]}")
        b0, b1 = spec["solo"]
        for scene, parts in SCENES.get(vn, []):
            nm, ps = sct[scene]; n_sc += 1
            what = " + ".join(f"{num} {tn}" for q, num, tn in ps if not parts or q in parts)
            print(f"   сцена {scene:3} {nm:16} {'партия ' + ','.join(map(str, parts)) if parts else 'вся':10} {what}")
        for scene, parts in SCENES.get(vn, []):
            print(f"   gmp take \"Беги от меня\" \"{rel}\" {vn} {scene}" + (f" --parts {','.join(map(str, parts))}" if parts else "")
                  + f" --bars {b0} {b1}")
        if spec["cand"]:
            n_t += len(spec["cand"])
            print("   тоны: " + ", ".join(f"{n} {rows[n]}" for n in spec["cand"]))
            both = "lead,lead_lo" if vn == "lead" else vn
            print(f"   gmp sweep \"Беги от меня\" \"{rel}\" {both} --bars {b0} {b1} "
                  f"--role {spec['role']} --tones {','.join(map(str, spec['cand']))}")
    print(f"\nвсего: {n_sc} дублей на сценах, {n_t} тонов; потом `prep_begi_ot_menya.py rank` — общий рейтинг сцен и тонов против стема")


def ranked(gp, song, part, sct, rows, vn):
    """[(score, spectrum, picture, octave, what, file)] of the kept takes of a voice, best first; + the stem of its bars."""
    import glob, re
    b0, b1 = VOICES[vn]["solo"]
    files = glob.glob(os.path.join(song.out, f"part-synths-{vn}-s*-{b0}-{b1}*.wav")) \
        + glob.glob(os.path.join(song.out, f"sweep-synths-{vn}*-{b0}-{b1}-t*.wav"))
    dur = (b1 - b0) * song.bar + 1.0
    ref = sum(song.read(f"{st}.wav", song.t_stem(b0), song.t_stem(b0) + dur) for st in part["stems"]).mean(1)
    R = gp.cqt_db(ref); out = []
    for f in files:
        x = gp.gmm.read_wav(f).mean(1)[:len(ref)]
        sc, spc, tf, o = gp.sweep_score(R, gp.cqt_db(x), song.semi); nm = os.path.basename(f)
        m = re.search(r"-s(\d+)-(all|p\d+)-", nm); t = re.search(r"-t(\d+)\.wav$", nm)
        what = (f"сцена {int(m[1])} {sct[int(m[1])][0]}" + ("" if m[2] == "all" else " · партия " + ",".join(m[2][1:])) if m
                else f"тон {int(t[1])} {rows[int(t[1])]}")
        out.append((sc, spc, tf, o, what, f))
    return sorted(out, reverse=True), ref


def cmd_rank():
    """Scene takes (gmp take) and tone takes (gmp sweep) of every voice in one ranking against the stems of its solo
    bars (gm800_part.sweep_score: mean spectrum + time-frequency picture). No GM-800: reads the kept takes."""
    gp, song = song_obj(); part = json.load(open(PART, encoding="utf-8")); sct = scene_table()
    rows = {int(r.split("\t")[0]): r.split("\t")[1].split("  ")[0] for r in open(os.path.join(REPO, "gear", "gm-800", "tones.tsv"), encoding="utf-8")}
    for vn, spec in VOICES.items():
        out, _ = ranked(gp, song, part, sct, rows, vn)
        if out:
            print(f"\n{vn}, такты {spec['solo'][0]}-{spec['solo'][1] - 1}:")
            for sc, spc, tf, o, what, f in out:
                print(f"  {sc:.3f}  спектр {spc:.3f}  картина {tf:.3f}  окт {o:+d}  {what}")


SOUND_TOP = 7                              # candidates a voice on the page
SOUND_KEEP = {"pad": ["-s003-"]}           # always on the page: Alex's own scene of this song
SOUND_TITLE = {"lead": "Лид (такты 144–147: в оригинале лид + пэд)", "whistle": "Свист (такты 1–4: в оригинале свист + лид + пэд)",
               "stab": "Удары припева (такты 43–46: в оригинале удары + свист)", "arp": "Арп (такты 76–79: в оригинале один)",
               "pad": "Пэд (такты 112–115: в оригинале пэд + арп)"}


def cmd_sound():
    """The page where Alex picks the sound: per voice the stem of its bars and the best takes (scenes and tones in one
    ranking), all at the stem's loudness, all the same length, in sync (tools/templates/part-listen-page.example.html)."""
    import re
    gp, song = song_obj(); part = json.load(open(PART, encoding="utf-8")); sct = scene_table(); gmm = gp.gmm
    rows = {int(r.split("\t")[0]): r.split("\t")[1].split("  ")[0] for r in open(os.path.join(REPO, "gear", "gm-800", "tones.tsv"), encoding="utf-8")}
    os.makedirs(PAGE, exist_ok=True); n = int((4 * song.bar + 1.0) * gmm.SR); T = []; groups = []
    keys = list("1234567890QWERTYUIOPASDFGHJKLZXCVBNM") + [""] * 60; k = 0

    def mp3(name, x):
        x = np.asarray(x, dtype=np.float32); x = x if x.ndim == 2 else np.stack([x, x], 1)
        x = np.vstack([x, np.zeros((max(0, n - len(x)), 2), np.float32)])[:n]
        subprocess.run(["ffmpeg", "-v", "quiet", "-y", "-f", "f32le", "-ar", str(gmm.SR), "-ac", "2", "-i", "-", "-b:a", "160k",
                        os.path.join(PAGE, name)], input=x.tobytes(), check=True)

    for vn in ("lead", "whistle", "stab", "arp", "pad"):
        out, _ = ranked(gp, song, part, sct, rows, vn)
        if not out:
            continue
        b0, b1 = VOICES[vn]["solo"]
        ref = sum(song.read(f"{st}.wav", song.t_stem(b0), song.t_stem(b0) + n / gmm.SR) for st in part["stems"])
        L = gmm.lufs(ref); gid = "g-" + vn; groups.append(f'<h2>{SOUND_TITLE[vn]}</h2>\n<div class="grid" id="{gid}"></div>')
        mp3(f"snd-{vn}-00-stem.mp3", ref); T.append([gid, keys[k], f"snd-{vn}-00-stem.mp3", "Оригинал", "стемы keys + strings", True]); k += 1
        pick = out[:SOUND_TOP] + [r for r in out[SOUND_TOP:] if any(t in os.path.basename(r[5]) for t in SOUND_KEEP.get(vn, []))]
        for i, (sc, spc, tf, o, what, f) in enumerate(pick, 1):
            x = gmm.read_wav(f); x = x * 10 ** ((L - gmm.lufs(x)) / 20)
            fn = f"snd-{vn}-{i:02d}.mp3"; mp3(fn, x)
            m = re.search(r"-s(\d+)-(all|p\d+)-", os.path.basename(f))
            tones = " + ".join(f"{num} {tn}" for q, num, tn in sct[int(m[1])][1] if m[2] == "all" or str(q) in m[2][1:]) if m else "отдельный тон, сухой"
            T.append([gid, keys[k], fn, what, f"{tones} · сходство {sc:.2f}", False]); k += 1
            print(f"  {vn:8} {i}. {sc:.3f} {what}  [{tones}]")
    tpl = open(os.path.join(REPO, "tools", "templates", "part-listen-page.example.html"), encoding="utf-8").read()
    head, rest = tpl.split("<main>", 1); body, tail = rest.split("</main>", 1); script = tail[tail.index("<script>"):]
    bar_html = tail[:tail.index("<script>")]
    bar_html = re.sub(r'<i style="left:[\d.]+%"></i>', "", bar_html)
    marks = "".join(f'<i style="left:{100 * q * song.bar / (n / gmm.SR):.1f}%"></i>' for q in (1, 2, 3, 4))
    bar_html = bar_html.replace('<div id="fill"></div>', '<div id="fill"></div>' + marks)
    script = re.sub(r"const BAR = [^;]+;", f"const BAR = {song.bar};", script)
    script = re.sub(r"const T = \[.*?\n\];", "const T = " + json.dumps(T, ensure_ascii=False) + ";", script, flags=re.S)
    script = re.sub(r"const KEYCODE = \{[^}]*\};", "const KEYCODE = {" + ", ".join(f'{c}: "Key{c}"' for c in "QWERTYUIOPASDFGHJKLZXCVBNM") + "};", script)
    main = ("<main>\n  <h1>Беги от меня — выбор звука</h1>\n  <p class=\"sub\">Четыре такта на голос, всё на одной громкости, играет по кругу; "
            "переключение идёт с того же места. В каждой группе оригинал и лучшие кандидаты — сцены и отдельные тоны в одном "
            "рейтинге (сходство с оригиналом: спектр и рисунок во времени). Цифры — только подсказка, выбираешь ты. "
            "<kbd>пробел</kbd> пауза, клавиши на кнопках.</p>\n" + "\n".join(groups) + "\n</main>")
    head = head.replace("<title>Прослушивание партии</title>", "<title>Беги от меня — выбор звука</title>")
    head = re.sub(r"<title>.*?</title>", "<title>Беги от меня — выбор звука</title>", head, flags=re.S)
    open(os.path.join(PAGE, "sound.html"), "w", encoding="utf-8").write(head + main + bar_html + script)
    print(os.path.join(PAGE, "sound.html"))


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
<p class="q">Не выписано: тонкая высокая линия струнных в 92–99 (B4 / C#5, очень тихо). Все семь голосов идут в плейбек
(твоё решение 2026-11-20), живых среди них нет.</p>
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
    {"notes": cmd_notes, "fx": cmd_fx, "plan": cmd_plan, "rank": cmd_rank, "sound": cmd_sound, "preview": cmd_preview}[sys.argv[1]]()
