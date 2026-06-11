#!/usr/bin/env python3
"""Export a JamZone song into the Stage Traxx 4 library.

Creates a Stage Traxx song with: all stems + the cues track as audio tracks,
sections as regions, and a time-synced chord+lyric chart in the lyrics field.
Default routing matches the in-ear duo setup — only Click + Cues are unmuted and
panned hard RIGHT; every stem is loaded but muted (unmute live as needed). The
built-in metronome is turned off (the JamZone Click track replaces it).

Requires the song already extracted (jamzone_extract.py) AND a cue track rendered
(jamzone_cues.py … --final or the cue_track.wav present in the song folder).

Stage Traxx must be CLOSED while writing — the script quits it first.

Usage:
    jamzone_stagetraxx.py <cat_id|query> [--playlist "NAME"] [--launch]

Format reverse-engineered from Stage Traxx 4 (de.dikant.StageTraxx4):
  - GRDB SQLite library `music_library.sqlite`; audio under Data/Documents/<title>/.
  - ids are 16-byte UUID blobs; datetimes `YYYY-MM-DD HH:MM:SS.mmm`.
  - track.volume is in dB (0.0 = unity); pan -1..+1; equalizer is a 4-band struct;
    filePath is Documents-relative ("<title>/<file>").
  - song.key JSON {"note":L,"accidental":-1|0|1,"quality":0(maj)|1(min)}.
  - lyrics: timestamped lines `[MM:SS.xx]`, `## Section` headers, inline `[chord]word`.
"""
import os, sys, re, json, hashlib, subprocess, sqlite3, uuid, shutil, glob, datetime

JAMS = os.path.expanduser("~/Library/Containers/com.recisio.jamzone.ios/Data/Library/"
                          "Application Support/com.recisio.jamzone.ios/jams")
STEMS = os.path.expanduser("~/projects/cherry-daddies/music/songs")
ST = os.path.expanduser("~/Library/Containers/de.dikant.StageTraxx4/Data")
DB = os.path.join(ST, "Library/Application Support/StageTraxx4/music_library.sqlite")
DOCS = os.path.join(ST, "Documents")
EQ = ('{"bands":[{"bw":1,"freq":100,"gain":0,"label":"LO","type":1},'
      '{"bw":1,"freq":500,"gain":0,"label":"LM","type":0},'
      '{"bw":2,"freq":2000,"gain":0,"label":"HM","type":0},'
      '{"bw":1,"freq":10000,"gain":0,"label":"HI","type":2}],"bypass":false}')

SHARP = {1:'C',2:'C#',3:'D',4:'D#',5:'E',6:'F',7:'F#',8:'G',9:'G#',10:'A',11:'A#',12:'B'}
FLAT  = {1:'C',2:'Db',3:'D',4:'Eb',5:'E',6:'F',7:'Gb',8:'G',9:'Ab',10:'A',11:'Bb',12:'Cb'}
QUAL = {1:'',2:'m',6:'m',7:'',8:'5',9:'maj7',10:'m7',11:'7',12:'m',13:'dim',14:'m',15:'m',
        16:'7',17:'7',18:'m',19:'',22:'',23:'m',24:'m',25:'m',28:'',34:'m',37:'m',39:'maj7',
        41:'m',42:'m',48:'m',49:'m',54:'',56:'',57:'',58:'',63:'',64:'m',65:'m',70:'m',
        73:'dim',76:'dim',77:'m',90:'',97:'m',98:'m'}
RICH = {'maj7':4,'m7':4,'7':4,'dim':3,'m':2,'5':1,'':1}

def key_for(cat): return hashlib.md5(cat.encode()).hexdigest().encode().hex()
def dj(cat, name):
    d = open(os.path.join(JAMS, cat, name), "rb").read()
    out = subprocess.run(["openssl","enc","-aes-256-cbc","-d","-K",key_for(cat),
                          "-iv",d[:16].hex()], input=d[16:], capture_output=True).stdout
    return json.loads(out)
def norm(s):
    import unicodedata
    s = unicodedata.normalize('NFKD', s or '')
    return re.sub(r'[^a-z0-9]','',s.encode('ascii','ignore').decode().lower())
def note(r):
    flat = r >= 100; b = r-100 if flat else r
    return (FLAT if flat else SHARP).get(b, '?')
def ts(t): return f"[{int(t)//60:02d}:{t%60:05.2f}]"

