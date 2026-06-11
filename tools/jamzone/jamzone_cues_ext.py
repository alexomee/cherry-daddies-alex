#!/usr/bin/env python3
"""Build a JamZone-style cue track for an EXTERNAL (non-JamZone) song from a
hand-authored blueprint. Reuses the lifted JamZone click samples (jamzone_click.py
`extract`) for the click, and macOS `say` for the spoken name + count clips.

Unlike jamzone_cues.py (which derives cues from JamZone structure.json), here the
cues are specified explicitly in a blueprint JSON — the editable source of truth.

  jamzone_cues_ext.py <blueprint.json> [--audition] [--final]

Blueprint:
{
  "song": "<full mix path>",            # for audition + final left channel
  "out_dir": "<output folder>",
  "title": "Artist - Title",
  "grid": {"phase":0.195,"period":0.47842,"down_res":null},  # beat grid (s); down_res=accent residue or null=auto
  "lead_bars": 2,                       # bars of count-in prepended before the song
  "retempo": [{"from":105.0,"to":110.97,"bpm":91}],  # re-grid a span (time_ref units) at a fixed bpm
                                        #   for tempo changes Moises mis-timed (e.g. voice-grooved breakdown)
  "voices": {"ru":"Milena","en":"Samantha"},
  "levels": {"song":0.85,"click":0.6,"cues":1.0},
  "cues": [
    {"id":"C01","name":"про красивую жизнь","lang":"ru","t":"start","count":true},
    {"id":"C02","name":"vocal in","lang":"en","t":16.708,"count":true},
    {"id":"C03","name":"stop","lang":"en","t":39.240,"count":true},
    ...
  ]
}
t = seconds in the SONG timeline (snapped to the grid), or "start" (first downbeat).
"""
import os, sys, json, subprocess, wave, hashlib, glob, re
import numpy as np

SR = 44100
HERE = os.path.expanduser("~/projects/cherry-daddies/music/songs")
DB = os.path.join(HERE, "jz_downbeat.wav")
BT = os.path.join(HERE, "jz_beat.wav")
DEFAULT_COUNT_FILES = {"3":"~/3.aiff","2":"~/2.aiff","1":"~/1.aiff"}

def wav_read(path):
    w = wave.open(path); x = np.frombuffer(w.readframes(w.getnframes()), "<i2").astype(np.float32)/32767; return x
