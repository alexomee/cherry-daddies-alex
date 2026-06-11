#!/usr/bin/env python3
"""Match the JamZone click for an external song at ANY bpm.

Two parts:
  extract  -> lift one clean downbeat sample + one clean beat sample from any
              JamZone Click stem (do this ONCE; samples are library-wide identical:
              downbeat ~200Hz +6dB, beat ~176Hz).
  build    -> re-grid those two samples onto a click track at the target bpm
              (4/4, accent on beat 1), with an optional spoken/extra count-in.

Usage:
  jamzone_click_match.py extract <cat_id>            -> jz_downbeat.wav, jz_beat.wav
  jamzone_click_match.py build  <bpm> <bars> [--countin N] [-o out.wav]
"""
import os, sys, hashlib, subprocess, wave
import numpy as np
SR=44100
JAMS=os.path.expanduser("~/Library/Containers/com.recisio.jamzone.ios/Data/Library/"
                        "Application Support/com.recisio.jamzone.ios/jams")
HERE=os.path.expanduser("~/projects/cherry-daddies/music/songs")
DB=os.path.join(HERE,"jz_downbeat.wav"); BT=os.path.join(HERE,"jz_beat.wav")

def key_for(cat): return hashlib.md5(cat.encode()).hexdigest().encode().hex()
def click_filename(cat):
    import json
    f=os.path.join(JAMS,cat,"tracks.json"); d=open(f,"rb").read()
    raw=subprocess.run(["openssl","enc","-aes-256-cbc","-d","-K",key_for(cat),
                        "-iv",d[:16].hex()],input=d[16:],capture_output=True).stdout
    return next(t["filename"] for t in json.loads(raw) if t.get("click"))
def decrypt_to(cat,name,out):
    d=open(os.path.join(JAMS,cat,name),"rb").read()
    open(out,"wb").write(subprocess.run(["openssl","enc","-aes-256-cbc","-d","-K",key_for(cat),
        "-iv",d[:16].hex()],input=d[16:],capture_output=True).stdout)
def decode_mono(path):
    raw=subprocess.run(["ffmpeg","-v","quiet","-i",path,"-ac","1","-ar",str(SR),"-f","f32le","-"],
                       capture_output=True).stdout
    return np.frombuffer(raw,np.float32).copy()
def wav_write(path,x):
    x=np.clip(x,-1,1); w=wave.open(path,"w"); w.setnchannels(1);w.setsampwidth(2);w.setframerate(SR)
    w.writeframes((x*32767).astype("<i2").tobytes()); w.close()
def wav_read(path):
    w=wave.open(path); x=np.frombuffer(w.readframes(w.getnframes()),"<i2").astype(np.float32)/32767; return x

def extract(cat):
    decrypt_to(cat, click_filename(cat), "/tmp/_jzclick.m4a")
    a=decode_mono("/tmp/_jzclick.m4a")
    win=int(0.005*SR); dt=win/SR
    env=np.array([np.sqrt((a[i:i+win]**2).mean()) for i in range(0,len(a),win)])
    thr=0.25*env.max()
    on=np.array([k*dt for k in range(1,len(env)) if env[k]>thr and env[k-1]<=thr])
    amps=np.array([np.max(np.abs(a[int(t*SR):int(t*SR)+int(0.06*SR)])) for t in on])
    loud=amps>0.9*amps.max()
    def grab(t,pre=0.004,post=0.13):
        s0=int((t-0.01)*SR);s1=int((t+0.02)*SR);pk=s0+int(np.argmax(np.abs(a[s0:s1])))
        seg=a[pk-int(pre*SR):pk+int(post*SR)].copy(); p=np.max(np.abs(seg))
        below=np.where(np.abs(seg)>0.01*p)[0]
        if len(below): seg=seg[:below[-1]+int(0.003*SR)]
        fl=min(int(0.002*SR),len(seg)//4); seg[-fl:]*=np.linspace(1,0,fl); return seg/p
    li=[i for i in range(10,300) if loud[i]][0]; qi=li+1
    os.makedirs(HERE,exist_ok=True)
    wav_write(DB, grab(on[li])); wav_write(BT, grab(on[qi]))
    print("wrote",DB,"and",BT)

def build(bpm,bars,countin=0,out="jz_click.wav"):
    db=wav_read(DB); bt=wav_read(BT)
    beat=60.0/bpm; n=bars*4
    pre=countin*beat
    total=int((pre + n*beat + 0.3)*SR); o=np.zeros(total,np.float32)
    def place(hit,t,g):
        s=int(t*SR); h=hit*g; o[s:s+len(h)]+=h
    for i in range(countin):                       # count-in: all on the accented (downbeat) sound
        place(db, i*beat, 1.0)
    for i in range(n):                             # body: accent every 4
        t=pre+i*beat
        place(db if i%4==0 else bt, t, 1.0 if i%4==0 else 0.5)
    wav_write(out, o/(np.max(np.abs(o)) or 1)*0.95)
    print("wrote",out,"(%.1fs, %g bpm, %d bars, %d count-in)"%(len(o)/SR,bpm,bars,countin))

if __name__=="__main__":
    if len(sys.argv)<2: sys.exit(__doc__)
    if sys.argv[1]=="extract": extract(sys.argv[2])
    elif sys.argv[1]=="build":
        bpm=float(sys.argv[2]); bars=int(sys.argv[3])
        ci=int(sys.argv[sys.argv.index("--countin")+1]) if "--countin" in sys.argv else 0
        out=sys.argv[sys.argv.index("-o")+1] if "-o" in sys.argv else "jz_click.wav"
        build(bpm,bars,ci,out)
    else: sys.exit(__doc__)
