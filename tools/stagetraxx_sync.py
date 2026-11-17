#!/usr/bin/env python3
"""Sync the band's auto-renders into the Stage Traxx 4 library (playback rig without MainStage).

For every song of the setlist (web/songs.json) builds/updates a Stage Traxx song:

    Click     bus 1   (in-ears)
    Cues      bus 2   (in-ears)
    PB Other  bus 3   (front of house; keys live here too)
    PB Bass   bus 4   (front of house)
    Drums     bus 3   MUTED (practice: unmute in the mixer to hear the drum kit)
    Vocals    bus 3   MUTED (practice: lead vocal)
    All       bus 3   MUTED (practice: auto-render/all.wav, the whole song in the band key)

Mute group 1 = all tracks but All, group 2 = all but All/Click/Cues (MUTE_GROUPS).

One track per bus, every pan centred; WHERE a bus plays is Stage Traxx's per-device output
map (prefs audio_busDeviceSettings), not the song: the rehearsal Rubix24 sends buses 1-4 to
its mono outputs 1-4 (four separate signals for the mixer), the home FLOW 8 sends buses 1+2 to
USB pair 1/2 and 3+4 to pair 3/4 so everything is heard in both ears (wiki stagetraxx-rig).
Stems are DOWNMIXED TO MONO on the way in.

MIDI for the lyric launcher goes into the song's lyrics field (the only per-song
outbound MIDI Stage Traxx 4 has):

    [midi: PC<clip>@<ch>]     song load  -> launcher ARMS clip NN
    [midi@play: START]        play       -> launcher rolls from 0
    [midi@stop: STOP]         stop       -> launcher freezes

clip NN comes from tools/lyric-launcher/songs.tsv. Stage Traxx sends to all MIDI
ports, so the launcher's virtual `LyricLauncher` port gets it (start launcher first).

BOSS GM-800 scenes (wiki/pipelines/gm-800.md) come from mix.json "gm800", on channel 2
(GM-800 Scene Rx Channel; the launcher's ch1 PCs don't touch it):

    "gm800": 1                                   whole song on one scene (1 = MUTE)
    "gm800": [{"bar": 1, "scene": 7},            scene changes; jamzone_render.py (full
              {"bar": 17, "scene": 8}, ...]      render or --check) writes each "abs_sec"

    [midi: PC6@2]               song load   -> start scene 7 (tag number = scene - 1, verified)
    [midi@00:00.00: PC6@2]      t=0         -> again, since the load tag doesn't repeat on replay
    [midi@00:31.304: PC7@2]     each change -> at its render second
No "gm800" key -> no GM-800 tags (the unit keeps whatever scene it is on).

GM-800 ASSIGN CCs (a CTL switch can't be pressed over MIDI; a scene ASSIGN with SOURCE = CC#n
does the same job — wiki gm-800 «CTL-кнопки и MIDI») come from mix.json "gm800_cc", on the
GM-800 channel, PODGO_LEAD early like POD Go changes:

    "gm800_cc": [{"bar": 1, "cc": 80, "value": 0},      first event per CC = start state
                 {"bar": 17, "cc": 80, "value": 127}]   (sent on load and at 00:00)

Line 6 POD Go presets (wiki/pipelines/pod-go.md) come from mix.json "podgo", on channel 3
(POD Go MIDI Base Channel; on ch1 it would follow the launcher's PCs):

    "podgo": "02A"                               whole song on one preset
    "podgo": [{"bar": 1, "preset": "02A"},       preset changes, timed by jamzone_render.py
              {"bar": 33, "preset": "03C"}, ...]

    preset 02A = PC4 (bank-1)*4 + A..D (verified). Same tags as the GM-800, but every change
    goes out PODGO_LEAD (200 ms) BEFORE the marked bar so the new preset is already up on it.

Song notes from the setlist dashboard (web/data/dashboard.db — the local board at
localhost:5173, same source as tools/stage_sheet.py) go under the MIDI tags, so they show in
the lyrics area. The sync owns that text: edit notes on the board, not in Stage Traxx (text
typed there is replaced on the next sync; dry-run flags it). No dashboard DB -> the songs'
existing text is kept.

Regions (Stage Traxx song sections: double-tap = seek, "Jump to Next Region") are generated
from the mix.json cues: one per cue, named '<bar> · <cue text>', starting at the cue's snap_sec
(1 bar before its first spoken word) so a jump replays the cue, then the section. The sync owns
the regions of its songs: hand-made regions of a synced song are replaced.

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
    ("click",    "1_Click.wav",    "Click",    0, 0.0),
    ("cues",     "2_Cues.wav",     "Cues",     1, 0.0),
    ("pb-other", "3_PB_Other.wav", "PB Other", 2, 0.0),
    ("pb-bass",  "4_PB_Bass.wav",  "PB Bass",  3, 0.0),
    ("drums",    "5_Drums.wav",    "Drums",    2, 0.0),     # practice: same bus as PB Other,
    ("vocal",    "6_Vocals.wav",   "Vocals",   2, 0.0),     # MUTED by default (see MUTED)
    ("all",      "7_All.wav",      "All",      2, 0.0),     # full band-key mix, MUTED by default
]
# Where a stem comes from inside auto-render/ (default <stem>.wav). drums/vocal are the render's
# per-category site stems (stems/*.mp3: same timeline as click.wav, sample-exact; drums = the kit
# only, percussion is never rendered; vocal = lead vocal, pitched to the band key).
SOURCES = {"drums": "stems/drums.mp3", "vocal": "stems/vocal.mp3"}
# Tracks written muted: drummer/singer play these live. Unmute in the Stage Traxx mixer to
# practise without them; every sync writes them muted again (bus 3 = front of house at a gig).
MUTED = {"drums", "vocal", "all"}
# Mute groups (Stage Traxx mixer, master section; global across songs): track bitmask, bit 0 =
# group 1. Group 1 = everything but All -> only the full mix plays; group 2 = the playback parts
# All already contains (not Click/Cues) -> full mix + click + cues. To listen to the song: unmute
# All in the mixer, then press 1 or 2.
MUTE_GROUPS = {"click": 0b01, "cues": 0b01, "pb-other": 0b11, "pb-bass": 0b11,
               "drums": 0b11, "vocal": 0b11, "all": 0}


def stem_src(render, stem):
    return os.path.join(render, SOURCES.get(stem, stem + ".wav"))


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


GM_CHANNEL = 2          # BOSS GM-800 Scene Rx Channel
PODGO_CHANNEL = 3       # Line 6 POD Go MIDI Base Channel (1 = launcher, 2 = GM-800)
PODGO_LEAD = 0.200      # POD Go switches this long BEFORE the marked bar (Alex, 2026-11-17)


def gm800_pc(scene):
    """GM-800 scene 1..128 -> PC number. Stage Traxx sends the raw number, the unit shows it +1."""
    if not isinstance(scene, int) or isinstance(scene, bool) or not 1 <= scene <= 128:
        raise ValueError('"scene" must be 1..128')
    return scene - 1


def podgo_pc(preset):
    """POD Go preset '01A'..'32D' -> PC number: 4 presets per bank (PC4 = 02A, verified)."""
    m = re.fullmatch(r"(\d{1,2})([A-Da-d])", preset) if isinstance(preset, str) else None
    if not m or not 1 <= int(m[1]) <= 32:
        raise ValueError('"preset" must be 01A..32D')
    return (int(m[1]) - 1) * 4 + "ABCD".index(m[2].upper())


# mix.json key -> how its entries become Program Changes. "whole" = type of the one-value form
# (whole song on one scene/preset); "lead" = how much earlier than the bar a change is sent.
DEVICES = {
    "gm800": {"name": "GM-800", "field": "scene", "whole": int, "pc": gm800_pc,
              "channel": GM_CHANNEL, "lead": 0.0},
    "podgo": {"name": "POD Go", "field": "preset", "whole": str, "pc": podgo_pc,
              "channel": PODGO_CHANNEL, "lead": PODGO_LEAD},
}


GM_CC_LEAD = PODGO_LEAD   # GM-800 ASSIGN CCs: also a bit before the bar (part on before the note)


def parse_cc(v):
    """mix.json "gm800_cc" -> [(render_sec, cc, value), ...] sorted by time, None when absent.
    CC numbers are the ones a GM-800 ASSIGN SOURCE accepts (1-31, 64-95), minus 71-79 (the
    unit's own tone-modify CCs)."""
    if v is None:
        return None
    if not isinstance(v, list) or not v:
        raise ValueError(f'"gm800_cc" must be a non-empty list, got {v!r}')
    out = []
    for e in v:
        cc = e.get("cc") if isinstance(e, dict) else None
        val = e.get("value") if isinstance(e, dict) else None
        if not isinstance(cc, int) or isinstance(cc, bool) or not (1 <= cc <= 31 or 64 <= cc <= 95) \
                or 71 <= cc <= 79:
            raise ValueError(f"gm800_cc entry {e!r}: \"cc\" must be 1..31 or 64..95 (not 71..79)")
        if not isinstance(val, int) or isinstance(val, bool) or not 0 <= val <= 127:
            raise ValueError(f'gm800_cc entry {e!r}: "value" must be 0..127')
        if "abs_sec" not in e:
            raise ValueError(f"gm800_cc entry {e!r} has no abs_sec — run jamzone_render.py --check")
        out.append((float(e["abs_sec"]), cc, val))
    if any(b[0] < a[0] for a, b in zip(out, out[1:])):
        raise ValueError("gm800_cc entries are not in time order")
    return out


def cc_block(events, channel, lead=GM_CC_LEAD):
    """[(sec, cc, value)] -> tags. Each CC's first event is its start state: on load AND at
    00:00 (after the scene PC, so it lands on the freshly loaded scene); later events at
    sec - lead; a value the CC already has is dropped."""
    if not events:
        return []
    start = {}
    for _sec, cc, val in events:
        start.setdefault(cc, val)
    lines = [f"[midi: CC{cc}.{v}@{channel}]" for cc, v in start.items()]
    lines += [f"[midi@00:00.000: CC{cc}.{v}@{channel}]" for cc, v in start.items()]
    cur, seen = dict(start), set()
    for sec, cc, val in events:
        if cc not in seen:                 # the start event itself
            seen.add(cc)
        elif cur[cc] != val:
            lines.append(f"[midi@{mmss(max(0.0, sec - lead))}: CC{cc}.{val}@{channel}]")
            cur[cc] = val
    return lines


def song_devices(sid):
    """mix.json device keys -> ({key: [(render_sec, pc, label), ...]}, {key: error})."""
    try:
        with open(os.path.join(SONGS, sid, "mix.json"), encoding="utf-8") as f:
            mix = json.load(f)
    except (OSError, ValueError):
        return {}, {}
    out, err = {}, {}
    for key in DEVICES:
        try:
            ch = parse_device(key, mix.get(key))
        except ValueError as e:
            err[key] = str(e)
            continue
        if ch:
            out[key] = ch
    try:
        cc = parse_cc(mix.get("gm800_cc"))
    except ValueError as e:
        err["gm800_cc"] = str(e)
    else:
        if cc:
            out["gm800_cc"] = cc
    return out, err


def parse_device(key, v):
    """mix.json "<key>" value -> [(render_sec, pc, label), ...] (first = start), None when absent.
    Raises ValueError with a readable reason when the entry is malformed or not timed yet."""
    if v is None:
        return None
    d = DEVICES[key]
    field = d["field"]
    if isinstance(v, d["whole"]) and not isinstance(v, bool):
        v = [{field: v, "abs_sec": 0.0}]
    if not isinstance(v, list) or not v:
        raise ValueError(f'"{key}" must be one {field} or a non-empty list, got {v!r}')
    out = []
    for e in v:
        try:
            pc = d["pc"](e.get(field) if isinstance(e, dict) else None)
        except ValueError as x:
            raise ValueError(f"{key} entry {e!r}: {x}") from None
        if "abs_sec" not in e:
            raise ValueError(f"{key} entry {e!r} has no abs_sec — run jamzone_render.py --check")
        out.append((float(e["abs_sec"]), pc, e[field]))
    if any(b[0] < a[0] for a, b in zip(out, out[1:])):
        raise ValueError(f"{key} entries are not in time order")
    return out


# Stage Traxx color index: highlight primary red orange yellow green teal blue purple pink gray
# black white clear (case order in the binary; confirmed on screen: 6 = teal-blue, 10 = gray).
RED, YELLOW, GREEN, BLUE, GRAY = 2, 4, 5, 7, 10
REGION_NEXT = 0                # RegionPlaybackMode: next(0) loop loopOnce stop skip — plain playback


def region_color(text):
    """Section type from the cue text: stop red · solo yellow · chorus green · verse blue ·
    anything else (all in, bridge, end, ...) one neutral gray. 'stop' = last word, as in the
    cue renderer, so 'stop and solo' is a solo and 'end stop' a stop."""
    t = text.lower()
    words = t.replace("-", " ").split()
    if words and words[-1] == "stop":
        return RED
    if "solo" in t or "соло" in t:
        return YELLOW
    if "chorus" in t or "припев" in t:
        return GREEN
    if "verse" in t or "куплет" in t:
        return BLUE
    return GRAY


def song_cues(sid):
    try:
        with open(os.path.join(SONGS, sid, "mix.json"), encoding="utf-8") as f:
            return json.load(f).get("cues") or []
    except (OSError, ValueError):
        return []


def cue_regions(cues, duration):
    """mix.json cues -> Stage Traxx regions [(name, start, end, color)]. A region starts at the cue's
    snap_sec (1 bar before its first spoken word — the web player's seek point), so jumping to it
    replays the whole spoken cue and then the section; abs_sec when there is no snap. Name =
    '<bar>[.<beat>] · <cue text>'. Regions tile the song: each ends where the next starts, the last
    at the song end; time before the first one becomes 'count-in'. Cues without abs_sec (not
    rendered yet) and starts that don't move forward are skipped."""
    pts = []
    for c in cues:
        if "abs_sec" not in c:
            continue
        start = float(c.get("snap_sec", c["abs_sec"]))
        if pts and start <= pts[-1][1]:
            start = float(c["abs_sec"])
            if start <= pts[-1][1]:
                continue
        beat = c.get("beat", 1)
        pos = f"{c['bar']}" + ("" if str(beat) in ("1", "1.0") else f".{beat}")
        pts.append((f"{pos} · {c['text']}"[:64], start, region_color(c["text"])))
    if not pts or pts[0][1] >= duration:
        return []
    if pts[0][1] > 1.0:
        pts.insert(0, ("count-in", 0.0, GRAY))
    ends = [p[1] for p in pts[1:]] + [duration]
    return [(n, s, e, col) for (n, s, col), e in zip(pts, ends) if e > s]


def write_regions(c, song_id, regions, t):
    c.execute("DELETE FROM region WHERE songID=?", (song_id,))
    for name, start, end, color in regions:
        c.execute("""INSERT INTO region (id,songID,name,startTime,endTime,color,playbackMode,
          lastModified) VALUES (?,?,?,?,?,?,?,?)""",
                  (uuid.uuid4().bytes, song_id, name, start, end, color, REGION_NEXT, t))


def mmss(sec):
    """Stage Traxx timed-tag clock: MM:SS.mmm (two-digit minutes, as its parser expects)."""
    ms = max(0, round(sec * 1000))
    m, rem = divmod(ms, 60000)
    return f"{m:02d}:{rem / 1000:06.3f}"


def device_block(changes, channel, lead=0.0):
    """[(sec, pc, label)] -> Stage Traxx tags. The start program goes out on load AND at 00:00
    (the load tag doesn't fire again when the song is replayed without reloading); every later
    change at sec - lead (POD Go: early, so the new preset is up on the bar); a change to the
    program already active is dropped (re-selecting it mid-song would only risk a glitch)."""
    if not changes:
        return []
    cur = changes[0][1]
    lines = [f"[midi: PC{cur}@{channel}]", f"[midi@00:00.000: PC{cur}@{channel}]"]
    for sec, pc, _label in changes[1:]:
        if pc != cur:
            lines.append(f"[midi@{mmss(max(0.0, sec - lead))}: PC{pc}@{channel}]")
            cur = pc
    return lines


def devices_block(devices, channels):
    return [ln for key, d in DEVICES.items()
            for ln in device_block(devices.get(key), channels.get(key, d["channel"]), d["lead"])] \
        + cc_block(devices.get("gm800_cc"), channels.get("gm800", GM_CHANNEL))


def lyrics_text(lyrics):
    """The non-MIDI text of a lyrics field (what Stage Traxx shows), leading blank lines dropped."""
    keep = [l for l in (lyrics or "").splitlines() if not l.strip().lower().startswith("[midi")]
    while keep and not keep[0].strip():
        keep.pop(0)
    return "\n".join(keep).rstrip()


def merge_lyrics(old, block, note=None):
    """Our MIDI tags first, then the dashboard note; note=None (no dashboard DB) keeps whatever
    non-MIDI text the song already had."""
    text = lyrics_text(old) if note is None else note
    return "\n".join(block + (["", text] if text else []))


DASH_DB = os.path.join(REPO, "web", "data", "dashboard.db")


def clean_note(text):
    """Stage-sheet cleanup: trimmed lines, blank lines and consecutive duplicates dropped."""
    out = []
    for ln in (text or "").splitlines():
        ln = ln.strip()
        if ln and (not out or ln != out[-1]) and not ln.lower().startswith("[midi"):
            out.append(ln)
    return "\n".join(out)


def load_web_notes(path=DASH_DB):
    """Dashboard notes -> {sid: text}, or None when the DB is missing/unreadable. A stray
    'NOFOLDER:<sid>' record (song added on the board before its folder existed) is merged in."""
    try:
        con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        try:
            raw = con.execute("SELECT data FROM app_state").fetchone()[0]
        finally:
            con.close()
        recs = json.loads(raw).get("songs") or {}
    except (sqlite3.Error, TypeError, ValueError):
        return None
    out = {}
    for key, rec in recs.items():
        sid = key[len("NOFOLDER:"):] if key.startswith("NOFOLDER:") else key
        note = clean_note((rec or {}).get("notes"))
        if note and note not in out.get(sid, ""):
            out[sid] = clean_note(out[sid] + "\n" + note) if sid in out else note
    return out


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


def live_bass(sid):
    """True when pb-bass carries a live-played bass layer (file name contains "живой бас")."""
    try:
        mix = json.load(open(os.path.join(SONGS, sid, "mix.json")))
    except (OSError, ValueError):
        return False
    layers = (mix.get("pb-bass") or {}).get("layers") or []
    return any("живой бас" in (l if isinstance(l, str) else l.get("file", "")) for l in layers)


def plan(sets, clips, song_filters, set_filter, notes=None):
    """-> (songs {sid: info}, playlists [(name, [sid...])]). notes = load_web_notes() result."""
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
                     if os.path.exists(stem_src(render, stem))]
            if live_bass(sid):                 # concert/live-played bass in pb-bass -> visible on stage
                stems = [(st_, fn, nm + " · живой бас" if st_ == "pb-bass" else nm, bus, pan) for st_, fn, nm, bus, pan in stems]
            if not any(x[0] == "click" for x in stems):
                print(f"  ! SKIP {sid}: no auto-render/click.wav")
                continue
            members.append(sid)
            if sid not in songs:
                devices, dev_err = song_devices(sid)
                songs[sid] = {
                    "sid": sid, "title": s.get("title") or sid, "artist": s.get("artist") or "",
                    "render": render, "stems": stems, "clip": clips.get(sid), "bpm": song_bpm(sid),
                    "devices": devices, "dev_err": dev_err,
                    "note": None if notes is None else notes.get(sid, ""),
                }
        if members:
            playlists.append((PL_PREFIX + name, members))
    return songs, playlists


