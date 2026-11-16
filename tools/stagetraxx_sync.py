#!/usr/bin/env python3
"""Sync the band's auto-renders into the Stage Traxx 4 library (playback rig without MainStage).

For every song of the setlist (web/songs.json) builds/updates a Stage Traxx song:

    out1 Click     bus0 pan -1     (in-ears)
    out2 Cues      bus0 pan +1     (in-ears)
    out3 PB Other  bus1 pan -1     (front of house; keys live here too)
    out4 PB Bass   bus1 pan +1     (front of house)

(each Stage Traxx bus = one stereo output pair; pan picks L/R inside it.) Stems are
DOWNMIXED TO MONO on the way in — pb-other/pb-bass are true stereo and a hard pan
on a stereo file would simply drop one side.

MIDI for the lyric launcher goes into the song's lyrics field (the only per-song
outbound MIDI Stage Traxx 4 has):

    [midi: PC<clip>@<ch>]     song load  -> launcher ARMS clip NN
    [midi@play: START]        play       -> launcher rolls from 0
    [midi@stop: STOP]         stop       -> launcher freezes

clip NN comes from tools/lyric-launcher/songs.tsv. Stage Traxx sends to all MIDI
ports, so the launcher's virtual `LyricLauncher` port gets it (start launcher first).

Songs this tool owns are tagged in song.notes (`cd-sync:<folder>`) and updated in
place; anything else in the library (hand-made songs, old imports) is left alone.
One playlist per set of web/songs.json, named `CD · <set>`.

DEFAULT IS DRY-RUN. --apply writes: Stage Traxx must be closed (--quit closes it),
the library DB is backed up first to ~/.cache/cherry-daddies/stagetraxx-backups/.

Usage:
    tools/stagetraxx_sync.py                      # dry-run, everything
    tools/stagetraxx_sync.py --apply --quit       # write everything
    tools/stagetraxx_sync.py --apply "S&M"        # only songs matching a substring
    tools/stagetraxx_sync.py --set "Music Hall"   # only sets matching a substring
"""
import argparse, csv, datetime, json, os, re, sqlite3, subprocess, sys, time, uuid, wave

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SONGS = os.path.join(REPO, "music", "songs")
ST = os.path.expanduser("~/Library/Containers/de.dikant.StageTraxx4/Data")
DB = os.path.join(ST, "Library/Application Support/StageTraxx4/music_library.sqlite")
DOCS = os.path.join(ST, "Documents")
BACKUPS = os.path.expanduser("~/.cache/cherry-daddies/stagetraxx-backups")
MARK = "cd-sync:"
PL_PREFIX = "CD · "
EQ = ('{"bands":[{"bw":1,"freq":100,"gain":0,"label":"LO","type":1},'
      '{"bw":1,"freq":500,"gain":0,"label":"LM","type":0},'
      '{"bw":2,"freq":2000,"gain":0,"label":"HM","type":0},'
      '{"bw":1,"freq":10000,"gain":0,"label":"HI","type":2}],"bypass":false}')

# stem -> (file name in Stage Traxx, track name, bus, pan)
ROUTING = [
    ("click",    "1_Click.wav",    "Click",    0, -1.0),
    ("cues",     "2_Cues.wav",     "Cues",     0,  1.0),
    ("pb-other", "3_PB_Other.wav", "PB Other", 1, -1.0),
    ("pb-bass",  "4_PB_Bass.wav",  "PB Bass",  1,  1.0),
]


def now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]


def load_setlist():
    with open(os.path.join(REPO, "web", "songs.json"), encoding="utf-8") as f:
        return json.load(f)["sets"]


def load_clips():
    clips = {}
    with open(os.path.join(REPO, "tools", "lyric-launcher", "songs.tsv"), encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            clips[os.path.basename(r["factory_dir"])] = int(r["clip"])
    return clips


def song_bpm(sid):
    for rel in ("mix.json", "auto-render/timeline.json"):
        try:
            with open(os.path.join(SONGS, sid, rel), encoding="utf-8") as f:
                v = json.load(f).get("bpm")
            if v:
                return float(v)
        except (OSError, ValueError, AttributeError):
            pass
    return 120.0


def wav_duration(path):
    with wave.open(path) as w:
        return w.getnframes() / float(w.getframerate())


def midi_block(clip, channel):
    lines = []
    if clip is not None:
        lines.append(f"[midi: PC{clip}@{channel}]")
    lines += ["[midi@play: START]", "[midi@stop: STOP]"]
    return lines


def merge_lyrics(old, block):
    """Our MIDI tags first, then whatever non-MIDI text the song already had."""
    keep = [l for l in (old or "").splitlines() if not l.strip().lower().startswith("[midi")]
    while keep and not keep[0].strip():
        keep.pop(0)
    return "\n".join(block + ([""] + keep if keep else []))


def safe_dir(sid):
    return re.sub(r"[/:]", "-", sid)


def downmix(src, dst):
    """Mono 16-bit copy of src (ffmpeg -ac 1 = 0.5L+0.5R). Skips when dst is fresh."""
    if os.path.exists(dst) and os.path.getmtime(dst) >= os.path.getmtime(src):
        return False
    tmp = dst + ".tmp.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-ac", "1",
                    "-c:a", "pcm_s16le", tmp], check=True)
    os.replace(tmp, dst)
    return True


