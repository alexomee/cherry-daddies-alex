#!/usr/bin/env python3
"""Re-bar a song's logic-render set so file t=0 sits EXACTLY on a bar line
(arpeggiator MIDI-clock rule, see music/arpeggiator-sync.md) and prepend one
full count-in bar of click.

What it does (all timings measured, not assumed):
  1. Grid: detects every click in the JamZone Click stem (accent ~200Hz = downbeat),
     least-squares fit -> beat, bar, first-downbeat phase.
  2. Bounce shift: cross-correlates a reference bounce against a source stem to find
     how far the Logic bounce timeline is from the stem timeline.
  3. Rebuild as WAV (no mp3 encoder-delay phase ambiguity):
       click.wav    = stem's own first click bar copied to t=0 (count-in) + full Click stem
       cues.wav     = cue_track.wav placed on the new grid
       pb-other.wav = old pb-other bounce re-aligned
       all.wav      = old all bounce re-aligned
     All files same length = whole number of bars.
  4. Writes logic-render/timeline.json {offset_sec, bar_sec, bpm} — the shift to add
     to stem-timeline times (cues.json / structure.json) to hit the new audio.
  5. Old mp3s moved to logic-render/_old-<date>/ (version-every-render rule).

Usage: logic_render_rebar.py "<song name or folder>" [--ref-stem <stem.m4a>]
"""
import os, sys, glob, json, shutil, subprocess, wave, datetime
import numpy as np

SR = 44100
SONGS = os.path.expanduser("~/projects/cherry-daddies/music/songs")

def find_folder(q):
    if os.path.isdir(q): return os.path.abspath(q)
    for d in sorted(glob.glob(os.path.join(SONGS, "*"))):
        if os.path.isdir(d) and q.lower() in os.path.basename(d).lower(): return d
    sys.exit(f"no song folder matches '{q}'")

def decode(p, stereo=True):
    ch = "2" if stereo else "1"
    raw = subprocess.run(["ffmpeg","-v","quiet","-i",p,"-ac",ch,"-ar",str(SR),"-f","f32le","-"],
                         capture_output=True).stdout
    a = np.frombuffer(raw, np.float32).copy()
    return a.reshape(-1, 2) if stereo else a

def onsets(mono, thr_ratio=0.3, min_gap=0.3):
    win = int(0.005*SR)
    env = np.sqrt(np.convolve(mono**2, np.ones(win)/win, mode="same"))
    thr = thr_ratio*env.max()
    raw = np.where((env[1:]>thr)&(env[:-1]<=thr))[0]/SR
    out = [raw[0]]
    for t in raw[1:]:
        if t-out[-1] > min_gap: out.append(t)
    return np.array(out)

def dom_freq(mono, t):
    s = mono[int(t*SR):int(t*SR)+int(0.08*SR)]
    S = np.abs(np.fft.rfft(s*np.hanning(len(s))))
    return np.fft.rfftfreq(len(s), 1/SR)[np.argmax(S)]

def fit_grid(click_mono):
    on = onsets(click_mono)
    k = np.round((on-on[0])/np.median(np.diff(on)))
    A = np.vstack([k, np.ones_like(k)]).T
    beat, phase = np.linalg.lstsq(A, on, rcond=None)[0]
    freqs = np.array([dom_freq(click_mono, t) for t in on[:16]])
    db_idx = int(np.argmax(freqs[:4]))           # accent (≈200Hz) within first 4 beats
    db0 = phase + db_idx*beat
    resid = np.abs(A@[beat, phase]-on)
    return beat, db0, float(resid.max()), len(on)

def xshift(ref, x, n_sec=170):
    """samples by which x content is EARLIER than ref (x[t] == ref[t+s/SR])"""
    N = min(len(ref), len(x), n_sec*SR)
    a = ref[:N].astype(np.float64); b = x[:N].astype(np.float64)
    n = 1
    while n < 2*N: n *= 2
    xc = np.fft.irfft(np.fft.rfft(a, n)*np.conj(np.fft.rfft(b, n)), n)
    L = 6*SR
    seg = np.concatenate([xc[-L:], xc[:L+1]])
    return int(np.argmax(seg)) - L

def shifted_corr(ref, x, s, t0=20, dur=150):
    i0, i1 = int(t0*SR), int((t0+dur)*SR)
    j0, j1 = i0+s, i1+s
    if j0 < 0 or i1 > len(ref) or j1 > len(x): return float("nan")
    return float(np.corrcoef(ref[i0:i1], x[j0:j1])[0,1])

def place(buf, audio, at_samp):
    s0 = max(0, at_samp); a0 = max(0, -at_samp)
    n = min(len(audio)-a0, len(buf)-s0)
    if n > 0: buf[s0:s0+n] += audio[a0:a0+n]

