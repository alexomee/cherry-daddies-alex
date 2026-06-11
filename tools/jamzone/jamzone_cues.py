#!/usr/bin/env python3
"""JamZone cue-track generator (duo mode).

Builds a click-aligned voiceover cue track from a song's structure + stems:
song name + section announcements + 3-2-1 counts, anchored to the lead-VOCAL
onset when the voice enters before the structural downbeat (voice takes priority),
and an END count on the last drum/bass downbeat (not the ring-out tail).

A cues.json blueprint is saved per song; renders load from it so manual edits
(or "remove the Verse 2 cue") survive. Force a fresh build with --regen.

Requires the song's stems to be extracted first (jamzone_extract.py --cat <id>).

Usage:
    jamzone_cues.py <cat_id|query> [--regen] [--audition] [--final]
      (default)     cue_track.wav + cues.json + printed cue list
      --audition    + <song> cue_preview.m4a   (song + cues, both channels, to approve)
      --final       + <song> [DUO click+cues R].wav   (click+cues hard-right, left silent)
"""
import os, sys, hashlib, subprocess, json, wave, glob, re
import numpy as np

JAMS = os.path.expanduser("~/Library/Containers/com.recisio.jamzone.ios/Data/Library/"
                          "Application Support/com.recisio.jamzone.ios/jams")
OUT = os.path.expanduser("~/projects/cherry-daddies/music/songs")
SR = 44100
CLICK_LVL, MIX_LVL, CUE_LVL = 0.6, 0.85, 1.0   # render levels

# ---- decode / synthesis helpers -------------------------------------------
def key_for(cat): return hashlib.md5(cat.encode()).hexdigest().encode().hex()
def dec(cat, name):
    d = open(os.path.join(JAMS, cat, name), "rb").read()
    return subprocess.run(["openssl","enc","-aes-256-cbc","-d","-K",key_for(cat),
                           "-iv",d[:16].hex()], input=d[16:], capture_output=True).stdout
def decode_mono(path, sr=SR):
    raw=subprocess.run(["ffmpeg","-v","quiet","-i",path,"-ac","1","-ar",str(sr),"-f","f32le","-"],
                       capture_output=True).stdout
    return np.frombuffer(raw,np.float32).copy()
def say_clip(text, rate=150):
    subprocess.run(["say","-r",str(rate),"-o","/tmp/_cue.aiff",text], check=True)
    a=decode_mono("/tmp/_cue.aiff"); thr=0.02*(np.max(np.abs(a)) or 1)
    nz=np.where(np.abs(a)>thr)[0]; return a[nz[0]:nz[-1]+1] if len(nz) else a
def mmss(t): return f"{int(t)//60}:{t%60:05.2f}"
def norm(s):
    import unicodedata
    s=unicodedata.normalize('NFKD', s or '')
    return re.sub(r'[^a-z0-9]','',s.encode('ascii','ignore').decode().lower())

def meta(cat):
    s=json.loads(dec(cat,"song.json"))
    a=s.get("artist"); a=a.get("en") if isinstance(a,dict) else a
    return a, s.get("title"), float(s.get("bpm")), float(s.get("duration"))

def resolve(q):
    if re.fullmatch(r'cat_\d+', q): return q
    nq=norm(q)
    for cat in sorted(os.listdir(JAMS)):
        if not os.path.isfile(os.path.join(JAMS,cat,"song.json")): continue
        try: s=json.loads(dec(cat,"song.json"))
        except Exception: continue
        a=s.get("artist"); a=a.get("en") if isinstance(a,dict) else a
        if nq in norm(f"{a}{s.get('title')}"): return cat
    sys.exit(f"No downloaded song matches '{q}'.")

def folder_for(cat):
    a,t,_,_=meta(cat)
    base=f"{a} - {t}".replace('/','-').replace(':','-')
    for d in sorted(glob.glob(os.path.join(OUT,"*"))):   # tolerate a setlist-number prefix ("03 Artist - Title")
        if os.path.isdir(d) and re.sub(r'^\d+[\s.\-]*','',os.path.basename(d))==base:
            return d
    return os.path.join(OUT, base)

def stem(folder, *keywords, exclude=()):
    fs=[f for f in glob.glob(os.path.join(folder,"*.m4a"))
        if any(k in os.path.basename(f).lower() for k in keywords)
        and not any(x in os.path.basename(f).lower() for x in exclude)]
    return sorted(fs)[0] if fs else None

def last_active(path, sr=22050, frac=0.05):
    a=decode_mono(path,sr); win=int(0.05*sr)
    env=np.array([np.sqrt((a[i:i+win]**2).mean()) for i in range(0,len(a),win)])
    act=np.where(env>frac*(env.max() or 1))[0]
    return act[-1]*0.05 if len(act) else None