def resolve(q):
    if re.fullmatch(r'cat_\d+', q): return q
    nq = norm(q)
    for cat in sorted(os.listdir(JAMS)):
        if not os.path.isfile(os.path.join(JAMS,cat,"song.json")): continue
        try: s = dj(cat,"song.json")
        except Exception: continue
        a = s.get("artist"); a = a.get("en") if isinstance(a,dict) else a
        if nq in norm(f"{a}{s.get('title')}"): return cat
    sys.exit(f"No downloaded song matches '{q}'.")

def stems_folder(artist, title):
    base = f"{artist} - {title}".replace('/','-').replace(':','-')
    for d in sorted(glob.glob(os.path.join(STEMS,"*"))):   # tolerate a "NN " setlist prefix
        if os.path.isdir(d) and re.sub(r'^\d+[\s.\-]*','',os.path.basename(d)) == base:
            return d
    return os.path.join(STEMS, base)

def chord_events(it):
    out = []
    for sb in it.get("subBeats", []):
        c = sb.get("chords")
        if not c or c.get("chord_is_repetition"): continue
        r, tid = c["chord_root"], c["chord_type_id"]; q = QUAL.get(tid,'')
        if out and out[-1][1] == r:
            if RICH.get(q,0) > RICH.get(QUAL.get(out[-1][2],''),0): out[-1] = (sb["time"],r,tid)
            continue
        out.append((sb["time"], r, tid))
    return [(t, note(r)+QUAL.get(tid,'')) for t,r,tid in out]

def syl_events(it):
    out = []
    w = it.get("words")
    if isinstance(w, dict):
        for groups in w.values():
            for g in groups:
                for i, s in enumerate(g.get("syllabes", [])):
                    out.append((s.get("start", it["start"]), s.get("text",""), i == 0))
    return sorted(out)

