#!/usr/bin/env python3
"""Per-bar stem activity map for cue authoring.

Decodes every stem in a song folder, fits the bar grid from the click
(JZ 01_Click.m4a, or a Moises metronome stem), and prints a per-bar
active/idle matrix + enter/stop transitions for each stem. This is the
"who enters / who stops" analysis behind hand-authored mix.json cues.

Usage:
  python3 stem_activity.py "<song folder or query>" [--bpm N] [--from BAR] [--to BAR]

Grid: JZ songs -> 01_Click.m4a least-squares fit (beat, downbeat).
      Moises songs -> metronome.mp3 onsets (fallback: --bpm + first onset).
"""
import sys, os, subprocess, glob, json, re
import numpy as np

SR = 44100
SONGS = "/Users/alex/projects/cherry-daddies/music/songs"

def decode(path):
    p = subprocess.run(["ffmpeg","-v","error","-i",path,"-ac","1","-ar",str(SR),
                        "-f","f32le","-"], capture_output=True)
    return np.frombuffer(p.stdout, dtype=np.float32)

def find_folder(q):
    if os.path.isdir(q): return q
    cand = [d for d in glob.glob(os.path.join(SONGS,"*")) if os.path.isdir(d)
            and q.lower() in os.path.basename(d).lower()]
    if not cand: sys.exit(f"no folder matches {q!r}")
    return cand[0]

def fit_grid_click(click):
    """lstsq fit: returns beat (samples), downbeat sample (db0)."""
    env = np.abs(click)
    # onset detect: local peaks above threshold spaced >0.15s
    win = int(0.02*SR)
    e = np.convolve(env, np.ones(win)/win, mode='same')
    thr = 0.15*e.max()
    on=[]; i=0; mind=int(0.18*SR)
    while i < len(e):
        if e[i] > thr:
            j = i+np.argmax(e[i:i+mind]) if i+mind<len(e) else i+np.argmax(e[i:])
            on.append(j); i = j+mind
        else: i += 1
    on = np.array(on, float)
    k = np.arange(len(on))
    A = np.vstack([k, np.ones_like(k)]).T
    beat, phase = np.linalg.lstsq(A, on, rcond=None)[0]
    return beat, phase, on

def main():
    args = sys.argv[1:]
    q = args[0]
    bpm = None; b_from=None; b_to=None
    for i,a in enumerate(args):
        if a=="--bpm": bpm=float(args[i+1])
        if a=="--from": b_from=int(args[i+1])
        if a=="--to": b_to=int(args[i+1])
    folder = find_folder(q)
    name = os.path.basename(folder)
    print(f"# {name}")

    click = None
    cp = os.path.join(folder,"01_Click.m4a")
    met = os.path.join(folder,"metronome.mp3")
    metw = os.path.join(folder,"metronome.wav")
    if os.path.exists(cp):
        click = decode(cp); beat,db0,on = fit_grid_click(click)
        print(f"# grid: JZ click  beat={beat/SR*1000:.1f}ms  bpm={60/(beat/SR):.2f}  db0={db0/SR:.3f}s  onsets={len(on)}")
    else:
        msrc = met if os.path.exists(met) else (metw if os.path.exists(metw) else None)
        if msrc:
            click = decode(msrc); beat,db0,on = fit_grid_click(click)
            print(f"# grid: metronome  beat={beat/SR*1000:.1f}ms  bpm={60/(beat/SR):.2f}  db0={db0/SR:.3f}s")
        elif bpm:
            beat = 60.0/bpm*SR; db0=0.0
            print(f"# grid: --bpm {bpm}  db0=0")
        else:
            sys.exit("no click/metronome and no --bpm")

    bar_samp = beat*4
    # stems = audio files excluding click/metronome/cue
    stems=[]
    for f in sorted(glob.glob(os.path.join(folder,"*.m4a"))+glob.glob(os.path.join(folder,"*.mp3"))+glob.glob(os.path.join(folder,"*.wav"))):
        b=os.path.basename(f).lower()
        if "click" in b or "metronome" in b or "cue" in b or "_click" in b: continue
        if re.match(r'^01_click', b): continue
        stems.append(f)
    # short labels
    def lab(f):
        b=os.path.splitext(os.path.basename(f))[0]
        b=re.sub(r'^\d+_','',b)
        return b[:14]

    # decode all, compute per-bar RMS
    total_dur = 0
    data={}
    for f in stems:
        x=decode(f); data[f]=x; total_dur=max(total_dur,len(x))
    nbars = int((total_dur-db0)/bar_samp)+1
    lo = (b_from or 1); hi = (b_to or nbars)

    # per-stem per-bar rms, normalized to that stem's own peak bar
    mat={}
    for f in stems:
        x=data[f]; rms=[]
        for bar in range(1,nbars+1):
            s=int(db0+(bar-1)*bar_samp); e=int(s+bar_samp)
            seg=x[max(0,s):e]
            rms.append(float(np.sqrt(np.mean(seg**2))) if len(seg) else 0.0)
        rms=np.array(rms); pk=rms.max() or 1
        mat[f]=rms/pk

    # print matrix
    hdr="bar |"+"".join(f"{lab(f)[:7]:>8}" for f in stems)
    print(hdr); print("-"*len(hdr))
    ACT=0.10  # active threshold (fraction of stem peak)
    for bar in range(lo,hi+1):
        cells=""
        for f in stems:
            v=mat[f][bar-1]
            c = "#" if v>0.5 else ("+" if v>ACT else (".") )
            cells+=f"{c:>8}"
        print(f"{bar:>3} |{cells}")
    # transitions
    print("\n# ENTER / STOP (bar where stem crosses active threshold):")
    for f in stems:
        a=mat[f]>ACT
        ent=[i+1 for i in range(lo-1,hi) if a[i] and (i==0 or not a[i-1])]
        stp=[i+1 for i in range(lo-1,hi) if not a[i] and i>0 and a[i-1]]
        print(f"  {lab(f):14} enter@{ent}  stop@{stp}")

if __name__=="__main__":
    main()
