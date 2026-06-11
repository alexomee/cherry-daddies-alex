#!/usr/bin/env python3
"""
JamZone per-track loudness normalizer — balances playback level INSIDE the app.

JamZone's live mixer is persisted in a Realm DB:
    ~/Library/Containers/com.recisio.jamzone.ios/Data/Library/Application Support/default.realm
Class `JamPreset` (primaryKey = song id == the cat_<id> number) holds
`tracks: list<TrackPreset>`, and each TrackPreset has `volume: double` (the fader
gain, unity = 1.0, fader maxes at 1.0 so only attenuation is possible), `isMuted`,
`isSolo`. The `volume` in the per-song tracks.json is a download default the app
IGNORES — the Realm preset is what actually drives playback (verified empirically).

Servers ship every track at volume 1.0, so soloing the "same" stem across songs
lurches in level (Drum Kit measured -15 / -11 / -22 LUFS across three songs = 11 dB).
This tool measures each stem's integrated LUFS and writes each track's `volume` so
every track lands at one target loudness (attenuate-only: turn loud tracks DOWN to
the target; leave tracks already quieter than the target at unity). Then whichever
1-2 stems you un-mute play at a consistent level across the whole library.

Only `volume` is written — `isMuted`/`isSolo` are preserved, and the metronome
(click) track is left untouched. Quit JamZone before applying (Realm is single-writer;
the tool quits it for you). The Realm is backed up before the first write; `restore`
reverts. Re-run `apply` after downloading new songs.

Realm I/O is done by node helpers in scripts/realm-tools/ (RealmJS). The file format
(v24) matches what JamZone writes, so writes don't upgrade/break the app's DB.

Usage:
  jamzone_normalize.py measure [<query>|--all] [--force]   # measure + cache LUFS
  jamzone_normalize.py plan    [<query>|--all] [--target T] # preview volumes
  jamzone_normalize.py apply   [<query>|--all] [--target T] # write Realm (default --all)
  jamzone_normalize.py status  [<query>|--all]              # read back Realm volumes
  jamzone_normalize.py restore                              # revert Realm from backup
Options: --target T  (target integrated LUFS, default -20)
         --min-gain g (floor linear gain, default 0.05)
Query matches artist or title (case-insensitive substring); default scope is --all.
"""
import os, sys, json, hashlib, subprocess, shutil, tempfile, re
from concurrent.futures import ThreadPoolExecutor

HOME = os.path.expanduser("~")
JAMS = (f"{HOME}/Library/Containers/com.recisio.jamzone.ios/Data/Library/"
        "Application Support/com.recisio.jamzone.ios/jams")
REALM = (f"{HOME}/Library/Containers/com.recisio.jamzone.ios/Data/Library/"
         "Application Support/default.realm")
RTOOLS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "realm-tools")
CACHE = f"{HOME}/projects/cherry-daddies/music/songs/.loudness_cache.json"
BACKUP = f"{HOME}/projects/cherry-daddies/music/songs/.realm-original.bak"   # immutable first backup
DEFAULT_TARGET = -20.0


# ---- crypto (mirrors jamzone_extract.py) ----
def key_for(cat):
    return hashlib.md5(cat.encode()).hexdigest().encode().hex()

def dec(data, key):
    return subprocess.run(
        ["openssl", "enc", "-aes-256-cbc", "-d", "-K", key, "-iv", data[:16].hex()],
        input=data[16:], capture_output=True).stdout

def en(v):
    return v.get("en") if isinstance(v, dict) else v


# ---- song discovery ----
def iter_songs():
    for cat in sorted(os.listdir(JAMS)):
        d = os.path.join(JAMS, cat)
        sjp = os.path.join(d, "song.json")
        if not os.path.isfile(sjp):
            continue
        key = key_for(cat)
        try:
            song = json.loads(dec(open(sjp, "rb").read(), key))
        except Exception:
            continue
        yield cat, key, song

def label_of(song):
    return f"{en(song.get('artist'))} - {song.get('title')}"

def tracks_of(cat, key):
    return json.loads(dec(open(os.path.join(JAMS, cat, "tracks.json"), "rb").read(), key))

def select(args):
    if "--all" in args or not any(a for a in args if not a.startswith("-")):
        return list(iter_songs())
    q = next(a for a in args if not a.startswith("-")).lower()
    hits = [t for t in iter_songs() if q in label_of(t[2]).lower()]
    if not hits:
        sys.exit(f"No song matches. Try: jamzone_extract.py list")
    return hits


# ---- loudness ----
def load_cache():
    try:
        return json.load(open(CACHE))
    except Exception:
        return {}

def save_cache(c):
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    json.dump(c, open(CACHE, "w"), indent=0)

