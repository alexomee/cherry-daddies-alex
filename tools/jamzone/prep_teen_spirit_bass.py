#!/usr/bin/env python3
"""Smells Like Teen Spirit: the GM-800 synth bass take -> parts/synth-bass.wav (pb-bass layer, stem frame).

The take (tools/synth_bass_gm800.py ARR 25 --dir full-128; scene 25 M&S BASS ONLY, line ARR (or B2) of
tools/synth_bass_audition.py) starts on the bar line of bar 1 = the first click of the click stem. It is
resampled to 44.1 kHz, put at that time in the stem frame and moved so that its attacks sit on the grid
where the attacks of the JamZone bass guitar sit (the tone speaks a few ms late).

  uv run -q --python 3.12 --with numpy --with scipy --with soundfile --with librosa --with pyloudnorm \
      python tools/jamzone/prep_teen_spirit_bass.py [ARR2|ARR|B2]     # the layer from that take
      ... prep_teen_spirit_bass.py splice                              # take ARR2 cut together from B2 + ARR, no GM-800
"""
import os, sys, json, numpy as np, soundfile as sf, librosa, pyloudnorm
from scipy.signal import resample_poly
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools", "jamzone"))
import jamzone_render as jr
SR = jr.SR
SONG = os.path.join(ROOT, "music", "songs", "Nirvana - Smells Like Teen Spirit")
SRC = os.path.join(ROOT, "analysis", "teen-spirit-synth-bass", "full-128")


def attack_dev(x, slots):
    """Median distance (ms) from the grid sixteenth to the attack next to it: peaks of the spectral flux."""
    hop = 64; o = librosa.onset.onset_strength(y=x, sr=SR, hop_length=hop, n_fft=1024)
    pk = librosa.util.peak_pick(o, pre_max=20, post_max=20, pre_avg=60, post_avg=60, delta=0.25 * o.std(), wait=40)
    t = pk * hop / SR; d = np.array([u - slots[np.argmin(np.abs(slots - u))] for u in t])
    d = d[np.abs(d) < 0.05] * 1000
    return float(np.median(d)), float(d.std()), len(d)


def splice(base="B2", donor="ARR", out="ARR2"):
    """The take of line `out` cut together from two recorded takes, no GM-800: `base` everywhere, and every cell
    (half bar) where `out` differs from `base` comes from a bar of `donor` that plays the same notes in that cell,
    the one closest in length (the click is not constant), moved eighth by eighth. Cuts sit 12 ms before a note,
    in the gap between notes, with 6 ms crossfades."""
    d = json.load(open(f"{SRC}/notes.json")); ss = np.array(d["slot_sec"]); b0 = d["bars"][0]
    def cells(line):
        c = {}
        for bar, k, ln, p in d["lines"][line]: c.setdefault(((bar - b0) * 2 + k // 8), []).append((k % 8, ln, p))
        return {i: tuple(sorted(v)) for i, v in c.items()}
    cb, cd, co = cells(base), cells(donor), cells(out)
    x, sr = sf.read(f"{SRC}/gm800-{base}-s025.wav", always_2d=True, dtype="float32")
    y, _ = sf.read(f"{SRC}/gm800-{donor}-s025.wav", always_2d=True, dtype="float32")
    pre, xf = int(0.012 * sr), int(0.006 * sr); res = x.copy(); n_cut = 0; worst = 0.0
    up, dn = np.linspace(0, 1, xf, dtype=np.float32)[:, None], np.linspace(1, 0, xf, dtype=np.float32)[:, None]
    for i in sorted(co):
        if co[i] == cb.get(i): continue
        t0, t1 = ss[i * 8], ss[i * 8 + 8]
        cand = [j for j in cd if cd[j] == co[i]]
        if not cand: sys.exit(f"cell {i} (bar {b0 + i // 2}): no bar of {donor} plays {co[i]}")
        j = min(cand, key=lambda j: abs((ss[j * 8 + 8] - ss[j * 8]) - (t1 - t0)))
        dd = (ss[j * 8 + 8] - ss[j * 8]) - (t1 - t0); worst = max(worst, abs(dd))
        for q in range(4):                      # eighth by eighth: every note lands on its own grid time even when
            a, z = int(ss[i * 8 + 2 * q] * sr) - pre, int(ss[i * 8 + 2 * q + 2] * sr) - pre   # the donor cell is longer/shorter
            a2 = int(ss[j * 8 + 2 * q] * sr) - pre; seg = y[a2:a2 + (z - a)].copy()
            seg[:xf] = seg[:xf] * up + res[a:a + xf] * dn; seg[-xf:] = seg[-xf:] * dn + res[z - xf:z] * up
            res[a:z] = seg
        n_cut += 1
        print(f"  bar {b0 + i // 2}.{'13'[i % 2]}: from bar {b0 + j // 2} of {donor} ({dd * 1000:+.1f} ms over the cell)")
    sf.write(f"{SRC}/gm800-{out}-s025.wav", res, sr, subtype="PCM_16")
    print(f"{n_cut} cells of {donor} in {base} -> gm800-{out}-s025.wav; longest stretch mismatch {worst * 1000:.1f} ms")


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "splice":
        return splice()
    d = json.load(open(f"{SRC}/notes.json")); ss = np.array(d["slot_sec"])
    t0 = float(jr.met_onsets(jr.decode(f"{SONG}/01_Click.m4a").mean(1))[0]); slots = ss + t0
    n = len(jr.decode(f"{SONG}/03_Bass.m4a"))
    take = sys.argv[1] if len(sys.argv) > 1 else "ARR2"         # line of notes.json: ARR = the arrangement, B2 = the plain motor
    y, sr = sf.read(f"{SRC}/gm800-{take}-s025.wav", always_2d=True, dtype="float32")
    y = resample_poly(y, SR, sr, axis=0).astype(np.float32)
    ref = attack_dev(jr.decode(f"{SONG}/03_Bass.m4a").mean(1), slots)
    buf = np.zeros((n, 2), np.float32); a = int(round(t0 * SR)); m = min(len(y), n - a); buf[a:a + m] = y[:m]
    raw = attack_dev(buf.mean(1), slots)
    sh = int(round((raw[0] - ref[0]) / 1000 * SR))                 # > 0: the take is late, move it earlier
    out = np.zeros_like(buf)
    if sh >= 0: out[:n - sh] = buf[sh:]
    else: out[-sh:] = buf[:n + sh]
    fin = attack_dev(out.mean(1), slots)
    os.makedirs(f"{SONG}/parts", exist_ok=True)
    sf.write(f"{SONG}/parts/synth-bass.wav", out, SR, subtype="PCM_24")
    lu = pyloudnorm.Meter(SR).integrated_loudness(out.astype(np.float64))
    print(f"attacks vs grid: bass guitar {ref[0]:+.1f} ms (sd {ref[1]:.1f}, n {ref[2]}), take {raw[0]:+.1f} ms (n {raw[2]}) -> moved "
          f"{-sh / SR * 1000:+.1f} ms -> {fin[0]:+.1f} ms")
    print(f"parts/synth-bass.wav: {n / SR:.1f} s, {lu:.1f} LUFS, peak {20 * np.log10(np.abs(out).max()):.1f} dBFS; "
          f"gain_db for the pb-bass norm -19.2: {-19.2 - lu:+.1f}")


if __name__ == "__main__":
    main()
