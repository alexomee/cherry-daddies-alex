#!/usr/bin/env python3
"""Concert (28.10 mixer multitrack) vs stem, per candidate take.
usage: concert_analyze.py [take substring ...]   (default: all)
Outputs: OUT/<slug>/{ab-stem.mp3, ab-concert.mp3, solo-stem.mp3, solo-concert.mp3, concert-part.wav}
         OUT/results.json (metrics), printed summary."""
import glob, json, os, re, subprocess, sys, tempfile, unicodedata
import numpy as np
sys.path.insert(0, "/Users/alex/projects/cherry-daddies/tools/jamzone")
import jamzone_render as jr

SR = 44100
REPO = "/Users/alex/projects/cherry-daddies/music/songs"
SCR = os.path.dirname(os.path.abspath(__file__))   # concert_align.json / verdicts.json live next to the scripts
OUT = "/Users/alex/projects/cherry-daddies/analysis/concert-2810"
ALIGN = json.load(open(SCR + "/concert_align.json"))   # coarse lags (cues/PB envelopes)
PART = {"Солнце": ["keys"], "Беги от меня (бис)": ["keys"], "Такая любовь (S1)": ["keys", "wind"],
        "Такая любовь (бис)": ["keys", "wind"], "Про красивую жизнь": ["keys", "other"], "Солнышко": ["keys", "other"],
        "Я устал": ["keys", "other"], "Медляк": ["keys"], "Мало тебя": ["keys", "other"],
        "Кислотный DJ": ["keys", "strings", "wind"], "Beverly Hills": ["keys", "other"],
        "Ту-лу-ла": ["bass"], "Медведица": ["bass"], "Pretty Fly": ["bass"], "Кукла колдуна": ["bass"]}
# Такая любовь: Roma's keys are already in playback as his recorded layer -> compare concert with that layer (+ wind stem)
LAYER_PART = {"Такая любовь (S1)": ["takaia_lubov_keys"], "Такая любовь (бис)": ["takaia_lubov_keys"]}
STEM_PART_OVERRIDE = {"Такая любовь (S1)": ["wind"], "Такая любовь (бис)": ["wind"]}
SLUG = lambda s: re.sub(r"[^\w]+", "-", unicodedata.normalize("NFC", s)).strip("-").lower()

def dec(p, ch=2, sr=SR):
    raw = subprocess.run(["ffmpeg", "-v", "quiet", "-i", p, "-ac", str(ch), "-ar", str(sr), "-f", "f32le", "-"], capture_output=True).stdout
    a = np.frombuffer(raw, np.float32).copy(); return a.reshape(-1, ch) if ch > 1 else a
def mono(x): return x.mean(1) if x.ndim > 1 else x
def place(buf, a, start):
    s0 = max(0, start); a0 = max(0, -start); n = min(len(a) - a0, len(buf) - s0)
    if n > 0: buf[s0:s0+n] += a[a0:a0+n]
