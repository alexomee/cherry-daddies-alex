#!/usr/bin/env python3
"""Smells Like Teen Spirit at 128 bpm instead of 118 (Alex 2026-11-20: «на 10 bpm быстрее»).

The render has no tempo change, so the stems themselves are made faster once:
  - the JamZone originals move to <song>/jamzone-orig/ (the render globs only NN_*.m4a at the top);
  - every stem is time-stretched by 128/118 with the rubberband CLI (R3, pitch kept), one ratio for
    all, so the stems stay in sync with each other: new time = old time / RATIO;
  - the click is not stretched (it smears): every hit of the original click is cut out and put at
    its old time / RATIO, so the tempo map of the JamZone click (click: follow) is kept, only faster;
  - written as ALAC in .m4a under the old names (lossless, no encoder delay).
JamZone structure.json / tiles.json times stay in the ORIGINAL tempo: divide by RATIO
(jamzone_render reads "stem_speed" of mix.json for --sections).

  uv run -q --python 3.12 --with numpy --with soundfile python tools/jamzone/prep_teen_spirit_tempo.py [--check]
"""
import os, sys, glob, shutil, subprocess, tempfile, numpy as np, soundfile as sf
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools", "jamzone"))
import jamzone_render as jr
SR = jr.SR
SONG = os.path.join(ROOT, "music", "songs", "Nirvana - Smells Like Teen Spirit")
ORIG = os.path.join(SONG, "jamzone-orig")
RATIO = 128.0 / 118.0


def alac(path, x):
    with tempfile.TemporaryDirectory() as td:
        w = os.path.join(td, "x.wav"); sf.write(w, x, SR, subtype="PCM_24")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", w, "-c:a", "alac", path], check=True)


def click(x):
    on = jr.met_onsets(x.mean(1)); n = int(np.ceil(len(x) / RATIO)); y = np.zeros((n, 2), np.float32)
    pre = int(0.006 * SR); fade = int(0.004 * SR)
    for i, t in enumerate(on):
        a = int(round(t * SR)) - pre; nxt = on[i + 1] if i + 1 < len(on) else t + 0.5
        ln = int(round((nxt - t) / RATIO * SR)) - 2          # up to the next hit at the new tempo
        seg = x[max(a, 0):a + ln].copy(); seg[-fade:] *= np.linspace(1, 0, fade, dtype=np.float32)[:, None]
        b = int(round(t / RATIO * SR)) - pre; b = max(b, 0)
        m = min(len(seg), n - b); y[b:b + m] += seg[:m]
    return y, on


def main():
    check = "--check" in sys.argv
    if not check:
        if os.path.isdir(ORIG):
            sys.exit(f"{ORIG} exists: the stems are already stretched (restore the originals first)")
        os.makedirs(ORIG)
        for p in sorted(glob.glob(os.path.join(SONG, "[0-9][0-9]_*.m4a"))): shutil.move(p, ORIG)
        for p in sorted(glob.glob(os.path.join(ORIG, "*.m4a"))):
            name = os.path.basename(p); x = jr.decode(p); out = os.path.join(SONG, name)
            if "Click" in name:
                y, on = click(x); alac(out, y); print(f"{name}: {len(on)} hits rebuilt"); continue
            with tempfile.TemporaryDirectory() as td:
                fi, fo = os.path.join(td, "i.wav"), os.path.join(td, "o.wav")
                pk = float(np.abs(x).max()) or 1.0; g = min(1.0, 0.7 / pk)   # rubberband hard-clips at 1.0
                sf.write(fi, x * g, SR, subtype="FLOAT")
                r = subprocess.run(["rubberband", "-3", "--tempo", f"{RATIO:.8f}", fi, fo], capture_output=True, text=True)
                if r.returncode: sys.exit("rubberband: " + r.stderr[-300:])
                y, _ = sf.read(fo, always_2d=True, dtype="float32"); y /= g
            n = int(np.ceil(len(x) / RATIO)); y = y[:n] if len(y) >= n else np.vstack([y, np.zeros((n - len(y), 2), np.float32)])
            alac(out, y); print(f"{name}: {len(x) / SR:.2f} s -> {len(y) / SR:.2f} s, peak {20 * np.log10(np.abs(y).max() + 1e-9):.1f}")
    # check: drum and bass attacks against the click, before and after (should differ by the same few ms everywhere)
    def hits(p, lo, hi):
        from scipy.signal import butter, sosfilt
        x = sosfilt(butter(4, [lo, hi], "bandpass", fs=SR, output="sos"), jr.decode(p).mean(1))
        w = int(0.003 * SR); e = np.sqrt(np.convolve(x ** 2, np.ones(w) / w, mode="same")); d = np.diff(e, prepend=0)
        thr = 0.25 * np.percentile(d, 99.9); idx = np.where((d[1:-1] > thr) & (d[1:-1] >= d[:-2]) & (d[1:-1] > d[2:]))[0] + 1
        out = []
        for i in idx:
            if not out or i - out[-1] > 0.12 * SR: out.append(i)
        return np.array(out) / SR
    for tag, folder, k in (("orig", ORIG, 1.0), ("new", SONG, RATIO)):
        ck = jr.met_onsets(jr.decode(os.path.join(folder, "01_Click.m4a")).mean(1))
        dr = hits(os.path.join(folder, "02_Drum_Kit.m4a"), 40, 120)
        rows = []
        for a, b in ((0, 0.34), (0.34, 0.67), (0.67, 1.0)):
            T = ck[-1]; sel = dr[(dr >= a * T) & (dr < b * T)]
            dev = np.array([t - ck[np.argmin(np.abs(ck - t))] for t in sel]); dev = dev[np.abs(dev) < 0.06] * 1000
            rows.append(f"{np.median(dev):+6.1f} ms (sd {dev.std():4.1f}, n {len(dev)})")
        ib = np.diff(ck)
        print(f"{tag:4s} click {len(ck)} hits, bpm median {60 / np.median(ib):.2f}, first {ck[0] * k:.4f} s (x ratio); kick - click by thirds: " + " | ".join(rows))


if __name__ == "__main__":
    main()
