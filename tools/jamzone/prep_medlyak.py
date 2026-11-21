#!/usr/bin/env python3
"""Mr. Credo «Медляк»: the keys (Moises keys + strings) written out as notes, to be played by ZENOLOGY tones into
a pb-other layer (wiki/pipelines/part-transcription-guide.md, wiki/pipelines/zenology.md; Alex 2026-11-21:
«помоги снять песню Медляк», everything goes to the playback - Alex plays guitar on the POD Go, GM-800 muted;
the MIDI is the one Alex found: parts/medlyak-midifind.mid).

  P="uv run -q --python 3.12 --with numpy --with scipy --with soundfile --with mido python"
  BP="uv run -q --python 3.11 --with basic-pitch[onnx]==0.4.0 --with numpy<2 --with setuptools<81 python"
  $BP tools/jamzone/prep_medlyak.py bp        # Basic Pitch note events of the keys / strings stems (analysis/)
  $P tools/jamzone/prep_medlyak.py notes      # -> parts/keys.notes.json (+ the MIDI as it is, for A/B)
  $P tools/jamzone/prep_medlyak.py preview    # page: original / my notes / MIDI as it is, whole song

Key: G minor, pitch_semitones 0 (the band plays it in the record's key). Bars = mix.json bars, 105 bpm.
The MIDI (midifind, 7 tracks, 105 bpm, 4/4) is only 32 bars long: intro 1-8, interlude 9-16, verse 17-32.
MIDI bar = our bar (checked on track 0 against the keys stem: C5 -> A#4 on 2.5 / 3 of bars 9-12, the D#4 of 10.1.5).

What the keys of the record are (keys + strings stems; tools/part_notes.py, Basic Pitch onsets folded over the
passes of a section, narrow-band envelopes of single notes by 32nds):
  chords  Gm Eb Cm D (intro, interlude, verses), chorus Gm Eb Bb D, breakdown | Gm Cm | F | Eb | F | Gm Cm | F | Eb
          | Dm Bb |, end Gm.
  poly    MIDI track 0 «Polysynth»: the intro riff (arpeggio of the chord on 1 1& 2, then a melody A4 G4 ... on
          2& and 3&), the interlude counter line (C5 A#4 on 2& 3, ...), the verse arpeggio (1 1& 2 only).
          Stem fix: on the D chord the arpeggio is F#3 A3 C4 (D7), the MIDI has D3 F#3 A3 (keys stem bars 4, 8,
          20, 24: no D3 at all, C4 on beat 2 at -4 dB).
  counter MIDI track 2, bars 17-32: the second line of the verse (A4 G4 on 2& 3&, ...). Stem fix: beat 4& of the
          Gm bar is A#4, not F4 (A#4 -1 dB, F4 -33 dB, bars 17 21 25 29).
  strings the strings stem: sustained triads; in the interlude (9-16) a step higher, as MIDI track 2 has them.
  stab    chorus (33-40, 65-80, 89-104): 8th-note chords with 16th pickups and octave tops, NOT in the MIDI.
          Basic Pitch onsets of the keys stem folded over the ten 4-bar passes of the choruses, kept where they
          recur in >= 5 of 10. The first 8th of each bar still sounds the previous chord in the record (7 of 10).
          The phrases 65-72 / 89-96 add a C over the D bars (D7): C4 on 3-4 of the 4th bar, C5 C6 on 2-3 of the 8th.
  brk     breakdown 81-88 (no drums, keys stem == strings stem, corr 0.995): a 16th-note arpeggio over the chords,
          Basic Pitch onsets that recur in both passes (81-84 / 85-88); brk_pad = the chords under it.
  end     113: the last Gm, rings two bars.
Not in the stems: MIDI track 1 «Bright» (intro melody G4 F4 D#4 ... and from bar 9 the vocal line) - the intro
melody is not in the keys stem (F4 on beat 1 of bar 2 at -30 dB), from bar 9 it doubles the vocal. Left out.
"""
import collections, importlib.util, json, os, subprocess, sys
import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
NAME = "Mr. Credo - Медляк"
SONG = os.path.join(REPO, "music", "songs", NAME)
MID = os.path.join(SONG, "parts", "medlyak-midifind.mid")
PART = os.path.join(SONG, "parts", "keys.notes.json")
OUT = os.path.join(REPO, "analysis", "gm800-match", NAME)
ALT = os.path.join(OUT, "keys-midi.notes.json")
BPDIR = os.path.join(OUT, "bp")
PAGE = os.path.join(OUT, "preview-part")
NAMES = "C C# D D# E F F# G G# A A# B".split()
END = 115                                   # bar after the last one
name = lambda p: f"{NAMES[p % 12]}{p // 12 - 1}"
midi_of = lambda s: NAMES.index(s[:-1]) + 12 * (int(s[-1]) + 1)

