#!/usr/bin/env python3
"""Render a song's playback set for Stage Traxx straight from the stems — no Logic.

Per-song manifest mix.json (in the song folder) says which stems go where:

    {
      "pb-other": {"stems": ["05_Synth_Bass", "06_Synth_Lead"], "gain_db": {"06_Synth_Lead": -2}},
      "pb-bass":  null
    }

click and cues need no manifest: click = the JamZone Click stem, cues = cue_track.wav.
all = every music stem (preview mix). Outputs land in <song>/auto-render/ as WAV,
aligned by construction: t=0 = bar line, stem downbeat on a bar line, whole bars
(arp MIDI-clock rule, music/arpeggiator-sync.md). auto-render/timeline.json records
{bpm, bar_sec, offset_sec} — offset to add to stem-timeline times (cues.json /
JamZone structure.json) to hit the rendered audio.

User artifacts (stems, cue_track.wav, cues.json, logic-render/) are READ-ONLY.

Usage: jamzone_render.py "<song name or folder>" [--check]
       --check = analyze + verify, write nothing
"""
import os, sys, glob, json, subprocess
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

def fit_grid(click_mono):
    on = onsets(click_mono)
    k = np.round((on-on[0])/np.median(np.diff(on)))
    A = np.vstack([k, np.ones_like(k)]).T
    beat, phase = np.linalg.lstsq(A, on, rcond=None)[0]
    def dom_freq(t):
        s = click_mono[int(t*SR):int(t*SR)+int(0.08*SR)]
        S = np.abs(np.fft.rfft(s*np.hanning(len(s))))
        return np.fft.rfftfreq(len(s), 1/SR)[np.argmax(S)]
    freqs = np.array([dom_freq(t) for t in on[:4]])
    db0 = phase + int(np.argmax(freqs))*beat       # accent (~200Hz) = downbeat
    resid = np.abs(A@[beat, phase]-on)
    return beat, db0, float(resid.max()), len(on)

def first_sound(a, thr=1e-3):
    nz = np.where(np.abs(a).max(1) > thr)[0]
    return nz[0]/SR if len(nz) else None

def place(buf, audio, at_samp):
    s0 = max(0, at_samp); a0 = max(0, -at_samp)
    n = min(len(audio)-a0, len(buf)-s0)
    if n > 0: buf[s0:s0+n] += audio[a0:a0+n]

def aiff_write(path, x, num_beats):
    """AIFF + Apple-Loops 'basc' chunk -> MainStage Playback sees tempo/bars, no Logic needed."""
    import struct
    x = np.clip(x, -1, 1)
    pcm = (x*32767).astype(">i2").tobytes()
    nfr = len(x)
    sr80 = b"\x40\x0e\xac\x44\x00\x00\x00\x00\x00\x00"        # 44100 as 80-bit extended
    comm = struct.pack(">hLh", 2, nfr, 16) + sr80
    ssnd = struct.pack(">LL", 0, 0) + pcm
    basc = struct.pack(">LLHHHH", 1, num_beats, 0, 3, 4, 4) + b"\x00"*68
    chunks = b""
    for cid, body in ((b"COMM", comm), (b"basc", basc), (b"SSND", ssnd)):
        chunks += cid + struct.pack(">L", len(body)) + body + (b"\x00" if len(body) % 2 else b"")
    with open(path, "wb") as f:
        f.write(b"FORM" + struct.pack(">L", 4+len(chunks)) + b"AIFF" + chunks)

