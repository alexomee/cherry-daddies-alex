#!/usr/bin/env python3
"""Warp external (Moises) stems onto a constant-bpm grid — rough timing repair.

Moises stems follow the original recording; if the record sags locally (e.g. a
voice-grooved breakdown with drums out — Демо «Солнышко» drifts +52ms at 2:14
and the outro runs -40ms early), a constant click diverges there. This tool
measures the deviation of the Moises metronome from the ideal constant grid,
smooths it (metronome onsets carry ±10ms mp3-frame quantization jitter; only
the slow real drift must survive), and time-warps stems onto that constant grid.

Audio stems are warped using RubberBand (CLI R2 engine with timemap) to PRESERVE
PITCH (preventing the tape-varispeed wobble of up to ±60 cents that naive linear
resampling causes on songs with significant tempo drift). The metronome stem is
resampled via linear interpolation to keep synthetic click transients sharp.

Originals are moved to <song>/moises-orig/ (or read directly from moises-orig/
if already warped previously); warped stems land in the root as 16-bit WAVs.

Grid PHASE is anchored at the song's START (dev(0) = 0): t=0 of the warped stems
== t=0 of the originals, and the drift is absorbed towards the end (output is
extended so nothing is lost there either).

--downbeat K: the true bar line is click K of the metronome. The warped metronome
is silenced before click K so the render anchors bars right.
--pitch P: optional pitch shift in semitones (e.g. -0.078 to tune 442 Hz to 440 Hz).

Usage: jamzone_warp_ext.py "<song name or folder>" --bpm N [--downbeat K] [--pitch P] [--check]
"""
import os, sys, glob, shutil, subprocess, tempfile, re, filecmp
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
    w = np.hanning(SMOOTH+2)[1:-1]; w /= w.sum()
    pad = SMOOTH//2
    sm = np.convolve(np.pad(dev, pad, mode="edge"), w, mode="valid")
    phase = float(sm[0])                              # grid phase = the song's START (see module
    dev -= phase; sm = sm - phase                     # doc): dev(0) = 0, nothing chopped off the front
    return phase + k*beat, sm, on, k

def warp_interp(a, grid_t, dev, n_out):
    """Linear time-domain resample (varispeed). Best for metronome / click pulses."""
    t_out = np.arange(n_out) / SR
    src = (t_out + np.interp(t_out, grid_t, dev)) * SR
    idx = np.arange(len(a))
    w = np.empty((n_out, 2), np.float32)
    for ch in range(2):
        w[:, ch] = np.interp(src, idx, a[:, ch])
    return w

def warp_rubberband(a, grid_t, dev, n_out, pitch_semitones=0.0):
    """Time-stretch audio stems with RubberBand time-mapping — PRESERVES PITCH."""
    n_in = len(a)
    keyframes = [(0, 0)]
    for gt, d in zip(grid_t, dev):
        src_f = int(round((gt + d) * SR))
        tgt_f = int(round(gt * SR))
        if 0 < src_f < n_in and 0 < tgt_f < n_out and src_f > keyframes[-1][0] and tgt_f > keyframes[-1][1]:
            keyframes.append((src_f, tgt_f))
    if n_in > keyframes[-1][0] and n_out > keyframes[-1][1]:
        keyframes.append((n_in, n_out))

    pk = float(np.abs(a).max())
    guard = 0.98 / pk if pk > 0.98 else 1.0

    with tempfile.TemporaryDirectory() as td:
        fin = os.path.join(td, "in.wav")
        fout = os.path.join(td, "out.wav")
        fmap = os.path.join(td, "map.txt")
        with open(fmap, "w") as f:
            for sf, tf in keyframes:
                f.write(f"{sf} {tf}\n")
        subprocess.run(["ffmpeg", "-v", "quiet", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-",
                        "-c:a", "pcm_f32le", fin], input=(a * guard).astype(np.float32).tobytes(), check=True)
        cmd = ["rubberband", "-2", "-M", fmap, "-t", f"{n_out/n_in:.8f}", fin, fout]
        if pitch_semitones:
            cmd.extend(["-p", f"{pitch_semitones:.4f}"])
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"rubberband failed: {res.stderr}")
        raw = subprocess.run(["ffmpeg", "-v", "quiet", "-i", fout, "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"],
                             capture_output=True).stdout
        out = np.frombuffer(raw, np.float32).reshape(-1, 2)
        if guard != 1.0:
            out = out / guard
        if len(out) < n_out:
            out = np.vstack([out, np.zeros((n_out - len(out), 2), np.float32)])
        else:
            out = out[:n_out]
        return out

