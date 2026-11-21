#!/usr/bin/env python3
"""SEREBRO «Мало тебя»: the keys (Moises keys + other) written out as notes for the GM-800
(wiki/pipelines/part-transcription-guide.md; Alex 2026-11-20: «большая задача на снятие партии клавиш»,
Roma's concert take = sound type / brightness reference, original stems = reference, the Nepke MIDI
«вроде похож»; «пока gm 800 занят делай все что требуется для записи» - nothing played on the GM-800 yet).

  P="uv run -q --python 3.12 --with numpy --with scipy --with soundfile --with mido python"
  $P tools/jamzone/prep_malo_tebya.py notes     # stem voicings -> parts/synths.notes.json
                                                #   (+ the MIDI as it is -> analysis/.../synths-midi.notes.json)
  $P tools/jamzone/prep_malo_tebya.py plan      # voices, bars, tone candidates, the sweep commands
  $P tools/jamzone/prep_malo_tebya.py preview   # A/B page: original / my notes / MIDI as it is / Roma
  $P tools/jamzone/prep_malo_tebya.py rank      # scene takes + tone takes of a voice in one ranking (no GM-800)
  $P tools/jamzone/prep_malo_tebya.py sound     # the page where Alex picks the pad: record / Roma / best takes
  gmp record "SEREBRO - Malo tebya" "music/songs/SEREBRO - Malo tebya/parts/synths.notes.json"   # GM-800 free
  $P tools/jamzone/prep_malo_tebya.py check     # every take against a plain synth of its notes
  $P tools/jamzone/prep_malo_tebya.py level     # balance of the voices from the record -> TAKE_DB, then `notes` again
  gmp layer  "SEREBRO - Malo tebya" "music/songs/SEREBRO - Malo tebya/parts/synths.notes.json"   # -> parts/pb-synths.wav
  $P tools/jamzone/prep_malo_tebya.py result    # the page record / layer / Roma, whole song (result.html)

Key: the record is in D minor, the band plays C minor (pitch_semitones -2); all notes below and in notes.json
are in C minor. Bars = mix.json bars. The MIDI (parts/malo-nepke.mid, Waldemar Nepke, type 0, 130 bpm, D minor):
MIDI bar = our bar + 1, transposed -2.

What the keys of the record are (keys + other stems; tools/part_notes.py per bar and --roll, pyin by 16ths,
band envelopes by 32nds):
  ONE wide supersaw pad through the whole song, 13-118, with a break at 94. It is the «обволакивающий» chorus:
    * voicings with 7ths / 9ths and common tones, not triads: Cm (G3 C4 D#4 G4 C5) | Ebmaj9 (A#3 D4 F4 G4 A#4 D5
      over D#2) | Abmaj7 (G#3 C4 D#4 G4 C5) | Fm add9 (F3 G#3 C4 F4 G4 C5); G4 and C5 ring through all four bars.
      The MIDI has triads an octave up (G4 C5 D#5 | G4 A#4 D#5 | G#4 C5 D#5 | F4 G#4 C5);
    * sidechain: the pad drops 6-9 dB on every kick (10-18 dB above 2 kHz) and is back by the off-beat. The
      MIDI's off-beat «EP» chords (ch 7) and off-beat bass are its author's reading of this pumping, there is
      no separate stab in the record -> "duck" of the layer, keyed by the drum stem;
    * filter by section: verse 13-20 dark (centroid 230 Hz, nothing above 1 kHz), chorus open (1050 Hz, 8-16 kHz
      only 18 dB under the total), verse 2 half open (560 Hz), bridge 85-93 dark again and narrow, the third
      «solo» 95-102 fully open (1660 Hz) with the chord doubled an octave up -> separate voices pad_v / pad_ch /
      pad_hi, so each gets its own tone / cutoff and level;
    * width: L and R are uncorrelated (corr -0.1 .. +0.1; side >= mid), the low octave is in anti-phase
      (corr -0.5 at 40-120 Hz). Stage Traxx plays pb-other as a MONO bus: the width is lost there, the density
      has to come from detune / chorus of the tone itself;
    * reverb is moderate: after the stop of 119 the level falls 25 dB in a quarter note; the stop of 94 is a cut.
  low     the pad's own low notes (roots in octaves 1-3), sustained. Separate voices (low_v / low_ch) to level
          or drop against the live bass.
  lead    the hook of the solos 37-44 and 77-84 (keys stem, pyin by 16ths), a 2-bar phrase:
          . . . C5(3&) D5(4) D#5(4&) | G5(1&) F5(2&) D#5(3&) D5(4)       and every second time
          . . . C5(3&) D5(4) D#5(4&) | G5(1&) C5 F5(2&) C5 D#5(3&) C5 D#5(4&)   (C5 on the beats is ducked by the
          sidechain; the one on beat 2 reads in bar 44 only). NOT what the MIDI has (ch 3: G4, C5 x6 | a scale
          C4 D#4 G4 A#4 C5 D#5 D5 C5). Alex plays the solos live (mix.json gm800: scene 12 at 37 / 77 / 95), so the
          lead is a voice of notes.json but NOT a take of the layer. In 95-102 the record has no lead at all.
Not notes: the hits of the `other` stem in the solos (a slide C4 -> D#4 with a top at A5, beats 2-3 of the odd
bars 37 39 41 43, and a cluster at the end of 38) and its riser 91-93 - FX; Alex's own parts/malo-sfx.wav already
covers the transitions, so nothing is cut from the stems here (ask Alex about the solo hits).
"""
import collections, importlib.util, json, os, shutil, subprocess, sys, time
import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
NAME = "SEREBRO - Malo tebya"
SONG = os.path.join(REPO, "music", "songs", NAME)
MID = os.path.join(SONG, "parts", "malo-nepke.mid")
PART = os.path.join(SONG, "parts", "synths.notes.json")
OUT = os.path.join(REPO, "analysis", "gm800-match", NAME)
ALT = os.path.join(OUT, "synths-midi.notes.json")
PAGE = os.path.join(OUT, "preview-part")
NAMES = "C C# D D# E F F# G G# A A# B".split()
END = 119                                   # the stop: bar after the last one with keys
name = lambda m: f"{NAMES[m % 12]}{m // 12 - 1}"
# keys 300-6000 Hz by 64ths of a beat pair, chorus: -7 dB flat for 145 ms from the kick, back to 0 by the off-beat (230 ms),
# already going down 30 ms before the next kick; with a 25 ms release the gain follows the kick's own low-band envelope
DUCK = {"stem": "drums", "db": 7.5, "release_ms": 25, "advance_ms": 30}

# ---- the record, bar by bar: (pad, low) ---------------------------------------------------------------------
CH = [("G3 C4 D#4 G4 C5", "C2 C3"), ("A#3 D4 F4 G4 A#4 D5", "D#2"),
      ("G#3 C4 D#4 G4 C5", "G#1 G#2"), ("F3 G#3 C4 F4 G4 C5", "F1 F2")]
HI = ["D#5 G5 C6 D#6", "F5 A#5 D6", "D#5 G5 C6", "C6"]                       # 95-102, on top of CH
V8 = [("G3 C4 D#4 G4 C5", "C2 C3"), ("A#3 D4 F4 G4 D5", "D#2"), ("G#3 C4 D#4 F4 G#4 C5", "G#1 G#2"),
      ("G3 C4 D4 F4 G4 C5", "G1 G2"), ("G3 C4 D#4 G4 C5 D#5", "C2 C3"), ("G#3 C4 D#4 F4 G#4 C5 D#5", "D#3"),
      ("G#3 C4 D#4 F4 G#4 C5 D#5", "F2"), ("G3 C4 D4 F4 G4 C5 D5", "G2")]    # verse 13-20