def measure_stem(cat, key, filename):
    raw = open(os.path.join(JAMS, cat, filename), "rb").read()
    with tempfile.NamedTemporaryFile(suffix=".m4a", delete=False) as t:
        tmp = t.name
        t.write(dec(raw, key))
    try:
        r = subprocess.run(
            ["ffmpeg", "-hide_banner", "-nostats", "-i", tmp,
             "-af", "loudnorm=print_format=json", "-f", "null", "-"],
            capture_output=True, text=True)
        m = re.search(r'"input_i"\s*:\s*"([-0-9.]+)"', r.stderr)
        return float(m.group(1)) if m else None
    finally:
        os.unlink(tmp)

def measure_song(cat, key, cache, force=False):
    tracks = tracks_of(cat, key)
    todo = [t for t in tracks
            if not t.get("click") and (force or t["filename"] not in cache)]
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(measure_stem, cat, key, t["filename"]): t for t in todo}
        for fu, t in futs.items():
            L = fu.result()
            if L is not None:
                cache[t["filename"]] = L
    return tracks


# ---- played-mix loudness (real mixdown of the audible stems) ----
def played_mix_lufs(cat, key, audible):
    """audible = [(filename, stem_volume)]; returns integrated LUFS of their sum."""
    tmps, inputs, fc = [], [], []
    try:
        for i, (fn, vol) in enumerate(audible):
            raw = open(os.path.join(JAMS, cat, fn), "rb").read()
            t = tempfile.NamedTemporaryFile(suffix=".m4a", delete=False)
            t.write(dec(raw, key)); t.close()
            tmps.append(t.name); inputs += ["-i", t.name]
            fc.append(f"[{i}:a]volume={vol}[a{i}]")
        lab = "".join(f"[a{i}]" for i in range(len(audible)))
        fc.append(f"{lab}amix=inputs={len(audible)}:normalize=0,"
                  f"loudnorm=print_format=json[m]")
        cmd = (["ffmpeg", "-hide_banner", "-nostats"] + inputs +
               ["-filter_complex", ";".join(fc), "-map", "[m]", "-f", "null", "-"])
        r = subprocess.run(cmd, capture_output=True, text=True)
        m = re.search(r'"input_i"\s*:\s*"([-0-9.]+)"', r.stderr)
        return float(m.group(1)) if m else None
    finally:
        for t in tmps:
            os.unlink(t)


# ---- gain planning (attenuate-only) ----
def opt(args, flag, default, cast=float):
    return cast(args[args.index(flag) + 1]) if flag in args else default

def plan_song(cat, key, cache, target, min_gain):
    """Return (rows, edits_map). rows=[(name,lufs,vol)]; edits_map={idx:vol}."""
    tracks = tracks_of(cat, key)
    rows, edits = [], {}
    for idx, t in enumerate(tracks):
        name = en(t.get("descriptions")) or "?"
        if t.get("click"):
            rows.append((name, None, None))          # metronome: untouched
            continue
        L = cache.get(t["filename"])
        if L is None:
            rows.append((name, None, None))
            continue
        vol = round(max(min_gain, min(10 ** ((target - L) / 20.0), 1.0)), 3)
        edits[str(idx)] = vol
        rows.append((name, L, vol))
    return rows, edits


# ---- realm helpers (node) ----
def quit_app():
    subprocess.run(["osascript", "-e", 'quit app "Jamzone"'],
                   capture_output=True)
    subprocess.run(["pkill", "-x", "Jamzone"], capture_output=True)

def realm_write(edits):
    if not os.path.exists(os.path.join(RTOOLS, "node_modules", "realm")):
        sys.exit(f"RealmJS not installed. Run:  cd {RTOOLS} && npm i realm")
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(edits, f); path = f.name
    r = subprocess.run(["node", os.path.join(RTOOLS, "realm_set.mjs"), REALM, path],
                       capture_output=True, text=True)
    os.unlink(path)
    if r.returncode != 0:
        sys.exit(f"realm write failed:\n{r.stdout}\n{r.stderr}")
    return r.stdout

def realm_read(song_ids):
    r = subprocess.run(["node", os.path.join(RTOOLS, "realm_get.mjs"), REALM,
                        ",".join(str(s) for s in song_ids)],
                       capture_output=True, text=True)
    return r.stdout


# ---- commands ----
def cmd_measure(args):
    cache = load_cache()
    songs = select(args)
    for i, (cat, key, song) in enumerate(songs, 1):
        print(f"[{i}/{len(songs)}] {label_of(song)} ({cat}) ...", flush=True)
        measure_song(cat, key, cache, force="--force" in args)
        save_cache(cache)
    print(f"cached {len(cache)} stems -> {CACHE}")

