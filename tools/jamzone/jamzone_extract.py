#!/usr/bin/env python3
"""
JamZone stem/structure extractor — no key capture needed.

The per-song AES-256 key is DERIVED, not server-only:
    key32 = md5("cat_<id>").hexdigest()          # 32 hex chars
    openssl_key = key32.encode().hex()           # 64 hex chars (ASCII of key32)
On-disk format per file: [16-byte IV][AES-256-CBC ciphertext, PKCS7].
One key decrypts every file in that cat folder (song.json, tracks.json,
structure.json, tiles.json, and all *.mp4 stems).

The song must already be DOWNLOADED in the original /Applications/Jamzone.app
(HQ ~124kb/s AAC-LC). If it isn't downloaded, there are no local files to
decrypt — see SKILL.md for the one-time download/hook fallback.

Usage:
    jamzone_extract.py list                       # list all downloaded songs
    jamzone_extract.py <query> [output_dir]       # extract songs matching query
    jamzone_extract.py --cat cat_68009 [out_dir]  # extract one folder by id
Query matches artist or title, case-insensitive, substring.
"""
import os, sys, hashlib, subprocess, json

JAMS = os.path.expanduser(
    "~/Library/Containers/com.recisio.jamzone.ios/Data/Library/"
    "Application Support/com.recisio.jamzone.ios/jams")
DEFAULT_OUT = os.path.expanduser("~/projects/cherry-daddies/music/songs")


def key_for(cat):
    """Derived openssl -K hex for a cat folder name, e.g. 'cat_68009'."""
    return hashlib.md5(cat.encode()).hexdigest().encode().hex()


def dec(data, key):
    return subprocess.run(
        ["openssl", "enc", "-aes-256-cbc", "-d", "-K", key, "-iv", data[:16].hex()],
        input=data[16:], capture_output=True).stdout


def load_json(cat_dir, name, key):
    return json.loads(dec(open(os.path.join(cat_dir, name), "rb").read(), key))


def en(v):
    return v.get("en") if isinstance(v, dict) else v


def safe(s):
    for a, b in [("/", "-"), (":", "-"), ("?", ""), ('"', "")]:
        s = s.replace(a, b)
    return s


def iter_songs():
    """Yield (cat, key, song_dict) for every decryptable downloaded folder."""
    for cat in sorted(os.listdir(JAMS)):
        cat_dir = os.path.join(JAMS, cat)
        sj = os.path.join(cat_dir, "song.json")
        if not os.path.isfile(sj):
            continue
        key = key_for(cat)
        try:
            song = json.loads(dec(open(sj, "rb").read(), key))
        except Exception:
            continue
        yield cat, key, song


def mmss(s):
    return f"{int(s)//60}:{int(s)%60:02d}"


def extract(cat, key, song, out_root):
    cat_dir = os.path.join(JAMS, cat)
    artist = en(song.get("artist"))
    title = song.get("title")
    label = safe(f"{artist} - {title}")
    dest = os.path.join(out_root, label)
    os.makedirs(dest, exist_ok=True)
    for f in os.listdir(dest):
        if f.endswith((".m4a", ".txt")):
            os.remove(os.path.join(dest, f))

    # structure.txt — one section per line (matches the player's top strip)
    struct = load_json(cat_dir, "structure.json", key)
    open(os.path.join(dest, "structure.txt"), "w").write(
        "\n".join(s["caption"] for s in struct) + "\n")

    # stems — sorted mp4 order == tracks.json order == UI left-to-right
    tracks = load_json(cat_dir, "tracks.json", key)
    mp4s = sorted(f for f in os.listdir(cat_dir) if f.endswith(".mp4"))
    print(f"=== {label} ({cat}) — {len(mp4s)} stems ===")
    for i, (mp4, tr) in enumerate(zip(mp4s, tracks), 1):
        name = safe(str(en(tr.get("descriptions")) or "track")).replace(" ", "_")
        out = dec(open(os.path.join(cat_dir, mp4), "rb").read(), key)
        open(os.path.join(dest, f"{i:02d}_{name}.m4a"), "wb").write(out)
        print(f"  {i:02d}_{name}.m4a  ({len(out)//1024} KB)")
    print(f"  -> {dest}")
    return dest


def main():
    if not os.path.isdir(JAMS):
        sys.exit(f"No JamZone container at:\n  {JAMS}")
    args = sys.argv[1:]
    if not args:
        sys.exit(__doc__)

    if args[0] == "list":
        rows = [(cat, en(s.get("artist")), s.get("title")) for cat, _, s in iter_songs()]
        for cat, a, t in rows:
            print(f"{cat:12} {a} - {t}")
        print(f"\n{len(rows)} downloaded songs")
        return

    if args[0] == "--cat":
        cat = args[1]
        out = args[2] if len(args) > 2 else DEFAULT_OUT
        extract(cat, key_for(cat), load_json(os.path.join(JAMS, cat), "song.json", key_for(cat)), out)
        return

    query = args[0].lower()
    out = args[1] if len(args) > 1 else DEFAULT_OUT
    hits = [(cat, key, s) for cat, key, s in iter_songs()
            if query in f"{en(s.get('artist'))} - {s.get('title')}".lower()]
    if not hits:
        sys.exit(f"No downloaded song matches '{args[0]}'. Try: jamzone_extract.py list")
    if len(hits) > 1:
        print(f"{len(hits)} matches — extracting all:")
    for cat, key, s in hits:
        extract(cat, key, s, out)


if __name__ == "__main__":
    main()
