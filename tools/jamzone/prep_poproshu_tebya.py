#!/usr/bin/env python3
"""One-off stem prep for «Вирус — Попрошу тебя» (12.12 new songs, 2026-11-14). Rebuildable.

  python3 tools/jamzone/prep_poproshu_tebya.py stems   # moises-orig/*.mp3 -> root *.wav (padded, ending
                                                       #   faded after the crash 119.1) + metronome.wav
  python3 tools/jamzone/prep_poproshu_tebya.py fx      # keys+other run-in 1.3-3.1 -> parts/pb-fx.wav (history only:
                                                       #   since 2026-11-16 pb-other = the whole keys stem)
  python3 tools/jamzone/prep_poproshu_tebya.py rhythm  # the keys stabs of parts/poproshu-midifind.mid (bars +2) in
                                                       #   the record's voicing -> parts/rhythm.notes.json (GM-800)
then: python3 tools/jamzone/jamzone_render.py "Вирус - Попрошу тебя"

Measured on the raw Moises stems (wiki/songs/virus-poproshu-tebya.md):
  * tempo dead-constant 140.09 bpm (metronome lstsq 140.089, kick lstsq 140.093; ±2 ms bins) -> no warp.
  * Moises metronome LAGS the drum transients by ~34 ms (like «Ты меня не ищи»). The kick-sub 50%-attack
    sits on the metronome too, so it is NOT a phase reference: the grid phase P0 comes from the transient
    bands (knock/snare/hats spectral-flux onsets), verified 0 ms after the 2026-11-15 fix.
  * The record opens with a keys/other "заезд" (run-in) from raw 0.415 s = 6 beats before the real
    downbeat (raw 2.985 s, drums+bass+vocals in, chord changes on that phase, snare on 2/4).
    Moises' first click (0.803 s) is NOT a downbeat.
  * So the stems are front-padded (PAD) so that bar 1.1 = the bar that holds the run-in:
      bar 1.1 = raw beat k=-3 (before the file start, now at PRE), run-in = bar 1.3,
      band/vocal downbeat = bar 3.1. metronome.wav is synthesized on that grid (first click = bar 1.1).
Beat index k below = raw Moises click index (k=0 at the first Moises click); bar = (k+3)//4 + 1.
"""
import os, sys, shutil, subprocess
import numpy as np

SR = 44100
SONG = os.path.expanduser("~/projects/cherry-daddies/music/songs/Вирус - Попрошу тебя")
SRC = os.path.join(SONG, "moises-orig")
BPM = 140.09
B = 60.0 / BPM
# raw time of k=0 = the drum TRANSIENTS. 2026-11-15 fix: the original 0.84306 was the kick-sub 50%-attack
# (slow sub swell) = exactly where the lagging Moises metronome sits, ~34 ms AFTER the real hits
# (spectral-flux onsets knock 150-1k / snare 1-5k / hats 6-16k all -33..-35 ms) -> click flammed late.
P0 = 0.84306 - 0.0345
K_BAR1 = -3                       # raw beat index of bar 1.1
PRE = 0.05                        # bar 1.1 lands here in the processed stems
PAD = PRE - (P0 + K_BAR1 * B)     # front silence added to every stem (0.5263 s)

STEMS = ["backing_vocals", "bass", "drums", "guitars", "keys", "other", "piano", "strings", "vocals"]

S = lambda t: int(round(t * SR))
tout = lambda k: PRE + (k - K_BAR1) * B          # raw beat k -> processed seconds
raw2out = lambda r: r + PAD                       # raw Moises seconds -> processed seconds

