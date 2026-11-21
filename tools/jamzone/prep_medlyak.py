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
  zr sweep ... / zr page ...                  # tone candidates (analysis/.../sweeps*.sh), then:
  $P tools/jamzone/prep_medlyak.py tonepage   # the tone page: what to listen for, Alex's picks, voice order

Key: G minor, pitch_semitones 0 (the band plays it in the record's key). Bars = mix.json bars, 105 bpm.
The MIDI (midifind, 7 tracks, 105 bpm, 4/4) is only 32 bars long: intro 1-8, interlude 9-16, verse 17-32.
MIDI bar = our bar (checked on track 0 against the keys stem: C5 -> A#4 on 2.5 / 3 of bars 9-12, the D#4 of 10.1.5).

What the keys of the record are (keys + strings stems; tools/part_notes.py, Basic Pitch onsets folded over the
passes of a section, narrow-band envelopes of single notes by 32nds):
  chords  Gm Eb Cm D (intro, interlude, verses), chorus Gm Eb Bb D, breakdown | Gm Cm | F | Eb | F | Gm Cm | F | Eb
          | Dm Bb |, end Gm.
  arp     the chord on 1 1& 2 (MIDI track 0 «Polysynth»): intro, interludes, verses. Stem fixes: on the D chord
          F#3 A3 C4 (D7), the MIDI has D3 F#3 A3 (keys stem bars 4, 8, 20, 24: no D3, C4 on beat 2 at -4 dB); the
          interludes have it too (D#3 G3 A#3 on 1 1& 2 of bar 10), the MIDI not; in the intro and the interludes it
          rings through the bar (G3 / A#3 of bars 1 5 9 41 105 still -5..-20 dB on beat 4), in the verse it is gone by
          beat 3 (-30..-47): there the notes are held to the end of the bar.
  lead    the verse's second line (MIDI track 2, A4 G4 on 2& 3&, ...) - the same line is the intro's melody, not what
          the MIDI has there (Alex 2026-11-21: «в интро 4 аккорд точно не тот, вроде так же как в куплете»; stem: A#4 on
          4& of bar 1, MIDI G3; D4 on 4 of bar 2, MIDI A#3; bar 4 G4 F#4 G4 A4, MIDI D4 C4). Stem fixes: beat 4& of the
          Gm bar is A#4, not F4 (A#4 -1 dB, F4 -33 dB, bars 17 21 25 29); the Cm bar is D4 (2&) C4 (3&) A#4 (4&), the MIDI
          has C4 D4 D#4 (same in the intro, bars 3 7).
  hookline the interlude's line (MIDI track 0, bars 9-16: C5 A#4 on 2& 3, ...; checked on the stem, right).
          arp / lead / hookline were one voice at first; Alex: «две разные партии пытаемся в одну запихнуть».
  Harmonics, not notes: the arpeggio's synth has a strong 3rd harmonic, so a held G3 A#3 D4 shows D5 F5 A5 and
          F#3 A3 shows C#5 E5 (they enter and leave with their fundamentals). A first draft took them for a pad
          with 9ths and «F#m on top of D»; Alex heard it was wrong.
  strings the strings stem: sustained triads; in the interlude (9-16) a step higher, as MIDI track 2 has them.
  chorus  (33-40, 65-80, 89-104; not in the MIDI) a pad and over it either a melody or a figure (Alex: «в оригинале
          звучит мелодия и подложка»; a first draft folded all onsets of the ten passes into one «8th-note chords» voice):
    cpad  triads D4 G4 A#4 | D#4 G4 A#4 | D4 F4 A#4 | D4 F#4 A4 with a slow attack (the chord seems to change late).
    mel   the 8-bar phrases 65-72 and 89-96: A#5 ... A#5 A5 G5 D5 | F5 D#5 . D#5 . D5 | D5 . D5 C5 | . C5 C5 D5 C5 | ...
          (the vocal's line A# A G F D# D with its own rhythm); Basic Pitch onsets >= C5 common to both passes.
    mel_lo  under it a low answer: C4 (3&) A#3 (4) A3 (4&) | A3 . A#3 (2) C4 (2&) | C4 . A#3 (2) of bars 3-5, C4 on 2 of 8.
    fig   33-40, 73-80, 97-104: 8ths, A5 on beats 1 3, the chord tone on 2 4 (G5 / D#5 / F5), A#5 on every &; on D
          a run C6 A#5 A5 G5 . F#5 F#5 A#5; the 8th bar D5 D6 A5 D6 F#5. Narrow-band envelopes by 16ths over 3 passes.
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
ARP_TOP = {"Gm": "D4", "Eb": "A#3", "Cm": "G3", "D": "C4"}    # highest note of the arpeggio on 1 1& 2
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


# chorus (Alex 2026-11-21: «в оригинале звучит мелодия и подложка»): over the pad the keys play either a melody
# (the 8-bar phrases 65-72, 89-96) or an 8th-note figure (33-40, 73-80, 97-104). Basic Pitch onsets >= C5 common to
# the passes (both melody passes, 2 of 3 figure passes), checked by narrow-band envelopes by 16ths.
FIG = ([[1, 1 + k / 2, 0.5, n] for k, n in enumerate("A5 A#5 G5 A#5 A5 A#5 G5 A#5".split())]          # Gm: A5 / G5
       + [[2, 1 + k / 2, 0.5, n] for k, n in enumerate("A5 A#5 D#5 A#5 A5 A#5 D#5 A#5".split())]      # Eb: A5 / D#5
       + [[3, 1 + k / 2, 0.5, n] for k, n in enumerate("A5 A#5 F5 A#5 A5 A#5 F5 A5".split())]        # Bb: A5 / F5
       + [[4, 1.0, 0.5, "C5 C6"], [4, 1.5, 0.5, "A#5"], [4, 2.0, 0.5, "A5"], [4, 2.5, 1.0, "G5"],       # D: run down
          [4, 3.5, 0.5, "F#5"], [4, 4.0, 0.5, "F#5"], [4, 4.5, 0.5, "A#5"]])
FIG = FIG + [[n[0] + 4, *n[1:]] for n in FIG if n[0] < 4] + [
    [8, 1.0, 0.5, "D5 D6"], [8, 1.5, 0.5, "A5"], [8, 2.0, 0.5, "D6"], [8, 2.5, 2.0, "F#5"]]           # last bar: D
# the figure is played in two octaves, the lower one louder (keys stem, 6 passes: A4 on 1 and 3 at 0 dB vs A5 -7, G4 on 2
# and 4 -1 vs G5 -6, A#4 on the &s 0 vs A#5 -5; Eb: D#4 0 vs D#5 -8)
_lo = lambda ps: " ".join(sorted({p for q in ps.split() for p in (q, NAMES[midi_of(q) % 12] + str(midi_of(q) // 12 - 2))}, key=midi_of))
FIG = [[b, bt, d, _lo(ps)] for b, bt, d, ps in FIG]
MEL = [[1, 1.75, 0.75, "A#5"], [1, 3.0, 0.5, "A#5"], [1, 3.5, 0.5, "A5"], [1, 4.0, 0.5, "G5"], [1, 4.5, 0.5, "D5"],
       [2, 1.0, 0.5, "F5"], [2, 1.5, 1.5, "D#5"], [2, 3.0, 1.5, "D#5"], [2, 4.5, 0.5, "D5"],
       [3, 1.0, 0.5, "D5"], [3, 1.5, 1.0, "D5"], [3, 3.0, 0.5, "D5"], [3, 3.5, 1.0, "C5"],
       [4, 2.5, 0.5, "C5"], [4, 3.0, 1.0, "C5"], [4, 4.0, 0.5, "D5"], [4, 4.5, 1.0, "C5"],
       [5, 3.0, 0.5, "A#5"], [5, 3.5, 0.5, "A5"], [5, 4.0, 0.5, "G5"], [5, 4.5, 0.5, "D5"],
       [6, 1.0, 0.5, "F5"], [6, 1.5, 1.5, "D#5"], [6, 3.0, 1.5, "D#5"], [6, 4.5, 0.5, "F5"],
       [7, 1.0, 0.5, "D#5"], [7, 1.5, 0.5, "D#5"], [7, 2.0, 0.5, "A#5"], [7, 2.5, 1.5, "A#5"], [7, 4.5, 0.5, "D5"],
       [8, 1.0, 0.5, "D#5"], [8, 1.5, 0.5, "D5"], [8, 2.25, 0.25, "C5"], [8, 2.5, 0.5, "C5 C6"], [8, 3.0, 0.5, "C5"],
       [8, 3.5, 0.75, "C5"], [8, 4.5, 0.5, "C5"]]
# under the melody a low answer, same phrases (keys stem by 8ths, both passes, against D4 of the pad: C4 -4 / A#3 -3 /
# A3 -4 dB in bar 3, A#3 -4 / C4 -1 in bar 4, A#3 -4 in bar 5, C4 -6 in bar 8)
MEL_LO = [[3, 3.5, 0.5, "C4"], [3, 4.0, 0.5, "A#3"], [3, 4.5, 1.5, "A3"], [4, 2.0, 0.5, "A#3"], [4, 2.5, 3.0, "C4"],
          [5, 2.0, 1.0, "A#3"], [8, 2.0, 1.0, "C4"]]
MEL_AT, FIG_AT = [65, 89], [33, 73, 97]
# tones Alex picked on the ZENOLOGY page (2026-11-21)
ZEN = {"strings": "ZEZ003 Liquid/7", "brk": "PRST_J Nebulous Forms/6",     # Mercurial, Dreamer Keys
       "arp": "ZEZ001 Hazy Pop/1", "cpad": "PRST_D Basic Synth/490",        # Rocket Pad, Dreaming 5
       "fig": "PRST_A Factory Presets/38",                                  # AX Analog Dream ...
       "mel": "PRST_F Essential/582",                                       # Fantasy 2 (F/582 or D/477: Alex to say)
       "lead": "PRST_D Basic Synth/381", "hookline": "PRST_F Essential/382"}  # Saw Dtune + FX, Trumpet + filter (round 5)
ZEN_LAYER = {"fig": ("PRST_D Basic Synth/891", -6.0)}                       # ... + Dance Saw 2 at -6 dB («жирок»)
ROMA = os.path.join(OUT, "roma", "roma-keys-stemframe.wav")   # Roma's keys of the 28.10 concert (ch 08) in the stem frame:
# concert_t = a + b * render_t of the render of 2026-11-17 (OFF 4.229 s), a/b from 472 clicks (tools/concert-2810);
# his attacks are 10 ms ahead of our 16th grid, no extra shift


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
    """The second line as Roma played it at the 28.10 concert (his keys channel, clean; Alex: «он там какую-то партию
    играл довольно точно»): Gm A4 (2&) G4 (3&) and nothing on 4& (the MIDI has F4, a first reading of the stem A#4 -
    the 2nd/3rd harmonics of the low pickups G3 / D#3 that the record plays on 4&); Cm D4 (2&) C4 (3&) C4 (4&), the
    MIDI has C4 D4 D#4. Intro and verse alike (Roma: bars 1-8, 17-20)."""
    out = []
    for b, bt, d, p in ns:
        if chord_of(b) == "Gm" and bt == 4.5:
            continue
        if chord_of(b) == "Gm" and bt == 3.5:
            d = 1.5
        if chord_of(b) == "Cm":
            p = {2.5: "D4", 3.5: "C4", 4.5: "C4"}.get(bt, p)
        out.append([b, bt, d, p])
    return out


# the line (intro melody = verse second line) by chord: Roma's notes (concert 28.10), lengths as in the record (keys stem,
# narrow band, end = 9 dB under the note's peak; Alex: «сильно долго ноты зажаты, на которых заканчиваются фразы»:
# the phrase ends G4 / C4 / A4 sound 3/4-1 beat, the first version held G4 1.5 beats)
LINE = {"Gm": [[2.5, 1.0, "A4"], [3.5, 0.75, "G4"]],
        "Eb": [[2.5, 1.0, "F4"], [3.5, 0.5, "D#4"], [4.0, 0.5, "D4"], [4.5, 0.5, "D#4"]],
        "Cm": [[2.5, 1.0, "D4"], [3.5, 1.0, "C4"]],
        "D": [[2.5, 1.0, "G4"], [3.5, 0.5, "F#4"], [4.0, 0.5, "G4"], [4.5, 0.75, "A4"]]}


def line_notes(bars):
    return [[b, bt, d, p] for b in bars for bt, d, p in LINE[chord_of(b)]]


def roma_events():
    p = os.path.join(BPDIR, "roma.events.json")
    return json.load(open(p)) if os.path.exists(p) else None


def roma_intro_arp(song):
    """Intro bars 1-8, the chord under the line as Roma played it (Alex: «нужно чтобы играли те же ноты, которые играет
    Рома»): his Basic Pitch notes up to D4, amplitude >= 0.5 - the arpeggio on 1 1& 2 and his chord repeats under the
    line (A#3 / A3 D4 on 2& 3&); each rings until the same pitch comes again or the bar ends (the record sustains)."""
    ev = roma_events(); t1 = song.t_stem(1); B = song.bar; hits = {}
    for s_, e, p, a in ev:
        q = int(round((s_ - t1) / B * 16)); bar = q // 16 + 1
        if 1 <= bar <= 8 and a >= 0.5 and p <= midi_of("D4"):
            hits[(bar, 1 + (q % 16) / 4, p)] = True
    ns = sorted(hits)
    out = []
    for i, (bar, bt, p) in enumerate(ns):
        t = bar + (bt - 1) / 4; nxt = min([b2 + (bt2 - 1) / 4 for b2, bt2, p2 in ns if p2 == p and b2 + (bt2 - 1) / 4 > t + 1e-6] + [bar + 1.0])
        out.append([bar, bt, round((nxt - t) * 4, 3), name(p)])
    return out


# breakdown solo (Alex: «на 3:08 потерялось соло, там должно быть ярко выраженное»): the long notes over the 16th-note
# arpeggio, keys stem 81-88, narrow-band envelopes by 16ths folded over the two passes; each 4 bars
SOLO = [[1, 3.0, 2.0, "C6"], [2, 1.0, 0.5, "C6"], [2, 1.5, 2.5, "A5"], [2, 4.0, 1.0, "F5"],
        [3, 1.0, 2.0, "D#5"], [3, 3.0, 2.0, "A#5"], [4, 1.75, 1.25, "A5"], [4, 3.0, 1.0, "C6"], [4, 4.25, 0.75, "D5"]]
# bar 88 leads into the chorus instead: A5 A5, then C5 ... A#4 C5 B4 A#4 (Basic Pitch on keys: C5 0.6-0.7, B4 0.77 on 4&)
SOLO_88 = [[88, 1.75, 0.75, "A5"], [88, 2.5, 0.5, "A5"], [88, 3.0, 0.5, "C5"], [88, 3.5, 0.5, "C5"],
           [88, 4.0, 0.25, "A#4"], [88, 4.25, 0.25, "C5"], [88, 4.5, 0.25, "B4"], [88, 4.75, 0.25, "A#4"]]


def held(ns, bars):
    """The arpeggio notes (1 1& 2, up to ARP_TOP) of the given bars ring to the end of the bar, or until the same
    pitch is struck again; every other note stays as it is. Duplicates (same bar, beat, pitch) are merged."""
    single = sorted({(b, bt, p): d for b, bt, d, ps in ns for p in ps.split()}.items())
    on = collections.defaultdict(list)
    for (b, bt, p), d in single:
        on[p].append(b + (bt - 1) / 4)
    out = []
    for (b, bt, p), d in single:
        if b in bars and bt in (1.0, 1.5, 2.0) and midi_of(p) <= midi_of(ARP_TOP[chord_of(b)]):
            t = b + (bt - 1) / 4; nxt = min([x for x in on[p] if x > t + 1e-6] + [b + 1.0])
            d = round((nxt - t) * 4, 3)
        out.append([b, bt, d, p])
    return out


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
    ns = [[6, 3.0, 2.0, "D#4 G4 A#4"], [7, 1.0, 4.0, "C4 D#4 G4"], [8, 1.0, 4.0, "D4 F#4 A4"]]   # intro: strings enter on 6.3
    for bar in list(range(9, 41)) + list(range(43, 81)) + list(range(89, 105)) + [108, 109, 110, 111, 112]:
        v = VOICING_HOOK if any(h <= bar < h + 8 for h in HOOK) else VOICING
        ns.append([bar, 1.0, 4.0, v[chord_of(bar)]])
    return ns


def build(song, as_midi=False):
    T = tracks(); V = {}
    if as_midi:
        V["poly"] = cut(T[0], 1, 33, 1) + cut(T[0], 9, 17, 41) + cut(T[0], 17, 33, 49) + cut(T[0], 9, 17, 105)
        V["counter"] = cut(T[2], 17, 33, 17) + cut(T[2], 17, 33, 49)
    else:   # three parts (Alex: «две разные партии пытаемся в одну запихнуть»)
        # arp: the chord on 1 1& 2 - intro (MIDI track 0), verses (track 0), interludes (the verse's, keys stem: D#3 G3
        # A#3 on 1 1& 2 of bar 10, the MIDI has none); rings through the bar in the intro and the interludes
        arp = (cut(T[0], 17, 33, 17) + cut(T[0], 17, 33, 49) + [n for h in HOOK for n in cut(T[0], 17, 25, h) if n[1] in (1.0, 1.5, 2.0)])
        arp = held(fix_poly(arp), {h + i for h in HOOK for i in range(8)})
        V["arp"] = (roma_intro_arp(song) if roma_events() else held(fix_poly([n for n in cut(T[0], 1, 9, 1) if n[1] in (1.0, 1.5, 2.0)]), set(range(1, 9)))) + arp
        # lead: the verse's second line, the same line is the intro's melody (LINE); bar 8: D4 only (Roma, no pickup)
        V["lead"] = line_notes(list(range(1, 8)) + list(range(17, 33)) + list(range(49, 65))) + [[8, 2.5, 1.5, "D4"]]
        # hookline: the interlude's line (track 0, bars 9-16: C5 A#4 on 2& 3, ...)
        V["hookline"] = [n for h in HOOK for n in cut(T[0], 9, 17, h)]
    if as_midi:
        V["strings"] = cut(T[2], 8, 17, 8)                                          # the MIDI's pad
        V["bright"] = cut(T[1], 1, 9, 1)
        return {vn: {"at": [1], "bars": END - 1, "notes": sorted(ns, key=lambda n: (n[0], n[1]))} for vn, ns in V.items()}
    V["strings"] = strings_notes()
    V["cpad"] = [[b, 1.0, 4.0, VOICING[chord_of(b)]] for at in CHORUS for b in range(at, at + 4)]
    V["mel"] = [[at + n[0] - 1, *n[1:]] for at in MEL_AT for n in MEL]
    V["mel_lo"] = [[at + n[0] - 1, *n[1:]] for at in MEL_AT for n in MEL_LO]
    V["fig"] = [[at + n[0] - 1, *n[1:]] for at in FIG_AT for n in FIG]
    solo = [[at + n[0] - 1, *n[1:]] for at in (81, 85) for n in SOLO if at + n[0] - 1 != 88] + SOLO_88
    V["solo"] = solo
    taken = {(b, bt, p) for b, bt, d, p in solo}                 # the arpeggio without the solo's own notes (no doubling)
    V["brk"] = [[b, bt, d, " ".join(q for q in ps.split() if not any((b, bt + dd, q) in taken for dd in (-0.25, 0, 0.25)))]
                for b, bt, d, ps in brk_notes(song)]
    V["brk"] = [n for n in V["brk"] if n[3]]
    V["brk_pad"] = [[b, 1.0 + 2 * h, 2.0, BRK_PAD[b][h]] for b in range(81, 89) for h in (0, 1)]
    V["end"] = [[113, 1.0, 8.0, "G2 D3 G3 A#3 D4 G4"]]
    return {vn: dict({"at": [1], "bars": END - 1, "notes": sorted(ns, key=lambda n: (n[0], n[1]))},
                     **({"gap": 0.002} if vn in ("strings", "brk_pad", "cpad") else {})) for vn, ns in V.items()}


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
    out.append(" }" + ("," if "layer" in part else ""))
    if "layer" in part:
        tk = part["layer"]["takes"]
        out.append(f' "layer": {{"file": {j(part["layer"]["file"])}, "takes": [')
        out += [f"  {j(t)}" + ("," if k < len(tk) - 1 else "") for k, t in enumerate(tk)]
        out.append(" ]}")
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
    for st, src in (("keys", os.path.join(SONG, "keys.wav")), ("strings", os.path.join(SONG, "strings.wav")), ("roma", ROMA)):
        if not os.path.exists(src):
            continue
        _, midi, ev = predict(src, model, onset_threshold=0.4, frame_threshold=0.25,
                              minimum_note_length=60, minimum_frequency=60, maximum_frequency=2500)
        midi.write(os.path.join(BPDIR, f"{st}.mid"))
        json.dump([[float(s), float(e), int(p), float(a)] for s, e, p, a, *_ in ev], open(os.path.join(BPDIR, f"{st}.events.json"), "w"))
        print(st, len(ev), "notes")


TRIM = {"mel": 6.0, "fig": 9.0, "cpad": -2.0, "solo": 9.0, "brk": 10.0, "brk_pad": -3.0}                                        # dB on top of the fitted gain (see cmd_calibrate)
GAINS = os.path.join(SONG, "parts", "keys.gains.json")      # "voice@tone" -> dB of its takes: written by `calibrate`


def layer_spec():
    """Voice -> [(take key, {zen, vel, fx})]: Alex's tones (ZEN), the effects he heard them with on the pages."""
    L = lambda nm, kw: [nm, kw]
    fxj = lambda chain: [L(nm, kw) for nm, kw in chain]
    sp = {"arp": [{"zen": ZEN["arp"]}], "lead": [{"zen": ZEN["lead"], "fx": fxj(FX_LEAD)}],
          "hookline": [{"zen": ZEN["hookline"], "vel": 80, "fx": [L("LowpassFilter", {"cutoff_frequency_hz": 3000})] + fxj(FX_BRASS)}],
          "strings": [{"zen": ZEN["strings"]}], "cpad": [{"zen": ZEN["cpad"]}], "mel": [{"zen": ZEN["mel"]}],
          "mel_lo": [{"zen": ZEN["mel"]}],                    # the low answer: the melody's tone (not picked on its own)
          "fig": [{"zen": ZEN["fig"]}, {"zen": ZEN_LAYER["fig"][0]}],
          "solo": [{"zen": ZEN.get("solo", ZEN["lead"]), "fx": fxj(FX_LEAD)}],                    # solo: lead's tone until picked
          "brk": [{"zen": ZEN["brk"]}], "brk_pad": [{"zen": ZEN["strings"]}],   # chords under the breakdown, the end chord:
          "end": [{"zen": ZEN["strings"]}]}                                      # Mercurial until Alex says otherwise
    return sp


def layer_takes(V):
    gains = json.load(open(GAINS, encoding="utf-8")) if os.path.exists(GAINS) else {}
    takes = []
    for vn, specs in layer_spec().items():
        for sp in spans(V[vn]["notes"]):
            for spec in specs:
                tk = dict({"voice": vn, "bars": sp, "gain_db": round(gains.get(f"{vn}@{spec['zen']}", 0.0), 1)}, **spec)
                takes.append(tk)
    return takes


def cmd_notes():
    song = load("gm800_match").Song(NAME)
    V = build(song)
    part = {"_about": "Keys of «Медляк» (Moises keys + strings) written out as notes; generated by "
                      "tools/jamzone/prep_medlyak.py notes (edit there, not here). The MIDI from midifind "
                      "(parts/medlyak-midifind.mid, bars 1-32) with the record's pitches where they differ, chorus "
                      "and breakdown from the stem. G minor, mix.json bars. All voices go to the playback.",
            "stems": ["keys", "strings"], "voices": V, "layer": {"file": "pb-keys", "takes": layer_takes(V)}}
    dump(part, PART)
    os.makedirs(OUT, exist_ok=True)
    dump({"_about": "The MIDI as it is (bars 1-32 and their repeats): A/B against parts/keys.notes.json",
          "stems": ["keys", "strings"], "voices": build(song, as_midi=True)}, ALT)
    print(PART)
    for vn, v in V.items():
        print(f"  {vn:8} {len(v['notes']):4} notes  bars " + " ".join(f"{a}-{b - 1}" for a, b in spans(v["notes"])))
    print(f"  layer: {len(part['layer']['takes'])} takes")
    print(ALT)


CAND = os.path.join(OUT, "pb-keys-candidate.wav")          # the layer to listen to before it goes to parts/ and mix.json
BANDS = [60, 120, 240, 480, 960, 1920, 3840, 7680, 15000]


def target_audio(song):
    """What the layer replaces: Moises keys + strings; in 82-88 the two stems are the same audio -> strings muted there."""
    import soundfile as sf
    rd = lambda p: sf.read(p, always_2d=True, dtype="float64")
    (k, sr), (st, _) = rd(song.stem("keys")), rd(song.stem("strings"))
    g = np.ones(len(st)); a, b = int(song.t_stem(81.5) * sr), int(song.t_stem(89) * sr); r = int(0.05 * sr)
    g[a:b] = 0; g[a - r:a] = np.linspace(1, 0, r); g[b:b + r] = np.linspace(0, 1, r)
    return k + st * g[:, None], sr


def bar_bands(x, sr, song):
    """Power by bar (1..END-1) and octave band: the picture the voice gains are fitted on."""
    from scipy.signal import stft
    f, t, Z = stft(x.mean(1) if x.ndim == 2 else x, fs=sr, nperseg=4096, noverlap=2048); P = np.abs(Z) ** 2
    out = np.zeros((END - 1, len(BANDS) - 1))
    for b in range(1, END):
        m = (t >= song.t_stem(b)) & (t < song.t_stem(b + 1))
        for i in range(len(BANDS) - 1):
            out[b - 1, i] = P[(f >= BANDS[i]) & (f < BANDS[i + 1])][:, m].sum() if m.any() else 0
    return out


def cmd_calibrate():
    """One gain per voice@tone: non-negative least squares of the bar x octave-band powers of every voice's own layer
    against keys + strings (each band weighted by its mean, so the lows do not decide alone) -> parts/keys.gains.json.
    Needs the takes (zr record) and pedalboard (the fx chains): run in the zr env."""
    import re, soundfile as sf
    from scipy.optimize import nnls
    gp = load("gm800_part"); song = gp.gmm.Song(NAME); part = json.load(open(PART, encoding="utf-8"))
    cal = os.path.join(OUT, "cal"); keys = sorted({(t["voice"], t["zen"]) for t in part["layer"]["takes"]}, key=lambda k: list(layer_spec()).index(k[0]))
    tgt, sr = target_audio(song); T = bar_bands(tgt, sr, song); cols = []; names = []
    for vn, z in keys:
        d = os.path.join(cal, re.sub(r"[^A-Za-z0-9]+", "_", f"{vn}_{z}")); os.makedirs(d, exist_ok=True)
        q = dict(part); q["layer"] = {"file": "x", "takes": [dict(t, gain_db=0.0) for t in part["layer"]["takes"] if (t["voice"], t["zen"]) == (vn, z)]}
        f = os.path.join(d, "keys.notes.json"); json.dump(q, open(f, "w", encoding="utf-8"), ensure_ascii=False)   # same basename:
        out = os.path.join(d, "layer.wav"); gp.cmd_layer(song, f, out)                                        # same take files
        y, ysr = sf.read(out, always_2d=True, dtype="float64"); cols.append(bar_bands(y, ysr, song)); names.append(f"{vn}@{z}")
    # the saw under AX Analog Dream sits where Alex picked it: 6 dB under AX at the same RMS -> one column, fixed ratio
    ax, saw = f"fig@{ZEN['fig']}", f"fig@{ZEN_LAYER['fig'][0]}"; ia, isw = names.index(ax), names.index(saw)
    pw = lambda c: c.sum() + 1e-12
    ratio = 10 ** (ZEN_LAYER["fig"][1] / 10) * pw(cols[ia]) / pw(cols[isw])          # power ratio saw : ax
    fit_cols = [c for i, c in enumerate(cols) if i != isw]; fit_cols[ia] = cols[ia] + ratio * cols[isw]
    fit_names = [n for i, n in enumerate(names) if i != isw]
    # bounds: a voice can not be louder than if it alone made all the energy of its band (its notes x 0.9 .. x 2.2) in its
    # bars of the stem it replaces, nor 9 dB under that (a plain fit drowned the chorus figure under the pads, -30 dB)
    from scipy.optimize import lsq_linear
    from scipy.signal import stft
    stem_p = {}
    def band_prior(nm, c_all):
        vn = nm.split("@")[0]; st = "strings" if vn == "strings" else "keys"
        if st not in stem_p:
            y, ysr = sf.read(song.stem(st), always_2d=True); f, t, Z = stft(y.mean(1), fs=ysr, nperseg=4096, noverlap=2048); stem_p[st] = (f, t, np.abs(Z) ** 2)
        tks = [t_ for t_ in part["layer"]["takes"] if f"{t_['voice']}@{t_['zen']}" == nm]
        notes = [n for t_ in tks for _, n, _ in gp.voice_line(song, part, vn, *t_["bars"])]
        lo, hi = 440 * 2 ** ((min(notes) - 69) / 12) * 0.9, 440 * 2 ** ((max(notes) - 69) / 12) * 2.2
        def bp(f, t, P):
            m = np.zeros(len(t), bool)
            for t_ in tks:
                m |= (t >= song.t_stem(t_["bars"][0])) & (t < song.t_stem(t_["bars"][1]))
            return P[(f >= lo) & (f < hi)][:, m].sum()
        y, ysr = c_all; f, t, Z = stft(y.mean(1), fs=ysr, nperseg=4096, noverlap=2048)
        return 10 * np.log10(bp(*stem_p[st]) / (bp(f, t, np.abs(Z) ** 2) + 1e-12))
    audio = {nm: sf.read(os.path.join(cal, re.sub(r"[^A-Za-z0-9]+", "_", nm.replace("@", "_")), "layer.wav"), always_2d=True) for nm in names}
    prior = {nm: band_prior(nm, audio[nm]) for nm in fit_names}
    w = 1 / (T.mean(0) + 1e-12)
    A = np.stack([(c * w).ravel() for c in fit_cols], 1)
    lb = np.array([10 ** ((prior[nm] - 9) / 10) for nm in fit_names]); ub = np.array([10 ** ((prior[nm] + 3) / 10) for nm in fit_names])
    g = lsq_linear(A, (T * w).ravel(), bounds=(lb, ub)).x
    db = {nm: float(10 * np.log10(x + 1e-12)) for nm, x in zip(fit_names, g)}
    print("band bounds (dB):", {k: round(v, 1) for k, v in prior.items()})
    db[saw] = db[ax] + 10 * np.log10(ratio)
    # by the notes (pn --take, candidate against the stem, chorus 89-92): the melody stood 8 dB lower against the pad
    # than in the record -> lifted after the fit
    for nm in names:
        db[nm] += TRIM.get(nm.split("@")[0], 0.0)
    # voices that play alone in their section are levelled to it (the global fit leaves the breakdown +3.6 dB, the end -3.7)
    for (b0, b1), vs in {(81, 89): ["brk", "brk_pad", "solo"], (113, 115): ["end"]}.items():
        Lc = sum(10 ** (db[nm] / 10) * c for nm, c in zip(names, cols))
        d = 10 * np.log10(T[b0 - 1:b1 - 1].sum() / (Lc[b0 - 1:b1 - 1].sum() + 1e-12))
        for nm in names:
            if nm.split("@")[0] in vs:
                db[nm] += d
    json.dump({k: round(v, 1) for k, v in db.items()}, open(GAINS, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("gains (dB):"); [print(f"  {k:48} {v:+6.1f}") for k, v in db.items()]
    L = sum(10 ** (db[nm] / 10) * c for nm, c in zip(names, cols))
    lvl = lambda M, b0, b1: 10 * np.log10(M[b0 - 1:b1 - 1].sum() + 1e-12)
    print("section    record   layer   (dB, all bands)")
    for (b0, nm), (b1, _) in zip(SECTIONS, SECTIONS[1:] + [(END, "")]):
        print(f"  {b0:3}-{b1 - 1:<3} {nm:24} {lvl(T, b0, b1) - lvl(T, 17, 33):+6.1f}  {lvl(L, b0, b1) - lvl(T, 17, 33):+6.1f}")
    print(GAINS)


def cmd_candidate():
    """The layer with the calibrated gains -> analysis/.../pb-keys-candidate.wav (stem frame); then `preview` puts it on
    the notes page next to the original. parts/ and mix.json stay as they are until Alex says so."""
    gp = load("gm800_part"); song = gp.gmm.Song(NAME); gp.cmd_layer(song, PART, CAND); print(CAND)


# ---- preview: plain synth, render timeline ----------------------------------------------------------------------
SR = 44100
TIMBRE = {"arp": ("saw", 3000, 0.9, 0.5), "lead": ("square", 2400, None, 0.45), "hookline": ("square", 2400, None, 0.45),
          "cpad": ("pad", 2000, None, 0.2), "mel": ("saw", 3500, None, 0.45), "mel_lo": ("saw", 2500, None, 0.45), "solo": ("saw", 3500, None, 0.5), "fig": ("square", 3000, 0.2, 0.35),
          "poly": ("saw", 3000, 0.9, 0.6), "pad": ("pad", 2200, None, 0.22), "counter": ("square", 2200, None, 0.45), "strings": ("pad", 2500, None, 0.3),
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
<tr><td>arp</td><td class="n">1–32, 41–64, 105–112</td><td>арпеджио на 1 1&amp; 2</td><td>MIDI, дорожка 0; на D F#3 A3 C4; в интро и проигрышах тянется весь такт, в куплете короткое; в проигрышах его в MIDI нет</td></tr>
<tr><td>lead</td><td class="n">1–8, 17–32, 49–64</td><td>мелодия интро = второй голос куплета: A4 G4 на 2&amp; и 3&amp;…</td><td>MIDI, дорожка 2, правки по Роме (концерт 28.10): на 4&amp; Gm ничего (в MIDI F4), на Cm D4 C4 C4 (в MIDI C4 D4 D#4)</td></tr>
<tr><td>hookline</td><td class="n">9–16, 41–48, 105–112</td><td>подголосок проигрыша: C5 A#4 на 2&amp; 3…</td><td>MIDI, дорожка 0</td></tr>
<tr><td>strings</td><td class="n">6–40, 43–80, 89–104, 108–112</td><td>тянущиеся аккорды</td><td>стем strings; в проигрыше расклад как в MIDI</td></tr>
<tr><td>cpad</td><td class="n">33–40, 65–80, 89–104</td><td>подложка припева: трезвучия</td><td>запись (в MIDI припева нет)</td></tr>
<tr><td>mel</td><td class="n">65–72, 89–96</td><td>мелодия припева: A#5 A5 G5 D5 | F5 D#5 … | D5 C5 | C5 D5 C5</td><td>запись</td></tr>
<tr><td>mel_lo</td><td class="n">67–69, 72, 91–93, 96</td><td>низкий ответ под мелодией: C4 A#3 A3 | A#3 C4 | A#3</td><td>запись</td></tr>
<tr><td>fig</td><td class="n">33–40, 73–80, 97–104</td><td>фигура восьмыми: A5 A#5 G5 A#5 … (на Eb D#5, на Bb F5), на D сбег</td><td>запись</td></tr>
<tr><td>solo</td><td class="n">81–88</td><td>соло брейкдауна: C6 | C6 A5 … F5 | D#5 A#5 | A5 C6 D5</td><td>запись</td></tr>
<tr><td>brk + brk_pad</td><td class="n">81–88</td><td>брейкдаун: арпеджио шестнадцатыми и аккорды под ним</td><td>запись (в MIDI нет)</td></tr>
<tr><td>end</td><td class="n">113</td><td>последний Gm</td><td>запись</td></tr>
</table></div>
<p class="q">«Как в MIDI» есть только для тактов 1–32 и их повторов. Мелодия интро из MIDI (дорожка Bright) в стеме
клавиш не слышна — в «Мои ноты» её нет, в «Как в MIDI» она есть.</p>
<p class="q">Исправлено после первого прослушивания: «пэд с 9-ми» и «F♯m сверху на D» оказались призвуками самого
арпеджио (у синта сильная 3-я гармоника: G3 A♯3 D4 дают D5 F5 A5, F♯3 A3 — C♯5 E5) — убраны. D в интро теперь как в
куплете.</p>
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
    if os.path.exists(ROMA):                                   # Roma at the concert, stem frame -> render frame
        r = rd(ROMA); rr = np.zeros(n); k = min(len(r), n - o); rr[o:o + k] = r[:k]; src["roma"] = rr
    if os.path.exists(CAND):                                   # the candidate layer at its calibrated level (no matching)
        r = rd(CAND); cc = np.zeros(n); k = min(len(r), n - o); cc[o:o + k] = r[:k]; src["cand"] = cc
    ref = rms(orig, 9, 17)
    for kk in ("mine", "midi"):
        src[kk] = src[kk] * ref / rms(src["mine"], 9, 17)
    if "roma" in src:
        src["roma"] *= ref / rms(src["roma"], 9, 17)
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
                       ["3", "midi.mp3", "Как в MIDI", "MIDI без правок (только такты 1–32 и их повторы)"]]
                      + ([["4", "roma.mp3", "Рома, концерт 28.10", "его клавиши с пульта; брейкдаун он не играл", True]] if "roma" in src else [])
                      + ([["5", "cand.mp3", "Слой: выбранные тоны", "все голоса тонами ZENOLOGY с эффектами, уровни по стему — кандидат в плейбек"]] if "cand" in src else []),
            "marks": [[1, "интро: мелодия как у Ромы (A G | F D# D D# | D C C | G F# G A)"], [4, "D: F#3 A3 C4 + G4 F#4 G4 A4, как в куплете"], [17, "куплет: та же линия, как у Ромы"], [9, "проигрыш: арпеджио + подголосок"], [33, "припев: фигура восьмыми + подложка"], [65, "припев: мелодия + подложка"], [73, "фигура"], [89, "мелодия"], [97, "фигура"],
                      [81, "брейкдаун: арпеджио"]],
            "html": HTML}
    tpl = open(os.path.join(REPO, "tools", "templates", "part-listen-full.html"), encoding="utf-8").read()
    open(os.path.join(PAGE, "index.html"), "w", encoding="utf-8").write(tpl.replace("/*META*/", json.dumps(meta, ensure_ascii=False)))
    print(os.path.join(PAGE, "index.html"))


# ---- the ZENOLOGY tone page (zenology_render.py page) with what to listen for in the original -----------------
HINT = {"arp": "в оригинале слушай арпеджио на 1 1& 2 (G3 A♯3 D4…, тянется весь такт); мелодия над ним — голос lead",
        "lead": "в оригинале слушай мелодию интро A4 G4 A♯4 | F4 D♯4 D4 D♯4 | D4 C4 A♯4 | G4 F♯4 G4 A4 (она же второй "
                "голос куплета); арпеджио под ней — голос arp",
        "hookline": "в оригинале слушай подголосок проигрыша C5 A♯4 на 2& 3; под ним арпеджио и струнные",
        "mel": "в оригинале слушай мелодию припева A♯5 A5 G5 D5 | F5 D♯5 … ; под ней подложка (cpad)",
        "fig": "в оригинале слушай фигуру восьмыми A5 A♯5 G5 A♯5 … ; под ней подложка (cpad)",
        "cpad": "в оригинале слушай подложку (трезвучия); над ней мелодия (mel)",
        "strings": "стем strings", "brk": "арпеджио брейкдауна шестнадцатыми; аккорды под ним — brk_pad"}
ORDER = ["arp", "lead", "hookline", "mel", "fig", "cpad", "strings", "brk"]


def cmd_tonepage():
    """Adds to the page of `zr page` what part to listen for in each original, marks Alex's picks, orders the voices."""
    import re, time
    page = os.path.join(OUT, "zenology", "page", "index.html"); html = open(page, encoding="utf-8").read()
    m = re.search(r"const M = (\{.*\});", html); M = json.loads(m.group(1))
    picked = {v: z.split("/") for v, z in ZEN.items()}
    for g in M["groups"]:
        vn = g["name"].split(",")[0]; g["name"] = g["name"].replace(" — выбрано", "")      # idempotent
        for c in g["clips"]:
            c[1] = c[1].replace("✓ ", "")
        if vn in picked:
            g["name"] += " — выбрано"
        g["note"] = f"<b>{HINT.get(vn, '')}</b><br>" + g["note"].split("<br>")[-1]
        for c in g["clips"]:
            if vn in picked and c[1] and picked[vn][1] in c[2].split(" · ")[0].split()[-1:] and picked[vn][0] in c[2]:
                c[1] = "✓ " + c[1]
    M["groups"].sort(key=lambda g: ORDER.index(g["name"].split(",")[0]) if g["name"].split(",")[0] in ORDER else 99)
    M["v"] = int(time.time())
    open(page, "w", encoding="utf-8").write(html[:m.start(1)] + json.dumps(M, ensure_ascii=False) + html[m.end(1):])
    print(page, [g["name"] for g in M["groups"]])


# ---- round 4 (Alex 2026-11-21): lead «обычная мягкая пила с эффектами», hookline «ближе к brass/trumpet с делеем»,
# mel «что-то типа magic piano / dreamy», fig «AX Analog Dream хорошо, но не хватает жирка, saw базовой в унисон».
# Sweeps: analysis/.../sweeps4.sh (notes copy keys-r4); this builds zenology/page/round4.html (run in the zr env).
FX_LEAD = [("Chorus", {"rate_hz": 0.6, "depth": 0.25, "mix": 0.35}), ("Delay", {"delay_bars": 3 / 16, "feedback": 0.3, "mix": 0.2}),
           ("Reverb", {"room_size": 0.6, "wet_level": 0.22, "dry_level": 0.85})]
FX_BRASS = [("Delay", {"delay_bars": 3 / 16, "feedback": 0.35, "mix": 0.25}), ("Reverb", {"room_size": 0.4, "wet_level": 0.12, "dry_level": 0.9})]
FX_BRASS8 = [("Delay", {"delay_bars": 1 / 8, "feedback": 0.35, "mix": 0.25}), ("Reverb", {"room_size": 0.4, "wet_level": 0.12, "dry_level": 0.9})]


def fx(x, chain, bar, sr=48000):
    import pedalboard
    units = []
    for nm, kw in chain:
        kw = dict(kw)
        if "delay_bars" in kw:
            kw["delay_seconds"] = kw.pop("delay_bars") * bar
        units.append(getattr(pedalboard, nm)(**kw))
    return pedalboard.Pedalboard(units)(x.T, sr).T


def cmd_round4():
    import soundfile as sf, subprocess, time
    from scipy.signal import resample_poly
    zr = load("zenology_render"); gp, song = zr.gp_song(NAME); zen = os.path.join(song.out, "zenology"); page = os.path.join(zen, "page")
    bar = song.bar; rd = lambda f: sf.read(os.path.join(zen, f), always_2d=True, dtype="float32")[0]
    rms = lambda v: np.sqrt((v ** 2).mean()) + 1e-9
    rank = lambda v, b0, b1, tag="keys-r4": json.load(open(os.path.join(zen, f"zen-{tag}-{v}-{b0}-{b1}.json"), encoding="utf-8"))
    import librosa
    part4 = json.load(open(os.path.join(OUT, "keys-r4.notes.json"), encoding="utf-8"))

    def octave(f, voice, b0, b1):   # energy centre of the notes' pitch classes against the written notes (12 st = octave off;
        x = rd(f).mean(1); line = gp.voice_line(song, part4, voice, b0, b1); pcs = {n % 12 for t, n, d in line}   # the sweep's
        E = (np.abs(librosa.cqt(x, sr=48000, hop_length=512, fmin=librosa.midi_to_hz(36), n_bins=72)) ** 2).sum(1)  # «oct» is
        i = [k for k in range(72) if (36 + k) % 12 in pcs]                                    # scored against the whole
        d = sum((36 + k) * E[k] for k in i) / sum(E[k] for k in i) - np.median([n for t, n, d in line])   # stem: unreliable
        return " · ⚠ звучит октавой выше" if d >= 10 else " · ⚠ слой октавой ниже" if d <= -10 else ""
    label = lambda t: f"{t['bank'].split()[0]}/{t['number']} · {t['category']}" + octave(t["file"], *OCT_OF[t["file"].split("-")[3]])
    OCT_OF = {"lead": ("lead", 1, 5), "hookline": ("hookline", 9, 13), "mel": ("mel", 89, 93), "fig": ("fig", 97, 101)}

    def render(tone, voice, b0, b1):          # a tone the sweep did not keep: rendered clean on its own (zr render)
        out = os.path.join(zen, f"r4-{voice}-{tone.replace('/', '-').replace(' ', '_')}.wav")
        if not os.path.exists(out):
            subprocess.run([sys.executable, os.path.join(REPO, "tools", "zenology_render.py"), "render", tone, NAME,
                            os.path.join(OUT, "keys-r4.notes.json"), voice, str(b0), str(b1), out], check=True)
        return sf.read(out, always_2d=True, dtype="float32")[0]

    groups = []
    def group(voice, b0, b1, hint, clips):
        n = int(round((b1 - b0) * bar * 44100))
        orig = sum(resample_poly(song.read(f"{st}.wav", song.t_stem(b0), song.t_stem(b0) + (b1 - b0) * bar).mean(1), 147, 160) for st in ["keys"])
        orig = np.pad(orig, (0, max(0, n - len(orig))))[:n]; out = [("orig", orig, "Оригинал", "стем keys", True)]
        for k, (nm, note, x) in enumerate(clips, 1):
            y = resample_poly(x.mean(1), 147, 160); y = np.pad(y, (0, max(0, n - len(y))))[:n]
            out.append((f"{k:02d}", y * rms(orig) / rms(y), nm, note, False))
        peak = max(np.abs(c[1]).max() for c in out); files = []
        for cid, x, nm, note, ref in out:
            x = x / peak * 0.8; k = int(0.008 * 44100); x[:k] *= np.linspace(0, 1, k); x[-k:] *= np.linspace(1, 0, k)
            fn = f"r4-{voice}-{cid}.wav"; sf.write(os.path.join(page, fn), x.astype(np.float32), 44100, subtype="PCM_16"); files.append([fn, nm, note, ref])
        groups.append({"name": f"{voice}, такты {b0}–{b1 - 1}", "note": f"<b>{hint}</b><br>по кругу, одна громкость", "clips": files})

    r = rank("lead", 1, 5); top = r["top"][:10]
    group("lead", 1, 5, HINT["lead"] + ". Мягкие пилы и лиды, все с хорусом, дилеем 3/16 и ревербом; первый — ещё и сухой",
          [(t["name"], label(t) + " · хорус + дилей + реверб", fx(rd(t["file"]), FX_LEAD, bar)) for t in top]
          + [(top[0]["name"] + " сухой", label(top[0]) + " · без эффектов", rd(top[0]["file"]))])
    r = rank("hookline", 9, 13); top = r["top"][:9]; tpt = "PRST_F Essential/383"            # Trumpet Echo: a trumpet with its own echo
    clips = [(t["name"], label(t) + " · дилей 3/16 + реверб", fx(rd(t["file"]), FX_BRASS, bar)) for t in top]
    clips += [(top[0]["name"] + ", дилей 1/8", label(top[0]) + " · дилей 1/8 + реверб", fx(rd(top[0]["file"]), FX_BRASS8, bar))]
    if not any(f"{t['bank'].split()[0]} " in tpt and t["number"] == "383" for t in top):
        clips.append(("Trumpet Echo", "F/383 · Solo Brass · своё эхо тона", render(tpt, "hookline", 9, 13)))
    group("hookline", 9, 13, HINT["hookline"] + ". Медь, с дилеем 3/16 (у первого ещё 1/8)", clips)
    r = rank("mel", 89, 93); top = r["top"][:12]
    group("mel", 89, 93, HINT["mel"] + ". Колокольные пэды, Celesta, Music Box, пиано — dreamy", [(t["name"], label(t), rd(t["file"])) for t in top])
    ax = rd("zen-keys-k-fig-97-101-PRST_A_Factory_Presets-0038.wav"); r = rank("fig", 97, 101); saws = r["top"][:6]
    mix = lambda s, db: (lambda a, b: a + b * 10 ** (db / 20) * rms(a) / rms(b))(*(lambda a, b: (np.pad(a, ((0, max(0, len(b) - len(a))), (0, 0))),
                                                                                      np.pad(b, ((0, max(0, len(a) - len(b))), (0, 0)))))(ax, rd(s["file"])))
    clips = [("AX Analog Dream", "A/38 · как выбрал", ax)]
    clips += [(f"AX + {s['name']} −6", f"{label(s)} слоем на 6 дБ тише", mix(s, -6)) for s in saws]
    clips += [(f"AX + {saws[0]['name']} −10", f"{label(saws[0])} слоем на 10 дБ тише", mix(saws[0], -10)),
              (f"AX + {saws[0]['name']} −3", f"{label(saws[0])} слоем на 3 дБ тише", mix(saws[0], -3))]
    group("fig", 97, 101, HINT["fig"] + ". AX Analog Dream + пила в унисон слоем", clips)
    meta = {"title": "Медляк — тоны, круг 4", "sub": "По твоим описаниям: lead — мягкая пила с эффектами, hookline — медь с дилеем, mel — "
            "dreamy, fig — AX Analog Dream + пила. Внутри голоса переключение сохраняет место; <kbd>←</kbd> <kbd>→</kbd> соседний вариант, "
            "<kbd>пробел</kbd> пауза. Порядок — по близости к стему, подсказка.", "groups": groups, "v": int(time.time())}
    tpl = open(os.path.join(REPO, "tools", "templates", "part-tone-pick.html"), encoding="utf-8").read()
    open(os.path.join(page, "round4.html"), "w", encoding="utf-8").write(tpl.replace("/*META*/", json.dumps(meta, ensure_ascii=False)))
    print(os.path.join(page, "round4.html"))


# ---- round 5 (Alex 2026-11-21): lead on Roma's notes (the same soft saws + FX), hookline «Trumpet Echo хорошо, но
# нужно помягче или тон похожий, но мягче» -> zenology/page/round5.html (run in the zr env)
SOFT_TPT = [("PRST_F Essential/402", "FrenchHorn2 Echo", None), ("PRST_E XV Collection/439", "Ballad Trump", FX_BRASS),
            ("PRST_F Essential/384", "Dark Trumpet", FX_BRASS), ("PRST_F Essential/395", "Mute Trumpet 1", FX_BRASS),
            ("PRST_F Essential/397", "Mute Trumpet 2", FX_BRASS), ("PRST_F Essential/382", "Trumpet + фильтр", [("LowpassFilter", {"cutoff_frequency_hz": 3000})] + FX_BRASS)]


def cmd_round5():
    import soundfile as sf, subprocess, time
    from scipy.signal import resample_poly
    zr = load("zenology_render"); gp, song = zr.gp_song(NAME); zen = os.path.join(song.out, "zenology"); page = os.path.join(zen, "page")
    bar = song.bar; rms = lambda v: np.sqrt((v ** 2).mean()) + 1e-9; notes = os.path.join(OUT, "keys-r5.notes.json")
    part = json.load(open(PART, encoding="utf-8")); part["stems"] = ["keys"]; json.dump(part, open(notes, "w"), ensure_ascii=False)

    def render(tone, voice, b0, b1, vel=100):
        out = os.path.join(zen, f"r5-{voice}-{tone.replace('/', '-').replace(' ', '_')}-v{vel}.wav")
        if not os.path.exists(out):
            subprocess.run([sys.executable, os.path.join(REPO, "tools", "zenology_render.py"), "render", tone, NAME, notes, voice,
                            str(b0), str(b1), out, "--vel", str(vel)], check=True, capture_output=True)
        return sf.read(out, always_2d=True, dtype="float32")[0]

    groups = []
    def group(voice, b0, b1, hint, clips, ref_note="стем keys", roma_note="его клавиши: ноты для сравнения"):
        n = int(round((b1 - b0) * bar * 44100))
        orig = resample_poly(song.read("keys.wav", song.t_stem(b0), song.t_stem(b0) + (b1 - b0) * bar).mean(1), 147, 160)
        orig = np.pad(orig, (0, max(0, n - len(orig))))[:n]; out = [("orig", orig, "Оригинал", ref_note, True)]
        if os.path.exists(ROMA):
            sr_ = sf.info(ROMA).samplerate; r, _ = sf.read(ROMA, start=int(song.t_stem(b0) * sr_), stop=int(song.t_stem(b1) * sr_), always_2d=True)
            r = resample_poly(r.mean(1), 44100, sr_); r = np.pad(r, (0, max(0, n - len(r))))[:n]
            out.append(("roma", r * rms(orig) / rms(r), "Рома, концерт 28.10", roma_note, True))
        for k, (nm, note, x) in enumerate(clips, 1):
            y = resample_poly(x.mean(1), 147, 160); y = np.pad(y, (0, max(0, n - len(y))))[:n]
            out.append((f"{k:02d}", y * rms(orig) / rms(y), nm, note, False))
        peak = max(np.abs(c[1]).max() for c in out); files = []
        for cid, x, nm, note, ref in out:
            x = x / peak * 0.8; k = int(0.008 * 44100); x[:k] *= np.linspace(0, 1, k); x[-k:] *= np.linspace(1, 0, k)
            fn = f"r5-{voice}-{cid}.wav"; sf.write(os.path.join(page, fn), x.astype(np.float32), 44100, subtype="PCM_16"); files.append([fn, nm, note, ref])
        groups.append({"name": f"{voice}, такты {b0}–{b1 - 1}", "note": f"<b>{hint}</b><br>по кругу, одна громкость", "clips": files})

    r4 = json.load(open(os.path.join(zen, "zen-keys-r4-lead-1-5.json"), encoding="utf-8"))["top"][:10]
    tag = lambda t: f"{t['bank']}/{t['number']}"
    clips = [(t["name"], f"{t['bank'].split()[0]}/{t['number']} · хорус + дилей + реверб", fx(render(tag(t), "lead", 1, 5), FX_LEAD, bar)) for t in r4]
    clips.append((r4[0]["name"] + " сухой", "без эффектов", render(tag(r4[0]), "lead", 1, 5)))
    group("lead", 1, 5, "НОТЫ ИСПРАВЛЕНЫ ПО РОМЕ: A G | F D♯ D D♯ | D C C | G F♯ G A. Те же мягкие пилы с хорусом, дилеем 3/16 и ревербом", clips)
    te = "PRST_F Essential/383"
    clips = [("Trumpet Echo", "F/383 · как выбрал", render(te, "hookline", 9, 13)),
             ("Trumpet Echo, мягче нажатие", "F/383 · сила 70 из 127", render(te, "hookline", 9, 13, 70)),
             ("Trumpet Echo, мягко + фильтр 3 кГц", "F/383 · сила 70, ФНЧ 3 кГц",
              fx(render(te, "hookline", 9, 13, 70), [("LowpassFilter", {"cutoff_frequency_hz": 3000})], bar)),
             ("Trumpet Echo, мягко + фильтр 2 кГц", "F/383 · сила 70, ФНЧ 2 кГц",
              fx(render(te, "hookline", 9, 13, 70), [("LowpassFilter", {"cutoff_frequency_hz": 2000})], bar)),
             ("Trumpet Echo, сила 50 + фильтр 2.5 кГц", "F/383 · сила 50, ФНЧ 2.5 кГц",
              fx(render(te, "hookline", 9, 13, 50), [("LowpassFilter", {"cutoff_frequency_hz": 2500})], bar))]
    for tone, nm, chain in SOFT_TPT:
        x = render(tone, "hookline", 9, 13, 80)
        clips.append((nm, f"{tone.split()[0]}/{tone.split('/')[-1]} · сила 80" + (" · дилей 3/16 + реверб" if chain else " · своё эхо тона"), fx(x, chain, bar) if chain else x))
    group("hookline", 9, 13, HINT["hookline"] + ". Trumpet Echo мягче (сила нажатия, фильтр) и похожие мягкие трубы", clips,
          roma_note="подголосок он не играл, тут у него линия интро")
    meta = {"title": "Медляк — тоны, круг 5", "sub": "lead на нотах, исправленных по концерту Ромы (его дорожка — вторая кнопка, для сравнения нот); "
            "hookline — Trumpet Echo мягче и похожие тоны. <kbd>←</kbd> <kbd>→</kbd> соседний вариант, <kbd>пробел</kbd> пауза.",
            "groups": groups, "v": int(time.time())}
    tpl = open(os.path.join(REPO, "tools", "templates", "part-tone-pick.html"), encoding="utf-8").read()
    open(os.path.join(page, "round5.html"), "w", encoding="utf-8").write(tpl.replace("/*META*/", json.dumps(meta, ensure_ascii=False)))
    print(os.path.join(page, "round5.html"))


def cmd_round6():
    """The breakdown solo (Alex: «на 3:08 потерялось соло, ярко выраженное»): what it plays now (the lead's tone + FX),
    the sweep's best (zr sweep ... keys-r6 solo 82 86), the tones of the melody and of the trumpet -> round6.html."""
    import soundfile as sf, subprocess, time
    from scipy.signal import resample_poly
    zr = load("zenology_render"); gp, song = zr.gp_song(NAME); zen = os.path.join(song.out, "zenology"); page = os.path.join(zen, "page")
    bar = song.bar; rms = lambda v: np.sqrt((v ** 2).mean()) + 1e-9; notes = os.path.join(OUT, "keys-r6.notes.json"); b0, b1 = 82, 86

    def render(tone, vel=100):
        out = os.path.join(zen, f"r6-solo-{tone.replace('/', '-').replace(' ', '_')}-v{vel}.wav")
        if not os.path.exists(out):
            subprocess.run([sys.executable, os.path.join(REPO, "tools", "zenology_render.py"), "render", tone, NAME, notes, "solo",
                            str(b0), str(b1), out, "--vel", str(vel)], check=True, capture_output=True)
        return sf.read(out, always_2d=True, dtype="float32")[0]
    rk = json.load(open(os.path.join(zen, "zen-keys-r6-solo-82-86.json"), encoding="utf-8"))["top"][:10]
    clips = [("Saw Dtune (сейчас)", "тон lead + хорус, дилей, реверб — так соло звучит в кандидате", fx(render(ZEN["lead"]), FX_LEAD, bar)),
             ("Fantasy 2", "тон мелодии припева", render(ZEN["mel"])),
             ("Trumpet + фильтр", "тон подголоска проигрыша", fx(render(ZEN["hookline"], 80), [("LowpassFilter", {"cutoff_frequency_hz": 3000})] + FX_BRASS, bar))]
    clips += [(t["name"], f"{t['bank'].split()[0]}/{t['number']} · {t['category']}", sf.read(os.path.join(zen, t["file"]), always_2d=True, dtype="float32")[0]) for t in rk]
    n = int(round((b1 - b0) * bar * 44100))
    orig = resample_poly(song.read("keys.wav", song.t_stem(b0), song.t_stem(b0) + (b1 - b0) * bar).mean(1), 147, 160)
    orig = np.pad(orig, (0, max(0, n - len(orig))))[:n]; out = [("orig", orig, "Оригинал", "стем keys (брейкдаун: соло над арпеджио)", True)]
    for k, (nm, note, x) in enumerate(clips, 1):
        y = resample_poly(x.mean(1), 147, 160); y = np.pad(y, (0, max(0, n - len(y))))[:n]; out.append((f"{k:02d}", y * rms(orig) / rms(y), nm, note, False))
    peak = max(np.abs(c[1]).max() for c in out); files = []
    for cid, x, nm, note, ref in out:
        x = x / peak * 0.8; k = int(0.008 * 44100); x[:k] *= np.linspace(0, 1, k); x[-k:] *= np.linspace(1, 0, k)
        fn = f"r6-solo-{cid}.wav"; sf.write(os.path.join(page, fn), x.astype(np.float32), 44100, subtype="PCM_16"); files.append([fn, nm, note, ref])
    meta = {"title": "Медляк — тон соло брейкдауна", "sub": "Соло отдельно (C6 | C6 A5 … F5 | D♯5 A♯5 | A5 C6 D5), в оригинале под ним арпеджио. "
            "<kbd>←</kbd> <kbd>→</kbd> соседний вариант, <kbd>пробел</kbd> пауза.",
            "groups": [{"name": "solo, такты 82–85", "note": "<b>в оригинале слушай длинные ноты сверху</b><br>по кругу, одна громкость", "clips": files}],
            "v": int(time.time())}
    tpl = open(os.path.join(REPO, "tools", "templates", "part-tone-pick.html"), encoding="utf-8").read()
    open(os.path.join(page, "round6.html"), "w", encoding="utf-8").write(tpl.replace("/*META*/", json.dumps(meta, ensure_ascii=False)))
    print(os.path.join(page, "round6.html"))


if __name__ == "__main__":
    {"bp": cmd_bp, "notes": cmd_notes, "preview": cmd_preview, "calibrate": cmd_calibrate, "candidate": cmd_candidate, "tonepage": cmd_tonepage, "round4": cmd_round4, "round5": cmd_round5, "round6": cmd_round6}[sys.argv[1]]()
