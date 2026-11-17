#!/usr/bin/env python3
"""Cut Roma's concert part (28.10 multitrack) into a render-frame layer: parts/<name>.wav.

usage: make_layer.py "<take>" <layer-name> [--declip] [--shift-ms N]
  take   = key of tools/concert-2810/concert_align.json (e.g. "Ту-лу-ла", "Беги от меня (бис)")
  shift  = default: the shift used in the A/B page (analysis/concert-2810/results.json) — the
           concert part moved onto the stem's feel (Roma's laptop latency removed on keys)
  declip = ffmpeg adeclip on the raw 48 kHz channel (mixer input overloaded), then alimiter at -1 dBFS
Channel: bass -> 07 Bass Guitar, keys -> 08 "Guitar LR" (labels 08/09 are swapped at this gig).
Mapping concert_t = a + b*render_t from click onsets; |b-1| > 0.002 = real tempo difference
(MainStage stretched the playback) -> rubberband time-stretch keeping pitch, else resample.
The file is NOT gain-matched (gain lives in mix.json); length = render length, t=0 = render t=0."""
import glob, json, os, subprocess, sys, tempfile
import numpy as np
sys.path.insert(0, "/Users/alex/projects/cherry-daddies/tools/jamzone")
import jamzone_render as jr

SR = 44100
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = "/Users/alex/projects/cherry-daddies/music/songs"
take, name = sys.argv[1], sys.argv[2]
AL = json.load(open(HERE + "/concert_align.json"))[take]
RES = json.load(open("/Users/alex/projects/cherry-daddies/analysis/concert-2810/results.json"))[take]
shift_ms = float(sys.argv[sys.argv.index("--shift-ms") + 1]) if "--shift-ms" in sys.argv else RES["concert_shift_ms_applied_in_ab"]
declip = "--declip" in sys.argv
folder = f"{REPO}/{AL['repo']}"; d = AL["dir"]
ch = glob.glob(d + ("07 *.wav" if AL["part"] == "bass" else "08 *.wav"))[0]

def dec(p, ch=2, sr=SR):
    raw = subprocess.run(["ffmpeg", "-v", "quiet", "-i", p, "-ac", str(ch), "-ar", str(sr), "-f", "f32le", "-"], capture_output=True).stdout
    a = np.frombuffer(raw, np.float32).copy(); return a.reshape(-1, ch) if ch > 1 else a
def clip_runs(x):
    cl = np.where(np.abs(x).max(1) > 0.999)[0] if x.ndim > 1 else np.where(np.abs(x) > 0.999)[0]
    return int(sum(1 for r in np.split(cl, np.where(np.diff(cl) > 1)[0] + 1) if len(r) >= 3)) if len(cl) else 0

COARSE = AL["lag_s"]
rclick = dec(folder + "/auto-render/click.wav", 1); total = len(dec(folder + "/auto-render/all.wav", 1))
co = jr.onsets(dec(glob.glob(d + "13 *.wav")[0], 1), 0.3, 0.1); ro = jr.onsets(rclick, 0.3, 0.1)
b0 = np.median(np.diff(co))/np.median(np.diff(ro)); best = None
for i in range(min(40, len(co))):
    for j in range(min(8, len(ro))):
        a0 = co[i] - b0*ro[j]; pred = a0 + b0*ro; k = np.clip(np.searchsorted(co, pred), 1, len(co)-1)
        hit = (np.minimum(np.abs(co[k]-pred), np.abs(co[k-1]-pred)) < 0.03).sum()
        if abs(b0 - 1) < 0.002 and abs(a0 - COARSE) > 0.25: continue   # periodic click: stay on the coarse (cues/PB) lag, not a bar off
        if best is None or hit > best[0]: best = (hit, a0)
pred = best[1] + b0*ro; k = np.clip(np.searchsorted(co, pred), 1, len(co)-1)
pick = np.where(np.abs(co[k]-pred) < np.abs(co[k-1]-pred), co[k], co[k-1]); m = np.abs(pick - pred) < 0.03
(a, b), *_ = np.linalg.lstsq(np.stack([np.ones(m.sum()), ro[m]], 1), pick[m], rcond=None)
print(f"{take}: concert = {a:+.4f} + {b:.6f}*render ({m.sum()}/{len(ro)} clicks), shift {shift_ms:+.1f} ms, declip {declip}")

with tempfile.TemporaryDirectory() as td:
    src = ch
    raw48 = dec(ch, 2, 48000); print(f"  raw: peak {20*np.log10(np.abs(raw48).max()+1e-12):.1f} dBFS, clip runs {clip_runs(raw48)}")
    if declip:
        src = os.path.join(td, "dc.wav")
        subprocess.run(["ffmpeg", "-v", "quiet", "-y", "-i", ch, "-af", "adeclip=window=55:overlap=75:arorder=8:threshold=10:hsize=1000",
                        "-c:a", "pcm_f32le", src])
        x = dec(src, 2, 48000); print(f"  declipped: peak {20*np.log10(np.abs(x).max()+1e-12):+.1f} dBFS, runs >= 0 dBFS now {clip_runs(x)}")
    if abs(b - 1) > 0.002:
        st = os.path.join(td, "st.wav")
        subprocess.run(["rubberband", "-3", "-T", f"{b:.8f}", src, st], capture_output=True); x = dec(st)
        print(f"  tempo ratio {b:.5f}: rubberband time-stretch (pitch kept)")
    else:
        raw = subprocess.run(["ffmpeg", "-v", "quiet", "-i", src, "-af", f"asetrate={48000*b:.4f},aresample={SR}", "-ac", "2", "-f", "f32le", "-"],
                             capture_output=True).stdout
        x = np.frombuffer(raw, np.float32).copy().reshape(-1, 2)
    buf = np.zeros((total, 2), np.float32); start = -int(round(a/b*SR)) + int(round(shift_ms/1000*SR))
    s0 = max(0, start); a0 = max(0, -start); n = min(len(x) - a0, total - s0); buf[s0:s0+n] = x[a0:a0+n]
    out = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else f"{folder}/parts/{name}.wav"
    os.makedirs(os.path.dirname(out), exist_ok=True)
    lim_db = float(sys.argv[sys.argv.index("--limit-db") + 1]) if "--limit-db" in sys.argv else -1.0   # peak ceiling IN THE FILE
    lim = 10**(lim_db/20)            # (with gain_db G in mix.json pass --limit-db -1-G so the group never clips)
    af = ["-af", f"alimiter=limit={lim:.4f}:attack=3:release=60:level=0"] if declip or np.abs(buf).max() > min(0.99, lim) else []
    if af:
        over = int((np.abs(buf).max(1) > lim).sum()); print(f"  limiter {lim_db:+.1f} dBFS: {over} samples above ({over/SR*1000:.0f} ms total), peak {20*np.log10(np.abs(buf).max()):+.1f} dBFS")
    subprocess.run(["ffmpeg", "-v", "quiet", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-"] + af + ["-c:a", "pcm_s24le", out],
                   input=buf.astype(np.float32).tobytes())
y = dec(out); print(f"  -> {out}: {len(y)/SR:.3f}s (render {total/SR:.3f}s), peak {20*np.log10(np.abs(y).max()+1e-12):.1f} dBFS")