def cmd_plan(args, do_apply=False):
    target = opt(args, "--target", DEFAULT_TARGET)
    min_gain = opt(args, "--min-gain", 0.05)
    cache = load_cache()
    songs = select(args)
    edits = {}
    for cat, key, song in songs:
        measure_song(cat, key, cache)              # fill any cache gaps
        rows, e = plan_song(cat, key, cache, target, min_gain)
        if e:
            edits[str(int(cat.split("_")[1]))] = e
        if not do_apply or len(songs) <= 3:
            print(f"\n{label_of(song)} ({cat})  target {target:.1f} LUFS")
            for name, L, vol in rows:
                ls = f"{L:7.1f}" if L is not None else "   --  "
                vs = "untouched" if vol is None else f"vol {vol}"
                print(f"   {str(name):22s} {ls} LUFS   {vs}")
    save_cache(cache)
    if do_apply:
        if not os.path.exists(BACKUP):             # immutable first backup
            os.makedirs(os.path.dirname(BACKUP), exist_ok=True)
            shutil.copy2(REALM, BACKUP)
            print(f"backed up original Realm -> {BACKUP}")
        quit_app()
        out = realm_write(edits)
        ok = out.count("\nOK") + out.startswith("OK")
        print(f"\napplied loudness normalization to {out.count('OK ')} songs "
              f"(target {target:.1f} LUFS). Reopen JamZone.")
        miss = [l for l in out.splitlines() if l.startswith("MISS")]
        if miss:
            print("no Realm preset (open the song once in the app, then re-run):")
            for m in miss: print("  ", m)

def cmd_mix(args, do_apply=False):
    """Per-song: normalize the played (audible) mix to target via the master only."""
    target = opt(args, "--target", -14.0)
    min_gain = opt(args, "--min-gain", 0.05)
    songs = select(args)
    for cat, key, song in songs:
        sid = int(cat.split("_")[1])
        raw = subprocess.run(["node", os.path.join(RTOOLS, "realm_song.mjs"), REALM,
                              str(sid)], capture_output=True, text=True).stdout
        st = json.loads(raw) if raw.strip().startswith("{") else None
        if not st:
            print(f"{label_of(song)}: no preset — open it once in JamZone first.")
            continue
        tj = tracks_of(cat, key)
        solo_any = any(t["isSolo"] for t in st["tracks"])
        audible = []
        for t in st["tracks"]:
            idx = t["idx"]
            if idx >= len(tj) or tj[idx].get("click"):
                continue
            aud = t["isSolo"] if solo_any else (t["isMuted"] % 2 == 1)
            if aud:
                audible.append((tj[idx]["filename"], t["volume"],
                                en(tj[idx].get("descriptions"))))
        if not audible:
            print(f"{label_of(song)}: nothing audible in the saved mix.")
            continue
        mix = played_mix_lufs(cat, key, [(fn, v) for fn, v, _ in audible])
        master = round(max(min_gain, min(10 ** ((target - mix) / 20.0), 1.0)), 3)
        print(f"\n{label_of(song)} (cat_{sid})  target {target:.1f} LUFS")
        print(f"  playing ({len(audible)}): " + ", ".join(n for _, _, n in audible))
        print(f"  played-mix loudness: {mix:6.1f} LUFS")
        print(f"  master: {st['master']:.3f} -> {master}"
              + ("   (already <= target, left at unity)" if master >= 1.0 and mix < target else ""))
        if do_apply:
            if not os.path.exists(BACKUP):
                os.makedirs(os.path.dirname(BACKUP), exist_ok=True)
                shutil.copy2(REALM, BACKUP)
            quit_app()
            out = subprocess.run(["node", os.path.join(RTOOLS, "realm_setmaster.mjs"),
                                  REALM, str(sid), str(master)],
                                 capture_output=True, text=True).stdout.strip()
            print("  applied:", out, "— reopen JamZone.")


def cmd_status(args):
    songs = select(args)
    ids = [int(cat.split("_")[1]) for cat, _, _ in songs]
    labels = {int(cat.split("_")[1]): label_of(s) for cat, _, s in songs}
    out = realm_read(ids)
    for line in out.splitlines():
        sid = line.split(":")[0]
        if sid.isdigit():
            print(f"{labels.get(int(sid),'?'):42s} {line}")

def cmd_restore(args):
    if not os.path.exists(BACKUP):
        sys.exit("No backup found — nothing to restore.")
    quit_app()
    shutil.copy2(BACKUP, REALM)
    print(f"restored Realm from {BACKUP}. Reopen JamZone.")


def main():
    if not os.path.isdir(JAMS):
        sys.exit(f"No JamZone container at:\n  {JAMS}")
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    cmd, rest = a[0], a[1:]
    apply_flag = "--apply" in rest
    {"measure": lambda: cmd_measure(rest),
     "plan":    lambda: cmd_plan(rest, False),
     "apply":   lambda: cmd_plan(rest, True),
     "mix":     lambda: cmd_mix(rest, apply_flag),   # per-song master normalize
     "status":  lambda: cmd_status(rest),
     "restore": lambda: cmd_restore(rest),
     }.get(cmd, lambda: sys.exit(__doc__))()


if __name__ == "__main__":
    main()