def plan(sets, clips, song_filters, set_filter):
    """-> (songs {sid: info}, playlists [(name, [sid...])])"""
    songs, playlists = {}, []
    for st in sets:
        name = st["name"] + (f" · {st['subtitle']}" if st.get("subtitle") else "")
        if set_filter and set_filter.lower() not in name.lower():
            continue
        members = []
        for s in st["songs"]:
            sid = s["sid"]
            hay = f"{sid} {s.get('title', '')}".lower()
            if song_filters and not any(q.lower() in hay for q in song_filters):
                continue
            render = os.path.join(SONGS, sid, "auto-render")
            stems = [(stem, fn, nm, bus, pan) for stem, fn, nm, bus, pan in ROUTING
                     if os.path.exists(os.path.join(render, stem + ".wav"))]
            if not any(x[0] == "click" for x in stems):
                print(f"  ! SKIP {sid}: no auto-render/click.wav")
                continue
            members.append(sid)
            songs.setdefault(sid, {
                "sid": sid, "title": s.get("title") or sid, "artist": s.get("artist") or "",
                "render": render, "stems": stems, "clip": clips.get(sid), "bpm": song_bpm(sid),
            })
        if members:
            playlists.append((PL_PREFIX + name, members))
    return songs, playlists


def app_running():
    return bool(subprocess.run(["pgrep", "-f", "Stage Traxx 4.app"],
                               capture_output=True).stdout.strip())


def backup(db):
    os.makedirs(BACKUPS, exist_ok=True)
    dst = os.path.join(BACKUPS, "music_library-" +
                       datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + ".sqlite")
    src, out = sqlite3.connect(db), sqlite3.connect(dst)
    src.backup(out)
    out.close(); src.close()
    return dst


def upsert_song(c, info, docs, channel):
    folder = safe_dir(info["sid"])
    dest = os.path.join(docs, folder)
    os.makedirs(dest, exist_ok=True)
    converted = 0
    for stem, fn, _nm, _bus, _pan in info["stems"]:
        converted += downmix(os.path.join(info["render"], stem + ".wav"), os.path.join(dest, fn))
    wanted = {fn for _s, fn, *_ in info["stems"]}
    for f in os.listdir(dest):                       # a stem that left the render leaves the rig
        if f.endswith(".wav") and f not in wanted and any(f == r[1] for r in ROUTING):
            os.remove(os.path.join(dest, f))
    dur = wav_duration(os.path.join(dest, "1_Click.wav"))
    t = now()
    mark = MARK + info["sid"]
    block = midi_block(info["clip"], channel)
    row = c.execute("SELECT id, lyrics FROM song WHERE notes=?", (mark,)).fetchone()
    if row:
        sid = row[0]
        c.execute("""UPDATE song SET title=?, artist=?, duration=?, bpm=?, endTime=?, lyrics=?,
                     metronomeMode=0, lastModified=? WHERE id=?""",
                  (info["title"], info["artist"], dur, info["bpm"], dur,
                   merge_lyrics(row[1], block), t, sid))
        c.execute("DELETE FROM track WHERE songID=?", (sid,))
    else:
        sid = uuid.uuid4().bytes
        c.execute("""INSERT INTO song (id,title,artist,added,duration,bpm,year,notes,color,volume,
          speed,pitch,tune,chordTranspose,pitchToChords,fadeIn,fadeOut,startTime,endTime,fontSize,
          lyrics,pdfPath,metronomeMode,metronomeType,playCount,lastPlayed,lastModified,
          timecodeOffset,midiCmd,midiPath,scrollSpeed,folderID,key,waveformTrackID)
          VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                  (sid, info["title"], info["artist"], t, dur, info["bpm"], None, mark, 3, 0.0,
                   1.0, 0, 0, 0, 0, 0.0, 0.0, 0.0, dur, 32,
                   merge_lyrics("", block), None, 0, 2, 0, None, t,
                   0.0, None, None, 1.2, None, None, None))
    for n, (_stem, fn, nm, bus, pan) in enumerate(info["stems"], 1):
        c.execute("""INSERT INTO track (id,songID,filePath,duration,volume,pan,mute,bus,number,
          hasMarkers,equalizer,lastModified,name,color,transpose,muteGroupMask)
          VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                  (uuid.uuid4().bytes, sid, f"{folder}/{fn}", dur, 0.0, pan, 0, bus, n,
                   0, EQ, t, nm, 0, 1, 0))
    return sid, converted, bool(row)