def wav_write(path, x):
    x = np.clip(x, -1, 1)
    w = wave.open(path, "w"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((x*32767).astype("<i2").tobytes()); w.close()

def main():
    folder = find_folder(sys.argv[1])
    rdir = os.path.join(folder, "logic-render")
    click_p = next(iter(glob.glob(os.path.join(folder, "*Click*.m4a"))), None) \
              or sys.exit("no Click stem")
    ref_p = (sys.argv[sys.argv.index("--ref-stem")+1] if "--ref-stem" in sys.argv
             else next(p for p in sorted(glob.glob(os.path.join(folder, "0*.m4a")))
                       if "Click" not in p))
    cue_p = os.path.join(folder, "cue_track.wav")

    click_st = decode(click_p); click_m = click_st.mean(1)
    beat, db0, resid, n_on = fit_grid(click_m)
    bar = 4*beat
    print(f"grid: beat={beat:.6f}s bpm={60/beat:.4f} bar={bar:.6f}s "
          f"first downbeat={db0:.4f}s  ({n_on} clicks, max resid {resid*1000:.1f}ms)")

    ref_m = decode(ref_p, stereo=False)
    old_all = decode(os.path.join(rdir, "all.mp3"))
    s = xshift(ref_m, old_all.mean(1))           # bounce earlier than stems by s samples
    c = shifted_corr(ref_m, old_all.mean(1), -s)
    print(f"bounce shift vs stems: {s/SR*1000:+.2f}ms (corr {c:.3f}) ref={os.path.basename(ref_p)}")
    if not (c > 0.3): sys.exit("bounce/stem alignment not confident — aborting")

    OFF = bar - (db0 % bar)                      # stems land at +OFF; t=0 = bar line, bar 0 = count-in
    off_samp = round(OFF*SR)
    print(f"new timeline = stem + {OFF:.5f}s  (count-in bar 0, first stem downbeat -> bar 1)")

    cue_st = decode(cue_p)
    old_pbo = decode(os.path.join(rdir, "pb-other.mp3"))
    bounce_at = off_samp + s                     # old bounce content placed back on stem grid
    end = max(off_samp+len(click_st), off_samp+len(cue_st),
              bounce_at+len(old_pbo), bounce_at+len(old_all))
    total = int(np.ceil(end/(bar*SR))*bar*SR)    # whole bars
    print(f"length: {total/SR:.3f}s = {total/SR/bar:.1f} bars")

    db0_samp = round(db0*SR)
    countin = click_st[db0_samp:db0_samp+round(bar*SR)]   # stem's own first click bar

    out = {}
    for name, srcs in {
        "click":    [(countin, 0), (click_st, off_samp)],
        "cues":     [(cue_st, off_samp)],
        "pb-other": [(old_pbo, bounce_at)],
        "all":      [(old_all, bounce_at)],
    }.items():
        buf = np.zeros((total, 2), np.float32)
        for audio, at in srcs: place(buf, audio, at)
        out[name] = buf

    # verify before writing (zero pre-roll so the t=0 click's rising edge is detectable)
    pre = 1000
    v_click = onsets(np.concatenate([np.zeros(pre, np.float32), out["click"].mean(1)])) - pre/SR
    err = [(t - round(t/beat)*beat)*1000 for t in v_click[:8]]
    print(f"verify click grid: first onset {v_click[0]*1000:.1f}ms, beat err first 8: "
          f"{[f'{e:+.1f}' for e in err]} ms")
    vc = shifted_corr(ref_m, out["all"].mean(1), off_samp)
    vq = shifted_corr(decode(cue_p, stereo=False), out["cues"].mean(1), off_samp)
    print(f"verify content: stems->all corr={vc:.3f}  cue_track->cues corr={vq:.3f}")
    if abs(v_click[0]) > 0.01 or max(abs(e) for e in err) > 3 or vc < 0.3 or vq < 0.9:
        sys.exit("verification failed — nothing written")

    old = os.path.join(rdir, "_old-" + datetime.date.today().isoformat())
    os.makedirs(old, exist_ok=True)
    for p in glob.glob(os.path.join(rdir, "*.mp3")):
        shutil.move(p, os.path.join(old, os.path.basename(p)))
    for name, buf in out.items():
        wav_write(os.path.join(rdir, name + ".wav"), buf)
    json.dump({"offset_sec": round(OFF, 6), "bar_sec": round(bar, 6),
               "bpm": round(60/beat, 4),
               "note": "add offset_sec to stem-timeline times (cues.json/structure.json); "
                       "t=0 = bar line; bar 0 = click count-in"},
              open(os.path.join(rdir, "timeline.json"), "w"), indent=1)
    print(f"✓ wrote {', '.join(n+'.wav' for n in out)} + timeline.json; old mp3s -> {os.path.basename(old)}/")

if __name__ == "__main__":
    main()