def last_attack(folder, sr=22050):
    """Time of the last strong ONSET across harmonic/rhythm stems (the final chord
    struck) — ignores the ring-out tail. None if no such stems."""
    keys=("drum","bass","guitar","piano","organ","key","string","synth")
    fs=[f for f in glob.glob(os.path.join(folder,"*.m4a"))
        if any(k in os.path.basename(f).lower() for k in keys)
        and "vocal" not in os.path.basename(f).lower()
        and not os.path.basename(f).startswith("01_Click")]
    if not fs: return None
    comb=None; win=int(0.03*sr)
    for f in fs:
        a=decode_mono(f,sr)
        e=np.array([np.sqrt((a[i:i+win]**2).mean()) for i in range(0,len(a),win)])
        if comb is None: comb=np.zeros(max(len(e),1))
        if len(e)>len(comb): comb=np.pad(comb,(0,len(e)-len(comb)))
        comb[:len(e)]+=e[:len(comb)]
    flux=np.maximum(0,np.diff(comb)); thr=0.12*(flux.max() or 1)
    hits=np.where(flux>thr)[0]
    return hits[-1]*0.03 if len(hits) else None

# ---- analysis -------------------------------------------------------------
def vocal_envelope(folder):
    f=stem(folder,"vocal",exclude=("adlib","ad_lib","ad-lib","(ad","backing")) or stem(folder,"vocal")
    if not f: return None
    a=decode_mono(f,22050); win=int(0.05*22050)
    env=np.array([np.sqrt((a[i:i+win]**2).mean()) for i in range(0,len(a),win)])
    return env, 0.04*(env.max() or 1), 0.05

def vocal_onset(env_pack, db, beat):
    if not env_pack: return None
    env,thr,dt=env_pack; gap=max(1,int(round(0.6*beat/dt)))
    lo=int((db-4*beat)/dt); hi=int((db+1.5*beat)/dt)
    onsets=[k*dt for k in range(max(lo,gap),min(hi,len(env)))
            if env[k]>thr and env[k-1]<=thr and np.all(env[k-gap:k]<=thr)]
    return min(onsets,key=lambda o:abs(o-db)) if onsets else None

def vocal_active_at(env_pack, t, beat):
    """True if the lead vocal carries this section (energy in [−0.25, +1] beat of the
    downbeat) — used to give vocal sections a 'ready, go' lead-in vs an instrumental 3-2-1."""
    if not env_pack: return False
    env,thr,dt=env_pack
    a=max(0,int((t-0.25*beat)/dt)); b=min(len(env),int((t+1.0*beat)/dt))
    return b>a and np.max(env[a:b])>thr

VOCAL_CAP=re.compile(r'verse|chorus|hook|bridge|refrain|pre.?chorus|vocal|rap', re.I)
INSTR_CAP=re.compile(r'intro|outro|instrumental|solo|break|interlude|riff|guitar|sax|build|drop|drum|bass', re.I)

def build_duo(cat, folder):
    a,t,bpm,dur=meta(cat); beat=60.0/bpm; barlen=4*beat
    st=json.loads(dec(cat,"structure.json"))
    env_pack=vocal_envelope(folder)
    secs=[s for s in st if not s["caption"].lower().startswith("precount")]
    first_db=secs[0]["begin"]
    snap=lambda x: first_db+round((x-first_db)/beat)*beat
    barno=lambda x: round((x-first_db)/barlen)+1
    cues=[]
    spoken=lambda x: re.sub(r'\s*\([^)]*\)','',x).strip()   # drop "(acoustic)", "(Bossa Nova Covers)"…
    for i,s in enumerate(secs):
        db=s["begin"]; cap=s["caption"]; base=spoken(t if i==0 else cap); target=db
        # vocal section? positive caption hint OR actual vocal-stem energy at the downbeat
        # (energy decides "Outro"/ambiguous: an outro that still sings is a vocal entry).
        is_vocal = bool(VOCAL_CAP.search(cap or '')) or vocal_active_at(env_pack,db,beat)
        on=vocal_onset(env_pack,db,beat)
        if on is not None and on < db-0.3*beat:               # clean pickup after silence → anchor to it
            target=snap(on); is_vocal=True
        if is_vocal:                                          # VOCAL entry → spoken "vocal in ready go"
            style="readygo"; label=base if i==0 else "vocal in"
        else:                                                 # instrumental entry → "3-2-1", part on downbeat
            style="321"; label=base
        cues.append({"t":round(target,3),"bar":barno(target),"name":label,
                     "count_style":style,"src":"start" if i==0 else "sec"})
    # END downbeat = the last chord actually STRUCK (last attack across harmonic/rhythm
    # stems), snapped to the grid — avoids the ring-out tail. Fallback: structure end.
    at=last_attack(folder)
    end_t=at if at is not None else secs[-1]["end"]
    end_db=first_db+round((end_t-first_db)/barlen)*barlen
    cues.append({"t":round(end_db,3),"bar":barno(end_db),"name":"end","src":"end"})
    cues.sort(key=lambda c:c["t"])
    for i,c in enumerate(cues,1): c["id"]=f"C{i:02d}"
    return beat,cues