def write_playlists(c, playlists, ids):
    t = now()
    for name, members in playlists:
        row = c.execute("SELECT id FROM playlist WHERE name=?", (name,)).fetchone()
        if row:
            pid = row[0]
            c.execute("DELETE FROM playlistSong WHERE playlistID=?", (pid,))
        else:
            pid = uuid.uuid4().bytes
            c.execute("""INSERT INTO playlist (id,name,added,autoplay,color,volume,lastModified,
              folderID) VALUES (?,?,?,?,?,?,?,?)""", (pid, name, t, 0, 3, 0.0, t, None))
        for order, sid in enumerate(members):
            c.execute("""INSERT INTO playlistSong (id,songID,playlistID,added,playbackMode,
              sortOrder,lastModified) VALUES (?,?,?,?,?,?,?)""",
                      (uuid.uuid4().bytes, ids[sid], pid, t, 0, order, t))


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("songs", nargs="*", help="only songs whose folder/title contains this")
    ap.add_argument("--set", dest="set_filter", help="only sets whose name contains this")
    ap.add_argument("--apply", action="store_true", help="write (default: dry-run)")
    ap.add_argument("--quit", action="store_true", help="quit Stage Traxx 4 before writing")
    ap.add_argument("--launch", action="store_true", help="open Stage Traxx 4 afterwards")
    ap.add_argument("--channel", type=int, default=1, help="MIDI channel of the PC (default 1)")
    ap.add_argument("--db", default=DB, help=argparse.SUPPRESS)      # tests: point at a copy
    ap.add_argument("--docs", default=DOCS, help=argparse.SUPPRESS)
    a = ap.parse_args()

    songs, playlists = plan(load_setlist(), load_clips(), a.songs, a.set_filter)
    if not songs:
        sys.exit("nothing matched")
    partial = bool(a.songs)       # a song filter never rewrites playlists (they'd shrink)

    for info in songs.values():
        stems = " ".join(nm for _s, _f, nm, *_ in info["stems"]).replace("PB ", "pb-")
        clip = f"PC{info['clip']:<3}" if info["clip"] is not None else "no-clip"
        print(f"  {clip}  {info['bpm']:6.1f}  {info['artist']} - {info['title']}   [{stems}]")
    noclip = [i["title"] for i in songs.values() if i["clip"] is None]
    print(f"\n{len(songs)} songs, {len(playlists)} playlists"
          + (" (playlists untouched: song filter)" if partial else ""))
    if noclip:
        print(f"no lyric clip (START/STOP only, no PC): {', '.join(noclip)}")
    if not a.apply:
        print("\ndry-run — nothing written. Re-run with --apply.")
        return

    live = os.path.abspath(a.db) == os.path.abspath(DB)
    if live and app_running():
        if not a.quit:
            sys.exit("Stage Traxx 4 is running — close it or pass --quit.")
        subprocess.run(["osascript", "-e", 'tell application "Stage Traxx 4" to quit'])
        for _ in range(20):
            if not app_running():
                break
            time.sleep(0.5)
        else:
            sys.exit("Stage Traxx 4 did not quit.")
    print("backup:", backup(a.db))

    con = sqlite3.connect(a.db)
    con.execute("PRAGMA foreign_keys=ON")
    c = con.cursor()
    ids, conv, new = {}, 0, 0
    try:
        for info in songs.values():
            sid, n, existed = upsert_song(c, info, a.docs, a.channel)
            ids[info["sid"]] = sid
            conv += n
            new += not existed
        if not partial:
            write_playlists(c, playlists, ids)
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()
    print(f"written: {len(songs)} songs ({new} new), {conv} stems converted"
          + ("" if partial else f", {len(playlists)} playlists"))
    if a.launch and live:
        subprocess.run(["open", "/Applications/Stage Traxx 4.app"])


if __name__ == "__main__":
    main()
