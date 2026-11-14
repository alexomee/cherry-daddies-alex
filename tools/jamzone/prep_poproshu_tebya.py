#!/usr/bin/env python3
"""One-off stem prep for «Вирус — Попрошу тебя» (12.12 new songs, 2026-11-14). Rebuildable.

  python3 tools/jamzone/prep_poproshu_tebya.py stems   # moises-orig/*.mp3 -> root *.wav (padded) + metronome.wav
  python3 tools/jamzone/prep_poproshu_tebya.py keys    # keys.wav -> parts/pb-keys.wav (pb-other track)
then: python3 tools/jamzone/jamzone_render.py "Вирус - Попрошу тебя"

Measured on the raw Moises stems (wiki/songs/virus-poproshu-tebya.md):
  * tempo dead-constant 140.09 bpm (metronome lstsq 140.089, kick lstsq 140.093; ±2 ms bins) -> no warp.
  * Moises metronome is ON the drums (kick 50%-attack -1.2 ms, programmed kit) — no lag.
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
P0 = 0.84306                      # raw time of k=0 on the kick grid (50%-attack, fitted at 140.09)
K_BAR1 = -3                       # raw beat index of bar 1.1
PRE = 0.05                        # bar 1.1 lands here in the processed stems
PAD = PRE - (P0 + K_BAR1 * B)     # front silence added to every stem (0.4918 s)

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

def do_stems():
    pad = np.zeros((S(PAD), 2), np.float32)
    n_out = None
    for nm in STEMS:
        o = np.vstack([pad, decode(os.path.join(SRC, nm + ".mp3"))])
        n_out = len(o)
        write_wav(os.path.join(SONG, nm + ".wav"), o)
        print(f"  ✓ {nm}.wav  {len(o)/SR:.3f}s  peak {np.abs(o).max():.3f}")
    write_wav(os.path.join(SONG, "metronome.wav"), metronome(n_out))
    print(f"  ✓ metronome.wav  synthetic {BPM} bpm, first click (bar 1.1) {PRE:.3f}s; pad {PAD:.4f}s; "
          f"run-in bar 1.3 = {tout(-1):.3f}s, band downbeat bar 3.1 = {tout(5):.3f}s")

# pb-keys (2026-11-14, Alex): pb-other track = the whole Moises Keys stem (initial version).
# KEYS_MUTES: raw Moises seconds where keys are cut out later (None = till the end).
KEYS_MUTES = []
MUTE_XF = 0.015

def do_keys():
    keys = decode(os.path.join(SONG, "keys.wav")); n = len(keys)
    for r0, r1 in KEYS_MUTES:
        a = S(raw2out(r0)); b = n if r1 is None else S(raw2out(r1)); f = S(MUTE_XF)
        keys[a-f:a] *= np.linspace(1, 0, f)[:, None]; keys[a:b] = 0
        if b + f <= n: keys[b:b+f] *= np.linspace(0, 1, f)[:, None]
        print(f"  keys muted raw {r0}-{r1 or 'end'}")
    os.makedirs(os.path.join(SONG, "parts"), exist_ok=True)
    dst = os.path.join(SONG, "parts", "pb-keys.wav")
    write_wav(dst, keys)
    print(f"  ✓ {dst}  {n/SR:.3f}s  peak {np.abs(keys).max():.3f}")

if __name__ == "__main__":
    step = sys.argv[1] if len(sys.argv) > 1 else ""
    if step == "stems": do_stems()
    elif step == "keys": do_keys()
    else: sys.exit(__doc__)