SECTIONS = [(1, "интро"), (9, "проигрыш"), (17, "куплет 1"), (33, "припев 1"), (41, "проигрыш"), (49, "куплет 2"),
            (65, "припев 2"), (81, "брейкдаун"), (89, "припев 3, без барабанов"), (97, "припев 3"),
            (105, "проигрыш-аутро"), (113, "конец")]
HOOK = [9, 41, 105]                         # interlude = MIDI 9-16
VERSE = [17, 49]                            # verse = MIDI 17-32
CHORUS = [33, 37, 65, 69, 73, 77, 89, 93, 97, 101]

# chords by half bar (strings voicings); interlude voicings = MIDI track 2
VOICING = {"Gm": "D4 G4 A#4", "Eb": "D#4 G4 A#4", "Cm": "D#4 G4 C5", "D": "D4 F#4 A4", "Bb": "D4 F4 A#4",
           "F": "C4 F4 A4", "Dm": "D4 F4 A4"}
VOICING_HOOK = {"Gm": "G4 A#4 D5", "Eb": "D#4 G4 A#4", "Cm": "C4 D#4 G4", "D": "D4 F#4 A4"}
# intro / interlude: a pad over the riff with the 9ths (keys stem, notes within 6 dB of the bar's loudest that the
# riff does not play: Gm D5 F5 A5, Eb A#4 D#5 F5, Cm G4 A#4 D5, D -> F#m on top: C#5 E5 from beat 1& to 4, bars 4 8 12 16)
PAD = ["D5 F5 A5", "A#4 D#5 F5", "G4 A#4 D5", "F#4 A4 C#5 E5"]
BRK_PAD = {81: ("G3 D4 G4 A4", "C4 D4 G4 A#4"), 82: ("A3 C4 F4 A4", "F3 A3 F4 A4 C5"),
           83: ("D#3 D#4 G4 A#4", "D#3 A#3 D#4 G4 A#4"), 84: ("A3 F4 A4 C5", "F3 A3 F4 A4 C5"),
           85: ("G3 D4 G4 A4", "C4 D4 G4 A#4"), 86: ("A3 C4 F4 A4", "F3 A3 F4 A4 C5"),
           87: ("D#3 D#4 G4 A#4", "D#3 A#3 D#4 G4 A#4"), 88: ("A3 D4 F4 A4", "A#3 D4 F4 A#4")}


def chord_of(bar):
    if 81 <= bar < 89:
        return None
    if any(c <= bar < c + 4 for c in CHORUS):
        return ["Gm", "Eb", "Bb", "D"][(bar - 1) % 4]
    return ["Gm", "Eb", "Cm", "D"][(bar - 1) % 4]