def main():
    folder = find_folder(sys.argv[1])
    mix_p = os.path.join(folder, "mix.json")
    if not os.path.exists(mix_p): sys.exit(f"no mix.json in {folder} — define pb-other/pb-bass first")
    mix = json.load(open(mix_p))

    stems = {os.path.basename(p)[:-4]: p for p in sorted(glob.glob(os.path.join(folder, "[0-9][0-9]_*.m4a")))}
    click_name = next((n for n in stems if "click" in n.lower()), None) or sys.exit("no Click stem")
    cue_p = os.path.join(folder, "cue_track.wav")
    if not os.path.exists(cue_p): sys.exit("no cue_track.wav")

    for grp in ("pb-other", "pb-bass"):
        for nm in ((mix.get(grp) or {}).get("stems", [])):
            if nm not in stems: sys.exit(f"mix.json: unknown stem '{nm}' in {grp}")

    click_st = decode(stems[click_name])
    beat, db0, resid, n_on = fit_grid(click_st.mean(1))
    bar = 4*beat
    print(f"grid: beat={beat:.6f}s bpm={60/beat:.4f} bar={bar:.6f}s "
          f"downbeat={db0:.4f}s ({n_on} clicks, max resid {resid*1000:.1f}ms)")

    audio = {n: decode(p) for n, p in stems.items()}
    cue_st = decode(cue_p)

    # t=0 = bar line at/before all content, stem downbeat lands on a bar line
    OFF = -db0
    earliest = min(t for a in [*audio.values(), cue_st] if (t := first_sound(a)) is not None)
    if earliest + OFF < 0:
        OFF += np.ceil(-(earliest+OFF)/bar)*bar
    off_samp = round(OFF*SR)
    end = max(len(a) for a in [*audio.values(), cue_st]) + off_samp
    total = int(np.ceil(end/(bar*SR))*bar*SR)
    print(f"timeline = stem {OFF:+.5f}s, length {total/SR:.3f}s = {total/SR/bar:.0f} bars")

    def mixdown(names, gains):
        buf = np.zeros((total, 2), np.float32)
        for n in names:
            g = 10**(gains.get(n, 0)/20)
            place(buf, audio[n]*g, off_samp)
        return buf

    music = [n for n in stems if n != click_name]
    out = {"click": mixdown([click_name], {}), "all": mixdown(music, {})}
    cues_buf = np.zeros((total, 2), np.float32); place(cues_buf, cue_st, off_samp)
    out["cues"] = cues_buf
    for grp in ("pb-other", "pb-bass"):
        m = mix.get(grp)
        if m: out[grp] = mixdown(m["stems"], m.get("gain_db", {}))

    for n, buf in out.items():                     # headroom: only ever attenuate
        pk = float(np.abs(buf).max())
        if pk > 0.99:
            buf *= 0.95/pk
            print(f"  {n}: peak {20*np.log10(pk):+.1f}dBFS -> normalized to -0.4dBFS")

    pre = 1000
    v = onsets(np.concatenate([np.zeros(pre, np.float32), out["click"].mean(1)])) - pre/SR
    err = [(t - round(t/beat)*beat)*1000 for t in v[:8]]
    bar_err = (v[0] - round(v[0]/bar)*bar)*1000
    print(f"verify click: first onset {v[0]*1000:.1f}ms (bar-line err {bar_err:+.1f}ms), "
          f"beat err {[f'{e:+.1f}' for e in err]} ms")
    if abs(bar_err) > 10 or max(abs(e) for e in err) > 3:
        sys.exit("verification failed — nothing written")
    if "--check" in sys.argv:
        print("✓ --check: all green, nothing written"); return

    adir = os.path.join(folder, "auto-render")
    os.makedirs(adir, exist_ok=True)
    num_beats = round(total/SR/beat)
    for n, buf in out.items():
        aiff_write(os.path.join(adir, n + ".aif"), buf, num_beats)  # ST + MainStage (Apple-Loops tempo tag)
    json.dump({"offset_sec": round(OFF, 6), "bar_sec": round(bar, 6), "bpm": round(60/beat, 4),
               "note": "add offset_sec to stem-timeline times (cues.json/structure.json); "
                       "t=0 = bar line; downbeat of stem grid on a bar line"},
              open(os.path.join(adir, "timeline.json"), "w"), indent=1)
    print(f"✓ auto-render/: {', '.join(n+'.aif' for n in out)} + timeline.json")

if __name__ == "__main__":
    main()