def build_lyrics(cat, title):
    tiles = dj(cat, "tiles.json")
    lines = [f"# {title}", ""]
    cur = None
    for it in tiles:
        cap = it.get("sectionCaption")
        if not cap or cap.lower().startswith("precount"): continue
        if cap != cur: lines.append(f"{ts(it['start'])}## {cap}"); cur = cap
        syls = syl_events(it)
        if syls:                                  # interleave chords above the words
            ev = [(t,"c",nm) for t,nm in chord_events(it)] + [(t,"s",txt,ws) for t,txt,ws in syls]
            ev.sort(key=lambda e: e[0])
            line = ""; last_text = False
            for e in ev:
                if e[1] == "c": line += f"[{e[2]}]"
                else:
                    if e[3] and last_text: line += " "
                    line += e[2]; last_text = True
            if line.strip(): lines.append(f"{ts(syls[0][0])}{line}")
        else:                                     # instrumental tile -> bar-grouped chord line
            bpm = it.get("bpm") or 0
            if not bpm: continue
            bl = 60/bpm; st = it["start"]; bd = {}
            for t,nm in chord_events(it): bd.setdefault(int(((t-st)/bl)//4), []).append(nm)
            ch = " | ".join(" ".join(v) for _,v in sorted(bd.items()))
            if ch: lines.append(f"{ts(st)}{ch}")
    return "\n".join(lines)

def key_json(keystr):
    keystr = keystr or "C"
    q = 1 if keystr.endswith("m") else 0
    n = keystr[:-1] if keystr.endswith("m") else keystr
    acc = 0
    if n.endswith("b"): acc, n = -1, n[:-1]
    elif n.endswith("#"): acc, n = 1, n[:-1]
    return json.dumps({"note": n or "C", "accidental": acc, "quality": q})

def track_meta(fname):
    if fname.startswith("01_Click"): return "Click", 0, 1.0
    if fname == "cue_track.wav":      return "Cues", 0, 1.0
    nm = re.sub(r'^\d+_', '', os.path.splitext(fname)[0]).replace('_',' ')
    return nm, 1, 0.0                              # other stems: muted, centered

def export(cat, playlist=None):
    song = dj(cat, "song.json")
    artist = song.get("artist"); artist = artist.get("en") if isinstance(artist,dict) else artist
    title = song.get("title"); bpm = float(song["bpm"]); dur = float(song["duration"])
    src = stems_folder(artist, title)
    audio = sorted(f for f in os.listdir(src) if f.endswith(".m4a") and "preview" not in f)
    if os.path.exists(os.path.join(src,"cue_track.wav")): audio.append("cue_track.wav")
    if not any(f.startswith("01_Click") for f in audio):
        sys.exit(f"No stems in {src} — run jamzone_extract.py first.")
    if "cue_track.wav" not in audio:
        print("  ! no cue_track.wav — run jamzone_cues.py first (continuing without a cues track)")

    dest = os.path.join(DOCS, title.replace('/','-').replace(':','-'))
    os.makedirs(dest, exist_ok=True)
    for f in os.listdir(dest):
        if f.endswith((".m4a",".wav")): os.remove(os.path.join(dest,f))
    for f in audio: shutil.copy2(os.path.join(src,f), os.path.join(dest,f))

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    folder = os.path.basename(dest)
    lyrics = build_lyrics(cat, title)
    secs = [s for s in dj(cat,"structure.json") if not s["caption"].lower().startswith("precount")]

    con = sqlite3.connect(DB); con.execute("PRAGMA foreign_keys=ON"); c = con.cursor()
    for (sid,) in c.execute("SELECT id FROM song WHERE title=?", (title,)).fetchall():
        c.execute("DELETE FROM track WHERE songID=?", (sid,))
        c.execute("DELETE FROM region WHERE songID=?", (sid,))
        c.execute("DELETE FROM playlistSong WHERE songID=?", (sid,))
        c.execute("DELETE FROM song WHERE id=?", (sid,))
    sid = uuid.uuid4().bytes
    c.execute("""INSERT INTO song (id,title,artist,added,duration,bpm,year,notes,color,volume,speed,pitch,
      tune,chordTranspose,pitchToChords,fadeIn,fadeOut,startTime,endTime,fontSize,lyrics,pdfPath,metronomeMode,
      metronomeType,playCount,lastPlayed,lastModified,timecodeOffset,midiCmd,midiPath,scrollSpeed,folderID,key,
      waveformTrackID) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
      (sid,title,artist or "",now,dur,bpm,None,None,3,0.0,1.0,0,0,0,0,0.0,0.0,0.0,dur,32,lyrics,None,0,2,
       0,None,now,0.0,None,None,1.2,None,key_json(song.get("key")),None))
    for i, f in enumerate(audio, 1):
        nm, mute, pan = track_meta(f)
        c.execute("""INSERT INTO track (id,songID,filePath,duration,volume,pan,mute,bus,number,hasMarkers,
          equalizer,lastModified,name,color,transpose,muteGroupMask) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
          (uuid.uuid4().bytes,sid,f"{folder}/{f}",dur,0.0,pan,mute,0,i,0,EQ,now,nm,0,1,0))
    for i, s in enumerate(secs):
        c.execute("""INSERT INTO region (id,songID,name,startTime,endTime,color,playbackMode,lastModified)
          VALUES (?,?,?,?,?,?,?,?)""",(uuid.uuid4().bytes,sid,s["caption"],s["begin"],s["end"],(i%8)+1,0,now))
    if playlist:
        row = c.execute("SELECT id FROM playlist WHERE name=?", (playlist,)).fetchone()
        if row: pid = row[0]
        else:
            pid = uuid.uuid4().bytes
            c.execute("""INSERT INTO playlist (id,name,added,autoplay,color,volume,lastModified,folderID)
              VALUES (?,?,?,?,?,?,?,?)""",(pid,playlist,now,0,3,0.0,now,None))
        nxt = (c.execute("SELECT COALESCE(MAX(sortOrder),-1)+1 FROM playlistSong WHERE playlistID=?",(pid,)).fetchone()[0])
        c.execute("""INSERT INTO playlistSong (id,songID,playlistID,added,playbackMode,sortOrder,lastModified)
          VALUES (?,?,?,?,?,?,?)""",(uuid.uuid4().bytes,sid,pid,now,0,nxt,now))
    con.commit(); con.close()
    print(f"  ✓ {artist} - {title}  ({len(audio)} tracks, {len(secs)} regions"
          + (f", + playlist '{playlist}'" if playlist else "") + ")")

def main():
    pos = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not pos: sys.exit(__doc__)
    pl = None
    if "--playlist" in sys.argv:
        i = sys.argv.index("--playlist"); pl = sys.argv[i+1] if i+1 < len(sys.argv) else None
    if subprocess.run(["pgrep","-f","Stage Traxx 4"], capture_output=True).stdout.strip():
        print("Quitting Stage Traxx 4…")
        subprocess.run(["osascript","-e",'tell application "Stage Traxx 4" to quit'])
        import time; time.sleep(2)
    for q in pos: export(resolve(q), playlist=pl)
    if "--launch" in sys.argv:
        subprocess.run(["open","/Applications/Stage Traxx 4.app"])
    else:
        print("Done. Relaunch Stage Traxx 4 to see the song(s).")

if __name__ == "__main__":
    main()
