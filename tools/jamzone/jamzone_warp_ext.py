#!/usr/bin/env python3
"""Warp external (Moises) stems onto a constant-bpm grid — rough timing repair.

Moises stems follow the original recording; if the record sags locally (e.g. a
voice-grooved breakdown with drums out — Демо «Солнышко» drifts +52ms at 2:14
and the outro runs -40ms early), a constant click diverges there. This tool
measures the deviation of the Moises metronome from the ideal constant grid,
smooths it (metronome onsets carry ±10ms mp3-frame quantization jitter; only
the slow real drift must survive), and time-warps ALL stems by that one shared
curve, so inter-stem alignment is untouched. Linear-interp resample: local rate
change is <1%, fine for a rough fix on mp3-sourced stems.

Originals are moved to <song>/moises-orig/ (jamzone_render globs only the song
folder root); warped stems land in the root as 16-bit WAVs with the same names.

--downbeat K: the true bar line is click K of the metronome (Moises clicks are
unaccented; jamzone_render takes "first metronome onset = downbeat"). The
warped metronome is silenced before click K so the render anchors bars right.

Usage: jamzone_warp_ext.py "<song name or folder>" --bpm N [--downbeat K] [--check]
"""
import os, sys, glob, shutil, subprocess
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jamzone_render import SR, find_folder, decode, onsets

SMOOTH = 7   # beats; hann window — kills click quantization jitter, keeps the sag

def grid_dev(metro_mono, bpm):
    """Per-click deviation from the constant grid. Returns (grid_times, dev_sec)."""
    on = onsets(metro_mono)
    d = np.diff(on)
    k = np.zeros(len(on), int)
    for i in range(1, len(on)):                       # cumulative indexing: robust when
        k[i] = k[i-1] + max(1, round(d[i-1]/np.median(d)))  # drift exceeds half a beat span-wise
    beat = 60.0/bpm
    dev = on - k*beat
    phase = np.median(dev)                            # grid phase = robust fit over all clicks
    dev -= phase
    w = np.hanning(SMOOTH+2)[1:-1]; w /= w.sum()
    pad = SMOOTH//2
    sm = np.convolve(np.pad(dev, pad, mode="edge"), w, mode="valid")
    return phase + k*beat, sm, on, k

def main():
    folder = find_folder(sys.argv[1])
    bpm = float(sys.argv[sys.argv.index("--bpm")+1])
    db_k = int(sys.argv[sys.argv.index("--downbeat")+1]) if "--downbeat" in sys.argv else 0
    check = "--check" in sys.argv

    stems = sorted(glob.glob(os.path.join(folder, "*.mp3")) + glob.glob(os.path.join(folder, "*.wav")))
    metro = next((p for p in stems if os.path.basename(p)[:-4].lower() in ("metronome", "click")), None) \
            or sys.exit("no metronome stem")

    grid_t, dev, on, k = grid_dev(decode(metro).mean(1), bpm)
    print(f"{len(on)} clicks, bpm {bpm}: smoothed dev min {dev.min()*1000:+.1f}ms max {dev.max()*1000:+.1f}ms")
    worst = np.argmax(np.abs(dev))
    print(f"  worst at t={grid_t[worst]:.1f}s ({dev[worst]*1000:+.1f}ms)")
    if check:
        for i in range(0, len(on), 8):
            print(f"  t={grid_t[i]:6.1f}s dev {dev[i]*1000:+6.1f}ms")
        return

    orig_dir = os.path.join(folder, "moises-orig")
    os.makedirs(orig_dir, exist_ok=True)
    for p in stems:
        name = os.path.basename(p)[:-4]
        a = decode(p)                                  # stereo float32
        t_out = np.arange(len(a))/SR
        src = (t_out + np.interp(t_out, grid_t, dev)) * SR   # flat extrapolation at both ends
        idx = np.arange(len(a))
        w = np.empty_like(a)
        for ch in range(2):
            w[:, ch] = np.interp(src, idx, a[:, ch])
        if p == metro and db_k > 0:                    # true downbeat = click db_k: silence the
            cut = grid_t[db_k] - 30/bpm                # warped clicks before it (half a beat back)
            w[:int(cut*SR)] = 0
            print(f"  metronome: first {db_k} clicks silenced (downbeat = click {db_k}, t={grid_t[db_k]:.3f}s)")
        out = os.path.join(folder, name + ".wav")
        subprocess.run(["ffmpeg","-v","quiet","-y","-f","f32le","-ar",str(SR),"-ac","2","-i","-",
                        "-c:a","pcm_s16le",out], input=w.astype(np.float32).tobytes(), check=True)
        shutil.move(p, os.path.join(orig_dir, os.path.basename(p)))
        print(f"  ✓ {name}.wav  (orig -> moises-orig/)")
    print(f"done: stems warped onto constant {bpm} grid")

if __name__ == "__main__":
    main()
