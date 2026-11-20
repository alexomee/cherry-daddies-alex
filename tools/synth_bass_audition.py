#!/usr/bin/env python3
"""Smells Like Teen Spirit: synth-pop bass instead of the bass guitar - audition variants by ear.

The bass line is taken from the JamZone bass stem on the click grid (the song is click: follow, so
tools/part_notes.py does not apply), then three lines are written over the same harmony and played
by a plain software synth (saw + sub through a 24 dB low-pass with a per-note envelope). The sound
is a sketch: the final sound comes from the GM-800, this only picks the line.

  A  the bass guitar line as it is, synth sound
  B  octave eighths low-low-high-high, the pattern of the intro of «Я устал»
  C  off-beat eurodance bass (eighths in the verse, rolling sixteenths in the chorus)

  uv run -q --python 3.12 --with numpy --with scipy --with librosa --with numba --with pyloudnorm \
      python tools/synth_bass_audition.py [--bars 1 54] [--scan]

Writes analysis/teen-spirit-synth-bass/*.mp3 (context = drums + guitars + vocal, and bass alone)
and notes.json (the three lines as [bar, sixteenth, length in sixteenths, midi]). Nothing in music/.
"""
import sys, os, json, argparse, subprocess, numpy as np, librosa, pyloudnorm
from numba import njit
from scipy.signal import butter, sosfilt
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools", "jamzone"))
import jamzone_render as jr
SR = jr.SR
SONG = os.path.join(ROOT, "music", "songs", "Nirvana - Smells Like Teen Spirit")
OUT = os.path.join(ROOT, "analysis", "teen-spirit-synth-bass")
F1, AB1, BB1, DB2 = 29, 32, 34, 37
LOOP = [(F1, BB1), (AB1, DB2)]                 # root of each half bar, bars alternate from bar 2
PRE = [(26, 34), (62, 70), (114, 122)]         # pre-choruses (JamZone sections), TO exclusive
RIFF = [(46, 50), (82, 86)]                    # the post-chorus riff: every variant plays the original line
NAMES = "C C# D D# E F F# G G# A A# B".split()
def nn(m): return f"{NAMES[m % 12]}{m // 12 - 1}"
def hz(m): return 440.0 * 2 ** ((m - 69) / 12)
def inr(b, rs): return any(a <= b < e for a, e in rs)

def grid():
    on = jr.met_onsets(jr.decode(f"{SONG}/01_Click.m4a").mean(1))
    b = list(on); step = float(np.diff(on)[-8:].mean())
    while len(b) < 4 * 152 + 1: b.append(b[-1] + step)
    b = np.array(b)
    s16 = np.concatenate([b[i] + (b[i + 1] - b[i]) * np.arange(4) / 4 for i in range(len(b) - 1)])
    return b, s16                               # s16[(bar-1)*16 + k] = time of sixteenth k of the bar

def transcribe(y, s16):
    """Notes of the bass stem: [slot, length in slots, midi]. Onsets snapped to sixteenths; pitch = pyin median
    over the note, then a fifth/octave-down check (pyin often locks on the 3rd harmonic of F1..A#1)."""
    sr = 11025; hop = 64
    x = librosa.resample(y, orig_sr=SR, target_sr=sr)
    f0, _, _ = librosa.pyin(x, fmin=32, fmax=260, sr=sr, frame_length=2048, hop_length=hop)
    tt = librosa.times_like(f0, sr=sr, hop_length=hop)
    rms = librosa.feature.rms(y=x, frame_length=512, hop_length=hop)[0]
    db = 20 * np.log10(rms / rms.max() + 1e-9)
    on = librosa.onset.onset_detect(y=x, sr=sr, hop_length=hop, units="time", backtrack=False, delta=0.06, wait=5)
    slots = sorted({int(np.argmin(np.abs(s16 - t))) for t in on})
    notes = []
    for i, s in enumerate(slots):
        a = s16[s]; e_slot = slots[i + 1] if i + 1 < len(slots) else s + 8
        k = s
        while k < e_slot and db[(tt >= s16[k]) & (tt < s16[k + 1])].max(initial=-99) > -32: k += 1
        if k == s: continue
        e = s16[k]
        m = (tt >= a + 0.025) & (tt < e - 0.01); f = f0[m]; f = f[~np.isnan(f)]
        if len(f) < 3: continue
        p = int(round(librosa.hz_to_midi(np.median(f))))
        seg = x[int((a + 0.02) * sr):int(e * sr)]
        if len(seg) > 0.17 * sr:
            n = 1 << 16; X = np.abs(np.fft.rfft(seg * np.hanning(len(seg)), n))
            def mag(fr): i0 = int(round(fr * n / sr)); return X[max(0, i0 - 3):i0 + 4].max()
            harm = lambda q: mag(hz(q)) + mag(2 * hz(q)) + mag(3 * hz(q))
            for down in (7, 12):                # true note lower: its own fundamental is present in the spectrum
                if p - down >= 28 and mag(hz(p - down)) > 0.3 * mag(hz(p)) and harm(p - down) > harm(p): p -= down; break
        notes.append([s, k - s, p])
    return notes

