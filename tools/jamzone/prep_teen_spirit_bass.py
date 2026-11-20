#!/usr/bin/env python3
"""Smells Like Teen Spirit: the GM-800 synth bass take -> parts/synth-bass.wav (pb-bass layer, stem frame).

The take (tools/synth_bass_gm800.py ARR 25 --dir full-128; scene 25 M&S BASS ONLY, line ARR (or B2) of
tools/synth_bass_audition.py) starts on the bar line of bar 1 = the first click of the click stem. It is
resampled to 44.1 kHz, put at that time in the stem frame and moved so that its attacks sit on the grid
where the attacks of the JamZone bass guitar sit (the tone speaks a few ms late).

  uv run -q --python 3.12 --with numpy --with scipy --with soundfile --with librosa --with pyloudnorm \
      python tools/jamzone/prep_teen_spirit_bass.py [ARR3|ARR2|ARR|B2]   # the layer from that take
      ... prep_teen_spirit_bass.py splice [ARR3]                          # that take cut together from B2 + ARR, no GM-800
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


def splice(out="ARR3", base="B2", donors=("B2", "ARR")):
    """The take of line `out` cut together from recorded takes, no GM-800: `base` everywhere, and every eighth
    where `out` differs from the line of `base` comes from an eighth of a donor take that plays the same note
    (the one closest in length: the click is not constant), or is silenced. Cuts sit 12 ms before a note, in the
    gap between notes, with 6 ms crossfades. Works for any reordering of eighth notes that some take already
    has; a note of another pitch or length needs a recording (tools/synth_bass_gm800.py)."""
    d = json.load(open(f"{SRC}/notes.json")); ss = np.array(d["slot_sec"]); b0 = d["bars"][0]
    def eighths(line):                          # eighth index -> pitch, for notes one eighth long on an eighth
        return {((bar - b0) * 16 + k) // 2: p for bar, k, ln, p in d["lines"][line] if ln == 2 and k % 2 == 0}
    def others(line): return sorted(tuple(n) for n in d["lines"][line] if not (n[2] == 2 and n[1] % 2 == 0))
    if others(out) != others(base): sys.exit(f"{out} and {base} differ in notes that are not plain eighths: record it")
    eo, eb = eighths(out), eighths(base); audio = {}; pool = {}
    for t in donors:
        audio[t], sr = sf.read(f"{SRC}/gm800-{t}-s025.wav", always_2d=True, dtype="float32")
        for e, p in eighths(t).items(): pool.setdefault(p, []).append((t, e))
    res = audio[base].copy(); pre, xf = int(0.012 * sr), int(0.006 * sr); n_cut = 0; bars = set()
    up, dn = np.linspace(0, 1, xf, dtype=np.float32)[:, None], np.linspace(1, 0, xf, dtype=np.float32)[:, None]
    ln = lambda e: ss[e * 2 + 2] - ss[e * 2]
    for e in sorted(set(eo) | set(eb)):
        if eo.get(e) == eb.get(e): continue
        a, z = int(ss[e * 2] * sr) - pre, int(ss[e * 2 + 2] * sr) - pre
        if e in eo:
            if eo[e] not in pool: sys.exit(f"bar {b0 + e // 8}: no recorded eighth of midi {eo[e]}: record it")
            t, j = min(pool[eo[e]], key=lambda c: abs(ln(c[1]) - ln(e)))
            a2 = int(ss[j * 2] * sr) - pre; seg = audio[t][a2:a2 + (z - a)].copy()
        else: seg = np.zeros((z - a, 2), np.float32)
        seg[:xf] = seg[:xf] * up + res[a:a + xf] * dn; seg[-xf:] = seg[-xf:] * dn + res[z - xf:z] * up
        res[a:z] = seg; n_cut += 1; bars.add(b0 + e // 8)
    sf.write(f"{SRC}/gm800-{out}-s025.wav", res, sr, subtype="PCM_16")
    print(f"{out}: {n_cut} eighths replaced in {len(bars)} bars of {base} ({', '.join(map(str, sorted(bars)))}) -> gm800-{out}-s025.wav")


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "splice":
        return splice(*sys.argv[2:3])
    d = json.load(open(f"{SRC}/notes.json")); ss = np.array(d["slot_sec"])
    t0 = float(jr.met_onsets(jr.decode(f"{SONG}/01_Click.m4a").mean(1))[0]); slots = ss + t0
    n = len(jr.decode(f"{SONG}/03_Bass.m4a"))
    take = sys.argv[1] if len(sys.argv) > 1 else "ARR3"         # line of notes.json: ARR = the arrangement, B2 = the plain motor
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