# ---- render ---------------------------------------------------------------
def song_mix(folder, exclude_click=True):
    mix=None
    for s in sorted(glob.glob(os.path.join(folder,"*.m4a"))):
        if exclude_click and os.path.basename(s).startswith("01_Click"): continue
        x=decode_mono(s)
        if mix is None: mix=np.zeros(len(x),np.float32)
        if len(x)>len(mix): mix=np.pad(mix,(0,len(x)-len(mix)))
        mix[:len(x)]+=x[:len(mix)]
    if mix is None: return np.zeros(SR,np.float32)
    return mix/(np.max(np.abs(mix)) or 1)

def cue_bed(folder):
    w=wave.open(os.path.join(folder,"cue_track.wav"))
    return np.frombuffer(w.readframes(w.getnframes()),"<i2").astype(np.float32).reshape(-1,2)[:,0].copy()/32767

def click_grid(folder, sr=SR):
    """Onset times of the actual Click stem — the true grid the counts must sit on.
    MUST decode at SR (the cue-track / Logic rate): resampling AAC to a different rate
    time-shifts the decode (~0.24s here), putting every detected click a half-beat off."""
    f=stem(folder,"click")
    if not f: return []
    a=decode_mono(f,sr); win=int(0.005*sr); dt=win/sr   # real window duration, NOT 0.005 (int() truncates win)
    env=np.array([np.sqrt((a[i:i+win]**2).mean()) for i in range(0,len(a),win)])
    thr=0.25*(env.max() or 1)
    return [k*dt for k in range(1,len(env)) if env[k]>thr and env[k-1]<=thr]