# chorus figure: Basic Pitch onsets of the keys stem folded over the ten passes (>= 5 of 10), [bar, beat, len, notes]
STAB = [
    [1, 1.0, 0.5, "D4 F#4 A4"], [1, 1.5, 0.25, "A#4"], [1, 1.75, 0.25, "A#4"], [1, 2.0, 0.5, "D4 G4"],
    [1, 2.25, 0.25, "D4"], [1, 2.5, 0.5, "D4 G4 A#4"], [1, 3.0, 0.5, "D4 G4 A#4"], [1, 3.5, 0.25, "D4 A#4"],
    [1, 3.75, 0.25, "D4 G4"], [1, 4.0, 0.5, "D4 G4 G5"], [1, 4.5, 0.5, "D4 G4 A#4"],
    [2, 1.0, 0.25, "D4 G4 A#4"], [2, 1.25, 0.25, "G4"], [2, 1.5, 0.5, "G4 A#4"], [2, 2.0, 0.5, "D#4 G4 D#5"],
    [2, 2.25, 0.25, "A#4"], [2, 2.5, 0.5, "D#4 G4 A#4"], [2, 3.0, 0.5, "D#4 G4 A#4"], [2, 3.5, 0.5, "G4 A#4"],
    [2, 4.0, 0.5, "D#4 G4 A#4"], [2, 4.5, 0.25, "D#4 G4 A#4"], [2, 4.75, 0.25, "G4"],
    [3, 1.0, 0.25, "D#4 G4 A#4 D#5"], [3, 1.25, 0.25, "A#4"], [3, 1.5, 0.25, "D#4 G4 A#4"], [3, 1.75, 0.25, "F4"],
    [3, 2.0, 0.5, "F4 F5"], [3, 2.25, 0.25, "A#4"], [3, 2.5, 0.25, "A#4 A#5"], [3, 2.75, 0.25, "F4"],
    [3, 3.0, 0.5, "D4 F4"], [3, 3.5, 0.25, "F4 A#4"], [3, 3.75, 0.25, "D4 A#4"], [3, 4.0, 0.25, "D4 F4"],
    [3, 4.25, 0.25, "A#4"], [3, 4.5, 0.5, "D4 F4 A4"],
    [4, 1.0, 0.5, "D4 F4"], [4, 1.25, 0.25, "A#4"], [4, 1.5, 0.5, "D4 A4"], [4, 2.0, 0.5, "D4 A4"],
    [4, 2.5, 0.25, "A4"], [4, 2.75, 0.25, "D4"], [4, 3.0, 0.5, "D4 A4"], [4, 3.5, 0.25, "F#4"], [4, 3.75, 0.25, "D4"],
    [4, 4.0, 0.5, "D4 F#4"], [4, 4.25, 0.25, "F#4"], [4, 4.5, 0.5, "F#4"]]
# the 8-bar phrases 65-72 and 89-96 add a C over the D bars (keys stem, narrow band: C4 0 dB on beats 3-4 of 68 / 92,
# C5 + C6 0 dB on beats 2-3 of 72 / 96); 33-40, 73-80, 97-104 have none (C4 / C5 below -35 dB there)
STAB_C = {65: [[4, 3.0, 2.0, "C4"], [8, 2.0, 2.0, "C5 C6"]], 89: [[4, 3.0, 2.0, "C4"], [8, 2.0, 2.0, "C5 C6"]]}


def tracks():
    import mido
    m = mido.MidiFile(MID); tpb = m.ticks_per_beat; out = {}
    for i, tr in enumerate(m.tracks):
        t = 0; on = collections.defaultdict(list); ns = []
        for msg in tr:
            t += msg.time
            if msg.type == "note_on" and msg.velocity > 0:
                on[msg.note].append(t)
            elif msg.type in ("note_off", "note_on") and on[msg.note]:
                s = on[msg.note].pop(0); ns.append((s / tpb, (t - s) / tpb, msg.note))
        out[i] = sorted(ns)
    return out


