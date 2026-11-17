#!/usr/bin/env python3
"""Align each concert candidate take to the current render timeline.
coarse: log-envelope xcorr of several concert channels vs their render counterparts (cues, pb-bass, pb-other, click onsets)
fine:   click-channel waveform xcorr within +-40 ms, in 15 s windows -> offset(t), drift
Writes concert_align.json: {take: {lag_s (concert_t = render_t + lag), drift_ppm, ...}}"""
import glob, json, os, subprocess, unicodedata, sys
import numpy as np

REPO = "/Users/alex/projects/cherry-daddies/music/songs"
DL = "/Users/alex/Downloads"
SCR = os.path.dirname(os.path.abspath(__file__))   # concert_align.json / verdicts.json live next to the scripts
SR = 44100
nfc = lambda s: unicodedata.normalize("NFC", s)
TAKES = [  # (take id, concert folder suffix, repo folder, part)
    ("Солнце", "Set 1/01 Солнце", "Елена Терлеева - Солнце", "keys"),
    ("Беги от меня (бис)", "Set 2/17 Беги от меня (бис)", "Беги от меня", "keys"),
    ("Такая любовь (S1)", "Set 1/04 Такая любовь", "Такая любовь", "keys"),
    ("Такая любовь (бис)", "Set 2/16 Такая любовь (бис)", "Такая любовь", "keys"),
    ("Про красивую жизнь", "Set 2/02 Про красивую жизнь", "Band'Eros - Pro krasivuju zhizn'", "keys"),
    ("Солнышко", "Set 2/03 Солнышко", "Demo - Solnyshko", "keys"),
    ("Я устал", "Set 2/04 Я устал", "Quest Pistols - Я устал", "keys"),
    ("Медляк", "Set 2/05 Медляк", "Mr. Credo - Медляк", "keys"),
    ("Мало тебя", "Set 2/06 Мало тебя", "SEREBRO - Malo tebya", "keys"),
    ("Кислотный DJ", "Set 2/12 Кислотный DJ", "Кислотный DJ", "keys"),
    ("Beverly Hills", "Set 2/01 Beverly Hills", "Beverly Hills", "keys"),
    ("Ту-лу-ла", "Set 1/05 Ту-лу-ла", "Чичерина - Ту-лу-ла", "bass"),
    ("Медведица", "Set 2/07 Медведица", "Мумий Тролль - Медведица", "bass"),
    ("Pretty Fly", "Set 2/08 Pretty Fly", "The Offspring - Pretty Fly (For A White Guy)", "bass"),
    ("Кукла колдуна", "Set 2/09 Кукла колдуна", "Король и Шут - Кукла колдуна", "bass"),
]
ALLDIRS = [nfc(d.rstrip("/")) + "/" for d in glob.glob(DL + "/**/Set */*/", recursive=True)]
RAWDIRS = {nfc(d.rstrip("/")): d for d in glob.glob(DL + "/**/Set */*/", recursive=True)}

def cdir(suffix):
    m = [raw for n, raw in RAWDIRS.items() if n.endswith(nfc(suffix))]
    assert len(m) == 1, (suffix, m); return m[0]
def dec(p, sr=SR):
    r = subprocess.run(["ffmpeg", "-v", "quiet", "-i", p, "-f", "f32le", "-ac", "1", "-ar", str(sr), "-"], capture_output=True)
    return np.frombuffer(r.stdout, np.float32).copy()
def chan(d, num):
    f = [x for x in glob.glob(d + "*.wav") if os.path.basename(x).startswith(num + " ")]
    return f[0] if f else None
HOP = 441
def logenv(x):
    n = len(x)//HOP; e = np.log(np.sqrt((x[:n*HOP].reshape(n, HOP)**2).mean(1) + 1e-12) + 1e-4); return e - e.mean()
def fluxenv(x):
    n = len(x)//HOP; e = np.sqrt((x[:n*HOP].reshape(n, HOP)**2).mean(1) + 1e-12)
    f = np.maximum(np.diff(np.log(e + 1e-4), prepend=0), 0); return f - f.mean()