def wav_write(path, L, R=None):
    L = np.clip(L,-1,1)
    if R is None:
        w=wave.open(path,"w"); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((L*32767).astype("<i2").tobytes()); w.close()
    else:
        R=np.clip(R,-1,1); n=max(len(L),len(R))
        L=np.pad(L,(0,n-len(L))); R=np.pad(R,(0,n-len(R)))
        inter=np.empty(n*2,np.float32); inter[0::2]=L; inter[1::2]=R
        w=wave.open(path,"w"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((inter*32767).astype("<i2").tobytes()); w.close()
def decode_mono(path):
    raw=subprocess.run(["ffmpeg","-v","quiet","-i",path,"-ac","1","-ar",str(SR),"-f","f32le","-"],
                       capture_output=True).stdout
    return np.frombuffer(raw,np.float32).copy()

_TTS_CACHE={}
def tts(text, voice, rate=150):
    """voice=None -> default system voice. rate in wpm (say -r)."""
    tag=(voice or "default")+f"|{rate}|"+text
    key=hashlib.md5(tag.encode()).hexdigest()
    if key in _TTS_CACHE: return _TTS_CACHE[key]
    aiff=f"/tmp/_jztts_{key}.aiff"
    cmd=["say","-r",str(rate)]
    if voice: cmd+=["-v",voice]
    cmd+=["-o",aiff,text]
    subprocess.run(cmd,check=True)
    x=decode_mono(aiff)
    p=np.max(np.abs(x)) or 1.0; x=x/p*0.9
    _TTS_CACHE[key]=x; return x

_CLIP_CACHE={}
def load_clip(path):
    path=os.path.expanduser(path)
    if path in _CLIP_CACHE: return _CLIP_CACHE[path]
    x=decode_mono(path); p=np.max(np.abs(x)) or 1.0; x=x/p*0.9
    _CLIP_CACHE[path]=x; return x

_AUD={}
def aud(path):
    path=os.path.expanduser(path)
    if path not in _AUD: _AUD[path]=decode_mono(path)
    return _AUD[path]

def metro_beats(path):
    """detect the click/metronome onset times (s) -> the true beat grid (tracks tempo drift)."""
    a=aud(path); win=int(0.005*SR); dt=win/SR
    env=np.array([np.sqrt((a[i:i+win]**2).mean()) for i in range(0,len(a),win)])
    thr=0.25*(env.max() or 1.0)
    return np.array([k*dt for k in range(1,len(env)) if env[k]>thr and env[k-1]<=thr])

def metro_downbeat_residue(metronome_path, BEATS):
    """if the click stem has an accented beat (JamZone click = loud downbeat), return its residue
    mod 4; else None. Lets JamZone tracks take the downbeat straight from the click."""
    a=aud(metronome_path)
    amp=np.array([np.max(np.abs(a[int(t*SR):int(t*SR)+int(0.05*SR)])) for t in BEATS])
    if amp.max()<=0 or len(amp)<8: return None
    means=[amp[r::4].mean() for r in range(4)]
    top=int(np.argmax(means)); others=np.mean([means[r] for r in range(4) if r!=top])
    return top if (others>0 and means[top]>1.4*others) else None

def beat_rms(a, beat_at, k):
    s=int(beat_at(k)*SR); e=int(beat_at(k+1)*SR); seg=a[s:e]
    return float(np.sqrt((seg**2).mean())) if 0<=s and len(seg) else 0.0

def first_drum_onset(drums_path):
    """time (s) of the first audible drum hit (rising edge over 15% of peak energy)."""
    a=aud(drums_path)
    win=int(0.01*SR); env=np.array([np.sqrt((a[i:i+win]**2).mean()) for i in range(0,len(a),win)])
    dt=win/SR; pk=env.max() or 1.0
    for k in range(1,len(env)):
        if env[k]>0.15*pk and env[k-1]<=0.15*pk: return k*dt
    return 0.0

def first_bass_onset(bass_path, head=15.0):
    """first audible bass onset, thresholded against the INTRO-window peak. A global-peak threshold
    (first_drum_onset) misses quiet intro bass when later choruses are far louder."""
    a=aud(bass_path); win=int(0.01*SR)
    env=np.array([np.sqrt((a[i:i+win]**2).mean()) for i in range(0,len(a),win)])
    dt=win/SR; h=max(1,int(head/dt)); pk=(env[:h].max() or env.max() or 1.0)
    for k in range(1,len(env)):
        if env[k]>0.15*pk and env[k-1]<=0.15*pk: return k*dt
    return 0.0

def refine_stop(a, beat_at, kc, span=3):
    """beat with the biggest relative energy drop from the previous beat, near kc -> the break."""
    best=kc; bestr=2.0
    for k in range(kc-span, kc+span+1):
        prev=beat_rms(a,beat_at,k-1); cur=beat_rms(a,beat_at,k)
        if prev<=1e-6: continue
        r=cur/prev
        if r<bestr: bestr=r; best=k
    return best

def refine_drum_end(a, beat_at, kc, span=5):
    """last beat near kc that is a strong drum hit followed by a sustained drop -> the final hit."""
    peak=max(beat_rms(a,beat_at,k) for k in range(kc-span,kc+span+1)) or 1.0
    last=kc
    for k in range(kc-span, kc+span+1):
        cur=beat_rms(a,beat_at,k)
        after=np.mean([beat_rms(a,beat_at,k+j) for j in (1,2,3)])
        if cur>0.3*peak and after<0.45*cur: last=k
    return last

def refine_bass_only(stems_dir, beat_at, nbeats):
    """start beat of the final sustained 'bass only' region: non-bass stems drop to ~silence while
    the bass keeps playing. Scans from the end back to the region's first beat."""
    bass=None; rest=[]
    for f in sorted(glob.glob(os.path.expanduser(stems_dir)+"/*")):
        n=os.path.basename(f).lower()
        if not f.lower().endswith((".mp3",".m4a",".wav")): continue
        if "metronome" in n or "click" in n: continue
        (rest.append(aud(f)) if "bass" not in n else None)
        if "bass" in n: bass=aud(f)
    if bass is None: return nbeats-1
    def is_bo(k):
        b=beat_rms(bass,beat_at,k); r=max((beat_rms(o,beat_at,k) for o in rest), default=0)
        return b>0.03 and r<0.06 and r<0.6*b
    k=nbeats-1
    while k>2 and not is_bo(k): k-=1            # last bass-only beat
    while k>2 and is_bo(k-1): k-=1             # walk back to the region's first beat
    return k

def refine_vocal_in(a, beat_at, kc, before=4, after=3, frac=0.35):
    """first beat in [kc-before, kc+after] with substantial sustained vocal energy (>frac of the
    window's loudest beat) -> the real entry, ignoring faint pickups/breaths before it."""
    ks=list(range(kc-before, kc+after+1))
    rms={k:beat_rms(a,beat_at,k) for k in ks}
    mx=max(rms.values()) or 1.0
    for k in ks:
        if rms[k] > frac*mx: return k
    return kc

def odelay(x):
    """time of the first 0.02s-window whose RMS exceeds 0.4*peak (the spoken vowel)."""
    win=int(0.02*SR);
    if len(x)<win: return 0.0
    env=np.array([np.sqrt((x[i:i+win]**2).mean()) for i in range(0,len(x)-win,win//2)])
    if not len(env): return 0.0
    thr=0.4*env.max()
    k=np.argmax(env>thr)
    return k*(win//2)/SR

def place(bed, clip, t, gain=1.0):
    s=int(t*SR)
    if s<0: clip=clip[-s:]; s=0
    if s>=len(bed): return
    n=min(len(clip), len(bed)-s)
    bed[s:s+n]+=clip[:n]*gain

def main():
    if len(sys.argv)<2: sys.exit(__doc__)
    bp=json.load(open(sys.argv[1]))
    audition="--audition" in sys.argv
    final="--final" in sys.argv
    g=bp.get("grid",{})
    V=bp.get("voices",{"ru":"Milena","en":None})   # None -> default system voice
    rate=bp.get("rate",150)
    count_files=bp.get("count_files",DEFAULT_COUNT_FILES)
    L=bp.get("levels",{}); SONGL=L.get("song",0.85); CLICKL=L.get("click",0.6); CUEL=L.get("cues",1.0)
    out=os.path.expanduser(bp["out_dir"]); os.makedirs(out,exist_ok=True)
    db=wav_read(DB); bt=wav_read(BT)

    song=decode_mono(os.path.expanduser(bp["song"]))
    song_dur=len(song)/SR

    # ---- beat grid = actual metronome onsets (song timeline; tracks tempo drift, no period math) ----
    BEATS=metro_beats(bp["metronome"]); nbeats=len(BEATS)
    period=float(np.median(np.diff(BEATS))); beat=period
    def sbeat(k):                                   # song-timeline beat time (extrapolate out of range)
        if 0<=k<nbeats: return float(BEATS[k])
        if k<0:         return float(BEATS[0]) + k*period
        return float(BEATS[-1]) + (k-nbeats+1)*period
    def snap_k(t):                                  # nearest beat index to a song-time
        if t<=BEATS[0]:  return int(round((t-BEATS[0])/period))
        if t>=BEATS[-1]: return nbeats-1+int(round((t-BEATS[-1])/period))
        return int(np.argmin(np.abs(BEATS-t)))

    lead=bp.get("lead_bars",2)*4*period
    cut=float(bp.get("cut_before",0.0))             # front trim (output time) applied to all exports
    def beat_time(k): return lead + sbeat(k)        # output timeline (song shifted right by `lead`)
    total=lead+song_dur+2.0; N=int(total*SR)
    # timeline conversion. logic-time = what you read off the exported aligned tracks in Logic
    # ( = song-time + lead - cut ). Set "time_ref":"logic" to give cue times straight from Logic.
    time_ref=bp.get("time_ref","song")
    def to_song(t):  return (t + cut - lead) if time_ref=="logic" else t
    def to_logic(song_t): return song_t + lead - cut

    # ---- optional tempo edits: re-grid a [from,to] span at a fixed bpm ----
    # Moises can mis-time a tempo change when there's nothing for it to track (e.g. a voice-grooved
    # breakdown with the drums dropped out). retempo replaces the metronome onsets in that span.
    # from/to are in the blueprint's time_ref; ends snap to real onsets so the new beats join cleanly.
    # NOTE: a span whose beat count isn't a multiple of 4 shifts the %4 downbeat-accent phase after it.
    for r in bp.get("retempo", []):
        a=to_song(float(r["from"])); b=to_song(float(r["to"]))
        a=float(BEATS[int(np.argmin(np.abs(BEATS-a)))])      # snap to nearest onset (clean left join)
        b=float(BEATS[int(np.argmin(np.abs(BEATS-b)))])      # nearest onset (kept as first beat after)
        pp=60.0/float(r["bpm"]); nfill=max(1,int(round((b-a)/pp))); pp=(b-a)/nfill   # even, exact join
        lo=[t for t in BEATS if t<a-1e-6]; hi=[t for t in BEATS if t>=b-1e-6]
        BEATS=np.array(sorted(lo+[a+i*pp for i in range(nfill)]+hi)); nbeats=len(BEATS)
        print(f"retempo: {r['bpm']}bpm over song {a:.3f}-{b:.3f}s -> {nfill} beats (was ~{int(round((b-a)/period))})")

    # downbeat residue: explicit, else anchored to the FIRST DRUM BEAT (bar 1), else vote from cues
    down_res=g.get("down_res")
    if down_res is None:
        down_res=metro_downbeat_residue(bp["metronome"], BEATS)   # accented click (JamZone) tells the downbeat
    if down_res is None and bp.get("drums"):
        down_res=snap_k(first_drum_onset(bp["drums"]))%4     # else the first drum hit is a downbeat
    if down_res is None:
        votes={}
        for c in bp["cues"]:
            if isinstance(c["t"],(int,float)):
                r=snap_k(to_song(float(c["t"])))%4; votes[r]=votes.get(r,0)+1
        down_res=max(votes,key=votes.get) if votes else 1
    first_db_k=next(k for k in range(0,4) if k%4==down_res)

    # ---- click bed (JZ hits on the real onsets; lead-in + extrapolated tail past the metronome) ----
    # the metronome stem can stop before the song ends; extrapolate so the click (and the end
    # count-in) covers the whole song.
    click=np.zeros(N,np.float32)
    kmin=int(-(lead)/period)-1
    kmax=int((song_dur-float(BEATS[0]))/period)+3
    for k in range(kmin, kmax+1):
        t=beat_time(k)
        if t<0 or t>=total: continue
        if k%4==down_res: place(click, db, t, 1.0)
        else:             place(click, bt, t, 0.5)

    # ---- cue bed ----
    cue=np.zeros(N,np.float32)
    printed=[]
    for c in bp["cues"]:
        lang=c.get("lang","en")
        # landing beat (output timeline)
        anchor=c.get("anchor","grid")
        center=0.0 if c["t"] in ("start","first_drum") else to_song(float(c["t"]))
        kc=snap_k(center)
        if c["t"]=="first_drum" or anchor=="first_drum":
            kl=snap_k(first_drum_onset(bp["drums"]))
        elif anchor=="stop":      kl=refine_stop(aud(bp["song"]),sbeat,kc)
        elif anchor=="drum_end":  kl=refine_drum_end(aud(bp["drums"]),sbeat,kc)
        elif anchor=="vocal_in":  kl=refine_vocal_in(aud(bp["vocals"]),sbeat,kc)
        elif anchor=="bass_only": kl=refine_bass_only(bp["stems_dir"],sbeat,nbeats)
        elif anchor=="bass_in":   kl=snap_k(first_bass_onset(bp["bass"]))   # first bass onset (intro-local threshold)
        elif c["t"]=="start":     kl=first_db_k
        else:                     kl=kc
        name=(c.get("name") or "").strip()
        # --- "ready go" style (meter:true): each word of the phrase lands on its own beat.
        #     Snap the landing to the nearest DOWNBEAT so the W words fill beats 1..W of the
        #     bar and the band event lands on the next downbeat (the beat after the last word). ---
        if c.get("meter"):
            kl=first_db_k+int(round((kl-first_db_k)/4.0))*4      # nearest downbeat
            words=name.split(); W=len(words) or 1
            for i,w in enumerate(words):
                bt=beat_time(kl-W+i)                             # word i on beat (kl-W+i)
                wc=tts(w, V.get(lang), rate)
                place(cue, wc, bt-odelay(wc), CUEL)
            tland=beat_time(kl)
            printed.append((c["id"], name+f"  [meter x{W}]", tland-lead, kl%4==down_res, kc, kl, anchor))
            continue
        tland=beat_time(kl)
        # counts on the 3 beats before the landing
        if c.get("count",True):
            for n in (3,2,1):
                ct=beat_time(kl-n)
                clip=load_clip(count_files[str(n)])
                place(cue, clip, ct-odelay(clip), CUEL)
            count_start=beat_time(kl-3)
        else:
            count_start=tland
        # name finishes just before the first count (skip for count-only cues with no name)
        if name:
            nm=tts(name, V.get(lang), rate); nd=len(nm)/SR
            gap=min(max(beat,0.30),0.90)
            ns=count_start - gap - nd
            place(cue, nm, ns, CUEL)
        printed.append((c["id"], name or "(3 2 1 only)", tland-lead, kl%4==down_res, kc, kl, anchor))

    # ---- report ----
    def mmss(s): m=int(s//60); return f"{m:d}:{s-60*m:06.3f}"
    print(f"grid: {nbeats} metro onsets, beat0 {BEATS[0]:.3f}s  median period {period:.5f}s ({60/period:.1f} bpm)  down_res {down_res}  lead {lead:.2f}s  cut {cut:.2f}s")
    print(f"cues (song-time | Logic-time [aligned, song+{lead:.2f}-{cut:.2f}]; *=on downbeat):")
    for cid,nm,t,isdb,kc,kl,anchor in printed:
        shift=f"  [{anchor}: beat {kc}->{kl}]" if (anchor!="grid" and kc!=kl) else ""
        print(f"  {cid}  {mmss(t):>9} | {mmss(to_logic(t)):>9}  {'*' if isdb else ' '}  {nm}{shift}")

    # ---- renders ----
    # cut_before: trim this many seconds off the FRONT of every output (uniformly, so tracks stay
    # in sync) to remove dead silence before the intro cue.
    cut=float(bp.get("cut_before",0.0)); cs=int(cut*SR)
    def C(arr): return arr[cs:] if cs>0 else arr

    cuetrack=os.path.join(out,"cue_track.wav"); wav_write(cuetrack, C(cue)); print("wrote",cuetrack)

    # click track export (aligned with the prepended stems)
    clickn=click/(np.max(np.abs(click)) or 1)*0.9
    clickwav=os.path.join(out, bp["title"]+" click.wav")
    wav_write(clickwav, C(clickn)); print("wrote",clickwav)

    if audition or final:
        songbed=np.zeros(N,np.float32); place(songbed, song, lead, 1.0)
    if audition:
        mix=songbed*SONGL + click*CLICKL + cue*CUEL
        mix=mix/(np.max(np.abs(mix)) or 1)*0.97
        wp=os.path.join(out, bp["title"]+" cue_preview.wav"); wav_write(wp, C(mix))
        mp=os.path.join(out, bp["title"]+" cue_preview.m4a")
        subprocess.run(["ffmpeg","-y","-v","quiet","-i",wp,"-c:a","aac","-b:a","192k",mp],check=True)
        os.remove(wp); print("wrote",mp)

    # aligned stems: prepend `lead` seconds of silence so every stem syncs with the
    # click/cue tracks (which carry the intro cue lead-in). Also drops click+cue in.
    if final or "--stems" in sys.argv:
        sd=os.path.expanduser(bp.get("stems_dir","")); adir=os.path.join(out,"aligned"); os.makedirs(adir,exist_ok=True)
        prepend=max(0.0, lead-cut)                              # net silence before each stem after the front cut
        af=f"adelay={int(round(prepend*1000))}:all=1" if prepend>0 else (f"atrim=start={cut-lead}" if cut>lead else "anull")
        if sd and os.path.isdir(sd):
            for f in sorted(os.listdir(sd)):
                low=f.lower()
                if not low.endswith((".mp3",".m4a",".wav")): continue
                if "metronome" in low: continue                # replaced by our click.wav
                # skip our OWN generated outputs (matters when out_dir == stems_dir)
                if low in ("cue_track.wav","_refmix.wav") or "cue_preview" in low \
                   or low.endswith(" click.wav") or low.endswith(" cues.wav"): continue
                dst=os.path.join(adir, os.path.splitext(f)[0]+".wav")
                subprocess.run(["ffmpeg","-y","-v","quiet","-i",os.path.join(sd,f),
                                "-af",af,"-c:a","pcm_s16le",dst],check=True)
            print("wrote aligned stems ->",adir,"(+%.3fs silence, cut %.3fs)"%(prepend,cut))
        wav_write(os.path.join(adir, bp["title"]+" click.wav"), C(clickn))
        wav_write(os.path.join(adir, bp["title"]+" cues.wav"), C(cue))

    if final:
        R=click*CLICKL + cue*CUEL
        fp=os.path.join(out, bp["title"]+" [DUO song L  click+cues R].wav")
        wav_write(fp, C(songbed), C(R)); print("wrote",fp)

def init_blueprint(folder, title=None):
    """Scaffold a cues.json from a Moises stem folder (auto-fill paths/title/bpm/key)."""
    folder=os.path.expanduser(folder).rstrip("/")
    base=os.path.basename(folder)
    m=re.match(r"(.*?)-([A-G][b#]?\s*(?:minor|major))-(\d+)\s*bpm", base, re.I)
    key=m.group(2) if m else ""; bpm=m.group(3) if m else ""
    title=title or (m.group(1) if m else base)
    def find(kw):
        g=[f for f in sorted(glob.glob(folder+"/*")) if kw in os.path.basename(f).lower()
           and f.lower().endswith((".mp3",".m4a",".wav"))]
        return g[0] if g else ""
    drums,vocals,metro,bass=find("drum"),find("vocal"),find("metronome"),find("bass")
    parent=os.path.dirname(folder); mix=""
    for ext in (".mp3",".wav",".m4a"):
        c=[f for f in glob.glob(parent+"/*"+ext) if os.path.basename(f).startswith(title)]
        if c: mix=c[0]; break
    bp={"song":mix or metro,"stems_dir":folder,"drums":drums,"vocals":vocals,"bass":bass,"metronome":metro,
        "out_dir":os.path.expanduser("~/projects/cherry-daddies/music/songs/"+title),"title":title,"key":key,"bpm":bpm,
        "voices":{"ru":"Milena","en":None},"rate":150,"count_files":DEFAULT_COUNT_FILES,
        "levels":{"song":0.85,"click":0.6,"cues":1.0},"lead_bars":2,"cut_before":0.0,"time_ref":"logic","retempo":[],
        "cues":[{"id":"C01","name":title.split(" - ")[-1],"lang":"ru","t":"start","anchor":"first_drum","count":True}]}
    os.makedirs(bp["out_dir"],exist_ok=True)
    p=os.path.join(bp["out_dir"],"cues.json"); json.dump(bp,open(p,"w"),ensure_ascii=False,indent=1)
    print("wrote",p,"\n  song:",mix or "(NOT FOUND — set 'song' manually)","\n  title:",title,key,bpm+"bpm")
    print("  time_ref=logic (give cue times straight from Logic). Edit cues[], then:")
    print(f"  python3 {sys.argv[0]} '{p}' --stems")
    return p

if __name__=="__main__":
    if len(sys.argv)>=3 and sys.argv[1]=="--init":
        t=sys.argv[3] if len(sys.argv)>3 and not sys.argv[3].startswith("--") else None
        init_blueprint(sys.argv[2], t)
    else:
        main()