def current_texts(db):
    """{sid: shown text} of the synced songs now in the library (read-only; {} if unreadable)."""
    try:
        con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        try:
            rows = con.execute("SELECT notes, lyrics FROM song WHERE notes LIKE ?",
                               (MARK + "%",)).fetchall()
        finally:
            con.close()
    except sqlite3.Error:
        return {}
    return {n[len(MARK):]: lyrics_text(l) for n, l in rows}


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


def upsert_song(c, info, docs, channel, dev_channels=None):
    folder = safe_dir(info["sid"])
    dest = os.path.join(docs, folder)
    os.makedirs(dest, exist_ok=True)
    converted = 0
    for stem, fn, _nm, _bus, _pan in info["stems"]:
        converted += downmix(stem_src(info["render"], stem), os.path.join(dest, fn))
    wanted = {fn for _s, fn, *_ in info["stems"]}
    for f in os.listdir(dest):                       # a stem that left the render leaves the rig
        if f.endswith(".wav") and f not in wanted and any(f == r[1] for r in ROUTING):
            os.remove(os.path.join(dest, f))
    dur = wav_duration(os.path.join(dest, "1_Click.wav"))
    t = now()
    mark = MARK + info["sid"]
    block = midi_block(info["clip"], channel) + devices_block(info.get("devices") or {}, dev_channels or {})
    row = c.execute("SELECT id, lyrics FROM song WHERE notes=?", (mark,)).fetchone()
    if row:
        sid = row[0]
        c.execute("""UPDATE song SET title=?, artist=?, duration=?, bpm=?, endTime=?, lyrics=?,
                     metronomeMode=0, lastModified=? WHERE id=?""",
                  (info["title"], info["artist"], dur, info["bpm"], dur,
                   merge_lyrics(row[1], block, info.get("note")), t, sid))
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
                   merge_lyrics("", block, info.get("note")), None, 0, 2, 0, None, t,
                   0.0, None, None, 1.2, None, None, None))
    write_regions(c, sid, cue_regions(song_cues(info["sid"]), dur), t)
    for n, (stem, fn, nm, bus, pan) in enumerate(info["stems"], 1):
        c.execute("""INSERT INTO track (id,songID,filePath,duration,volume,pan,mute,bus,number,
          hasMarkers,equalizer,lastModified,name,color,transpose,muteGroupMask)
          VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                  (uuid.uuid4().bytes, sid, f"{folder}/{fn}", dur, 0.0, pan, int(stem in MUTED), bus, n,
                   0, EQ, t, nm, 0, 1, MUTE_GROUPS.get(stem, 0)))
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
    ap.add_argument("--gm-channel", type=int, default=GM_CHANNEL,
                    help=f"GM-800 Scene Rx Channel (default {GM_CHANNEL})")
    ap.add_argument("--podgo-channel", type=int, default=PODGO_CHANNEL,
                    help=f"POD Go MIDI Base Channel (default {PODGO_CHANNEL})")
    ap.add_argument("--db", default=DB, help=argparse.SUPPRESS)      # tests: point at a copy
    ap.add_argument("--docs", default=DOCS, help=argparse.SUPPRESS)
    a = ap.parse_args()

    notes = load_web_notes()
    if notes is None:
        print(f"  ! no dashboard notes ({DASH_DB}) — songs keep their current text")
    songs, playlists = plan(load_setlist(), load_clips(), a.songs, a.set_filter, notes)
    shown = current_texts(a.db)
    if not songs:
        sys.exit("nothing matched")
    partial = bool(a.songs)       # a song filter never rewrites playlists (they'd shrink)

    for info in songs.values():
        stems = " ".join(nm for _s, _f, nm, *_ in info["stems"]).replace("PB ", "pb-")
        clip = f"PC{info['clip']:<3}" if info["clip"] is not None else "no-clip"
        gm = ""
        for key, ch in info["devices"].items():
            if key == "gm800_cc":
                seen = set()
                parts = []
                for t, c, v in ch:                 # first event of a CC = start state (load/00:00)
                    parts.append(f"{c}={v}" if c not in seen else
                                 f"{c}={v}@{mmss(max(0.0, t - GM_CC_LEAD))[:-4]}")
                    seen.add(c)
                gm += "  GM-800 CC " + " → ".join(parts)
                continue
            gm += f"  {DEVICES[key]['name']} " + " → ".join(
                f"{lb}@{mmss(max(0.0, t - DEVICES[key]['lead']))[:-4]}" if i else str(lb)
                for i, (t, _pc, lb) in enumerate(ch))
        nreg = len(cue_regions(song_cues(info["sid"]),
                               wav_duration(os.path.join(info["render"], "click.wav"))))
        nt = f"  notes {len(info['note'].splitlines())}" if info["note"] else ""
        print(f"  {clip}  {info['bpm']:6.1f}  {info['artist']} - {info['title']}   [{stems}]"
              f"  reg {nreg}{gm}{nt}")
        old = shown.get(info["sid"])
        if info["note"] is not None and old and old != info["note"]:
            print("     ~ text in Stage Traxx differs from the board note -> replaced")
        for key, e in info["dev_err"].items():
            print(f"     ! {DEVICES.get(key, {}).get('name', key)} tags skipped: {e}")
    bad = [f"{i['title']} ({'/'.join(i['dev_err'])})" for i in songs.values() if i["dev_err"]]
    if bad and a.apply:
        sys.exit(f"fix mix.json first: {', '.join(bad)}")
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
            sid, n, existed = upsert_song(c, info, a.docs, a.channel,
                                          {"gm800": a.gm_channel, "podgo": a.podgo_channel})
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