def bar_energy(b16, loud_env, bars):
    """0 quiet, 1 pre-chorus, 2 loud (distorted rhythm guitars present)."""
    e = {}
    for b in bars:
        a, z = int(b16[(b - 1) * 16] * SR), int(b16[b * 16] * SR)
        e[b] = 1 if inr(b, PRE) else (2 if loud_env[a:z].mean() > 0.25 else 0)
    return e

def lines(orig, bars, energy, active):
    """Variant note lists as [slot, len, midi]. B and C follow the root loop where the bass guitar plays the loop;
    the riff bars, the pick-up into bar 6 and the last held note come from the original line."""
    by_bar = {}
    for s, l, p in orig: by_bar.setdefault(s // 16 + 1, []).append([s, l, p])
    out = {"A": [n for b in bars for n in by_bar.get(b, [])], "B": [], "C": []}
    for b in bars:
        own = by_bar.get(b, [])
        if b < 6 or inr(b, RIFF) or b >= 142:
            out["B"] += own; out["C"] += own; continue
        for half, root in enumerate(LOOP[b % 2]):
            s0 = (b - 1) * 16 + half * 8
            if active[s0:s0 + 8].mean() < 0.5: continue
            hi = root + 12; e = energy[b]
            fill = (b % 2 == 1 and half == 1)   # the D-flat cell closes the two-bar loop: the sixteenth figure of «Я устал»
            if fill: cell = [(0, 2, root), (2, 2, root), (4, 1, hi), (5, 1, hi), (6, 2, hi)]
            else:    cell = [(0, 2, root), (2, 2, root), (4, 2, hi), (6, 2, hi)]
            out["B"] += [[s0 + k, l, p] for k, l, p in cell]
            if e == 0:   cell = [(2, 2, root), (6, 2, root)]
            elif e == 1: cell = [(2, 2, root), (6, 2, hi)]
            else:        cell = [(1, 1, root), (2, 1, hi), (3, 1, root), (5, 1, root), (6, 1, hi), (7, 1, root)]
            out["C"] += [[s0 + k, l, p] for k, l, p in cell]
    return out

@njit(cache=True)
def lp24(x, fc, q, sr):
    y = np.empty_like(x); a = b = c = d = 0.0
    for i in range(len(x)):
        g = np.tan(np.pi * fc[i] / sr)
        k = 1.41; a1 = 1 / (1 + g * (g + k)); a2 = g * a1; a3 = g * a2
        v3 = x[i] - b; v1 = a1 * a + a2 * v3; v2 = b + a2 * a + a3 * v3; a = 2 * v1 - a; b = 2 * v2 - b
        k = 1 / q; a1 = 1 / (1 + g * (g + k)); a2 = g * a1; a3 = g * a2
        w3 = v2 - d; w1 = a1 * c + a2 * w3; w2 = d + a2 * c + a3 * w3; c = 2 * w1 - c; d = 2 * w2 - d
        y[i] = w2
    return y

def synth(notes, s16, energy, n, sweep):
    """saw + detuned saw + sub sine -> 24 dB low-pass, cutoff falls per note; louder sections open the filter and
    add drive. sweep: slow movement of the cutoff over 8 bars (the filter of the «Я устал» intro moves)."""
    finc = np.zeros(n); amp = np.zeros(n); fc = np.full(n, 120.0); drv = np.ones(n); sub = np.zeros(n)
    for s, l, p in notes:
        a, z = int(s16[s] * SR), int(s16[s + l] * SR); b = s // 16 + 1; e = energy.get(b, 0)
        z = a + max(int(0.06 * SR), int((z - a) * (0.82 if l <= 2 else 0.96)))
        z = min(z, n); m = z - a
        if m <= 0: continue
        t = np.arange(m) / SR
        base, amt, tau, lvl, dr = [(190, 1000, 0.09, 1.0, 1.0), (240, 1500, 0.11, 0.9, 1.6), (330, 2900, 0.16, 0.8, 2.6)][e]
        if sweep: amt *= 1.0 + 0.55 * np.sin(2 * np.pi * (s / 16) / 8 - np.pi / 2)
        acc = 1.0 if s % 4 == 0 else 0.86
        env = np.minimum(1, t / 0.003) * (0.62 + 0.38 * np.exp(-t / 0.14)); r = min(m, int(0.035 * SR)); env[-r:] *= np.linspace(1, 0, r)
        f = hz(p)
        finc[a:z] = f / SR; amp[a:z] = env * lvl * acc; fc[a:z] = base + amt * acc * np.exp(-t / tau) + 2.2 * f; drv[a:z] = dr
        sub[a:z] = (2 * f if f < 60 else f) / SR    # below 60 Hz a PA has little: the sine doubles the 2nd harmonic there
    ph = np.cumsum(finc)
    x = 0.6 * (2 * (ph % 1) - 1) + 0.4 * (2 * ((ph * 1.006) % 1) - 1)
    y = lp24(x * amp, np.minimum(fc, 9000.0), 2.4, float(SR)) + 0.45 * np.sin(2 * np.pi * np.cumsum(sub)) * amp
    y = np.tanh(y * drv) / np.tanh(drv)
    return sosfilt(butter(2, 48, "highpass", fs=SR, output="sos"), y).astype(np.float32)

def mp3(path, x):
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-",
                          "-c:a", "libmp3lame", "-q:a", "2", path], stdin=subprocess.PIPE)
    p.communicate(x.astype(np.float32).tobytes())

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--bars", nargs=2, type=int, default=[1, 54]); ap.add_argument("--scan", action="store_true")
    a = ap.parse_args(); b0, b1 = a.bars; bars = range(b0, b1)
    beats, s16 = grid()
    bass = jr.decode(f"{SONG}/03_Bass.m4a").mean(1)
    orig = transcribe(bass, s16)
    stems = sorted(f for f in os.listdir(SONG) if f.endswith(".m4a"))
    rhythm = sum(jr.decode(f"{SONG}/{f}").mean(1) for f in stems if "Rhythm" in f)
    w = int(0.4 * SR); env = np.sqrt(np.convolve(rhythm ** 2, np.ones(w) / w, mode="same")); env /= np.percentile(env, 99)
    energy = bar_energy(s16, env, range(1, 148))
    w = int(0.02 * SR); benv = np.sqrt(np.convolve(bass ** 2, np.ones(w) / w, mode="same")); benv /= benv.max()
    active = np.array([benv[int(s16[k] * SR):int(s16[k + 1] * SR)].max() > 0.02 for k in range(147 * 16)])
    if a.scan:
        by = {}
        for s, l, p in orig: by.setdefault(s // 16 + 1, []).append((s % 16, l, p))
        for b in range(1, 148):
            row = ["."] * 16
            for k, l, p in by.get(b, []):
                row[k] = nn(p)
                for j in range(k + 1, min(16, k + l)): row[j] = "~"
            print(f"{b:3d} e{energy[b]} " + " ".join("|" * (i % 4 == 0) + f"{c:3s}" for i, c in enumerate(row)))
        return
    os.makedirs(OUT, exist_ok=True)
    v = lines(orig, bars, energy, active)
    t0, t1 = s16[(b0 - 1) * 16], s16[(b1 - 1) * 16]; i0, i1 = int(t0 * SR), int(t1 * SR)
    ctx = sum(jr.decode(f"{SONG}/{f}").mean(1) for f in stems if "Click" not in f and "Bass" not in f)[i0:i1]
    ref = bass[i0:i1]; meter = pyloudnorm.Meter(SR); target = meter.integrated_loudness(ref)
    takes = {}
    for key in "ABC":
        y = synth(v[key], s16, energy, len(bass), sweep=(key == "B"))[i0:i1]
        takes[key] = y * 10 ** ((target - meter.integrated_loudness(y)) / 20)
    mixes = {"0": ctx + ref, **{k: ctx + y for k, y in takes.items()}}
    g = 0.89 / max(np.abs(m).max() for m in mixes.values()); gs = 0.89 / max(np.abs(ref).max(), max(np.abs(y).max() for y in takes.values()))
    names = {"0": "original", "A": "A-same-line", "B": "B-ya-ustal-octaves", "C": "C-offbeat"}
    for k, m in mixes.items(): mp3(f"{OUT}/ctx-{names[k]}.mp3", m * g)
    mp3(f"{OUT}/solo-original.mp3", ref * gs)
    for k, y in takes.items(): mp3(f"{OUT}/solo-{names[k]}.mp3", y * gs)
    marks = [[b, round(float(s16[(b - 1) * 16] - t0), 3)] for b in bars]
    json.dump({"bars": [b0, b1], "bar_sec": marks, "energy": {str(b): energy[b] for b in bars},
               "lines": {k: [[s // 16 + 1, s % 16, l, p] for s, l, p in ns] for k, ns in v.items()}},
              open(f"{OUT}/notes.json", "w"))
    print(f"bars {b0}-{b1 - 1}, {t1 - t0:.1f} s, bass {target:.1f} LUFS; notes A {len(v['A'])} B {len(v['B'])} C {len(v['C'])} -> {OUT}")

if __name__ == "__main__":
    main()