V2A = [("G3 C4 D#4 G4 C5 D#5", "C3"), ("A#3 D4 G4 A#4 D5 F5", "D#2 D#3"), ("G#3 C4 D#4 G4 D#5", "G#2 D#3"),
       ("G3 C4 D4 G4 C5 D5", "G2"), ("G3 C4 D#4 G4", "C3"), ("A#3 D#4 G4", "D#2 D#3"),
       ("G#3 A#3 C4 D#4 G#4", "G#2 D#3"), ("G3 C4 D4 G4", "G2")]             # verse 2, 45-52: thinner
V2B = [("G3 C4 D#4 G4 C5 D#5", "C3"), ("G3 A#3 D4 F4 G4 A#4 D5 F5", "D#2"), ("G#3 C4 D#4 F4 G#4 C5 D#5", "G#2"),
       ("G3 C4 D4 F4 G4 C5 D5", ""), ("G3 C4 D#4 G4 C5 D#5", "C3"), ("G#3 C4 D#4 F4 G#4 C5 D#5 F5", ""),
       ("G#3 C4 D#4 F4 G#4 C5 D#5 F5", "F2"), ("G3 C4 D4 F4 G4 C5 D5", "G2")]  # 53-60 = verse 1 without the lowest octave
BR = [("G3 C4 D#4 G4", "C3"), ("A#3 D4 G4", "D#2 D#3"), ("G#3 C4 D#4 G4", "G#2 D#3"), ("G3 C4 D4 G4", "G2 D3"),
      ("G3 C4 D#4", "C3"), ("A#3 D4 G4", "D#2 D#3"), ("G#3 C4 D#4 G4", "G#2 D#3"), ("G3 C4 D4 G4", "G2"),
      ("G3 C4 D4 F4 G4 F5", "G2 D3")]                                        # bridge 85-93
VERSE = [(13, V8), (45, V2A), (53, V2B), (85, BR)]
CHORUS = [(21, 24), (61, 24), (95, 24)]                                      # chorus + solo: CH looped
LEAD_A = [(3.5, 0.5, "C5"), (4, 0.5, "D5"), (4.5, 1.0, "D#5")]
LEAD_B = [(1.5, 1.0, "G5"), (2.5, 1.0, "F5"), (3.5, 0.5, "D#5"), (4, 0.5, "D5")]
LEAD_B2 = [(1.5, 0.5, "G5"), (2, 0.5, "C5"), (2.5, 0.5, "F5"), (3, 0.5, "C5"), (3.5, 0.5, "D#5"), (4, 0.5, "C5"), (4.5, 0.5, "D#5")]
SOLOS = [37, 77]

# tone = provisional pick by patch name (nothing has been played on the GM-800 yet); cand = the short list for
# `gmp sweep --tones`; solo = bars for the sweep (the pad is the only thing in keys there).
PADS = [1021, 1022, 1018, 1024, 1025, 314, 315, 322, 316, 317, 281, 284, 1020, 974, 1017, 913, 384, 385]   # 384/385 Side Chain: pumping tones
# Tones: Alex's pick by ear on the sound page, 2026-11-21 (keys "4" and "A"): chorus = 316 Trance Syn Poly, verse =
# 270 JP-6 Pad. Both are single ROM tones as the sweep played them (dry, part 1 of the INIT scene, notes as written):
# the layer takes get "shift": 0 for that reason (the octave probe is not asked).
VOICES = {
    "pad_ch": dict(tone=316, role="pad", solo=(21, 25), cand=PADS, live=False,
                   what="пэд припевов и соло (Cm · Ebmaj9 · Abmaj7 · Fm add9), открытый фильтр"),
    "low_ch": dict(tone=316, role="pad", solo=(21, 25), cand=[], live=False, what="низ пэда в припевах (октавы 1–3)"),
    "pad_hi": dict(tone=316, role="pad", solo=(95, 99), cand=[], live=False, what="третье соло 95–102: тот же аккорд октавой выше"),
    "pad_v":  dict(tone=270, role="pad-dark", solo=(13, 17), cand=[259, 270, 276, 998, 1000, 1007, 1031, 281, 284, 1021],
                   live=False, what="пэд куплетов и бриджа, закрытый фильтр"),
    "low_v":  dict(tone=270, role="pad-dark", solo=(13, 17), cand=[], live=False, what="низ пэда в куплетах"),
    "lead":   dict(tone=None, role="lead", solo=(37, 41), cand=[], live=True,
                   what="хук соло 37–44, 77–84; Alex играет вживую (сцена 12) — в слой не пишется"),
}
# Scenes (presets) first, single ROM tones second (Alex 2026-11-20, «Беги от меня»: «кандидатов из пресетов нет?»).
# From the contents of the liveset (prep_begi_ot_menya.scene_table); (scene, parts or None = the whole scene); slots up
# to 128 only (gm800_part.py take loads with bank 0). 11 MALO TEBYA CH = Alex's own attempt at this pad.
SCENES = {
    "pad_ch": [(11, None), (23, [3, 4]), (24, [2]), (24, None), (121, None), (60, None), (76, [4]), (101, None), (91, [2, 3]),
               (81, None), (128, [1])],
    "pad_v":  [(11, None), (3, None), (57, None), (62, None), (70, None), (81, None), (16, None), (117, [3, 4])],
}
# Balance of the voices inside the layer, dB (cmd_level, takes of 2026-11-21): the chorus pad = 0; the verse pad sits
# 2.3 LU under the record's chorus as in the record; pad_hi = what the record's 95-102 has over its 103-118.
TAKE_DB = {"pad_v": -2.3, "low_v": -2.3, "pad_hi": 2.3}
SWEEP = {"pad_ch": "pad_ch,low_ch", "pad_v": "pad_v,low_v"}        # what is played for the audition of a voice
GAP = {vn: -0.04 for vn in ("pad_ch", "low_ch", "pad_hi", "pad_v", "low_v")}   # chords back to back: overlap, no hole


def shared():
    s = importlib.util.spec_from_file_location("prep_solnyshko", os.path.join(os.path.dirname(__file__), "prep_solnyshko.py"))
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


def build():
    V = collections.defaultdict(list)
    for b0, rows in VERSE:
        for i, (pad, low) in enumerate(rows):
            V["pad_v"].append([b0 + i, 1.0, 4.0, pad])
            if low:
                V["low_v"].append([b0 + i, 1.0, 4.0, low])
    for b0, n in CHORUS:
        for i in range(n):
            pad, low = CH[i % 4]
            V["pad_ch"].append([b0 + i, 1.0, 4.0, pad]); V["low_ch"].append([b0 + i, 1.0, 4.0, low])
            if b0 == 95 and i < 8:
                V["pad_hi"].append([b0 + i, 1.0, 4.0, HI[i % 4]])
    for b0 in SOLOS:
        for k in range(4):
            V["lead"] += [[b0 + 2 * k, bt, d, p] for bt, d, p in LEAD_A]
            V["lead"] += [[b0 + 2 * k + 1, bt, d, p] for bt, d, p in (LEAD_B2 if k % 2 else LEAD_B)]
    return wrap(V)


