#!/usr/bin/env python3
"""Click prep for «Мумий Тролль — Владивосток 2000» (12.12 new songs, 2026-11-15). Rebuildable.

  python3 tools/jamzone/prep_vladivostok_2000.py click   # moises-orig/metronome.mp3 -> root metronome.wav
then: python3 tools/jamzone/jamzone_render.py "Мумий Тролль - Владивосток 2000"

Measured on the raw Moises stems (wiki/songs/mumiy-troll-vladivostok-2000.md):
  * Moises export has 7 real stems (no empty ones); Lead/Rhythm Guitars kept separate, count-in not imported.
  * tempo ~constant: Moises metronome lstsq 129.947 bpm (filename "130"), residual ±8 ms in 10-s bins,
    drum transients vs the constant grid ±7 ms -> no warp, constant 129.95.
  * first Moises click (0.252 s) IS the downbeat: kick on beats 1/3, snare on 2/4, chord changes on 1;
    the whole band enters on it (vocal pickup on bar 4 beat 4).
  * Moises metronome LAGS the drum transients by ~27 ms (knock/snare/hats spectral-flux onsets -27/-27/-25 ms,
    constant through the song) -> the click is synthesized on the drum-transient grid instead (LAG).
Stems stay the original Moises mp3s in the song root; only the metronome is replaced
(original -> moises-orig/metronome.mp3).
"""
import os, sys, shutil, subprocess
import numpy as np

SR = 44100
SONG = os.path.expanduser("~/projects/cherry-daddies/music/songs/Мумий Тролль - Владивосток 2000")
ORIG = os.path.join(SONG, "moises-orig")
BPM = 129.95
B = 60.0 / BPM
LAG = 0.027                       # Moises metronome is this late vs the drum transients

S = lambda t: int(round(t * SR))

def decode(p, ch=2):
    raw = subprocess.run(["ffmpeg", "-v", "quiet", "-i", p, "-ac", str(ch), "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, ch).copy()

def moises_phase(met):
    """lstsq phase (s) of the Moises metronome at BPM; k = 0 at its first click."""
    a = np.abs(met[:, 0]); thr = 0.05 * a.max()
    idx = np.where((a[1:] > thr) & (a[:-1] <= thr))[0]; on = []
    for i in idx:
        if not on or i - on[-1] > 0.25 * SR: on.append(i)
    on = np.array(on) / SR
    k = np.round((on - on[0]) / B)
    return float(np.median(on - k * B)), len(on)

def do_click():
    os.makedirs(ORIG, exist_ok=True)
    src = os.path.join(SONG, "metronome.mp3"); orig = os.path.join(ORIG, "metronome.mp3")
    if os.path.exists(src):
        shutil.move(src, orig)
    met = decode(orig)
    p_moises, n = moises_phase(met)
    p0 = p_moises - LAG
    n_out = len(decode(os.path.join(SONG, "drums.mp3"), 1))
    out = np.zeros((n_out, 2), np.float32)
    L = S(0.03); t = np.arange(L) / SR
    hit = (np.sin(2 * np.pi * 2000 * t) * np.exp(-t / 0.006)).astype(np.float32) * 0.8
    k = 0
    while S(p0 + k * B) + L <= n_out:
        s = S(p0 + k * B); out[s:s+L, 0] += hit; out[s:s+L, 1] += hit; k += 1
    dst = os.path.join(SONG, "metronome.wav")
    subprocess.run(["ffmpeg", "-v", "quiet", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-",
                    "-c:a", "pcm_s16le", dst], input=out.tobytes(), check=True)
    print(f"  ✓ metronome.wav  synthetic {BPM} bpm, {k} clicks; Moises phase {p_moises:.4f}s ({n} clicks) "
          f"- lag {LAG*1000:.0f}ms -> first click (bar 1.1) {p0:.4f}s")

if __name__ == "__main__":
    step = sys.argv[1] if len(sys.argv) > 1 else ""
    if step == "click": do_click()
    else: sys.exit(__doc__)