def write_wav(path, left, right):
    L=max(len(left),len(right)); left=np.pad(left,(0,L-len(left))); right=np.pad(right,(0,L-len(right)))
    st=np.stack([(np.clip(left,-1,1)*32767).astype("<i2"),(np.clip(right,-1,1)*32767).astype("<i2")],1)
    w=wave.open(path,"w"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(st.tobytes()); w.close()

def render(cat, regen=False, audition=False, final=False):
    a,t,bpm,dur=meta(cat); beat=60.0/bpm
    folder=folder_for(cat)
    if not glob.glob(os.path.join(folder,"*.m4a")):
        sys.exit(f"No stems in {folder}\n  run: jamzone_extract.py --cat {cat}")
    jpath=os.path.join(folder,"cues.json")
    if os.path.exists(jpath) and not regen:
        cues=json.load(open(jpath)); print(f"(loaded {len(cues)} cues from cues.json)")
    else:
        beat,cues=build_duo(cat,folder)
        gap=min(max(beat,0.30),0.90); clips={c["id"]:say_clip(c["name"]) for c in cues}
        occ=[]; kept=[]; dropped=[]
        for c in sorted(cues,key=lambda c:c["t"]):
            T=c["t"]; offs=(4,3,2,1) if c.get("count_style")=="readygo" else (3,2,1)
            cstart=T-offs[0]*beat                  # first count word (−4 for ready/go phrase, −3 for 3-2-1)
            nm=clips[c["id"]]; nd=len(nm)/SR
            ns=max(0.0,cstart-gap-nd); s=int(ns*SR); e=s+len(nm)
            if c["src"]=="start":            # song name is never dropped
                occ.append((s,e)); kept.append(c); continue
            if any(s<oe and e>os_ for os_,oe in occ) or ns+nd>cstart-0.05:
                dropped.append(c); continue
            occ.append((s,e))
            for off in offs: occ.append((int((T-off*beat)*SR),int((T-off*beat+0.35)*SR)))
            kept.append(c)
        cues=kept; json.dump(cues,open(jpath,"w"),indent=1)
        if dropped: print("dropped (too tight): "+", ".join(f"{c['id']} {c['name']}" for c in dropped))
    # cue_track.wav (cues on both channels)
    gap=min(max(beat,0.30),0.90)
    N=int((max(dur,max(c["t"] for c in cues))+1.0)*SR); bed=np.zeros(N,np.float32)
    counts={n:say_clip(n) for n in ("3","2","1","vocal","in","ready","go")}
    def odelay(clip,frac=0.4):               # delay to the vowel (felt beat), past the soft consonant
        win=int(0.02*SR)
        e=np.array([np.sqrt((clip[i:i+win]**2).mean()) for i in range(0,len(clip),win)])
        return int(np.argmax(e>frac*(e.max() or 1)))*0.02
    cdelay={n:odelay(counts[n]) for n in counts}
    def place(clip,t0):
        s=int(max(0.0,t0)*SR); e=s+len(clip)
        if e>N: clip=clip[:N-s]; e=N
        bed[s:e]+=clip
    clicks=click_grid(folder)
    def nclick(t):                           # snap to the real click when one is within half a beat
        if not clicks: return t
        c=min(clicks,key=lambda x:abs(x-t)); return c if abs(c-t)<0.5*beat else t
    for c in sorted(cues,key=lambda c:c["t"]):
        T=c["t"]
        if not c.get("count",True):          # spoken-only cue: name finishes ~gap before the downbeat
            nm=say_clip(c["name"]); place(nm, max(0.0, nclick(T)-gap-len(nm)/SR)); continue
        if c.get("count_style")=="readygo":  # VOCAL entry: "vocal in ready go"; vocal enters the beat AFTER "go"
            seq=[("vocal",4),("in",3),("ready",2),("go",1)]   # go on −1, voice on the downbeat (0)
            announce = c["src"]=="start"     # speak the song title only at the very start; phrase carries the rest
        else:                                # instrumental: name + "3 2 1", the part lands on the downbeat
            seq=[("3",3),("2",2),("1",1)]; announce=True
        c0=nclick(T-seq[0][1]*beat); name_end=c0-gap
        if announce:                         # place the section/song name just before the first count word
            nm=say_clip(c["name"]); nd=len(nm)/SR; place(nm, max(0.0,c0-gap-nd)); name_end=max(name_end,c0-gap)
        for word,off in seq:                 # count vowel lands exactly on the click (pre-roll by clip attack)
            ct=nclick(T-off*beat) if off else nclick(T)
            if ct<0: continue
            place(counts[word], ct - cdelay[word])
    write_wav(os.path.join(folder,"cue_track.wav"), bed, bed)
    print(f"\n{a} - {t}   {bpm:g}bpm   mode=duo   -> cue_track.wav  ({mmss(dur)})")
    print(f"{'ID':4}{'time':>8} {'bar':>4}  {'spoken':22} {'count':16} src")
    for c in sorted(cues,key=lambda c:c["t"]):
        if not c.get("count",True): cnt="(spoken only)"
        elif c.get("count_style")=="readygo": cnt="vocal in ready go" if c["src"]!="start" else "+vocal in ready go"
        else: cnt="3 2 1"
        print(f"{c['id']:4}{mmss(c['t']):>8} {c['bar']:>4}  {c['name']:22} {cnt:16} {c['src']}")
    if audition:
        mix=song_mix(folder, exclude_click=False); cb=cue_bed(folder)   # include click in preview
        L=max(len(mix),len(cb)); mix=np.pad(mix,(0,L-len(mix))); cb=np.pad(cb,(0,L-len(cb)))
        m=mix*MIX_LVL + cb*CUE_LVL; write_wav("/tmp/_aud.wav", m, m)
        ap=os.path.join(folder, f"{a} - {t} cue_preview.m4a")
        subprocess.run(["ffmpeg","-v","quiet","-y","-i","/tmp/_aud.wav","-c:a","aac","-b:a","160k",ap])
        print("audition:",os.path.basename(ap))
    if final:
        cf=stem(folder,"01_click","click")
        click=decode_mono(cf) if cf else np.zeros(1,np.float32)
        click=click/(np.max(np.abs(click)) or 1)*CLICK_LVL
        cb=cue_bed(folder); L=max(len(click),len(cb))
        click=np.pad(click,(0,L-len(click))); cb=np.pad(cb,(0,L-len(cb)))
        fp=os.path.join(folder, f"{a} - {t} [DUO click+cues R].wav")
        write_wav(fp, np.zeros(L,np.float32), click+cb)   # left silent, right=click+cues
        print("final:",os.path.basename(fp))

if __name__=="__main__":
    pos=[x for x in sys.argv[1:] if not x.startswith("--")]
    if not pos: sys.exit(__doc__)
    render(resolve(pos[0]), regen="--regen" in sys.argv,
           audition="--audition" in sys.argv, final="--final" in sys.argv)
