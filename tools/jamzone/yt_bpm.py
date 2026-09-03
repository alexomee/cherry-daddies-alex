#!/usr/bin/env python3
"""bpm + first downbeat of a plain recording (YouTube mp3) for click-only songs.

Run:  uv run --with librosa --with numpy --python 3.12 python tools/jamzone/yt_bpm.py "<file.mp3>" [...]

Per file: librosa beat_track -> cumulative beat indexing -> lstsq (bpm, phase) with
outlier rejection (the tracker's own `tempo` is bin-quantized — two different songs both
read "129.20"); residual per 30s window = tempo drift (live bands wobble; the rig plays a
constant click anyway); chroma-flux mod 4 over the fitted grid -> downbeat phase; first
downbeat >= first sound = where the synthetic metronome.wav starts (see
wiki/pipelines/youtube-click-only.md).
"""
import sys, numpy as np, librosa, warnings; warnings.filterwarnings("ignore")
for p in sys.argv[1:]:
    y, sr = librosa.load(p, sr=22050, mono=True); dur=len(y)/sr
    oenv = librosa.onset.onset_strength(y=y, sr=sr, hop_length=512)
    _, beats = librosa.beat.beat_track(onset_envelope=oenv, sr=sr, hop_length=512, units="time", trim=False, tightness=100)
    d=np.diff(beats); k=np.r_[0, np.cumsum(np.round(d/np.median(d)))]
    A=np.vstack([k, np.ones_like(k)]).T
    for _ in range(3):
        b, ph = np.linalg.lstsq(A, beats, rcond=None)[0]
        res=beats-(k*b+ph); keep=np.abs(res)<0.25*b
        A=A[keep]; beats=beats[keep]; k=k[keep]
    res=beats-(k*b+ph)
    bpm=60/b
    # candidates: also check 2x/0.5x sanity by onset-envelope autocorrelation peak near bpm
    print(f"\n### {p.split('/')[-1]}  dur {dur:.1f}s")
    print(f"  lstsq bpm {bpm:.3f}  (beat {b:.5f}s, phase {ph:.4f}s, kept {keep.sum()}/{len(keep)})")
    print("  residual vs constant grid per 30s (median ms):", " ".join(f"{t0}s:{np.median(res[(beats>=t0)&(beats<t0+30)])*1000:+.0f}" for t0 in range(0,int(dur),30) if ((beats>=t0)&(beats<t0+30)).sum()>3))
    C=librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=512)
    kk=np.arange(int(np.ceil((dur-ph)/b))-1); gt=ph+kk*b
    gf=librosa.time_to_frames(gt, sr=sr, hop_length=512)
    Cb=np.array([C[:, gf[i]:gf[i+1]].mean(1) for i in range(len(gf)-1)]); Cb/=(Cb.sum(1,keepdims=True)+1e-9)
    flux=np.r_[0,np.abs(np.diff(Cb,axis=0)).sum(1)]
    # low-band energy (kick/bass) at grid beats
    yl=librosa.effects.preemphasis(y, coef=0.0); 
    S=np.abs(librosa.stft(y, n_fft=2048, hop_length=512)); fr=librosa.fft_frequencies(sr=sr, n_fft=2048); low=S[(fr<150)].sum(0)
    E=np.array([low[gf[i]:gf[i]+4].mean() for i in range(len(gf)-1)])
    phs=[float(flux[np.arange(len(flux))%4==r].mean()) for r in range(4)]; els=[float(E[np.arange(len(E))%4==r].mean()) for r in range(4)]
    db=int(np.argmax(phs))
    first=np.nonzero(np.abs(y)>0.01)[0][0]/sr
    fdb=ph+db*b
    while fdb < first-0.05: fdb+=4*b
    print(f"  chroma flux mod4: {[round(x,3) for x in phs]}   low-energy mod4: {[round(x,1) for x in els]}  -> downbeat phase idx {db}")
    print(f"  first sound {first:.3f}s ; first downbeat >= first sound: {fdb:.3f}s ; grid beat before it: {fdb-b:.3f}s")