def wrap(V):
    return {vn: dict({"at": [1], "bars": END - 1, "notes": sorted(ns, key=lambda n: (n[0], n[1]))},
                     **({"gap": GAP[vn]} if vn in GAP else {})) for vn, ns in V.items()}


def build_midi():
    """The MIDI as it is: MIDI bar - 1, -2 semitones. ch 8 = pad (ch 9 doubles it), ch 7 = off-beat chords, ch 3 = lead."""
    import mido
    m = mido.MidiFile(MID); tpb = m.ticks_per_beat; t = 0; on = {}; ns = collections.defaultdict(list)
    for msg in m.tracks[0]:
        t += msg.time
        if msg.type == "note_on" and msg.velocity > 0:
            on[(msg.channel, msg.note)] = t
        elif msg.type in ("note_off", "note_on") and (msg.channel, msg.note) in on:
            s = on.pop((msg.channel, msg.note)); ns[msg.channel + 1].append((round(s / tpb * 4) / 4, (t - s) / tpb, msg.note - 2))
    def cut(ch, keep=lambda p: True, quant=0.25):
        grp = collections.OrderedDict()
        for s, d, p in sorted(ns[ch]):
            b = int(s // 4)                                       # our bar = MIDI bar - 1
            if 1 <= b < END and keep(p):
                grp.setdefault((b, round(s % 4 + 1, 3), max(quant, round(d / quant) * quant)), set()).add(p)
        return [[b, bt, d, " ".join(name(p) for p in sorted(ps))] for (b, bt, d), ps in grp.items()]
    return wrap({"pad_ch": cut(8, lambda p: p >= 55, 1.0), "low_ch": cut(8, lambda p: p < 55, 1.0), "stab": cut(7), "lead": cut(3)})


def cmd_notes():
    sh = shared(); V = build()
    if not os.path.exists(MID):
        src = os.path.expanduser("~/Downloads/malo_tebja_[waldemar_nepke].mid")
        shutil.copy(src, MID); print("copied", src, "->", MID)
    takes = [{"voice": vn, "tone": VOICES[vn]["tone"], "base": 33, "shift": 0, "bars": sp, "gain_db": TAKE_DB.get(vn, 0.0)}
             for vn in VOICES if not VOICES[vn]["live"] for sp in sh.spans(V[vn]["notes"])]
    part = {"_about": "Keys of «Мало тебя» (Moises keys + other) written out for the GM-800; generated by "
                      "tools/jamzone/prep_malo_tebya.py notes (edit there, not here). Notes = the record's voicings "
                      "(part_notes.py per bar), C minor = band key (the record is in D minor, pitch_semitones -2), mix.json "
                      "bars. One supersaw pad in three registers of its filter (pad_v dark, pad_ch open, pad_hi the octave "
                      "of 95-102) + its low notes; the sidechain pumping of the record = layer.duck. lead = the hook of the "
                      "solos, played live by Alex (GM-800 scene 12): a voice, not a take. Tones = Alex's pick by ear on the "
                      "sound page (2026-11-21): chorus 316 Trance Syn Poly, verse 270 JP-6 Pad.",
            "stems": ["keys", "other"], "voices": V, "layer": {"file": "pb-synths", "takes": takes, "duck": DUCK}}
    sh.dump(part, PART)
    txt = open(PART, encoding="utf-8").read()                      # dump() writes file + takes only: add the duck
    if '"duck"' not in txt:
        i = txt.rindex("]}"); txt = txt[:i] + f'], "duck": {json.dumps(DUCK)}}}' + txt[i + 2:]
        open(PART, "w", encoding="utf-8").write(txt)
    json.load(open(PART, encoding="utf-8"))
    os.makedirs(OUT, exist_ok=True)
    sh.dump({"_about": "The Nepke MIDI as it is (bar - 1, -2 semitones): A/B against parts/synths.notes.json",
             "stems": ["keys", "other"], "voices": build_midi()}, ALT)
    print(PART)
    for vn, v in V.items():
        print(f"  {vn:7} {len(v['notes']):4} notes  bars " + " ".join(f"{a}-{b - 1}" for a, b in sh.spans(v["notes"])))
    print(f"  layer: {len(takes)} takes, {sum(b - a for t in takes for a, b in [t['bars']])} bars to record, duck {DUCK}")
    print(ALT)


def song_obj():
    load = lambda nm: (lambda s: (lambda m: (s.loader.exec_module(m), m)[1])(importlib.util.module_from_spec(s)))(
        importlib.util.spec_from_file_location(nm, os.path.join(REPO, "tools", nm + ".py")))
    gp = load("gm800_part"); return gp, gp.gmm.Song(NAME)


def begi():
    s = importlib.util.spec_from_file_location("prep_begi_ot_menya", os.path.join(os.path.dirname(__file__), "prep_begi_ot_menya.py"))
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


def tone_rows():
    return {int(r.split("\t")[0]): r.split("\t")[1].split("  ")[0] for r in open(os.path.join(REPO, "gear", "gm-800", "tones.tsv"), encoding="utf-8")}


def cmd_plan():
    sh = shared(); part = json.load(open(PART, encoding="utf-8")); rows = tone_rows(); sct = begi().scene_table()
    rel = os.path.relpath(PART, REPO)
    for vn, spec in VOICES.items():
        sp = " ".join(f"{a}-{b - 1}" for a, b in sh.spans(part["voices"][vn]["notes"]))
        tone = f"пока тон {spec['tone']} {rows[spec['tone']]}" if spec["tone"] else "живьём"
        print(f"\n{vn}: {spec['what']}; такты {sp}; {tone}")
        b0, b1 = spec["solo"]
        for scene, parts in SCENES.get(vn, []):
            nm, ps = sct[scene]
            what = " + ".join(f"{num} {tn}" for q, num, tn in ps if not parts or q in parts)
            print(f"   сцена {scene:3} {nm:16} {'партия ' + ','.join(map(str, parts)) if parts else 'вся':10} {what}")
        for scene, parts in SCENES.get(vn, []):
            print(f"   gmp take \"{NAME}\" \"{rel}\" {SWEEP[vn]} {scene}" + (f" --parts {','.join(map(str, parts))}" if parts else "")
                  + f" --bars {b0} {b1}")
        if spec["cand"]:
            print("   тоны: " + ", ".join(f"{n} {rows[n]}" for n in spec["cand"]))
            print(f"   gmp sweep \"{NAME}\" \"{rel}\" {SWEEP.get(vn, vn)} --bars {b0} {b1} "
                  f"--role {spec['role']} --tones {','.join(map(str, spec['cand']))}")


def ranked(gp, song, part, sct, rows, vn):
    """[(score, spectrum, picture, octave, what, file)] of the kept takes of a voice, best first (scene takes of
    gmp take and tone takes of gmp sweep in one ranking against the stems of the voice's bars)."""
    import glob, re
    b0, b1 = VOICES[vn]["solo"]; v = SWEEP[vn].replace(",", "+")
    files = glob.glob(os.path.join(song.out, f"part-synths-{v}-s*-{b0}-{b1}.wav")) \
        + glob.glob(os.path.join(song.out, f"sweep-synths-{v}-{b0}-{b1}-t*.wav"))
    dur = (b1 - b0) * song.bar + 1.0
    ref = sum(song.read(f"{st}.wav", song.t_stem(b0), song.t_stem(b0) + dur) for st in part["stems"]).mean(1)
    R = gp.cqt_db(ref); out = []
    for f in files:
        x = gp.gmm.read_wav(f).mean(1)[:len(ref)]
        if np.sqrt((x ** 2).mean()) < 1e-4:
            continue
        sc, spc, tf, o = gp.sweep_score(R, gp.cqt_db(x), song.semi); nm = os.path.basename(f)
        m = re.search(r"-s(\d+)-(all|p\d+)-", nm); t = re.search(r"-t(\d+)\.wav$", nm)
        what = (f"сцена {int(m[1])} {sct[int(m[1])][0]}" + ("" if m[2] == "all" else " · партия " + ",".join(m[2][1:])) if m
                else f"тон {int(t[1])} {rows[int(t[1])]}")
        out.append((sc, spc, tf, o, what, f))
    return sorted(out, reverse=True)


def cmd_rank():
    gp, song = song_obj(); part = json.load(open(PART, encoding="utf-8")); sct = begi().scene_table(); rows = tone_rows()
    for vn in SWEEP:
        out = ranked(gp, song, part, sct, rows, vn)
        if out:
            print(f"\n{vn}, такты {VOICES[vn]['solo'][0]}-{VOICES[vn]['solo'][1] - 1}:")
            for sc, spc, tf, o, what, f in out:
                x = gp.gmm.read_wav(f).mean(1); F = np.abs(np.fft.rfft(x[:4 * gp.gmm.SR] * np.hanning(4 * gp.gmm.SR))) ** 2
                fr = np.fft.rfftfreq(4 * gp.gmm.SR, 1 / gp.gmm.SR); k = (fr > 40) & (fr < 16000)
                print(f"  {sc:.3f}  спектр {spc:.3f}  картина {tf:.3f}  окт {o:+d}  центр {(F * fr)[k].sum() / F[k].sum():5.0f} Гц  {what}")


SOUND_TOP = 8
SOUND_KEEP = ["-s011-", "-t1018", "-t1025"]    # always on the page: Alex's own scene of this song; the parts of the mixes
# Measured on the takes (2026-11-21): no single tone has both the record's highs (4-16 kHz 12 dB under the total) and its
# width (L/R corr -0.1): 1024 / 1025 Trance Saws have the highs (-11) but are narrow (+0.97 / +0.76), 1018 Super Saws is
# the widest (+0.14) but dark (-25), 1021 S-Saw Pad (best score) is mono and 7 dB darker. So: mixes of two takes, equal
# loudness each, as extra candidates of the chorus pad (a scene with two parts would be this).
MIXES = [(1018, 1025), (1018, 1024), (316, 1025), (1021, 1025)]
SOUND_TITLE = {"pad_ch": "Пэд припева (такты 21–24), с качанием от бочки, как будет в слое",
               "pad_v": "Пэд куплета (такты 13–16, барабанов ещё нет)"}


def orig_bandkey(song):
    """The original keys + other for the ear: the raw Moises stems (NOT the site stems - with Roma's layer "replaces"
    them they ARE Roma's take) transposed to the band key (cached, stereo, 44.1 kHz, raw-stem time)."""
    op = os.path.join(OUT, "orig-keys-other-bandkey.wav")
    if not os.path.exists(op):
        tmp = op[:-4] + "-src.wav"
        subprocess.run(["ffmpeg", "-v", "quiet", "-y", "-i", song.stem("keys"), "-i", song.stem("other"), "-filter_complex",
                        "amix=inputs=2:normalize=0", "-ar", "44100", tmp], check=True)
        subprocess.run(["rubberband", "-q", "-3", "-p", str(song.semi), tmp, op], check=True); os.remove(tmp)
    return op


def cmd_sound():
    """The page where Alex picks the sound: per voice the record, Roma and the best takes (scenes and tones in one
    ranking), all at the record's loudness, in sync. The chorus takes get the layer's duck (the pumping is half of
    that sound). The record is heard in the band key (orig_bandkey: Alex compares by ear, a tone apart is no
    comparison); the scores and the hints are measured against the untouched stems."""
    import re, soundfile as sf
    gp, song = song_obj(); part = json.load(open(PART, encoding="utf-8")); sct = begi().scene_table(); gmm = gp.gmm; rows = tone_rows()
    os.makedirs(PAGE, exist_ok=True); n = int((4 * song.bar + 1.0) * gmm.SR); T = []; groups = []
    keys = list("1234567890QWERTYUIOPASDFGHJKLZXCVBNM") + [""] * 60; k = 0
    dk = gp.duck_gain(song, DUCK, int(sf.info(song.stem("drums")).duration * gmm.SR), gmm.SR)
    lay = next(l for l in song.mix["pb-other"]["layers"] if isinstance(l, dict) and l.get("file") == "roma-keys-2810")

    def mp3(name, x):
        x = np.asarray(x, dtype=np.float32); x = x if x.ndim == 2 else np.stack([x, x], 1)
        x = np.vstack([x, np.zeros((max(0, n - len(x)), 2), np.float32)])[:n]
        subprocess.run(["ffmpeg", "-v", "quiet", "-y", "-f", "f32le", "-ar", str(gmm.SR), "-ac", "2", "-i", "-", "-b:a", "160k",
                        os.path.join(PAGE, name)], input=x.tobytes(), check=True)

    for vn in SWEEP:
        out = ranked(gp, song, part, sct, rows, vn)
        if not out:
            continue
        b0, b1 = VOICES[vn]["solo"]; t0 = song.t_stem(b0)
        ref = sum(song.read(f"{st}.wav", t0, t0 + n / gmm.SR) for st in part["stems"])
        def stat(x):                                          # (L/R correlation, 4-16 kHz against the total, dB)
            x = np.asarray(x, dtype=np.float64)[:int(4 * song.bar * gmm.SR)]; m = x.mean(1)
            F = np.abs(np.fft.rfft(m * np.hanning(len(m)))) ** 2; fr = np.fft.rfftfreq(len(m), 1 / gmm.SR)
            return (np.corrcoef(x[:, 0], x[:, 1])[0, 1],
                    10 * np.log10(F[(fr >= 4000) & (fr < 16000)].sum() / F[(fr > 40) & (fr < 16000)].sum() + 1e-12))
        def cen(x):                                           # spectral centre, Hz (the verse of the record has no highs at all)
            m = np.asarray(x, dtype=np.float64)[:int(4 * song.bar * gmm.SR)].mean(1)
            F = np.abs(np.fft.rfft(m * np.hanning(len(m)))) ** 2; fr = np.fft.rfftfreq(len(m), 1 / gmm.SR); q = (fr > 40) & (fr < 16000)
            return (F * fr)[q].sum() / F[q].sum()
        c0, h0 = stat(ref)
        hint = ((lambda x: (lambda c, h: f"верха {h - h0:+.0f} дБ к записи · стерео {c:+.1f}")(*stat(x))) if vn == "pad_ch" else
                (lambda x: f"центр спектра {cen(x):.0f} Гц (запись {cen(ref):.0f}) · стерео {stat(x)[0]:+.1f}"))
        L = gmm.lufs(ref); gid = "g-" + vn; groups.append(f'<h2>{SOUND_TITLE[vn]}</h2>\n<div class="grid" id="{gid}"></div>')
        rk = song.read(orig_bandkey(song), t0, t0 + n / gmm.SR); rk = rk * 10 ** ((L - gmm.lufs(rk)) / 20)
        mp3(f"snd-{vn}-00-stem.mp3", rk); T.append([gid, keys[k], f"snd-{vn}-00-stem.mp3", "Оригинал", f"стемы keys + other, −2 полутона (наша тональность) · стерео {c0:+.1f}", True]); k += 1
        ro = song.read(os.path.join("parts", "roma-keys-2810.wav"), t0 + lay["rec_off"], t0 + lay["rec_off"] + n / gmm.SR)
        ro = ro * 10 ** ((L - gmm.lufs(ro)) / 20); mp3(f"snd-{vn}-00-roma.mp3", ro)
        T.append([gid, keys[k], f"snd-{vn}-00-roma.mp3", "Рома, концерт 28.10", "сейчас в плейбеке · " + hint(ro), False]); k += 1
        g = dk[int(t0 * gmm.SR):int(t0 * gmm.SR) + n][:, None] if vn == "pad_ch" else 1.0
        pick = out[:SOUND_TOP] + [r for r in out[SOUND_TOP:] if any(t in os.path.basename(r[5]) for t in SOUND_KEEP)]
        for i, (sc, spc, tf, o, what, f) in enumerate(pick, 1):
            x = gmm.read_wav(f); x = np.vstack([x, np.zeros((max(0, n - len(x)), 2), x.dtype)])[:n] * g
            x = x * 10 ** ((L - gmm.lufs(x)) / 20)
            fn = f"snd-{vn}-{i:02d}.mp3"; mp3(fn, x)
            m = re.search(r"-s(\d+)-(all|p\d+)-", os.path.basename(f))
            tones = " + ".join(f"{num} {tn}" for q, num, tn in sct[int(m[1])][1] if m[2] == "all" or str(q) in m[2][1:]) if m else "отдельный тон, сухой"
            T.append([gid, keys[k], fn, what, f"{tones} · сходство {sc:.2f} · {hint(x)}", False]); k += 1
            print(f"  {vn:7} {i}. {sc:.3f} {what}  [{tones}]  {hint(x)}")
        if vn == "pad_ch":                                    # two takes at equal loudness = a two-part scene
            tk = lambda num: (lambda x: x * 10 ** ((L - gmm.lufs(x)) / 20))(gmm.read_wav(os.path.join(song.out, f"sweep-synths-pad_ch+low_ch-{b0}-{b1}-t{num:04d}.wav")).astype(np.float64))
            R = gp.cqt_db(ref.mean(1))
            for j, (t1, t2) in enumerate(MIXES, 1):
                xa, xb = tk(t1), tk(t2); m_ = min(len(xa), len(xb)); raw = xa[:m_] + xb[:m_]
                sc = gp.sweep_score(R, gp.cqt_db(raw.mean(1)[:len(ref)]), song.semi)[0]
                x = np.vstack([raw, np.zeros((max(0, n - len(raw)), 2))])[:n] * g
                x = x * 10 ** ((L - gmm.lufs(x)) / 20); fn = f"snd-{vn}-mix{j}.mp3"; mp3(fn, x)
                T.append([gid, keys[k], fn, f"смесь {t1} + {t2}", f"{rows[t1]} + {rows[t2]}, поровну · сходство {sc:.2f} · {hint(x)}", False]); k += 1
                print(f"  {vn:7} mix {t1} + {t2}: {sc:.3f}  {hint(x)}")
    tpl = open(os.path.join(REPO, "tools", "templates", "part-listen-page.example.html"), encoding="utf-8").read()
    head, rest = tpl.split("<main>", 1); body, tail = rest.split("</main>", 1); script = tail[tail.index("<script>"):]
    bar_html = tail[:tail.index("<script>")]
    bar_html = re.sub(r'<i style="left:[\d.]+%"></i>', "", bar_html)
    marks = "".join(f'<i style="left:{100 * q * song.bar / (n / gmm.SR):.1f}%"></i>' for q in (1, 2, 3, 4))
    bar_html = bar_html.replace('<div id="fill"></div>', '<div id="fill"></div>' + marks)
    script = re.sub(r"const BAR = [^;]+;", f"const BAR = {song.bar};", script)
    script = re.sub(r"const T = \[.*?\n\];", lambda _: "const T = " + json.dumps(T, ensure_ascii=False) + ";", script, flags=re.S)
    ver = time.strftime("%m%d-%H%M%S")                        # a rebuilt mp3 keeps its name: without this the browser plays the cached one
    script = script.replace('const VER = "";', f'const VER = "?v={ver}";')
    script = re.sub(r"const KEYCODE = \{[^}]*\};", "const KEYCODE = {" + ", ".join(f'{c}: "Key{c}"' for c in "QWERTYUIOPASDFGHJKLZXCVBNM") + "};", script)
    main = ("<main>\n  <h1>Мало тебя — выбор звука пэда</h1>\n  <p class=\"sub\">Четыре такта на голос, всё на одной громкости, играет по кругу; "
            "переключение идёт с того же места. В каждой группе оригинал, Рома и лучшие кандидаты — твои сцены и отдельные тоны в одном "
            "рейтинге (сходство с оригиналом — только подсказка, выбираешь ты). Оригинал опущен на тон, в нашу тональность. "
            "Дубли с прибора в стерео. <kbd>пробел</kbd> пауза, клавиши на кнопках.</p>\n" + "\n".join(groups) + "\n</main>")
    head = re.sub(r"<title>.*?</title>", "<title>Мало тебя — выбор звука</title>", head, flags=re.S)
    open(os.path.join(PAGE, "sound.html"), "w", encoding="utf-8").write(head + main + bar_html + script)
    print(os.path.join(PAGE, "sound.html") + f"   open as sound.html?v={ver} (the page itself is cached the same way)")


HTML = """
<h2>Голоса</h2>
<div class="wrap"><table>
<tr><th>Голос</th><th>Такты</th><th>Что играет</th><th>Откуда</th></tr>
<tr><td>pad_ch + low_ch</td><td class="n">21–44, 61–84, 95–118</td><td>Cm (G3 C4 D#4 G4 C5) · Ebmaj9 (A#3 D4 F4 G4 A#4 D5) · Abmaj7 (G#3 C4 D#4 G4 C5) · Fm add9 (F3 G#3 C4 F4 G4 C5); низ C2 C3 · D#2 · G#1 G#2 · F1 F2</td><td>запись (в MIDI трезвучия октавой выше)</td></tr>
<tr><td>pad_hi</td><td class="n">95–102</td><td>тот же аккорд октавой выше: D#5 G5 C6 D#6 · F5 A#5 D6 · D#5 G5 C6 · C6</td><td>запись</td></tr>
<tr><td>pad_v + low_v</td><td class="n">13–20, 45–60, 85–93</td><td>Cm · Ebmaj9 · Ab6 · G7sus4 · Cm · Fm7/Eb · Fm7 · G7sus4; куплет 2 первые 8 тактов реже; бридж Cm · Eb · Ab · Gsus4 ×2, в 93 G7sus4</td><td>запись (в MIDI Cm Eb Ab G · Cm Eb Fm G)</td></tr>
<tr><td>lead (живьём)</td><td class="n">37–44, 77–84</td><td>· · · C5 D5 D#5 | G5 F5 D#5 D5, каждый второй раз G5 C5 F5 C5 D#5 C5 D#5</td><td>запись (в MIDI другая мелодия)</td></tr>
<tr><td>сайдчейн</td><td class="n">везде, где бочка</td><td>пэд проседает на 8 дБ на каждую бочку и возвращается к «и»</td><td>запись (в MIDI — аккорды на «и»)</td></tr>
</table></div>
<p class="q">«Мои ноты» сыграны простым синтом в моно: проверяются ноты, ритм и качание, не звук. Лид на странице звучит,
в слой плейбека он не пишется (ты играешь его на сцене 12). Не выписано: удары стема other в соло (слайд к D#4 на
долях 2–3 нечётных тактов) и его райзер 91–93.</p>
"""

SR = 44100
#           kind   lowpass decay level
TIMBRE = {"pad_ch": ("pad", 6000, None, 1.0), "low_ch": ("pad", 700, None, 0.9), "pad_hi": ("pad", 8000, None, 0.6),
          "pad_v":  ("pad", 900,  None, 1.0), "low_v":  ("pad", 350, None, 0.9), "lead":   ("saw", 5000, None, 1.0),
          "stab":   ("saw", 5000, 0.10, 0.6)}


def render(song, gp, part, n):
    sh = shared(); out = {}
    for vn, v in part["voices"].items():
        buf = np.zeros(n); kind, fc, dec, g = TIMBRE[vn]
        for t, m, d in gp.voice_line(song, part, vn, 1, END):
            x = sh.synth(kind, fc, dec, 440 * 2 ** ((m - 69) / 12), max(d, 0.03)) * g
            a = int((song.t_render(1) + t) * SR); k = min(len(x), n - a)
            buf[a:a + k] += x[:k]
        out[vn] = buf
    return out


def cmd_preview():
    import soundfile as sf
    gp, song = song_obj(); os.makedirs(PAGE, exist_ok=True)
    n = sf.info(os.path.join(SONG, "auto-render", "all.wav")).frames
    def rd(p):
        raw = subprocess.run(["ffmpeg", "-v", "quiet", "-i", p, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"], capture_output=True).stdout
        return np.frombuffer(raw, np.float32).astype(np.float64)
    fit = lambda x: np.pad(x, (0, max(0, n - len(x))))[:n]
    seg = lambda x, a, b: x[int(song.t_render(a) * SR):int(song.t_render(b) * SR)]
    rms = lambda x, a, b: np.sqrt((seg(x, a, b) ** 2).mean()) + 1e-12
    st = lambda p: fit(rd(os.path.join(SONG, "auto-render", "stems", p)))      # site stems: render time, band key
    off = int(round(song.off * SR))
    orig = fit(np.concatenate([np.zeros(off), rd(orig_bandkey(song))]))        # the original in the band key, at the render offset
    duck = fit(np.concatenate([np.ones(off), gp.duck_gain(song, DUCK, int(sf.info(song.stem("drums")).duration * SR), SR)]))
    duck[len(duck) - 1] = 1.0
    mine, alt = json.load(open(PART, encoding="utf-8")), json.load(open(ALT, encoding="utf-8"))
    vm = render(song, gp, mine, n); va = render(song, gp, alt, n)
    left = lambda tot, known: np.sqrt(max(tot ** 2 - known ** 2, (0.25 * tot) ** 2))
    g = {}
    ch = (vm["pad_ch"] + vm["low_ch"]) * duck; vs = (vm["pad_v"] + vm["low_v"]) * duck
    g["ch"] = rms(orig, 21, 37) / rms(ch, 21, 37)
    g["v"] = rms(orig, 14, 20) / rms(vs, 14, 20)
    g["hi"] = left(rms(orig, 95, 103), g["ch"] * rms(ch, 95, 103)) / rms(vm["pad_hi"] * duck, 95, 103)
    g["lead"] = left(rms(orig, 37, 45), g["ch"] * rms(ch, 37, 45)) / rms(vm["lead"] * duck, 37, 45)
    print("page gains (dB): " + ", ".join(f"{k} {20 * np.log10(v):+.1f}" for k, v in g.items()))
    my = (g["ch"] * (vm["pad_ch"] + vm["low_ch"]) + g["v"] * (vm["pad_v"] + vm["low_v"]) + g["hi"] * vm["pad_hi"]
          + g["lead"] * vm["lead"]) * duck
    mpad = g["ch"] * (va["pad_ch"] + va["low_ch"] + va["stab"])
    mpad *= rms(orig, 21, 37) / rms(mpad, 21, 37)                              # the MIDI's own balance: chorus and solo as loud
    midi = mpad + va["lead"] * left(rms(orig, 37, 45), rms(mpad, 37, 45)) / rms(va["lead"], 37, 45)   # as the record's
    roma = rd(os.path.join(SONG, "parts", "roma-keys-2810.wav"))
    lay = next(l for l in song.mix["pb-other"]["layers"] if isinstance(l, dict) and l.get("file") == "roma-keys-2810")
    sh_ = int(round((song.off - lay.get("rec_off", song.off)) * SR))            # today's render = the take's render + this
    roma = fit(np.concatenate([np.zeros(sh_), roma]) if sh_ >= 0 else roma[-sh_:])
    roma *= rms(orig, 21, 37) / rms(roma, 21, 37)
    src = {"orig": orig, "mine": my, "midi": midi, "roma": roma}
    for a, b, what in ((13, 21, "verse"), (21, 37, "chorus"), (37, 45, "solo"), (45, 53, "verse 2a"), (53, 61, "verse 2b"),
                       (85, 94, "bridge"), (95, 103, "solo 3"), (103, 119, "chorus 3")):
        print(f"  {what:9} bars {a}-{b - 1}:  " + "  ".join(f"{k} {20 * np.log10(rms(v, a, b)):6.1f}" for k, v in src.items()) + " dBFS")
    # the pumping, original against mine: 300-6000 Hz, level by 64th of a beat (16 steps), chorus 21-36
    from scipy.signal import butter, sosfiltfilt
    bp = lambda x: sosfiltfilt(butter(4, [300, 6000], "bandpass", fs=SR, output="sos"), x)
    def pump(x):
        x = bp(x); e = []; st_ = song.bar / 64
        for k in range(16):
            v = [np.sqrt((x[int((song.t_render(b) + q * song.bar / 4 + k * st_) * SR):int((song.t_render(b) + q * song.bar / 4 + (k + 1) * st_) * SR)] ** 2).mean())
                 for b in range(21, 37) for q in range(4)]
            e.append(20 * np.log10(np.median(v) + 1e-12))
        return " ".join(f"{v - max(e):4.0f}" for v in e)
    print("  pump, chorus, 64ths of a beat:  orig " + pump(orig) + "\n" + " " * 34 + "mine " + pump(my))
    ctx = st("drums.mp3") + st("vocal.mp3") + fit(rd(os.path.join(SONG, "auto-render", "pb-bass.mp3")))
    ctx *= rms(orig, 21, 37) / rms(ctx, 21, 37) * 2.0
    peak = max(np.abs(v + ctx).max() for v in src.values())
    for k, v in src.items():
        for tag, x in (("", v), ("-ctx", v + ctx)):
            p = os.path.join(PAGE, f"{k}{tag}.mp3")
            subprocess.run(["ffmpeg", "-v", "quiet", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", "-b:a", "128k", p],
                           input=(x / peak * 0.9).astype(np.float32).tobytes(), check=True)
            print(p)
    cues = [(c["bar"], c["text"]) for c in song.mix["cues"] if str(c.get("beat", 1)) == "1"]
    meta = {"bar": song.bar, "bar1": song.t_render(1), "cues": cues, "dur": n / SR, "ctx": "-ctx",
            "title": "Мало тебя — клавиши нотами для GM-800",
            "sub": "Вся песня. Синтезаторные варианты сыграны простым синтом: здесь проверяются "
                   "<b>ноты, ритм и качание от бочки</b>, не звук — звук подберём на GM-800. Переключение сохраняет место.",
            "tracks": [["1", "orig.mp3", "Оригинал", "стемы keys + other, −2 полутона", True],
                       ["2", "mine.mp3", "Мои ноты", "аккорды по записи + сайдчейн"],
                       ["3", "midi.mp3", "Как в MIDI", "Nepke: трезвучия, аккорды на «и», другой лид"],
                       ["4", "roma.mp3", "Рома, концерт 28.10", "сейчас в плейбеке; ориентир по типу звука", True]],
            "marks": [[13, "куплет: тёмный пэд, Ebmaj9 / Ab6 / G7sus4"], [21, "припев: maj7/9 + качание от бочки"],
                      [37, "соло: лид по записи (в MIDI другой)"], [45, "куплет 2: реже, без нижней октавы"],
                      [53, "куплет 2, вторая половина = куплет 1"], [85, "бридж: тёмный, узкий"],
                      [95, "третье соло: в записи лида нет, пэд + октава вверх"], [103, "припев"]],
            "html": HTML}
    tpl = open(os.path.join(REPO, "tools", "templates", "part-listen-full.html"), encoding="utf-8").read()
    open(os.path.join(PAGE, "index.html"), "w", encoding="utf-8").write(tpl.replace("/*META*/", json.dumps(meta, ensure_ascii=False)))
    print(os.path.join(PAGE, "index.html"))


# ---- the recorded layer: check of the takes, balance of the voices, the page layer / record / Roma ----------------
GROUP = {"pad_ch": "ch", "low_ch": "ch", "pad_hi": "hi", "pad_v": "v", "low_v": "v"}


def cmd_check():
    """Every recorded take against a plain synth of the same notes: silent eighths, the time of the attacks, the
    notes (chroma). A take that is off here was disturbed or sent wrong."""
    import librosa
    gp, song = song_obj(); sh = shared(); part = json.load(open(PART, encoding="utf-8")); bad = 0; sr = gp.gmm.SR
    for i, tk in enumerate(part["layer"]["takes"]):
        b0, b1 = tk["bars"]; vn = tk["voice"]; x = gp.gmm.read_wav(gp.rec_path(song, PART, tk)).mean(1)
        n = int((b1 - b0) * song.bar * sr); x = x[:n]; kind, fc, dec, g = TIMBRE[vn]; y = np.zeros(int(n * SR / sr) + SR)
        for t, m, d in gp.voice_line(song, part, vn, b0, b1):
            z = sh.synth(kind, fc, dec, 440 * 2 ** ((m - 69) / 12), max(d, 0.03)); a = int(t * SR); k = min(len(z), len(y) - a); y[a:a + k] += z[:k]
        X = librosa.resample(x.astype(np.float32), orig_sr=sr, target_sr=22050); Y = librosa.resample(y.astype(np.float32), orig_sr=SR, target_sr=22050)[:len(X)]
        ch = lambda v: librosa.feature.chroma_cqt(y=v, sr=22050, hop_length=512)
        cx, cy = ch(X), ch(Y); k = min(cx.shape[1], cy.shape[1]); act = cy[:, :k].sum(0) > 1e-6
        csim = float(((cx[:, :k] * cy[:, :k]).sum(0) / (np.linalg.norm(cx[:, :k], axis=0) * np.linalg.norm(cy[:, :k], axis=0) + 1e-9))[act].mean())
        on = lambda v: np.maximum(0, np.diff(librosa.feature.rms(y=v, frame_length=256, hop_length=32)[0]))
        ox, oy = on(X), on(Y); m = int(0.08 * 22050 / 32); k = min(len(ox), len(oy))
        cc = [np.dot(ox[m:k - m], oy[m + l:k - m + l]) for l in range(-m, m)]; lag = -(int(np.argmax(cc)) - m) * 32 / 22050 * 1000
        e = 8 * (b1 - b0); q = len(X) // e; lv = lambda v, j: 20 * np.log10(np.sqrt((v[j * q:(j + 1) * q] ** 2).mean()) + 1e-9)
        ymax = max(lv(Y, j) for j in range(e)); silent = [j for j in range(e) if lv(Y, j) > ymax - 20 and lv(X, j) < -65]
        flag = "  <-- CHECK" if silent or csim < 0.55 or abs(lag) > 45 else ""; bad += bool(flag)
        print(f"take {i:2} {vn:7} t{tk['tone']:<4} bars {b0:3}-{b1 - 1:<3} rms {20 * np.log10(np.sqrt((x ** 2).mean()) + 1e-9):6.1f} dB  "
              f"peak {20 * np.log10(np.abs(x).max() + 1e-9):6.1f}  attacks {lag:+4.0f} ms  notes {csim:.2f}  silent eighths {silent or '-'}{flag}")
    print("takes to look at:", bad)


def groups(gp, song, raw=True):
    """({"ch" | "v" | "hi": the takes of the group, summed}, record in the band key, duck curve): stem frame, stereo,
    gmm.SR. raw = without the takes' gain_db (the balance is what cmd_level is asked for)."""
    import soundfile as sf
    gmm = gp.gmm; sr = gmm.SR; dur = sf.info(song.stem("keys")).duration; n = int(dur * sr)
    part = json.load(open(PART, encoding="utf-8")); G = {k: np.zeros((n, 2)) for k in ("ch", "v", "hi")}
    for tk in part["layer"]["takes"]:
        x = gmm.read_wav(gp.rec_path(song, PART, tk)).astype(np.float64) * (1 if raw else 10 ** (tk.get("gain_db", 0) / 20))
        k = int(0.3 * sr); x[-k:] *= np.linspace(1, 0, k)[:, None]
        a = int(round(song.t_stem(tk["bars"][0]) * sr)); m = min(len(x), n - a); G[GROUP[tk["voice"]]][a:a + m] += x[:m]
    orig = song.read(orig_bandkey(song), 0, dur).astype(np.float64)
    orig = np.vstack([orig, np.zeros((max(0, n - len(orig)), 2))])[:n]
    return G, orig, gp.duck_gain(song, DUCK, n, sr)[:, None]


def cmd_level():
    """Balance of the voice groups from the record -> the TAKE_DB to put above. The chorus pad (pad_ch + low_ch) is the
    reference, 0 dB. pad and low of one tone keep the balance the tone gives them (that is what Alex heard and
    picked). Verse group: the record's verse 13-20 against its chorus 21-36, LUFS. pad_hi: what the record's 95-102
    has over 103-118 beyond the chorus pad (power). Also: the separate takes pad + low against the joint take of the
    sweep (is the tone's chain linear enough to record the voices apart)."""
    gp, song = song_obj(); gmm = gp.gmm; sr = gmm.SR; G, orig, dk = groups(gp, song)
    seg = lambda x, a, b: x[int(song.t_stem(a) * sr):int(song.t_stem(b) * sr)]; L = lambda x, a, b: gmm.lufs(seg(x, a, b))
    ch, v, hi = G["ch"] * dk, G["v"] * dk, G["hi"] * dk
    gv = (L(orig, 13, 21) - L(orig, 21, 37)) - (L(v, 13, 21) - L(ch, 21, 37))
    P = lambda x, a, b: 10 ** (L(x, a, b) / 10); r = P(orig, 95, 103) / P(orig, 103, 119)
    need = max(r * P(ch, 103, 119) - P(ch, 95, 103), 0.06 * P(ch, 95, 103)); ghi = 10 * np.log10(need / P(hi, 95, 103))
    print(f"record: verse 13-20 {L(orig, 13, 21):.1f}, chorus 21-36 {L(orig, 21, 37):.1f}, solo 3 95-102 {L(orig, 95, 103):.1f}, "
          f"chorus 3 103-118 {L(orig, 103, 119):.1f} LUFS")
    print(f"takes : verse {L(v, 13, 21):.1f}, chorus {L(ch, 21, 37):.1f}, chorus pad in 95-102 {L(ch, 95, 103):.1f}, pad_hi {L(hi, 95, 103):.1f} LUFS")
    print(f'TAKE_DB = {{"pad_v": {gv:.1f}, "low_v": {gv:.1f}, "pad_hi": {ghi:.1f}}}')
    j = os.path.join(song.out, f"sweep-synths-pad_ch+low_ch-21-25-t{VOICES['pad_ch']['tone']:04d}.wav")
    if os.path.exists(j):
        from scipy.signal import butter, sosfilt
        a = gmm.read_wav(j).astype(np.float64); b = seg(G["ch"], 21, 25); k = min(len(a), len(b)); a, b = a[:k], b[:k]
        bands = [(60, 250), (250, 1000), (1000, 4000), (4000, 12000)]
        d = [10 * np.log10(((sosfilt(butter(4, bd, "bandpass", fs=sr, output="sos"), b.mean(1)) ** 2).mean() + 1e-15) /
                           ((sosfilt(butter(4, bd, "bandpass", fs=sr, output="sos"), a.mean(1)) ** 2).mean() + 1e-15)) for bd in bands]
        print("pad + low recorded apart against the joint take of the sweep, bars 21-24: " +
              "  ".join(f"{lo}-{hi_} Hz {x:+.1f} dB" for (lo, hi_), x in zip(bands, d)) + f"   total {gmm.lufs(b) - gmm.lufs(a):+.1f} LU")


def cmd_result():
    """The page of the recorded layer, whole song: record (band key) / the layer as built by gmp layer / Roma, alone
    and with drums + vocal + bass. Everything at the record's chorus loudness; levels by section printed."""
    import soundfile as sf
    gp, song = song_obj(); gmm = gp.gmm; sr = gmm.SR; os.makedirs(PAGE, exist_ok=True)
    dur = sf.info(song.stem("keys")).duration; n = int(dur * sr); off = int(round(song.off * sr))
    fit = lambda x: np.vstack([x.astype(np.float64), np.zeros((max(0, n - len(x)), 2))])[:n]
    orig = fit(song.read(orig_bandkey(song), 0, dur)); lay = fit(song.read(os.path.join("parts", "pb-synths.wav"), 0, dur))
    rl = next(l for l in song.mix["pb-other"]["layers"] if isinstance(l, dict) and l.get("file") == "roma-keys-2810")
    roma = fit(song.read(os.path.join("parts", "roma-keys-2810.wav"), rl["rec_off"], rl["rec_off"] + dur))
    seg = lambda x, a, b: x[int(song.t_stem(a) * sr):int(song.t_stem(b) * sr)]; L = lambda x, a, b: gmm.lufs(seg(x, a, b))
    lay *= 10 ** ((L(orig, 21, 37) - L(lay, 21, 37)) / 20); roma *= 10 ** ((L(orig, 21, 37) - L(roma, 21, 37)) / 20)
    src = {"orig": orig, "layer": lay, "roma": roma}
    for a, b, what in ((13, 21, "verse"), (21, 37, "chorus"), (37, 45, "solo"), (45, 53, "verse 2a"), (53, 61, "verse 2b"), (61, 77, "chorus 2"),
                       (85, 94, "bridge"), (95, 103, "solo 3"), (103, 119, "chorus 3")):
        print(f"  {what:9} bars {a}-{b - 1}:  " + "  ".join(f"{k} {L(x, a, b):6.1f}" for k, x in src.items()) + " LUFS")
    rt = lambda x: np.vstack([np.zeros((off, 2)), x])                             # stem frame -> render time
    st = lambda p: np.vstack([fit(song.read(p, 0, dur + song.off))[off:], np.zeros((off, 2))])   # render time -> stem frame
    ctx = st(os.path.join("auto-render", "stems", "drums.mp3")) + st(os.path.join("auto-render", "stems", "vocal.mp3")) + st(os.path.join("auto-render", "pb-bass.mp3"))
    ctx *= 10 ** ((L(orig, 21, 37) + 6 - L(ctx, 21, 37)) / 20)
    peak = max(np.abs(x + ctx).max() for x in src.values()); ver = time.strftime("%m%d-%H%M%S")
    for k, x in src.items():
        for tag, y in (("", x), ("-ctx", x + ctx)):
            subprocess.run(["ffmpeg", "-v", "quiet", "-y", "-f", "f32le", "-ar", str(sr), "-ac", "2", "-i", "-", "-b:a", "160k",
                            os.path.join(PAGE, f"res-{k}{tag}.mp3")], input=(rt(y) / peak * 0.9).astype(np.float32).tobytes(), check=True)
    cues = [(c["bar"], c["text"]) for c in song.mix["cues"] if str(c.get("beat", 1)) == "1"]
    tn = tone_rows(); tc, tv = VOICES["pad_ch"]["tone"], VOICES["pad_v"]["tone"]
    meta = {"bar": song.bar, "bar1": song.t_render(1), "cues": cues, "dur": (n + off) / sr, "ctx": "-ctx", "ver": f"?v={ver}",
            "title": "Мало тебя — слой клавиш с GM-800",
            "sub": "Вся песня, стерео. Слой записан с прибора выбранными тонами, с качанием от бочки; оригинал опущен в нашу "
                   "тональность. Все три на громкости припева оригинала. Переключение сохраняет место.",
            "tracks": [["1", "res-orig.mp3", "Оригинал", "стемы keys + other, −2 полутона", True],
                       ["2", "res-layer.mp3", "Слой GM-800", f"припев и соло {tc} {tn[tc]}, куплет и бридж {tv} {tn[tv]}"],
                       ["3", "res-roma.mp3", "Рома, концерт 28.10", "сейчас в плейбеке", True]],
            "marks": [[13, "куплет: тон куплета"], [21, "припев: тон припева + качание от бочки"], [37, "соло: лида в слое нет, ты играешь его вживую"],
                      [45, "куплет 2"], [85, "бридж"], [95, "третье соло: пэд + октава вверх"], [103, "припев"]],
            "html": ""}
    tpl = open(os.path.join(REPO, "tools", "templates", "part-listen-full.html"), encoding="utf-8").read()
    open(os.path.join(PAGE, "result.html"), "w", encoding="utf-8").write(tpl.replace("/*META*/", json.dumps(meta, ensure_ascii=False)))
    print(os.path.join(PAGE, "result.html") + f"   open as result.html?v={ver}")


if __name__ == "__main__":
    {"notes": cmd_notes, "plan": cmd_plan, "rank": cmd_rank, "sound": cmd_sound, "preview": cmd_preview, "check": cmd_check,
     "level": cmd_level, "result": cmd_result}[sys.argv[1]]()