def xc(a, b):
    n = 1 << int(np.ceil(np.log2(len(a) + len(b)))); c = np.fft.irfft(np.fft.rfft(a, n)*np.conj(np.fft.rfft(b, n)), n)
    i = int(np.argmax(c)); lag = i if i < n//2 else i - n
    return lag, float(c[i]/np.sqrt((a**2).sum()*(b**2).sum() + 1e-12))

res = {}
for take, suf, repo, part in TAKES:
    d = cdir(suf); F = f"{REPO}/{repo}/auto-render"
    pairs = [("14", "cues.wav", logenv), ("11", "pb-bass.wav", logenv), ("12", "pb-other.wav", logenv), ("13", "click.wav", fluxenv)]
    cands = []
    for num, rf, fn in pairs:
        c = chan(d, num)
        if not c or not os.path.exists(f"{F}/{rf}"): continue
        x = dec(c)
        if np.sqrt(np.mean(x**2)) < 1e-4: continue
        lag, r = xc(fn(x), fn(dec(f"{F}/{rf}")))
        cands.append((r, lag*HOP/SR, num))
    cands.sort(reverse=True)
    # consensus: best corr among non-click; click only if nothing else
    best = next((c for c in cands if c[2] != "13"), cands[0] if cands else None)
    info = {"repo": repo, "part": part, "dir": d, "coarse": [(round(r, 2), round(l, 3), n) for r, l, n in cands]}
    if best is None:
        res[take] = info; print(take, "NO ALIGN"); continue
    lag0 = best[1]
    # fine: waveform xcorr in 15 s windows (+-40 ms) on the first channel that matches its render file
    L0 = int(round(lag0*SR)); W = int(15*SR); M = int(0.04*SR)
    for num, rf in (("12", "pb-other.wav"), ("11", "pb-bass.wav"), ("14", "cues.wav"), ("13", "click.wav")):
        cc = chan(d, num)
        if not cc or not os.path.exists(f"{F}/{rf}"): continue
        x = dec(cc); y = dec(f"{F}/{rf}"); fine = []
        for s0 in range(int(2*SR), len(y) - W, W//2):
            seg = y[s0:s0+W]
            if np.sqrt(np.mean(seg**2)) < 3e-3: continue
            cs = s0 + L0 - M; ce = s0 + L0 + W + M
            if cs < 0 or ce > len(x): continue
            tgt = x[cs:ce]
            c = np.correlate(tgt, seg, "valid")
            k = int(np.argmax(np.abs(c))); r = abs(c[k])/np.sqrt(np.sum(seg**2)*np.sum(tgt[k:k+W]**2) + 1e-12)
            fine.append((s0/SR, (L0 - M + k)/SR, float(r)))
        good = [f for f in fine if f[2] > 0.6]
        if len(good) >= 3:
            t = np.array([g[0] for g in good]); l = np.array([g[1] for g in good])
            A = np.stack([np.ones_like(t), t], 1); coef, *_ = np.linalg.lstsq(A, l, rcond=None)
            resid = l - A @ coef
            info.update(fine_ch=num, fine_n=len(fine), fine_good=len(good), lag_s=float(coef[0]), drift_ppm=float(coef[1]*1e6),
                        resid_ms=float(np.abs(resid).max()*1000), lag_span_ms=float((l.max()-l.min())*1000),
                        fine_r=float(np.median([g[2] for g in good])))
            break
    info.setdefault("lag_s", lag0)
    res[take] = info
    print(f"{take:22s} | fine {info.get('fine_good','-')}/{info.get('fine_n','-')} "
          f"lag {info['lag_s']:+.4f}s via {info.get('fine_ch','-')} r{info.get('fine_r',0):.2f} drift {info.get('drift_ppm', float('nan')):+.1f}ppm resid {info.get('resid_ms', float('nan')):.2f}ms")
json.dump(res, open(SCR + "/concert_align.json", "w"), ensure_ascii=False, indent=1)