def main():
    folder = find_folder(sys.argv[1])
    bpm = float(sys.argv[sys.argv.index("--bpm")+1])
    db_k = int(sys.argv[sys.argv.index("--downbeat")+1]) if "--downbeat" in sys.argv else 0
    pitch = float(sys.argv[sys.argv.index("--pitch")+1]) if "--pitch" in sys.argv else 0.0
    check = "--check" in sys.argv

    orig_dir = os.path.join(folder, "moises-orig")
    from_orig = os.path.isdir(orig_dir) and any(f.endswith((".mp3", ".wav")) for f in os.listdir(orig_dir))
    source_dir = orig_dir if from_orig else folder

    all_source = sorted(glob.glob(os.path.join(source_dir, "*.mp3")) + glob.glob(os.path.join(source_dir, "*.wav")))
    all_source = [p for p in all_source if os.path.isfile(p)]

    CANONICAL = {"metronome", "click", "drums", "bass", "guitars", "keys", "strings", "vocals", "backing_vocals", "other", "piano"}
    canonical_stems = [p for p in all_source if os.path.basename(p)[:-4].lower().replace(" ", "_") in CANONICAL
                       or os.path.basename(p)[:-4].lower() in CANONICAL]
    # Short Moises names can coexist with the untouched, long-named imports.
    # Apart from service count-ins, only skip a raw import when its same-role
    # short name has identical bytes; numbered/custom musical parts must survive.
    stems = []
    archive_only = []
    for p in all_source:
        name = os.path.basename(p)[:-4]
        if name.lower() in ("count-in", "count_in") or re.search(
                r"-Count-in-[^-]+-\d+(?:\.\d+)?bpm-\d+(?:\.\d+)?hz$", name, re.I):
            archive_only.append(p)
            continue
        raw = re.search(r"-([^-]+)-[^-]+-\d+(?:\.\d+)?bpm-\d+(?:\.\d+)?hz$",
                        name, re.I)
        if raw:
            role = raw[1].lower().replace(" ", "_")
            if role == "background_vocals":
                role = "backing_vocals"
            if any(os.path.basename(q)[:-4].lower().replace(" ", "_") == role
                   and filecmp.cmp(p, q, shallow=False) for q in canonical_stems):
                archive_only.append(p)
                continue
        stems.append(p)

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

    os.makedirs(orig_dir, exist_ok=True)
    has_rubberband = shutil.which("rubberband") is not None
    if not has_rubberband:
        print("⚠️ rubberband CLI not found, falling back to linear interp (warning: pitch may wobble)")

    for p in stems:
        name = os.path.basename(p)[:-4].lower().replace(" ", "_")
        if name not in CANONICAL and canonical_stems:
            name = os.path.basename(p)[:-4]
        a = decode(p)                                  # stereo float32
        n_out = len(a) + int(np.ceil(max(0.0, -float(dev[-1]))*SR))   # end drifts early -> output grows

        if p == metro or not has_rubberband:
            w = warp_interp(a, grid_t, dev, n_out)
        else:
            w = warp_rubberband(a, grid_t, dev, n_out, pitch_semitones=pitch)

        if p == metro and db_k > 0:                    # true downbeat = click db_k: silence clicks before it
            cut = grid_t[db_k] - 30/bpm
            w[:int(cut*SR)] = 0
            print(f"  metronome: first {db_k} clicks silenced (downbeat = click {db_k}, t={grid_t[db_k]:.3f}s)")

        out = os.path.join(folder, name + ".wav")
        # Encode away from the source: a first-run WAV may already be named out.
        # Archive only after encoding succeeds, then install the warped file.
        with tempfile.TemporaryDirectory(dir=folder) as td:
            staged = os.path.join(td, name + ".wav")
            subprocess.run(["ffmpeg","-v","quiet","-y","-f","f32le","-ar",str(SR),"-ac","2","-i","-",
                            "-c:a","pcm_s16le",staged], input=w.astype(np.float32).tobytes(), check=True)
            if not from_orig:
                shutil.move(p, os.path.join(orig_dir, os.path.basename(p)))
            os.replace(staged, out)
        if not from_orig:
            print(f"  ✓ {name}.wav  (orig -> moises-orig/)")
        else:
            print(f"  ✓ {name}.wav  (re-warped from moises-orig/)")
    if not from_orig:
        # Keep raw aliases and service count-ins out of the renderer's stem glob.
        for p in archive_only:
            shutil.move(p, os.path.join(orig_dir, os.path.basename(p)))
    engine_note = f"rubberband (pitch preserved, pitch shift: {pitch:+.3f}st)" if has_rubberband else "linear interp"
    print(f"done: stems warped onto constant {bpm} grid using {engine_note}")

if __name__ == "__main__":
    main()