def write_mp3(path, x):
    subprocess.run(["ffmpeg", "-v", "quiet", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-", "-b:a", "192k", path],
                   input=x.astype(np.float32).tobytes())
def lufs(x):
    with tempfile.NamedTemporaryFile(suffix=".wav") as f:
        subprocess.run(["ffmpeg", "-v", "quiet", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-", "-c:a", "pcm_f32le", f.name],
                       input=x.astype(np.float32).tobytes())
        o = subprocess.run(["ffmpeg", "-nostats", "-i", f.name, "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True).stderr
    v = re.findall(r"I:\s+(-?[\d.]+) LUFS", o); return float(v[-1]) if v else -70.0
H = 44
def onset_times(x, thr=0.25):
    m = mono(x); n = len(m)//H; e = np.sqrt((m[:n*H].reshape(n, H)**2).mean(1) + 1e-12)
    f = np.maximum(np.diff(np.log(e + 1e-4), prepend=0), 0)
    sm = np.convolve(f, np.ones(5)/5, "same"); thrv = thr*np.percentile(sm, 99.5)
    pk = [i for i in range(2, n-2) if sm[i] > thrv and sm[i] >= sm[i-1] and sm[i] > sm[i+1] and e[i+2] > 10**(-50/20)]
    out = []
    for i in pk:
        if not out or i - out[-1] > 60: out.append(i)       # >=60 ms apart
    return np.array(out)*H/SR

def fit_map(d, render_click, COARSE):
    """concert_t = a + b*render_t from click onsets (scale searched from IOI ratio)."""
    cc = glob.glob(d + "13 *.wav")[0]
    co = jr.onsets(dec(cc, 1), 0.3, 0.1); ro = jr.onsets(mono(render_click), 0.3, 0.1)
    b0 = np.median(np.diff(co))/np.median(np.diff(ro))
    best = None
    for i in range(min(40, len(co))):
        for j in range(min(8, len(ro))):
            a0 = co[i] - b0*ro[j]; pred = a0 + b0*ro
            k = np.searchsorted(co, pred); k = np.clip(k, 1, len(co)-1)
            dd = np.minimum(np.abs(co[k] - pred), np.abs(co[k-1] - pred)); hit = (dd < 0.03).sum()
            if abs(b0 - 1) < 0.002 and abs(a0 - COARSE) > 0.25: continue   # periodic click: stay on the coarse (cues/PB) lag, not a bar off
            if best is None or hit > best[0]: best = (hit, a0)
    a0 = best[1]; pred = a0 + b0*ro
    k = np.clip(np.searchsorted(co, pred), 1, len(co)-1); pick = np.where(np.abs(co[k]-pred) < np.abs(co[k-1]-pred), co[k], co[k-1])
    m = np.abs(pick - pred) < 0.03
    A = np.stack([np.ones(m.sum()), ro[m]], 1); (a, b), *_ = np.linalg.lstsq(A, pick[m], rcond=None)
    res = pick[m] - (a + b*ro[m])
    return float(a), float(b), int(m.sum()), len(ro), float(np.percentile(np.abs(res), 90)*1000)

def concert_on_render(chfile, a, b, total):
    with tempfile.TemporaryDirectory() as td:
        src = chfile
        if abs(b - 1) > 0.002:      # real tempo difference (MainStage stretched playback): time-stretch, keep pitch
            out = os.path.join(td, "st.wav")
            subprocess.run(["rubberband", "-3", "-T", f"{b:.8f}", chfile, out], capture_output=True)
            src, rate = out, None
            x = dec(src)            # times now = c/b
        else:                       # clock drift only: resample (pitch change < 0.002 st)
            raw = subprocess.run(["ffmpeg", "-v", "quiet", "-i", chfile, "-af", f"asetrate={48000*b:.4f},aresample={SR}",
                                  "-ac", "2", "-f", "f32le", "-"], capture_output=True).stdout
            x = np.frombuffer(raw, np.float32).copy().reshape(-1, 2)
    buf = np.zeros((total, 2), np.float32); place(buf, x, -int(round(a/b*SR))); return buf

def bar_of(t, t1, beat):
    k = (t - t1)/beat; bar = int(np.floor(k/4)) + 1; bt = k - (bar-1)*4 + 1; return f"{bar}.{bt:.1f}"
def mmss(t): return f"{int(t//60)}:{t%60:04.1f}"

def chroma_frames(x, edges, lo, hi):
    m = mono(x); C = []; act = []
    for s, e in zip(edges[:-1], edges[1:]):
        seg = m[int(s*SR):int(e*SR)]
        if len(seg) < 512: C.append(np.zeros(12)); act.append(False); continue
        S = np.abs(np.fft.rfft(seg*np.hanning(len(seg)))); f = np.fft.rfftfreq(len(seg), 1/SR); sel = (f > lo) & (f < hi)
        pc = (np.round(12*np.log2(f[sel]/440)) % 12).astype(int); v = np.bincount(pc, S[sel], 12)
        C.append(v/(np.linalg.norm(v) + 1e-9)); act.append(np.sqrt(np.mean(seg**2)) > 10**(-48/20))
    return np.array(C), np.array(act)

def runs(mask, minlen):
    out = []; s = None
    for i, v in enumerate(list(mask) + [False]):
        if v and s is None: s = i
        if not v and s is not None:
            if i - s >= minlen: out.append((s, i))
            s = None
    return out

sel = sys.argv[1:]
results = json.load(open(OUT + "/results.json")) if os.path.exists(OUT + "/results.json") else {}
for take, part in PART.items():
    if sel and not any(q in take for q in sel): continue
    al = ALIGN[take]; folder = f"{REPO}/{al['repo']}"; d = al["dir"]; kind = al["part"]
    mix = json.load(open(folder + "/mix.json")); semi = mix.get("pitch_semitones") or 0
    tl = json.load(open(folder + "/auto-render/timeline.json")); OFF = int(round(tl["offset_sec"]*SR))
    allw = dec(folder + "/auto-render/all.wav"); total = len(allw)
    rclick = dec(folder + "/auto-render/click.wav")
    a, b, nhit, nclk, p90 = fit_map(d, rclick, al["lag_s"])
    # ---- stem side
    stems = jr._stem_paths(folder)
    drop = set(mix.get("exclude_stems") or mix.get("drop_stems") or [])
    replaced = set()
    for g in jr.pb_group_names(mix):
        for ent in (mix.get(g) or {}).get("layers", []):
            if isinstance(ent, dict): replaced |= set(ent.get("replaces", []))
    music = [n for n in stems if n.lower() not in ("metronome", "click") and not jr.is_percussion(n) and n not in drop and n not in replaced]
    miss = [p for p in part if p not in music]
    if miss: print(take, "missing stems", miss); continue
    def mixdown(names):
        buf = np.zeros((total, 2), np.float32)
        for n in names: place(buf, dec(stems[n]), OFF)
        return jr.pitch_shift(buf, semi) if semi else buf
    sp_stems = STEM_PART_OVERRIDE.get(take, part)
    stem_part = mixdown(sp_stems); band = mixdown([n for n in music if n not in part])
    lpart = LAYER_PART.get(take, []); pb_items = {}
    def stem_on_render(n):
        bb = np.zeros((total, 2), np.float32); place(bb, dec(stems[n]), OFF); return bb
    for n in ((mix.get("pb-other") or {}).get("stems") or []):
        if n in stems and n not in part: pb_items["stem:" + n] = stem_on_render(n)
    for g in jr.pb_group_names(mix):
        m_ = mix.get(g) or {}
        for ent in m_.get("layers", []):
            ent = ent if isinstance(ent, dict) else {"file": ent}
            if ent.get("derived"): continue
            lp = sorted(glob.glob(glob.escape(folder) + "/parts/" + ent["file"] + ".*"))[0]
            start = (OFF if ent.get("frame", "render") == "stem" else 0) + int(round(ent.get("offset_ms", 0)/1000*SR))
            gdb = ent.get("gain_db", (m_.get("gain_db") or {}).get(ent["file"], 0))
            lbuf = np.zeros((total, 2), np.float32); place(lbuf, dec(lp), start)
            ag, _ = jr.auto_gain_db(lbuf, jr.classify(ent["file"], (m_.get("roles") or {})))   # fx/back-vox auto-level, as render
            if ent["file"] in lpart: stem_part += lbuf*10**((ag + gdb)/20)
            else:
                band += lbuf*10**((ag + gdb)/20)
                if g == "pb-other": pb_items["layer:" + ent["file"]] = lbuf
    recon = band + stem_part if not lpart else None
    if recon is not None:
        gA = np.dot(mono(allw), mono(recon))/np.dot(mono(recon), mono(recon))
        rr = mono(allw) - gA*mono(recon); recon_res = 10*np.log10(np.sum(rr**2)/np.sum(mono(allw)**2))
    else: recon_res = float("nan")
    # ---- concert side
    ch = glob.glob(d + ("07 *.wav" if kind == "bass" else "08 *.wav"))[0]
    conc = concert_on_render(ch, a, b, total)
    # ---- grid: render click onsets as beats; bar labels from cues
    beats = jr.onsets(mono(rclick), 0.3, 0.1)
    beat = float(np.median(np.diff(beats)))
    c0 = next(c for c in mix["cues"] if isinstance(c.get("beat", 1), (int, float)))
    t1 = c0["abs_sec"] - ((c0["bar"]-1)*4 + (c0.get("beat", 1)-1))*beat
    edges = np.concatenate([beats, [beats[-1] + beat]])
    lo, hi = (35, 500) if kind == "bass" else (110, 3500)
    Cs, As = chroma_frames(stem_part, edges, lo, hi); Cc, Ac = chroma_frames(conc, edges, lo, hi)
    both = As & Ac; sim = np.sum(Cs*Cc, 1)
    # bar-level (4 beats) aggregation
    nb = len(sim)//4
    bar_sim = np.array([sim[i*4:(i+1)*4][both[i*4:(i+1)*4]].mean() if both[i*4:(i+1)*4].sum() >= 2 else np.nan for i in range(nb)])
    bar_c = np.array([Ac[i*4:(i+1)*4].sum() >= 2 for i in range(nb)]); bar_s = np.array([As[i*4:(i+1)*4].sum() >= 2 for i in range(nb)])
    lbl = lambda i: f"{mmss(beats[min(i*4, len(beats)-1)])} (такт {bar_of(beats[min(i*4, len(beats)-1)], t1, beat).split('.')[0]})"
    low = runs((bar_sim < 0.6) & ~np.isnan(bar_sim), 2)
    conc_only = runs(bar_c & ~bar_s, 2); stem_only = runs(bar_s & ~bar_c, 2)
    def bar_active(x):
        _, act_ = chroma_frames(x, edges, 40, 8000); return np.array([act_[i*4:(i+1)*4].sum() >= 2 for i in range(nb)])
    pb_act = {k_: bar_active(v_) for k_, v_ in pb_items.items()}
    conc_only_cov = [(lbl(s_), e_ - s_, [k_ for k_, a_ in pb_act.items() if a_[s_:e_].mean() > 0.5]) for s_, e_ in conc_only]
    # ---- timing vs click grid (16ths), librosa onsets; latency = median signed, looseness = spread around it
    import librosa, warnings; warnings.filterwarnings("ignore")
    g16 = np.sort(np.concatenate([beats + k*beat/4 for k in range(4)]))
    def grid_dev(x):
        on = librosa.onset.onset_detect(y=librosa.resample(mono(x), orig_sr=SR, target_sr=22050), sr=22050, units="time", hop_length=128)
        return on, np.array([t_ - g16[np.argmin(np.abs(g16 - t_))] for t_ in on])*1000
    def tstats(on, dv):
        if len(dv) < 20: return None
        med = float(np.median(dv)); spread = float(np.median(np.abs(dv - med)))
        tight = float(np.mean(np.abs(dv - med) < 15))*100
        loose = []
        for i in range(0, len(beats) - 16, 16):
            m_ = (on >= beats[i]) & (on < beats[i+16])
            if m_.sum() >= 6:
                mm = float(np.median(dv[m_])); sp = float(np.median(np.abs(dv[m_] - mm)))
                if abs(mm - med) > 20 or sp > 25: loose.append((mmss(beats[i]), round(mm - med), round(sp)))
        return {"latency_ms": round(med, 1), "spread_ms": round(spread, 1), "tight_pct": round(tight), "n": int(len(dv)), "loose_4bar": loose[:8]}
    ts = tstats(*grid_dev(stem_part)); tc = tstats(*grid_dev(conc))
    # ---- quality
    cm = mono(conc); span = (cm != 0)
    n100 = int(0.1*SR); w = [np.sqrt(np.mean(cm[i:i+n100]**2)) for i in range(OFF, total - n100, n100)]
    w = np.array(w); nf = 20*np.log10(np.percentile(w[w > 0], 5) + 1e-12) if (w > 0).any() else -120
    raw = dec(ch, 2, 48000); pk = 20*np.log10(np.abs(raw).max() + 1e-12); clip = int((np.abs(raw) > 0.999).sum())
    L_s = lufs(stem_part); L_c = lufs(conc); k = 10**((L_s - L_c)/20)
    shift_ms = 0.0
    if ts and tc and abs(tc["latency_ms"] - ts["latency_ms"]) > 5:
        shift_ms = round(ts["latency_ms"] - tc["latency_ms"], 1)      # move concert onto the stem's feel
    conc_m = np.zeros_like(conc); place(conc_m, conc*k, int(round(shift_ms/1000*SR)))
    rawm = mono(raw); wq = np.array([np.sqrt(np.mean(rawm[i:i+4800]**2)) for i in range(0, len(rawm) - 4800, 4800)])
    silence_db = float(20*np.log10(np.percentile(wq, 1) + 1e-12))
    cl = np.where(np.abs(raw).max(1) > 0.999)[0]
    clip_runs = int(sum(1 for r_ in np.split(cl, np.where(np.diff(cl) > 1)[0] + 1) if len(r_) >= 3)) if len(cl) else 0
    # ---- A/B
    A = band + stem_part; B = band + conc_m
    g = 0.89/max(np.abs(A).max(), np.abs(B).max(), 1e-9)
    od = f"{OUT}/{SLUG(take)}"; os.makedirs(od, exist_ok=True)
    write_mp3(od + "/ab-stem.mp3", A*g); write_mp3(od + "/ab-concert.mp3", B*g)
    gs = 0.89/max(np.abs(stem_part).max(), np.abs(conc_m).max(), 1e-9)
    write_mp3(od + "/solo-stem.mp3", stem_part*gs); write_mp3(od + "/solo-concert.mp3", conc_m*gs)
    r = {"take": take, "repo": al["repo"], "kind": kind, "stem_part": part, "pitch": semi,
         "map": {"a": a, "b": b, "clicks_matched": f"{nhit}/{nclk}", "p90_ms": round(p90, 1), "tempo_ratio": round(b, 5)},
         "recon_vs_all_db": round(recon_res, 1),
         "coverage": {"concert_bars": int(bar_c.sum()), "stem_bars": int(bar_s.sum()), "bars": int(nb)},
         "notes": {"mean_sim": round(float(np.nanmean(bar_sim)), 3), "low_runs": [(lbl(s), e - s) for s, e in low][:12],
                   "pct_bars_low": round(float(np.nanmean(bar_sim < 0.6))*100, 1)},
         "concert_only": conc_only_cov[:12], "stem_only": [(lbl(s), e - s) for s, e in stem_only][:12],
         "timing": {"stem": ts, "concert": tc},
         "quality": {"silence_dbfs": round(silence_db, 1), "peak_dbfs": round(pk, 1), "clip_runs": clip_runs},
         "concert_shift_ms_applied_in_ab": shift_ms,
         "lufs": {"stem": round(L_s, 1), "concert": round(L_c, 1), "gain_db_to_match": round(L_s - L_c, 1)},
         "files": od}
    results[take] = r
    json.dump(results, open(OUT + "/results.json", "w"), ensure_ascii=False, indent=1, default=float)
    q = r["quality"]
    print(f"\n=== {take} ({kind}: {'+'.join(part)}, pitch {semi}) map b={b:.5f} clicks {nhit}/{nclk} p90 {p90:.1f}ms | recon vs all {recon_res:.1f} dB")
    print(f"  coverage: concert {bar_c.sum()} / stem {bar_s.sum()} of {nb} bars; concert-only {r['concert_only'][:5]}; stem-only {r['stem_only'][:5]}")
    print(f"  notes: mean bar sim {r['notes']['mean_sim']} ({r['notes']['pct_bars_low']}% bars < 0.6); low runs {r['notes']['low_runs'][:6]}")
    print(f"  timing vs click: stem {ts and {k: ts[k] for k in ('latency_ms','spread_ms','tight_pct')}} | concert {tc and {k: tc[k] for k in ('latency_ms','spread_ms','tight_pct')}}; concert loose 4-bar {tc and tc['loose_4bar'][:5]}")
    print(f"  quality: silence {q['silence_dbfs']} dBFS, peak {q['peak_dbfs']}, clip runs {q['clip_runs']} | LUFS stem {L_s:.1f} concert {L_c:.1f} | A/B concert shift {shift_ms} ms")
