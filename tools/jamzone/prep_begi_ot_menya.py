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
  $P tools/jamzone/prep_begi_ot_menya.py round2    # second round: the picked plugin tones rendered clean + the asked variants
  $P tools/jamzone/prep_begi_ot_menya.py round3    # the lead on a short list of tones, clean, with the approved 1/8 repeat
  $P tools/jamzone/prep_begi_ot_menya.py zenpicks  # after `zenology_render.py sweep` of every voice: his GM-800 choice as the
                                                   #   first take of each ZENOLOGY ranking (then `zenology_render.py page`)
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


# What Alex chose on the GM-800 page (2026-11-21): lead «2», whistle «0 но звучит не так мягко и сглажено», stab «0»
# (no such key in that group: read as the letter O = scene 60 - NOT confirmed by him), arp «X но не хватает обработки
# какой то тоже чтобы сглаженнее звучало», pad «сцена 3 BEGI OT MENYA». Then: «перезапусти подбор звука на ZENOLOGY».
PICKS = {"lead":    ("part-synths-lead-s084-all-144-148.wav", "сцена 84 SYNTH PLEDGE"),
         "whistle": ("sweep-synths-whistle-1-5-t0886.wav", "тон 886 Sine Lead"),
         "stab":    ("part-synths-stab-s060-all-43-47.wav", "сцена 60 JP POLY SYNTH"),
         "arp":     ("sweep-synths-arp-76-80-t0680.wav", "тон 680 TB Bass 2"),
         "pad":     ("part-synths-pad-s003-all-112-116.wav", "сцена 3 BEGI OT MENYA")}


# The two picks Alex found too raw, as the SAME tone out of the plugin (PRST_F Essential carries the GM-800's second
# tone bank under the same names: 477 Sine Lead = GM 886, 271 TB Bass 2 = GM 680; scores match within 0.01) with
# processing on the take (pedalboard). (label, [(effect, {parameters})]); delay times in bars.
ZEN_FX = {
    "whistle": ("PRST_F Essential/477", [
        ("Sine Lead мягче: фильтр 3 кГц + реверб", [("LowpassFilter", {"cutoff_frequency_hz": 3000}), ("Reverb", {"room_size": 0.5, "wet_level": 0.22, "dry_level": 0.8})]),
        ("Sine Lead ещё мягче: фильтр 1.8 кГц + хорус + реверб", [("LowpassFilter", {"cutoff_frequency_hz": 1800}), ("Chorus", {"rate_hz": 0.8, "depth": 0.2, "mix": 0.3}),
                                                                 ("Reverb", {"room_size": 0.65, "wet_level": 0.3, "dry_level": 0.75})])]),
    "arp": ("PRST_F Essential/271", [
        ("TB Bass 2 с обработкой: фильтр 2.5 кГц + дилей 1/8 + реверб", [("LowpassFilter", {"cutoff_frequency_hz": 2500}), ("Delay", {"delay_bars": 1 / 8, "feedback": 0.3, "mix": 0.22}),
                                                                        ("Reverb", {"room_size": 0.45, "wet_level": 0.18, "dry_level": 0.85})]),
        ("TB Bass 2 глубже: фильтр 1.5 кГц + дилей 3/16 + реверб", [("LowpassFilter", {"cutoff_frequency_hz": 1500}), ("Delay", {"delay_bars": 3 / 16, "feedback": 0.35, "mix": 0.3}),
                                                                   ("Reverb", {"room_size": 0.6, "wet_level": 0.28, "dry_level": 0.8})])]),
}


def zen_fx(song, zen, vn, rk, ref, gp):
    """The processed variants of ZEN_FX[vn] as takes right after the GM-800 pick (needs pedalboard: run in the zr env)."""
    import pedalboard, re, soundfile as sf
    tag, variants = ZEN_FX[vn]; b0, b1 = VOICES[vn]["solo"]; dry = os.path.join(zen, f"fxsrc-{vn}.wav")
    subprocess.run([sys.executable, os.path.join(REPO, "tools", "zenology_render.py"), "render", tag, "Беги от меня", PART, vn, str(b0), str(b1), dry],
                   check=True, capture_output=True)
    x, sr = sf.read(dry, always_2d=True, dtype="float32"); rk["top"] = [t for t in rk["top"] if not t.get("fx")]; new = []
    for i, (label, chain) in enumerate(variants, 1):
        fx = []
        for nm, kw in chain:
            kw = dict(kw)
            if "delay_bars" in kw:
                kw["delay_seconds"] = kw.pop("delay_bars") * song.bar
            fx.append(getattr(pedalboard, nm)(**kw))
        y = pedalboard.Pedalboard(fx)(x.T, sr).T; fn = f"zen-synths-{vn}-{b0}-{b1}-fx{i}.wav"; sf.write(os.path.join(zen, fn), y, sr, subtype="PCM_16")
        sc = gp.sweep_score(gp.cqt_db(ref), gp.cqt_db(y.mean(1)[:len(ref)]), song.semi)[0]
        bank, num = tag.split("/")
        new.append({"bank": bank, "number": num, "name": label, "category": "тон плагина + обработка", "score": round(sc, 3), "oct": 0, "file": fn, "fx": True, "tone": tag})
        print(f"   {label}: {sc:.3f}")
    rk["top"] = rk["top"][:1] + new + rk["top"][1:]