def decode(p):
    raw = subprocess.run(["ffmpeg", "-v", "quiet", "-i", p, "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).copy()

def write_wav(path, x, codec="pcm_f32le"):      # float: Moises mp3s decode slightly over 0 dBFS -> no clipping
    subprocess.run(["ffmpeg", "-v", "quiet", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-",
                    "-c:a", codec, path], input=x.astype(np.float32).tobytes(), check=True)

def metronome(n_out):
    out = np.zeros((n_out, 2), np.float32)
    L = S(0.03); t = np.arange(L) / SR
    hit = (np.sin(2 * np.pi * 2000 * t) * np.exp(-t / 0.006)).astype(np.float32) * 0.8
    k = K_BAR1
    while S(tout(k)) + L <= n_out:
        s = S(tout(k)); out[s:s+L, 0] += hit; out[s:s+L, 1] += hit; k += 1
    return out

# Ending (2026-11-19, Alex: «была срезана — вернуть, но только до 3:20, там где голос заканчивает»).
# Until then the render cut the song after the crash on bar 93.1 (mix.json cut_after_last_cue). Now it
# ends on the crash 119.1 (raw 3:21.7, render 3:25.6): crash + bass out, the vocal's last word rings to
# ~119.3. The record's drum pickup into its instrumental outro starts on 119.3e, and the render's cut can
# only end on a bar line -> every stem fades 119.2& -> 119.3e - 20 ms here and is silent after.
END_K = 471.25                    # raw beat of bar 119.3e (bar = (k+3)//4 + 1)
END_FADE_K = 470.5                # 119.2&
LEAD = 0.02

def end_cut(o):
    e, f = S(tout(END_K) - LEAD), S(tout(END_FADE_K))
    o[f:e] *= np.linspace(1, 0, e - f, dtype=np.float32)[:, None]
    o[e:] = 0
    return o

def do_stems():
    pad = np.zeros((S(PAD), 2), np.float32)
    n_out = None
    for nm in STEMS:
        o = end_cut(np.vstack([pad, decode(os.path.join(SRC, nm + ".mp3"))]))
        n_out = len(o)
        write_wav(os.path.join(SONG, nm + ".wav"), o)
        print(f"  ✓ {nm}.wav  {len(o)/SR:.3f}s  peak {np.abs(o).max():.3f}")
    write_wav(os.path.join(SONG, "metronome.wav"), metronome(n_out))
    print(f"  ✓ metronome.wav  synthetic {BPM} bpm, first click (bar 1.1) {PRE:.3f}s; pad {PAD:.4f}s; "
          f"run-in bar 1.3 = {tout(-1):.3f}s, band downbeat bar 3.1 = {tout(5):.3f}s")

# pb-fx (2026-11-16, Alex): playback = ONLY the synth run-in ("заезд") before the main theme; the keys from
# the band downbeat on are played live. History: 2026-11-14 pb-keys = the whole Keys stem; 2026-11-16
# keys removed from playback entirely; same day corrected: the run-in stays, renamed pb-fx.
#   * The run-in lives in keys (-19 dBFS) + other (-28) over bars 1.3-3.1; piano/guitars/strings ~silent
#     there (<= -70 dBFS), drums only the 2.4& pickup -> pb-fx = keys + other.
#   * Kept from the file start up to the band downbeat bar 3.1 (raw k=5), faded out over FX_XF ENDING on
#     that bar line (the band's 3.1 hit masks the cut); silence after. Native level (no gain).
FX_SRC = ["keys", "other"]
FX_END_K = 5                      # raw beat index of bar 3.1 (band/vocal downbeat)
FX_XF = 0.020

def do_fx():
    x = None
    for nm in FX_SRC:
        a = decode(os.path.join(SONG, nm + ".wav")); x = a if x is None else x + a
    n = len(x); e = S(tout(FX_END_K)); f = S(FX_XF)
    x[e-f:e] *= np.linspace(1, 0, f, dtype=np.float32)[:, None]; x[e:] = 0
    os.makedirs(os.path.join(SONG, "parts"), exist_ok=True)
    dst = os.path.join(SONG, "parts", "pb-fx.wav")
    write_wav(dst, x)
    print(f"  ✓ {dst}  {'+'.join(FX_SRC)} up to bar 3.1 = {tout(FX_END_K):.3f}s (fade {FX_XF*1000:.0f} ms), "
          f"peak {np.abs(x).max():.3f}")

# ---- rhythm: the keys stabs for the GM-800 where Alex plays lead/solo on scene 29 (Alex 2026-11-20: «вместо
# стемовых ритмов записать с моими пресетами там, где я поверх играю соло»). Rhythm and chords from the MIDI of the
# web (parts/poproshu-midifind.mid, track «Гитара»; MIDI bar N = our bar N+2: «Клавиши» enter on MIDI 9 = our 11,
# «Соло» on MIDI 18 = our 20); the voicing as the record's keys stem plays it (part_notes.py on the bars where the
# stem holds the stabs only, 3-10 and 103-110 agree). Played on scene 28 POPROSHU TEBY "as played": every part the
# same note, so the Saw Seq parts stay two octaves up as on the guitar.
MIDI_SRC = os.path.join(SONG, "parts", "poproshu-midifind.mid")
MIDI_SHIFT = 2                    # our bar = MIDI bar + 2
BLOCKS = [(11, 19), (20, 28), (44, 52), (53, 61), (85, 93), (94, 102)]    # Alex on scene 29 over the stabs
VOICING = {"Cm": "C5 D#5 C6", "Ab": "C5 G#5 C6", "Eb": "D#5 G5 D#6 G6", "Eb2": "D#5 G5",
           "Bb": "A#4 D5 A#5 D6", "G": "B4 G5 B5"}
STAB = 1.25                       # 16ths: the record's stab is ~130 ms (a 16th = 107 ms)
OCT = 0                           # semitones on top of the record's pitch (the scene as played): at the record's pitch
                                  # scene 28 matches the stem 0.841 with no octave shift; an octave down only shifted
VEL = 63                          # how hard: scene 28 opens its filter with velocity; 63 = the record's brightness
                                  # (spectral centroid 3.46 vs 3.50 kHz; 100 gave 5.2 kHz: «звучит по-другому», Alex)
TAKE_DB = 4.2                     # take (USB) -> the stem's stabs, bars 3-6 (mono LUFS -28.7 vs -24.6, slot 28 + 316 + echo,
                                  # vel 63; was -1.4 for the old preset at vel 100); + the keys gain
                                  # of pb-other (+1.6) on the layer in mix.json
RHYTHM_PART = os.path.join(SONG, "parts", "rhythm.notes.json")


def midi_stabs():
    """{our bar: [(16th, chord name)]} from track 0 of the MIDI."""
    import mido
    m = mido.MidiFile(MIDI_SRC); tpb = m.ticks_per_beat; tick = 0; on = {}; ev = {}
    for msg in m.tracks[0]:
        tick += msg.time
        if msg.type == "note_on" and msg.velocity > 0:
            on[msg.note] = tick
        elif msg.type in ("note_off", "note_on") and msg.note in on:
            t0 = on.pop(msg.note); pos = t0 / tpb / 4
            ev.setdefault((int(pos) + 1 + MIDI_SHIFT, round((pos - int(pos)) * 16)), set()).add(msg.note)
    names = {frozenset({0, 3, 7}): "Cm", frozenset({8, 0, 3}): "Ab", frozenset({3, 7, 10}): "Eb",
             frozenset({10, 2, 5}): "Bb", frozenset({7, 11, 2}): "G"}
    out = {}
    for (b, q), ns in sorted(ev.items()):
        c = names[frozenset(n % 12 for n in ns)]
        if c == "Eb" and min(ns) < 70:            # the low Eb (D#4 G4 A#4) at the end of the long phrase
            c = "Eb2"
        out.setdefault(b, []).append((q, c))
    return out


def do_rhythm(blocks=BLOCKS, path=RHYTHM_PART, oct_=OCT, voice="rhythm", extra=None):
    import json
    N = "C C# D D# E F F# G G# A A# B".split()
    tr = lambda s: (lambda m: f"{N[m % 12]}{m // 12 - 1}")(N.index(s[:-1]) + 12 * (int(s[-1]) + 1) + oct_)
    st = midi_stabs(); notes = []
    for a, b in blocks:
        for bar in range(a, b):
            for q, c in st.get(bar, []):
                notes.append([bar, 1 + q / 4, STAB / 4, " ".join(tr(x) for x in VOICING[c].split())])
    part = {"_about": "Keys stabs of «Попрошу тебя» for the GM-800 scene 28 (as played), where Alex plays lead/solo on "
                      "scene 29; generated by tools/jamzone/prep_poproshu_tebya.py rhythm (edit there).",
            "stems": ["keys"], "voices": {voice: {"at": [1], "bars": 200, "notes": notes}}}
    if extra is None and path == RHYTHM_PART:       # the playback layer: one take of scene 28 a block
        extra = {"layer": {"file": "pb-rhythm", "takes": [
            {"voice": voice, "scene": 28, "as_played": True, "vel": VEL, "bars": [a, b], "gain_db": TAKE_DB}
            for a, b in blocks]}}
    if extra:
        part.update(extra)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(part, f, ensure_ascii=False, indent=0)
    print(f"  ✓ {path}: {len(notes)} stabs in bars {blocks}")


if __name__ == "__main__":
    step = sys.argv[1] if len(sys.argv) > 1 else ""
    if step == "stems": do_stems()
    elif step == "fx": do_fx()
    elif step == "rhythm": do_rhythm()
    else: sys.exit(__doc__)