def cut(ns, mb0, mb1, ours):
    """Notes of MIDI bars [mb0, mb1) (1-based) -> [[our bar, beat, beats, "pitches"]], our bar of mb0 = ours."""
    grp = collections.OrderedDict()
    for s, d, p in ns:
        mb = int(s // 4) + 1
        if mb0 <= mb < mb1:
            grp.setdefault((ours + mb - mb0, round(s % 4 + 1, 3), round(d, 3)), set()).add(p)
    return [[b, bt, d, " ".join(name(p) for p in sorted(ps))] for (b, bt, d), ps in grp.items()]


def fix_poly(ns):
    """D-chord arpeggio: F#3 A3 C4 in the record, D3 F#3 A3 in the MIDI (bars with the arpeggio on 1 1.5 2)."""
    out = []
    for b, bt, d, p in ns:
        if chord_of(b) == "D" and bt in (1.0, 1.5, 2.0) and p in ("D3", "F#3", "A3"):
            p = {"D3": "F#3", "F#3": "A3", "A3": "C4"}[p]
        out.append([b, bt, d, p])
    return out


def fix_counter(ns):
    return [[b, bt, d, "A#4" if (chord_of(b) == "Gm" and bt == 4.5 and p == "F4") else p] for b, bt, d, p in ns]


def bp_events(stem):
    return json.load(open(os.path.join(BPDIR, f"{stem}.events.json")))


def brk_notes(song):
    """Breakdown 81-88: Basic Pitch onsets (amp >= 0.3) quantized to 16ths, kept where the same 16th and pitch has an
    onset in the other pass too (81-84 vs 85-88); bars 84 / 88 (different chords) keep their own strong ones."""
    t1 = song.t_stem(1); B = song.bar; hits = collections.defaultdict(list)
    for s, e, p, a in bp_events("keys"):
        q = int(round((s - t1) / B * 16)); bar = q // 16 + 1
        if 81 <= bar < 89 and a >= 0.3 and midi_of("D#2") <= p <= midi_of("C6"):
            hits[(bar, q % 16, p)].append((a, max(1, min(4, round((e - s) / B * 16)))))
    out = {}
    for (bar, k, p), v in hits.items():
        other = (bar + 4 if bar < 85 else bar - 4, k, p)
        if other in hits or (bar in (84, 88) and max(x[0] for x in v) >= 0.4):
            out.setdefault((bar, 1 + k / 4, int(np.median([x[1] for x in v]))), set()).add(p)
    return [[b, bt, ln / 4, " ".join(name(p) for p in sorted(ps))] for (b, bt, ln), ps in sorted(out.items())]


def strings_notes():
    ns = [[6, 3.0, 2.0, "G4 A#4 D5"], [7, 1.0, 4.0, "C4 G4 C5"], [8, 1.0, 4.0, "F#4 A4 C5"]]   # intro: strings enter on 6.3
    for bar in list(range(9, 41)) + list(range(43, 81)) + list(range(89, 105)) + [108, 109, 110, 111, 112]:
        v = VOICING_HOOK if any(h <= bar < h + 8 for h in HOOK) else VOICING
        ns.append([bar, 1.0, 4.0, v[chord_of(bar)]])
    return ns


def build(song, as_midi=False):
    T = tracks(); V = {}
    poly = cut(T[0], 1, 33, 1) + cut(T[0], 9, 17, 41) + cut(T[0], 17, 33, 49) + cut(T[0], 9, 17, 105)
    if not as_midi:     # the interlude has the verse arpeggio under the counter line (keys stem: D#3 G3 A#3 on 1 1& 2
        poly += [n for h in HOOK for n in cut(T[0], 17, 25, h) if n[1] in (1.0, 1.5, 2.0)]   # of bar 10), MIDI not
    V["poly"] = poly if as_midi else fix_poly(poly)
    counter = cut(T[2], 17, 33, 17) + cut(T[2], 17, 33, 49)
    V["counter"] = counter if as_midi else fix_counter(counter)
    if as_midi:
        V["strings"] = cut(T[2], 8, 17, 8)                                          # the MIDI's pad
        V["bright"] = cut(T[1], 1, 9, 1)
        return {vn: {"at": [1], "bars": END - 1, "notes": sorted(ns, key=lambda n: (n[0], n[1]))} for vn, ns in V.items()}
    V["strings"] = strings_notes()
    V["pad"] = [[at + k, 1.0, 4.0, PAD[k % 4]] for at in [1, 5] + [h + i for h in HOOK for i in (0, 4)] for k in range(4)]
    V["stab"] = [[at + n[0] - 1, *n[1:]] for at in CHORUS for n in STAB] + [[at + n[0] - 1, *n[1:]] for at, ns in STAB_C.items() for n in ns]
    V["brk"] = brk_notes(song)
    V["brk_pad"] = [[b, 1.0 + 2 * h, 2.0, BRK_PAD[b][h]] for b in range(81, 89) for h in (0, 1)]
    V["end"] = [[113, 1.0, 8.0, "G2 D3 G3 A#3 D4 G4"]]
    return {vn: dict({"at": [1], "bars": END - 1, "notes": sorted(ns, key=lambda n: (n[0], n[1]))},
                     **({"gap": 0.002} if vn in ("strings", "brk_pad") else {})) for vn, ns in V.items()}


def spans(notes):
    out = []
    for n in notes:
        b0 = int(n[0]); b1 = max(int(np.ceil(n[0] + (n[1] - 1 + n[2]) / 4 - 1e-6)), b0 + 1)
        if out and b0 <= out[-1][1] + 2:
            out[-1][1] = max(out[-1][1], b1)
        else:
            out.append([b0, b1])
    return out


def dump(part, path):
    """One note a line (json.dump with an indent makes thousands of lines)."""
    j = lambda x: json.dumps(x, ensure_ascii=False)
    out = ["{", f' "_about": {j(part["_about"])},', f' "stems": {j(part["stems"])},', ' "voices": {']
    vs = list(part["voices"].items())
    for i, (vn, v) in enumerate(vs):
        head = ", ".join(f"{j(k)}: {j(x)}" for k, x in v.items() if k != "notes")
        out.append(f'  {j(vn)}: {{{head}, "notes": [')
        out += [f"   {j(n)}" + ("," if k < len(v["notes"]) - 1 else "") for k, n in enumerate(v["notes"])]
        out.append("  ]}" + ("," if i < len(vs) - 1 else ""))
    out.append(" }")
    out.append("}")
    open(path, "w", encoding="utf-8").write("\n".join(out) + "\n")


def load(nm):
    s = importlib.util.spec_from_file_location(nm, os.path.join(REPO, "tools", nm + ".py"))
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


def cmd_bp():
    """Basic Pitch on the keys / strings stems -> analysis/.../bp/<stem>.events.json (needs the $BP env above)."""
    from pathlib import Path
    from basic_pitch.inference import predict
    import basic_pitch
    model = Path(basic_pitch.__file__).parent / "saved_models/icassp_2022/nmp.onnx"
    os.makedirs(BPDIR, exist_ok=True)
    for st in ("keys", "strings"):
        _, midi, ev = predict(os.path.join(SONG, f"{st}.wav"), model, onset_threshold=0.4, frame_threshold=0.25,
                              minimum_note_length=60, minimum_frequency=60, maximum_frequency=2500)
        midi.write(os.path.join(BPDIR, f"{st}.mid"))
        json.dump([[float(s), float(e), int(p), float(a)] for s, e, p, a, *_ in ev], open(os.path.join(BPDIR, f"{st}.events.json"), "w"))
        print(st, len(ev), "notes")


def cmd_notes():
    song = load("gm800_match").Song(NAME)
    V = build(song)
    part = {"_about": "Keys of «Медляк» (Moises keys + strings) written out as notes; generated by "
                      "tools/jamzone/prep_medlyak.py notes (edit there, not here). The MIDI from midifind "
                      "(parts/medlyak-midifind.mid, bars 1-32) with the record's pitches where they differ, chorus "
                      "and breakdown from the stem. G minor, mix.json bars. All voices go to the playback.",
            "stems": ["keys", "strings"], "voices": V}
    dump(part, PART)
    os.makedirs(OUT, exist_ok=True)
    dump({"_about": "The MIDI as it is (bars 1-32 and their repeats): A/B against parts/keys.notes.json",
          "stems": ["keys", "strings"], "voices": build(song, as_midi=True)}, ALT)
    print(PART)
    for vn, v in V.items():
        print(f"  {vn:8} {len(v['notes']):4} notes  bars " + " ".join(f"{a}-{b - 1}" for a, b in spans(v["notes"])))
    print(ALT)


# ---- preview: plain synth, render timeline ----------------------------------------------------------------------
SR = 44100
TIMBRE = {"poly": ("saw", 3000, 0.9, 0.6), "pad": ("pad", 2200, None, 0.22), "counter": ("square", 2200, None, 0.45), "strings": ("pad", 2500, None, 0.3),
          "stab": ("saw", 3500, 0.15, 0.4), "brk": ("square", 2600, 0.25, 0.45), "brk_pad": ("pad", 1800, None, 0.25),
          "end": ("pad", 2500, None, 0.4), "bright": ("square", 2600, None, 0.5)}


def synth(kind, fc, dec, f, dur):
    from scipy.signal import butter, sosfilt
    n = int((dur + 0.08) * SR); t = np.arange(n) / SR; ph = (f * t) % 1
    if kind == "square":
        x = np.where(ph < 0.5, 1.0, -1.0)
    elif kind == "pad":
        x = (2 * ph - 1) + (2 * ((f * 1.006 * t) % 1) - 1) + (2 * ((f * 0.994 * t) % 1) - 1)
    else:
        x = 2 * ph - 1
    if fc:
        x = sosfilt(butter(2, min(fc, 0.45 * SR), "lowpass", fs=SR, output="sos"), x)
    a = 0.12 if kind == "pad" else 0.004
    e = np.minimum(1, t / a)
    if dec:
        e = e * np.exp(-t / dec)
    r = int(0.06 * SR); e[-r:] *= np.linspace(1, 0, r)
    return x * e * 0.2


def render(song, gp, part, voices):
    n = int(round(song.t_render(END) * SR)) + 2 * SR; buf = np.zeros(n)
    for vn in voices:
        if vn not in part["voices"]:
            continue
        kind, fc, dec, g = TIMBRE[vn]
        for t, m, d in gp.voice_line(song, part, vn, 1, END):
            x = synth(kind, fc, dec, 440 * 2 ** ((m - 69) / 12), max(d, 0.03)) * g
            a = int((song.t_render(1) + t) * SR); k = min(len(x), n - a)
            buf[a:a + k] += x[:k]
    return buf


HTML = """
<h2>Голоса</h2>
<div class="wrap"><table>
<tr><th>Голос</th><th>Такты</th><th>Что играет</th><th>Откуда</th></tr>
<tr><td>poly</td><td class="n">1–32, 41–64, 105–112</td><td>рифф интро (арпеджио + мелодия), подголосок проигрыша, арпеджио куплета</td><td>MIDI, дорожка 0; на аккорде D арпеджио F#3 A3 C4 по записи; в проигрыше под подголоском арпеджио куплета (в MIDI его нет)</td></tr>
<tr><td>counter</td><td class="n">17–32, 49–64</td><td>второй голос куплета: A4 G4 на 2&amp; и 3&amp;</td><td>MIDI, дорожка 2; на 4&amp; аккорда Gm A#4 вместо F4</td></tr>
<tr><td>pad</td><td class="n">1–16, 41–48, 105–112</td><td>пэд с 9-ми под риффом: Gm9, E♭add9, Cm9, на D сверху F♯m (C♯ E)</td><td>запись (в MIDI нет)</td></tr>
<tr><td>strings</td><td class="n">6–40, 43–80, 89–104, 108–112</td><td>тянущиеся аккорды</td><td>стем strings; в проигрыше расклад как в MIDI</td></tr>
<tr><td>stab</td><td class="n">33–40, 65–80, 89–104</td><td>припев: аккорды восьмыми с подхватами шестнадцатыми и верхней октавой</td><td>запись (в MIDI припева нет)</td></tr>
<tr><td>brk + brk_pad</td><td class="n">81–88</td><td>брейкдаун: арпеджио шестнадцатыми и аккорды под ним</td><td>запись (в MIDI нет)</td></tr>
<tr><td>end</td><td class="n">113</td><td>последний Gm</td><td>запись</td></tr>
</table></div>
<p class="q">«Как в MIDI» есть только для тактов 1–32 и их повторов. Мелодия интро из MIDI (дорожка Bright) в стеме
клавиш не слышна — в «Мои ноты» её нет, в «Как в MIDI» она есть.</p>
"""


def cmd_preview():
    import soundfile as sf
    gp = load("gm800_part"); song = gp.gmm.Song(NAME); os.makedirs(PAGE, exist_ok=True)
    n = sf.info(os.path.join(SONG, "auto-render", "all.wav")).frames
    rd = lambda p: sf.read(p, always_2d=True, dtype="float64")[0].mean(1)
    fit = lambda x: np.pad(x, (0, max(0, n - len(x))))[:n]
    rms = lambda x, a, b: np.sqrt((x[int(song.t_render(a) * SR):int(song.t_render(b) * SR)] ** 2).mean()) + 1e-9
    # original: keys + strings at the render offset; in 82-88 the two stems carry the same audio -> strings muted there
    keys, strings = rd(song.stem("keys")), rd(song.stem("strings"))
    g = np.ones(len(strings)); a, b = int(song.t_stem(81.5) * SR), int(song.t_stem(89) * SR); r = int(0.05 * SR)
    g[a:b] = 0; g[a - r:a] = np.linspace(1, 0, r); g[b:b + r] = np.linspace(0, 1, r)
    orig = np.zeros(n); x = keys + strings * g; o = int(round(song.off * SR)); k = min(len(x), n - o); orig[o:o + k] = x[:k]
    mine, alt = json.load(open(PART, encoding="utf-8")), json.load(open(ALT, encoding="utf-8"))
    src = {"orig": orig, "mine": fit(render(song, gp, mine, list(TIMBRE))), "midi": fit(render(song, gp, alt, list(TIMBRE)))}
    ref = rms(orig, 9, 17)
    for kk in ("mine", "midi"):
        src[kk] = src[kk] * ref / rms(src["mine"], 9, 17)
    ctx = sum(fit(rd(os.path.join(SONG, "auto-render", p))) for p in ("stems/drums.mp3", "stems/vocal.mp3", "stems/bass.mp3"))
    ctx *= ref / rms(ctx, 17, 33) * 2.0
    peak = max(np.abs(v + ctx).max() for v in src.values())
    for kk, v in src.items():
        for tag, x in (("", v), ("-ctx", v + ctx)):
            p = os.path.join(PAGE, f"{kk}{tag}.mp3")
            subprocess.run(["ffmpeg", "-v", "quiet", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", "-b:a", "160k", p],
                           input=(x / peak * 0.9).astype(np.float32).tobytes(), check=True)
            print(p)
    import time
    meta = {"bar": song.bar, "bar1": song.t_render(1), "cues": SECTIONS, "dur": n / SR, "ctx": "-ctx",
            "ver": f"?v={int(time.time())}",
            "title": "Медляк — клавиши нотами",
            "sub": "Вся песня. Варианты сыграны простым синтом: здесь проверяются <b>ноты и ритм</b>, не звук — звук "
                   "подберём на ZENOLOGY. Переключение сохраняет место; L — петля по секции, C — с группой.",
            "tracks": [["1", "orig.mp3", "Оригинал", "стемы keys + strings", True],
                       ["2", "mine.mp3", "Мои ноты", "MIDI + правки по записи, припев и брейкдаун по записи"],
                       ["3", "midi.mp3", "Как в MIDI", "MIDI без правок (только такты 1–32 и их повторы)"]],
            "marks": [[1, "пэд с 9-ми"], [4, "D: арпеджио F#3 A3 C4, сверху F#m"], [9, "проигрыш: арпеджио + подголосок"], [17, "куплет: A#4 на 4& вместо F4"], [33, "припев: фигура восьмыми"], [68, "припев 2: C на D (D7)"],
                      [81, "брейкдаун: арпеджио"]],
            "html": HTML}
    tpl = open(os.path.join(REPO, "tools", "templates", "part-listen-full.html"), encoding="utf-8").read()
    open(os.path.join(PAGE, "index.html"), "w", encoding="utf-8").write(tpl.replace("/*META*/", json.dumps(meta, ensure_ascii=False)))
    print(os.path.join(PAGE, "index.html"))


if __name__ == "__main__":
    {"bp": cmd_bp, "notes": cmd_notes, "preview": cmd_preview}[sys.argv[1]]()