def cmd_zenpicks():
    """Alex's GM-800 choice of every voice as the first take of that voice's ZENOLOGY sweep (tools/zenology_render.py
    sweep), so `zenology_render.py page` plays it next to the plugin's tones. Run after the sweeps, before `page`."""
    import shutil
    gp, song = song_obj(); part = json.load(open(PART, encoding="utf-8")); zen = os.path.join(song.out, "zenology")
    for vn, (fn, what) in PICKS.items():
        b0, b1 = VOICES[vn]["solo"]; jf = os.path.join(zen, f"zen-synths-{vn}-{b0}-{b1}.json")
        if not os.path.exists(jf):
            print(f"{vn}: no ZENOLOGY sweep yet"); continue
        dur = (b1 - b0) * song.bar + 1.0
        ref = sum(song.read(f"{st}.wav", song.t_stem(b0), song.t_stem(b0) + dur) for st in part["stems"]).mean(1)
        x = gp.gmm.read_wav(os.path.join(song.out, fn)).mean(1)[:len(ref)]
        sc = gp.sweep_score(gp.cqt_db(ref), gp.cqt_db(x), song.semi)[0]
        shutil.copyfile(os.path.join(song.out, fn), os.path.join(zen, "gm800-" + fn))
        rk = json.load(open(jf, encoding="utf-8"))
        rk["top"] = [{"bank": "GM-800", "number": "", "name": what + " — выбрано на приборе", "category": "прибор", "score": round(sc, 3),
                      "oct": 0, "file": "gm800-" + fn, "gm": True}] + [t for t in rk["top"] if not t.get("gm")]
        if vn in ZEN_FX:
            zen_fx(song, zen, vn, rk, ref, gp)
        json.dump(rk, open(jf, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"{vn}: {what} ({sc:.3f}) first of {len(rk['top'])}; best ZENOLOGY: " + ", ".join(f"{t['name']} {t['score']:.2f}" for t in rk["top"][1:4]))


# ---- round 2 on ZENOLOGY: clean renders ------------------------------------------------------------------------
# Measured 2026-11-21: `zenology_render.py sweep` swaps tone states inside one plugin instance (reset=False), and a take
# then carries what the tones loaded before it left behind - echoes, reverb tails, sometimes dropped notes (Margherita
# Pizz: bar by 16ths -2 -12 -19 in the sweep take, -1 -18 -38 on its own; the 1/8 echo of the «Wheel of Chaos» take is
# not in that tone at all). A render in a process of its own with reset=True (10 s a call) is the same every time. So the
# sweep is a rough short list, and whatever Alex picks is rendered again here, clean, before it goes anywhere.
# And a single render can still have holes (the «Солнышко» session saw them too, same day): it is the first take after
# the load that loses notes, see zen_take.
# What he picked on the ZENOLOGY page (2026-11-21): lead «Margherita Pizz, НО нужен эффект как на Wheel of Chaos который
# вызывает чувство быстрого повторения нажатой ноты»; whistle «Porta Sine Lead но ... в оригинале вообще нет ощущения
# нажатия ноты ("молоточка") между нотами»; stab «Scented»; arp «TB Bass 2 глубже: фильтр 1.5 кГц + дилей 3/16 + реверб»;
# pad «Soft Storm Pad».
ZEN = {"lead": "PRST_I Sun Gate/62", "whistle": "PRST_F Essential/478", "stab": "PRST_J Nebulous Forms/31",
       "arp": "PRST_F Essential/271", "pad": "PRST_L Essential 2/207"}
ZEN_TAKE = {"lead": "zen-synths-lead-144-148-PRST_I_Sun_Gate-0062.wav", "whistle": "zen-synths-whistle-1-5-PRST_F_Essential-0478.wav",
            "stab": "zen-synths-stab-43-47-PRST_J_Nebulous_Forms-0031.wav", "arp": "zen-synths-arp-76-80-fx2.wav",
            "pad": "zen-synths-pad-112-116-PRST_L_Essential_2-0207.wav"}
WOC_TAKE = "zen-synths-lead-144-148-PRST_K_Volatile_Memories-0043.wav"
ARP_FX = ZEN_FX["arp"][1][1][1]                       # the chain of «TB Bass 2 глубже»


def cmd_zenrender():
    """_zenrender TAG VOICE[,VOICE] B0 B1 OUT [GAP]: the voices together on a plugin tone, clean (a process of its own,
    reset=True), note gains of the first voice applied. Called by round2 / zenlayer; needs the zr environment."""
    import soundfile as sf
    from mido import Message
    tag, voices, b0, b1, out = sys.argv[2], sys.argv[3].split(","), float(sys.argv[4]), float(sys.argv[5]), sys.argv[6]
    load = lambda nm: (lambda sp: (lambda m: (sp.loader.exec_module(m), m)[1])(importlib.util.module_from_spec(sp)))(
        importlib.util.spec_from_file_location(nm, os.path.join(REPO, "tools", nm + ".py")))
    zr = load("zenology_render"); gp, song = zr.gp_song("Беги от меня"); part = json.load(open(PART, encoding="utf-8"))
    if len(sys.argv) > 7:
        for vn in voices:
            part["voices"][vn]["gap"] = float(sys.argv[7])
    b0, b1 = (int(b0) if b0 == int(b0) else b0), (int(b1) if b1 == int(b1) else b1)
    line = sorted(sum((gp.voice_line(song, part, vn, b0, b1) for vn in voices), []))
    ev = sorted([Message("note_on", note=n, velocity=100, time=t) for t, n, d in line] + [Message("note_off", note=n, time=t + d) for t, n, d in line],
                key=lambda m: (m.time, m.type == "note_on"))
    x, dev, k = zen_take(zr, zr.plugin(tag), ev, (b1 - b0) * song.bar + 3.0)        # fresh instance, warm-up, two takes that agree
    x = gp.apply_gains(x, gp.voice_gains(song, part, voices[0], b0, b1), zr.SR)
    sf.write(out, x, zr.SR, subtype="FLOAT")
    print(out, f"{len(line)} notes, peak {20 * np.log10(np.abs(x).max() + 1e-9):.1f} dBFS; takes agree within {dev:.1f} dB ({k} played)"
          + ("  <-- NOT CLEAN" if dev > 4 else ""))


def zen_take(zr, pl, ev, dur):
    """A take that can be trusted (measured 2026-11-21, tone D/891, 15 s takes): the FIRST take after the plugin and
    its tone are loaded loses notes when the machine is busy (whole notes at -156 dB in 2 of 4 parallel processes; the
    tone is still being set up in the background while the offline render already runs), every later take of the same
    instance is the same within 1 dB (14 of 14, alone or four at once). So: reset once on silence, one warm-up take
    thrown away, then two takes that must agree (level by 100 ms, loud steps, 4 dB), a third one if they do not.
    -> (take, worst disagreement dB, takes played)"""
    w = int(0.1 * zr.SR); env = lambda x: 10 * np.log10((x.mean(1)[:len(x) // w * w].reshape(-1, w) ** 2).mean(1) + 1e-10)
    play = lambda: (pl([], duration=2.0, sample_rate=zr.SR, reset=False), pl(ev, duration=dur, sample_rate=zr.SR, reset=False).T.astype(np.float32))[1]
    pl([], duration=0.5, sample_rate=zr.SR, reset=True); play()
    takes = [play(), play()]
    def far(a, b):
        ea, eb = env(a), env(b); on = np.maximum(ea, eb) > max(ea.max(), eb.max()) - 30
        return float(np.abs(ea - eb)[on].max()) if on.any() else 0.0
    d = far(*takes)
    if d > 4:
        takes.append(play()); pairs = [(far(takes[i], takes[j]), i) for i in range(3) for j in range(3) if i < j]; d, i = min(pairs)
        return takes[i], d, 4
    return takes[0], d, 3


def cmd_zenmany():
    """_zenmany OUTDIR VOICE[,VOICE] B0 B1 TRANSPOSE TAG...: the voices on every tone, one after another in one plugin
    instance, each with reset=True (a full re-initialisation: nothing of the tone before it, and note levels that
    repeat - with reset=False some tones, Margherita Pizz for one, play every note at a random level, 10-20 dB apart).
    One wav a tone in OUTDIR, named by the tone."""
    import re, soundfile as sf
    from mido import Message
    out, voices, b0, b1, tr, tags = sys.argv[2], sys.argv[3].split(","), int(sys.argv[4]), int(sys.argv[5]), int(sys.argv[6]), sys.argv[7:]
    load = lambda nm: (lambda sp: (lambda m: (sp.loader.exec_module(m), m)[1])(importlib.util.module_from_spec(sp)))(
        importlib.util.spec_from_file_location(nm, os.path.join(REPO, "tools", nm + ".py")))
    zr = load("zenology_render"); gp, song = zr.gp_song("Беги от меня"); part = json.load(open(PART, encoding="utf-8"))
    line = sorted(sum((gp.voice_line(song, part, vn, b0, b1) for vn in voices), []))
    ev = sorted([Message("note_on", note=n + tr, velocity=100, time=t) for t, n, d in line] + [Message("note_off", note=n + tr, time=t + d) for t, n, d in line],
                key=lambda m: (m.time, m.type == "note_on"))
    pl = zr.plugin(tags[0]) if len(tags) == 1 else zr.plugin(); os.makedirs(out, exist_ok=True)
    for tag in tags:
        if len(tags) > 1:
            pl.raw_state = zr.tone_state(tag)[0]          # several tones in one instance: for a rough ranking only
        x, d, k = zen_take(zr, pl, ev, (b1 - b0) * song.bar + 3.0)
        x = gp.apply_gains(x, gp.voice_gains(song, part, voices[0], b0, b1), zr.SR)
        fn = os.path.join(out, re.sub(r"[^A-Za-z0-9]+", "_", tag).strip("_") + (f"_tr{tr:+d}" if tr else "") + ".wav")
        sf.write(fn, x, zr.SR, subtype="FLOAT"); print(tag, f"peak {20 * np.log10(np.abs(x).max() + 1e-9):.1f} dBFS; takes agree within {d:.1f} dB ({k} played)", flush=True)


def zen_many(out, voices, b0, b1, tags, tr=0, jobs=8, single=False):
    """Takes of many tones, `jobs` processes side by side; single = a process of its own for every tone (the only way
    that does not lose notes: tones swapped inside one instance do, reset=True or not). -> {tag: wav path}"""
    import re
    path = lambda t: os.path.join(out, re.sub(r"[^A-Za-z0-9]+", "_", t).strip("_") + (f"_tr{tr:+d}" if tr else "") + ".wav")
    todo = [t for t in tags if not os.path.exists(path(t))]
    lots = [[t] for t in todo] if single else [todo[k::jobs] for k in range(jobs) if todo[k::jobs]]
    for i in range(0, len(lots), jobs):
        procs = [subprocess.Popen([sys.executable, os.path.abspath(__file__), "_zenmany", out, voices, str(b0), str(b1), str(tr)] + lot,
                                  stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True) for lot in lots[i:i + jobs]]
        for pr in procs:
            err = pr.communicate()[1]
            if pr.returncode:
                raise SystemExit(err[-2000:])
    return {t: path(t) for t in tags}


def zen_best(out, voices, b0, b1, tags, cells, bar, tr=0, plays=2):
    """Every tone `plays` times, each in a process of its own; kept: the take whose note levels (16th cells that carry a
    note) sit closest to the median of the plays. -> {tag: (wav path, worst distance of a note of the kept take from the
    median dB, spread of the plays dB)}"""
    import soundfile as sf
    k16 = int(bar / 16 * 48000); res = {}
    lev = lambda f: (lambda x: np.array([20 * np.log10(np.sqrt((x[c * k16:(c + 1) * k16] ** 2).mean()) + 1e-9) for c in cells]))(sf.read(f, always_2d=True)[0].mean(1))
    files = [zen_many(os.path.join(out, f"play{j + 1}"), voices, b0, b1, tags, tr, single=True) for j in range(plays)]
    for t in tags:
        L = np.array([np.maximum(np.nan_to_num(lev(fs[t]), nan=-180.0, posinf=20.0, neginf=-180.0), -120) for fs in files]); med = np.median(L, 0)
        dev = np.abs(L - med).max(1); j = int(dev.argmin()); res[t] = (files[j][t], float(dev[j]), float(dev.max()))
    return res


def zen_clean(tag, voices, b0, b1, out, gap=None):
    if not os.path.exists(out):
        r = subprocess.run([sys.executable, os.path.abspath(__file__), "_zenrender", tag, voices, str(b0), str(b1), out] + ([str(gap)] if gap is not None else []),
                           capture_output=True, text=True)
        if r.returncode:
            raise SystemExit(r.stderr[-2000:])
        print("  " + r.stdout.strip().splitlines()[-1][-110:], flush=True)
    import soundfile as sf
    return sf.read(out, always_2d=True, dtype="float32")[0]


def fx(x, chain, bar, sr=48000):
    import pedalboard
    units = []
    for nm, kw in chain:
        kw = dict(kw)
        if "delay_bars" in kw:
            kw["delay_seconds"] = kw.pop("delay_bars") * bar
        units.append(getattr(pedalboard, nm)(**kw))
    return pedalboard.Pedalboard(units)(x.T, sr).T


def cmd_round2():
    """Second listening round on clean renders -> analysis/.../zenology/page/round2.html: per voice the original, the take
    Alex chose (as he heard it), the same tone clean, and the variants he asked for (lead: the repeat; whistle: legato)."""
    import soundfile as sf
    from scipy.signal import resample_poly
    gp, song = song_obj(); part = json.load(open(PART, encoding="utf-8")); zen = os.path.join(song.out, "zenology")
    r2 = os.path.join(zen, "round2"); page = os.path.join(zen, "page"); os.makedirs(r2, exist_ok=True); os.makedirs(page, exist_ok=True)
    bar = song.bar; cos = lambda A, B: float((A[:, :min(A.shape[1], B.shape[1])] * B[:, :min(A.shape[1], B.shape[1])]).sum()
                                             / (np.linalg.norm(A[:, :min(A.shape[1], B.shape[1])]) * np.linalg.norm(B[:, :min(A.shape[1], B.shape[1])]) + 1e-9))
    pic = lambda x: gp.cqt_db(x.mean(1) if x.ndim == 2 else x)
    rev = lambda room, wet: ("Reverb", {"room_size": room, "wet_level": wet, "dry_level": 1 - wet * 0.6})
    dly = lambda bars, fb, mix: ("Delay", {"delay_bars": bars, "feedback": fb, "mix": mix})

    def like(x, take):
        """Reverb + 1/8 delay on a clean render that brings it closest to a sweep take (what Alex heard)."""
        T = pic(take); best = (cos(T, pic(x)), None)
        for room in (0.3, 0.5, 0.7):
            for wet in (0.08, 0.16, 0.25):
                for mix in (0.0, 0.1, 0.18):
                    ch = [rev(room, wet)] + ([dly(1 / 8, 0.3, mix)] if mix else [])
                    c = cos(T, pic(fx(x, ch, bar)))
                    if c > best[0]:
                        best = (c, ch)
        return best

    groups = []; rd = lambda f: sf.read(os.path.join(zen, f), always_2d=True, dtype="float32")[0]; report = {}
    for vn in ("lead", "whistle", "stab", "arp", "pad"):
        b0, b1 = VOICES[vn]["solo"]; n = int(round((b1 - b0) * bar * 44100)); tag = ZEN[vn]; clips = []
        orig = sum(resample_poly(song.read(f"{st}.wav", song.t_stem(b0), song.t_stem(b0) + (b1 - b0) * bar + 0.2).mean(1), 147, 160) for st in part["stems"])
        add = lambda nm, note, x, ref=False: clips.append((nm, note, np.asarray(x), ref))
        add("Оригинал", "стемы keys + strings", orig, True)
        take = rd(ZEN_TAKE[vn]); voices = "lead,lead_lo" if vn == "lead" else vn
        clean = zen_clean(tag, voices, b0, b1, os.path.join(r2, f"{vn}-clean.wav")); c0 = cos(pic(take), pic(clean)); report[vn] = [round(c0, 2)]
        name = tag.split("/")[0].split()[0] + "/" + tag.split("/")[1]
        if vn == "arp":
            add("TB Bass 2 глубже — как ты выбрал", "файл со страницы", take)
            add("TB Bass 2 глубже — чистый рендер", f"{name} + фильтр 1.5 кГц + дилей 3/16 + реверб; так будет в слое", fx(clean, ARP_FX, bar))
        else:
            add(f"{'Margherita Pizz' if vn == 'lead' else 'Porta Sine Lead' if vn == 'whistle' else 'Scented' if vn == 'stab' else 'Soft Storm Pad'} — как ты слышал",
                "дубль из перебора: в нём хвосты от чужих тонов, точно так не повторить", take)
            add("Тот же тон, чистый рендер", f"{name} как он есть; близость к дублю {c0:.2f}", clean)
        if vn in ("lead", "stab"):
            c, ch = like(clean, take); report[vn].append(round(c, 2))
            if ch:
                what = " + ".join(f"реверб {k['room_size']:.1f}/{k['wet_level']:.2f}" if u == "Reverb" else f"дилей 1/8 {k['mix']:.2f}" for u, k in ch)
                add("Чистый + хвост, как в дубле", f"{what}; близость к дублю {c:.2f}", fx(clean, ch, bar)); report[vn].append(what)
        if vn == "lead":
            woc = rd(WOC_TAKE); add("Wheel of Chaos — дубль из перебора", "эффект, который ты назвал: это эхо в 1/8 такта на −12 дБ, в самом тоне его нет", woc)
            for nm, note, ch in (("Margherita + повтор 1/8", "дилей 1/8 такта, −12 дБ, обратная связь 0.4 — как в том дубле", [dly(1 / 8, 0.4, 0.25), rev(0.3, 0.08)]),
                                 ("Margherita + повтор 1/8, плотнее", "дилей 1/8, обратная связь 0.55, громче", [dly(1 / 8, 0.55, 0.33), rev(0.3, 0.08)]),
                                 ("Margherita + повтор 1/16", "дилей 1/16 такта: повтор вдвое быстрее", [dly(1 / 16, 0.5, 0.3), rev(0.3, 0.08)]),
                                 ("Margherita + повтор 3/16", "дилей 3/16 такта: повторы попадают между нотами", [dly(3 / 16, 0.45, 0.28), rev(0.3, 0.08)])):
                add(nm, note, fx(clean, ch, bar))
            echo = zen_clean(tag, "lead_echo", b0, b1, os.path.join(r2, "lead-echo.wav"))
            add("Margherita + повтор нотами", "повторы сыграны нотами, как в MIDI (−10 дБ), без дилея", fx(clean + echo[:len(clean)], [rev(0.3, 0.08)], bar))
        if vn == "whistle":
            leg = zen_clean(tag, vn, b0, b1, os.path.join(r2, "whistle-legato.wav"), gap=-0.04)
            add("Porta Sine Lead легато", "ноты внахлёст: новая нота без атаки, подъезд по высоте", leg)
            add("Легато + мягче", "ноты внахлёст + фильтр 2.5 кГц + реверб", fx(leg, [("LowpassFilter", {"cutoff_frequency_hz": 2500}), rev(0.5, 0.2)], bar))
            sine = zen_clean("PRST_F Essential/477", vn, b0, b1, os.path.join(r2, "whistle-sine-legato.wav"), gap=-0.04)
            add("Sine Lead легато + мягче", "F/477 (твой первый выбор) внахлёст + фильтр 2.5 кГц + реверб", fx(sine, [("LowpassFilter", {"cutoff_frequency_hz": 2500}), rev(0.5, 0.2)], bar))
        # one loudness, one length, 44.1 kHz
        rms = lambda v: np.sqrt((v ** 2).mean()) + 1e-9; out = []; fitted = []
        for nm, note, x, ref in clips:
            y = x if ref else resample_poly(x.mean(1) if x.ndim == 2 else x, 147, 160)
            y = np.pad(y, (0, max(0, n - len(y))))[:n]; fitted.append(y if ref else y * rms(clips[0][2][:n]) / rms(y))
        peak = max(np.abs(y).max() for y in fitted)
        for k, ((nm, note, x, ref), y) in enumerate(zip(clips, fitted)):
            y = y / peak * 0.8; f = int(0.008 * 44100); y[:f] *= np.linspace(0, 1, f); y[-f:] *= np.linspace(1, 0, f)
            fn = f"r2-{vn}-{k:02d}.wav"; sf.write(os.path.join(page, fn), y.astype(np.float32), 44100, subtype="PCM_16"); out.append([fn, nm, note, ref])
        groups.append({"name": f"{SOUND_TITLE[vn].split(' (')[0]}, такты {b0}–{b1 - 1}", "note": "по кругу, одна громкость", "clips": out})
        print(vn, report[vn], [c[0] for c in clips])
    meta = {"title": "Беги от меня — второй круг, чистые рендеры", "groups": groups,
            "sub": "Дубли быстрого перебора несли хвосты и эхо от тонов, загруженных перед ними. Здесь каждый выбранный тон отрендерен "
                   "заново и чисто: так он будет звучать в слое. <kbd>←</kbd> <kbd>→</kbd> соседний вариант, <kbd>пробел</kbd> пауза."}
    tpl = open(os.path.join(REPO, "tools", "templates", "part-tone-pick.html"), encoding="utf-8").read()
    open(os.path.join(page, "round2.html"), "w", encoding="utf-8").write(tpl.replace("/*META*/", json.dumps(meta, ensure_ascii=False)))
    print(os.path.join(page, "round2.html"))


# ---- round 3: the lead's tone -------------------------------------------------------------------------------------
# Alex on round 2 (2026-11-21): «Margherita + повтор 1/8 хорошо но надо теперь поискать тон, этот сильно сухой
# относительно оригинала не хватает чего то»; whistle «Легато + мягче»; stab «Scented — как ты слышал»; «ост ок».
LEAD_REPEAT = [("Delay", {"delay_bars": 1 / 8, "feedback": 0.4, "mix": 0.25}), ("Reverb", {"room_size": 0.3, "wet_level": 0.08, "dry_level": 0.95})]
LEAD_NAMES = r"(?i)trance|pluck|pizz|supersaw|super saw|s-saw|saws|dance|rave|house"
WHISTLE_FX = [("LowpassFilter", {"cutoff_frequency_hz": 2500}), ("Reverb", {"room_size": 0.5, "wet_level": 0.2, "dry_level": 0.88})]
WHISTLE_GAP = -0.04


def like_take(x, take, bar, gp):
    """Reverb + delay on a clean take that bring it closest to a sweep take Alex chose by ear (time x frequency picture).
    -> (cosine, chain, cosine of the clean take)"""
    pic = lambda v: gp.cqt_db(v.mean(1) if v.ndim == 2 else v); T = pic(take)
    def cos(B):
        n = min(T.shape[1], B.shape[1]); return float((T[:, :n] * B[:, :n]).sum() / (np.linalg.norm(T[:, :n]) * np.linalg.norm(B[:, :n]) + 1e-9))
    c0 = cos(pic(x)); best = (c0, [])
    for room in (0.5, 0.7, 0.9):
        for wet in (0.12, 0.2, 0.3):
            for bars, mix in ((0, 0), (1 / 8, 0.12), (1 / 8, 0.2), (3 / 16, 0.12), (3 / 16, 0.2)):
                ch = ([("Delay", {"delay_bars": bars, "feedback": 0.35, "mix": mix})] if mix else []) + [("Reverb", {"room_size": room, "wet_level": wet, "dry_level": 1 - wet * 0.6})]
                c = cos(pic(fx(x, ch, bar)))
                if c > best[0]:
                    best = (c, ch)
    return best[0], best[1], c0


def cmd_round3():
    """The lead on a short list of plugin tones, every take clean (reset=True) and with the 1/8 repeat Alex approved,
    ranked against the original -> zenology/page/round3.html. Short list = the top of the (rough) sweep ranking +
    tones with trance / pluck / saw names."""
    import re, soundfile as sf
    from scipy.signal import resample_poly
    load = lambda nm: (lambda sp: (lambda m: (sp.loader.exec_module(m), m)[1])(importlib.util.module_from_spec(sp)))(
        importlib.util.spec_from_file_location(nm, os.path.join(REPO, "tools", nm + ".py")))
    zr = load("zenology_render"); gp, song = zr.gp_song("Беги от меня"); part = json.load(open(PART, encoding="utf-8"))
    zen = os.path.join(song.out, "zenology"); r3 = os.path.join(zen, "round3"); page = os.path.join(zen, "page"); bar = song.bar; b0, b1 = VOICES["lead"]["solo"]
    rk = json.load(open(os.path.join(zen, "zen-synths-lead-144-148.json"), encoding="utf-8"))
    cat = {f"{r['bank']}/{r['number']}": r for r in zr.read_catalog()}
    tags = [t["tone"] for t in rk["all"][:36]] + [k for k, r in cat.items() if r["category"] in ("Synth Lead", "Synth PolyKey", "Synth Pluck") and re.search(LEAD_NAMES, r["name"])]
    tags = list(dict.fromkeys(tags)); print(len(tags), "tones on the short list", flush=True)
    dur = (b1 - b0) * bar + 1.0
    ref = sum(song.read(f"{st}.wav", song.t_stem(b0), song.t_stem(b0) + dur) for st in part["stems"]).mean(1); R = gp.cqt_db(ref)
    k16 = int(bar / 16 * 48000); cells = sorted({int(round(t / (bar / 16))) for t, n, d in gp.voice_line(song, part, "lead", b0, b1)})
    notes = lambda x: np.array([20 * np.log10(np.sqrt((x.mean(1)[c * k16:(c + 1) * k16] ** 2).mean()) + 1e-9) for c in cells])

    def score(files, tr):
        out = {}
        for t, f in files.items():
            x = sf.read(f, always_2d=True, dtype="float32")[0]
            if not np.isfinite(x).all() or np.sqrt((x ** 2).mean()) < 1e-4 or np.abs(x).max() > 8:      # a tone that blew up or stayed silent
                continue
            y = fx(x, LEAD_REPEAT, bar); sc, sp, tf, o = gp.sweep_score(R, gp.cqt_db(y.mean(1)[:len(ref)]), song.semi)
            out[t] = (sc, o, f, tr)
        return out
    res = score(zen_many(r3, "lead,lead_lo", b0, b1, tags), 0)
    off = collections.defaultdict(list)                       # tones that sound an octave off: once more, transposed
    for t, (sc, o, f, tr) in res.items():
        if o:
            off[12 * o].append(t)
    for tr, ts in off.items():
        res.update(score(zen_many(r3, "lead,lead_lo", b0, b1, ts, tr), tr))
    top = sorted(res.items(), key=lambda kv: -kv[1][0])
    short = [t for t, _ in top[:24]]
    if ZEN["lead"] not in short:
        short.append(ZEN["lead"])
    res[ZEN["lead"]] = (0, 0, "", 0)                          # the tone he heard in round 2: at the written pitch
    # the tones of the top again, each in a process of its own (zen_take), twice: do two processes give the same notes?
    best = {}
    for tr in sorted({res[t][3] for t in short}):
        best.update(zen_best(os.path.join(r3, "best2"), "lead,lead_lo", b0, b1, [t for t in short if res[t][3] == tr], cells, bar, tr))
    final = {}
    for t in short:
        f, dev, spread = best[t]; x = sf.read(f, always_2d=True, dtype="float32")[0]
        if not np.isfinite(x).all() or np.sqrt((x ** 2).mean()) < 1e-4:
            continue
        sc = gp.sweep_score(R, gp.cqt_db(fx(x, LEAD_REPEAT, bar).mean(1)[:len(ref)]), song.semi)[0]; final[t] = (sc, f, dev, spread, res[t][3])
    keep = [t for t, _ in sorted(final.items(), key=lambda kv: -kv[1][0]) if final[t][2] < 6][:14]
    if ZEN["lead"] in final and ZEN["lead"] not in keep:
        keep.append(ZEN["lead"])
    clips = []; n = int(round((b1 - b0) * bar * 44100)); rms = lambda v: np.sqrt((v ** 2).mean()) + 1e-9
    orig = sum(resample_poly(song.read(f"{st}.wav", song.t_stem(b0), song.t_stem(b0) + (b1 - b0) * bar + 0.2).mean(1), 147, 160) for st in part["stems"])
    clips.append(("Оригинал", "стемы keys + strings", orig, True)); print("score  transpose  kept-take-to-median  spread-of-plays  tone")
    for t, (sc, f, dev, spread, tr) in sorted(final.items(), key=lambda kv: -kv[1][0]):
        r = cat[t]; print(f"{sc:.3f}  {tr:+3d}  {dev:5.1f} dB  {spread:6.1f} dB  {t.split()[0]}/{r['number']} {r['name']} ({r['category']})" + ("" if t in keep else "   - not on the page"), flush=True)
    for t in keep:
        sc, f, dev, spread, tr = final[t]; x = sf.read(f, always_2d=True, dtype="float32")[0]; r = cat[t]
        clips.append((r["name"] + (" — тон, что был" if t == ZEN["lead"] else ""), f"{t.split()[0]}/{r['number']} · {r['category']} · повтор 1/8 · близость {sc:.2f}"
                      + (f" · сыграно на октаву {'выше' if tr > 0 else 'ниже'}" if tr else ""), fx(x, LEAD_REPEAT, bar), False))
    res[ZEN["lead"]] = (0, 0, final[ZEN["lead"]][1], 0)
    mp = sf.read(res[ZEN["lead"]][2], always_2d=True, dtype="float32")[0]
    clips.append(("Margherita, больше объёма", "тот же тон + хорус + реверб побольше + повтор 1/8",
                  fx(mp, [("Chorus", {"rate_hz": 0.6, "depth": 0.25, "mix": 0.35}), LEAD_REPEAT[0], ("Reverb", {"room_size": 0.6, "wet_level": 0.22, "dry_level": 0.85})], bar), False))
    fitted = []
    for nm, note, x, isref in clips:
        y = x if isref else resample_poly(x.mean(1), 147, 160); y = np.pad(y, (0, max(0, n - len(y))))[:n]; fitted.append(y if isref else y * rms(orig[:n]) / rms(y))
    peak = max(np.abs(y).max() for y in fitted); out = []
    for k, ((nm, note, x, isref), y) in enumerate(zip(clips, fitted)):
        y = y / peak * 0.8; f = int(0.008 * 44100); y[:f] *= np.linspace(0, 1, f); y[-f:] *= np.linspace(1, 0, f)
        fn = f"r3-lead-{k:02d}.wav"; sf.write(os.path.join(page, fn), y.astype(np.float32), 44100, subtype="PCM_16"); out.append([fn, nm, note, isref])
    # the stab: «Scented — как ты слышал» = the sweep take with other tones' tails in it; the clean tone + a tail fitted to it
    sb0, sb1 = VOICES["stab"]["solo"]; sn = int(round((sb1 - sb0) * bar * 44100))
    sx = zen_clean(ZEN["stab"], "stab", sb0, sb1, os.path.join(r3, "stab-clean.wav")); take = sf.read(os.path.join(zen, ZEN_TAKE["stab"]), always_2d=True, dtype="float32")[0]
    c, ch, c0 = like_take(sx, take, bar, gp); print(f"stab: clean to the take {c0:.3f}, with the fitted tail {c:.3f}: {ch}")
    sorig = sum(resample_poly(song.read(f"{st}.wav", song.t_stem(sb0), song.t_stem(sb0) + (sb1 - sb0) * bar + 0.2).mean(1), 147, 160) for st in part["stems"])
    what = " + ".join(f"дилей {'1/8' if k['delay_bars'] == 1 / 8 else '3/16'} {k['mix']:.2f}" if u == "Delay" else f"реверб {k['room_size']:.1f}/{k['wet_level']:.2f}" for u, k in ch) or "без обработки"
    sclips = [("Оригинал", "стемы keys + strings", sorig, True), ("Scented — как ты слышал", "дубль из перебора, с чужими хвостами", take, False),
              ("Scented + хвост — так будет в слое", f"чистый тон + {what}; близость к дублю {c:.2f} (без хвоста {c0:.2f})", fx(sx, ch, bar), False)]
    sfit = []
    for nm, note, x, isref in sclips:
        y = x if isref else resample_poly(x.mean(1), 147, 160); y = np.pad(y, (0, max(0, sn - len(y))))[:sn]; sfit.append(y if isref else y * rms(sorig[:sn]) / rms(y))
    speak = max(np.abs(y).max() for y in sfit); sout = []
    for k, ((nm, note, x, isref), y) in enumerate(zip(sclips, sfit)):
        y = y / speak * 0.8; f = int(0.008 * 44100); y[:f] *= np.linspace(0, 1, f); y[-f:] *= np.linspace(1, 0, f)
        fn = f"r3-stab-{k:02d}.wav"; sf.write(os.path.join(page, fn), y.astype(np.float32), 44100, subtype="PCM_16"); sout.append([fn, nm, note, isref])
    json.dump({"stab_fx": ch}, open(os.path.join(r3, "stab-fx.json"), "w"), ensure_ascii=False)
    meta = {"title": "Беги от меня — тон для лида", "groups": [{"name": "Лид, такты 144–147", "note": f"шорт-лист {len(res)} тонов, лучшие переиграны в отдельных запусках с проверкой; на каждом повтор 1/8; по кругу, одна громкость", "clips": out},
                                                             {"name": "Удары припева, такты 43–46", "note": "твой выбор и то, как он будет воспроизведён", "clips": sout}],
            "sub": "Все варианты отрендерены чисто и с тем повтором 1/8, который ты одобрил. Порядок — по близости к оригиналу, это подсказка. "
                   "<kbd>←</kbd> <kbd>→</kbd> соседний вариант, <kbd>пробел</kbd> пауза."}
    tpl = open(os.path.join(REPO, "tools", "templates", "part-tone-pick.html"), encoding="utf-8").read()
    open(os.path.join(page, "round3.html"), "w", encoding="utf-8").write(tpl.replace("/*META*/", json.dumps(meta, ensure_ascii=False)))
    json.dump([{"tone": t, "name": cat[t]["name"], "score": round(v[0], 3), "transpose": v[4], "note_dev_db": round(v[2], 1), "plays_spread_db": round(v[3], 1)}
               for t, v in sorted(final.items(), key=lambda kv: -kv[1][0])], open(os.path.join(r3, "ranking.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(os.path.join(page, "round3.html"))


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
    {"notes": cmd_notes, "fx": cmd_fx, "plan": cmd_plan, "rank": cmd_rank, "sound": cmd_sound, "zenpicks": cmd_zenpicks, "_zenrender": cmd_zenrender, "_zenmany": cmd_zenmany, "round2": cmd_round2, "round3": cmd_round3, "preview": cmd_preview}[sys.argv[1]]()
