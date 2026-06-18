#!/usr/bin/env python3
"""Build (and validate) songs.tsv — the lyric-launcher manifest.

Authoritative ordering/numbering comes from the web setlist:
  F/web/songs.json   (top-level `sets`[]; each set has `songs`[] in order).
Flatten every set's songs in order -> the 1-based position IS the set number.
Each song's `sid` is the factory dir name (music/songs/<sid>/). Entries whose sid
starts with "NOFOLDER:" are not real asset songs and are skipped (their position
number is simply unused).

Per kept song we reconcile the three naming schemes:
  1. position    -> set / clip (zero-padded 2) / pc_field (position+1)
  2. JamZone cat -> <jams>/cat_XXXX/ (decrypted song.json artist/title + tiles.json)
  3. factory     -> F/music/songs/<sid>/auto-render/{timeline.json,all.wav}
  4. bed folder  -> R/cherry-daddies-setlist-2026-06-16/<...>/ (matched by title/sid)
  5. concert     -> R/2000.concert/Concert.patch/<name>.patch  (anchor table by sid)

A song is `jamzone` (auto-lyrics) iff a matching cat with tiles.json exists AND its
factory auto-render has both timeline.json and all.wav. Otherwise `manual` (cat /
factory blank) — a manual {time,line} table is wired later.

Modes:
  --dry-run : print the resolved table + a list of rows needing human attention.
  (default) : write songs.tsv.
  --check   : validate songs.tsv (cats/tiles real, timeline+all.wav real,
              no duplicate clip/pc_field).

Run with the venv python:
  tools/lyric-launcher/.venv/bin/python tools/lyric-launcher/build_manifest.py --dry-run
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
F = os.path.abspath(os.path.join(HERE, "..", ".."))                  # factory repo root
R = os.path.abspath(os.path.join(F, "..", "cherry-daddies-2000"))    # rig repo root

SONGS_JSON = os.path.join(F, "web", "songs.json")
SETLIST_DIR = os.path.join(R, "cherry-daddies-setlist-2026-06-16")
FACTORY_SONGS = os.path.join(F, "music", "songs")
CONCERT_PATCH = os.path.join(R, "2000.concert", "Concert.patch")
JAMS = os.path.expanduser(
    "~/Library/Containers/com.recisio.jamzone.ios/Data/Library/"
    "Application Support/com.recisio.jamzone.ios/jams")

TSV = os.path.join(HERE, "songs.tsv")
COLUMNS = ["set", "song", "clip", "pc_field", "source",
           "cat", "factory_dir", "bed_dir", "concert_patch"]

# --- Hand-anchored concert-patch table ---------------------------------------
# songs.json `sid` (= factory dir name) -> top-level *.patch folder name under
# Concert.patch. The patch folder names are idiosyncratic (artist nicknames,
# lyric snippets, MainStage-mangled prefixes), so they're spelled out for review.
PATCH_FOR_SID = {
    "Alice Deejay - Better Off Alone":                     "Alice Deejay.patch",
    "A Touch of Class - Around the World (La La La La La)": "La la la.patch",
    "Shakira - Whenever, Wherever":                        "whenever.patch",
    "Guru Josh - Infinity 2008":                           "Guru Josh.patch",
    "Alexandra Stan - Mr. Saxobeat":                       "Alexandra Stan.patch",
    "Alex Gaudino - Destination Calabria":                 "Destenation.patch",
    "Coldplay - Adventure of a Lifetime":                  "Adventure of a Lifetime.patch",
    "The Weeknd - Blinding Lights":                        "Blinding Lights.patch",
    "Laurent Wolf & Eric Carter - No Stress":              "Laurent Wolf.patch",
    "Gala - Freed from Desire":                            "Freed From Desire.patch",
    "Bruno Mars & Mark Ronson - Uptown Funk":              "Uptown Funk.patch",
    "Demo - Solnyshko":                                    "Demo.patch",
    "Band'Eros - Pro krasivuju zhizn'":                    "Бандерос.patch",
    "SEREBRO - Malo tebya":                                "Серебро.patch",
    "Quest Pistols - Я устал":                             "Quest pistols.patch",
    "Basshunter - Now You're Gone":                        "Basshunter.patch",
    "Rihanna - S&M":                                       "Rihanna.patch",
    "Beverly Hills":                                       "beverly hills.patch",
    "Rihanna & Calvin Harris - We Found Love":             "1__#$!@%!#__Rihanna.patch",
    "Cascada - Everytime We Touch":                        "Cascada.patch",
    "Yeah Yeah Yeahs - Heads Will Roll":                   "heads will roll.patch",
    "Icona Pop & Charli XCX - I Love It":                  "I dont care.patch",
    "t.A.T.u. - Ya Soshla S Uma (Я сошла с ума)":          "tatu.patch",
}


# --- JamZone decryption (same scheme as make_song_clip.py) -------------------
def key_for(cat):
    return hashlib.md5(cat.encode()).hexdigest().encode().hex()


def dj(cat, name):
    p = os.path.join(JAMS, cat, name)
    d = open(p, "rb").read()
    out = subprocess.run(
        ["openssl", "enc", "-aes-256-cbc", "-d", "-K", key_for(cat),
         "-iv", d[:16].hex()],
        input=d[16:], capture_output=True).stdout
    return json.loads(out)


def norm(s):
    """Loose key for artist/title comparison: lowercase, drop everything that
    isn't a Unicode letter or digit (keeps Cyrillic — ASCII-only stripping would
    collapse every Russian title to '' and make them collide)."""
    return re.sub(r"[^\w]+", "", (s or "").lower(), flags=re.UNICODE).replace("_", "")


def build_cat_index():
    """{ (norm_artist, norm_title): cat } for every cat that has tiles.json."""
    idx = {}
    if not os.path.isdir(JAMS):
        return idx
    for cat in sorted(os.listdir(JAMS)):
        if not cat.startswith("cat_"):
            continue
        d = os.path.join(JAMS, cat)
        if not os.path.isfile(os.path.join(d, "tiles.json")):
            continue
        try:
            sj = dj(cat, "song.json")
        except Exception:
            continue
        art = sj.get("artist")
        if isinstance(art, dict):
            art = art.get("en") or next(iter(art.values()), "")
        title = sj.get("title", "")
        idx[(norm(art), norm(title))] = cat
    return idx


def sid_artist_title(sid):
    """`Artist - Title` factory/sid name -> (artist, title). Names without ' - '
    (e.g. 'Beverly Hills') carry no artist -> treat the whole name as title."""
    if " - " in sid:
        art, title = sid.split(" - ", 1)
        return art, title
    return "", sid


def resolve_cat(sid, cat_index):
    """Find the JamZone cat (with tiles) for this sid, or None.
    Matches on (norm_artist, norm_title); falls back to a unique title-only hit
    (handles featured-artist / nickname mismatches between sid and cat library)."""
    art, title = sid_artist_title(sid)
    na, nt = norm(art), norm(title)
    if (na, nt) in cat_index:
        return cat_index[(na, nt)]
    title_hits = [c for (a, t), c in cat_index.items() if t == nt]
    if len(title_hits) == 1:
        return title_hits[0]
    return None


def has_render(sid):
    ar = os.path.join(FACTORY_SONGS, sid, "auto-render")
    return (os.path.isfile(os.path.join(ar, "timeline.json")),
            os.path.isfile(os.path.join(ar, "all.wav")))


def build_bed_index():
    """Map bed (setlist) folders two ways:
       - by exact folder name (un-numbered folders == sid)
       - by title with a leading 'NN ' stripped (numbered folders)
    Returns (by_name, by_title): folder-name/norm-title -> relpath-from-R."""
    by_name, by_title = {}, {}
    if not os.path.isdir(SETLIST_DIR):
        return by_name, by_title
    for folder in sorted(os.listdir(SETLIST_DIR)):
        full = os.path.join(SETLIST_DIR, folder)
        if not os.path.isdir(full):
            continue
        rel = os.path.relpath(full, R)
        by_name[folder] = rel
        m = re.match(r"^\d+\s+(.*)$", folder)
        if m:
            by_title.setdefault(norm(m.group(1)), rel)
    return by_name, by_title


def resolve_bed(sid, title, by_name, by_title):
    """sid/title -> setlist bed folder relpath, or None."""
    if sid in by_name:                       # un-numbered folder named by sid
        return by_name[sid]
    nt = norm(title)
    if nt in by_title:                       # numbered folder, matched on title
        return by_title[nt]
    _, stitle = sid_artist_title(sid)        # last resort: sid's title part
    nst = norm(stitle)
    if nst in by_title:
        return by_title[nst]
    return None


# --- Discovery from web/songs.json -------------------------------------------
def discover():
    """Flatten web/songs.json sets in order; return rows + (song,[issues]) list."""
    if not os.path.isfile(SONGS_JSON):
        sys.exit(f"songs.json not found: {SONGS_JSON}")
    data = json.load(open(SONGS_JSON))

    cat_index = build_cat_index()
    by_name, by_title = build_bed_index()

    rows = []
    problems = []
    pos = 0
    for st in data.get("sets", []):
        for song in st.get("songs", []):
            pos += 1
            sid = song.get("sid", "")
            if sid.startswith("NOFOLDER:"):
                # not a real asset song -> this position number stays unused
                continue
            title = song.get("title") or sid
            issues = []

            # factory render
            fdir = os.path.join(FACTORY_SONGS, sid)
            if not os.path.isdir(fdir):
                issues.append(f"factory dir missing: music/songs/{sid}")
                has_tl = has_aw = False
            else:
                has_tl, has_aw = has_render(sid)

            # JamZone cat
            cat = resolve_cat(sid, cat_index)

            # concert patch
            patch = PATCH_FOR_SID.get(sid)
            if patch is None:
                issues.append(f"no concert-patch mapping for sid: {sid}")
            elif not os.path.isdir(os.path.join(CONCERT_PATCH, patch)):
                issues.append(f"concert patch not found: {patch}")

            # bed folder
            bed = resolve_bed(sid, title, by_name, by_title)
            if bed is None:
                issues.append(f"no bed (setlist) folder matched for: {title} / {sid}")

            # source decision
            if cat and has_tl and has_aw:
                source = "jamzone"
            else:
                source = "manual"
                if cat and not (has_tl and has_aw):
                    miss = []
                    if not has_tl:
                        miss.append("timeline.json")
                    if not has_aw:
                        miss.append("all.wav")
                    issues.append(
                        f"cat {cat} found but render missing {', '.join(miss)} "
                        f"-> downgraded to manual")

            rows.append(_row(pos, title, source, cat, sid, bed, patch, issues))
            if issues:
                problems.append((f"{pos:02d} {title}", issues))

    return rows, problems


def _row(pos, title, source, cat, sid, bed, patch, issues):
    if source == "jamzone":
        cat_out = cat or ""
        fac_out = f"music/songs/{sid}"
    else:  # manual rows carry no cat/factory per spec
        cat_out = ""
        fac_out = ""
    return {
        "set": str(pos),
        "song": title,
        "clip": f"{pos:02d}",
        "pc_field": str(pos + 1),
        "source": source,
        "cat": cat_out,
        "factory_dir": fac_out,
        "bed_dir": bed or "",
        "concert_patch": patch or "",
        "_issues": issues,
    }


# --- Output ------------------------------------------------------------------
def print_table(rows, problems):
    widths = {c: max(len(c), *(len(str(r[c])) for r in rows)) for c in COLUMNS}
    print("  ".join(c.ljust(widths[c]) for c in COLUMNS))
    print("  ".join("-" * widths[c] for c in COLUMNS))
    for r in rows:
        print("  ".join(str(r[c]).ljust(widths[c]) for c in COLUMNS))

    nj = sum(1 for r in rows if r["source"] == "jamzone")
    nm = sum(1 for r in rows if r["source"] == "manual")
    print(f"\n{len(rows)} songs: {nj} jamzone, {nm} manual")

    if problems:
        print(f"\n--- {len(problems)} row(s) needing attention ---")
        for song, issues in problems:
            for i in issues:
                print(f"  [{song}] {i}")
    else:
        print("\nno unresolved rows — all matched cleanly.")


def write_tsv(rows):
    with open(TSV, "w") as f:
        f.write("\t".join(COLUMNS) + "\n")
        for r in rows:
            f.write("\t".join(str(r[c]) for c in COLUMNS) + "\n")
    print(f"wrote {TSV} ({len(rows)} rows)")


# --- Validation --------------------------------------------------------------
def check():
    if not os.path.isfile(TSV):
        sys.exit(f"no songs.tsv at {TSV} — run without --check first")
    with open(TSV) as f:
        lines = [ln.rstrip("\n") for ln in f if ln.strip()]
    hdr = lines[0].split("\t")
    if hdr != COLUMNS:
        sys.exit(f"bad header: {hdr}\nexpected: {COLUMNS}")
    rows = [dict(zip(COLUMNS, ln.split("\t"))) for ln in lines[1:]]

    cat_index = build_cat_index()
    valid_cats = set(cat_index.values())
    problems = []

    clips, pcs = {}, {}
    nj = nm = 0
    for r in rows:
        song = r["song"]
        src = r["source"]
        if src == "jamzone":
            nj += 1
            cat = r["cat"]
            if not cat:
                problems.append(f"[{song}] jamzone row with empty cat")
            elif cat not in valid_cats:
                problems.append(f"[{song}] cat {cat} has no tiles.json / not found")
            fac = r["factory_dir"]
            if not fac:
                problems.append(f"[{song}] jamzone row with empty factory_dir")
            else:
                ar = os.path.join(F, fac, "auto-render")
                if not os.path.isfile(os.path.join(ar, "timeline.json")):
                    problems.append(f"[{song}] missing {fac}/auto-render/timeline.json")
                if not os.path.isfile(os.path.join(ar, "all.wav")):
                    problems.append(f"[{song}] missing {fac}/auto-render/all.wav")
        elif src == "manual":
            nm += 1
            if r["cat"]:
                problems.append(f"[{song}] manual row should have blank cat (got {r['cat']})")
            if r["factory_dir"]:
                problems.append(f"[{song}] manual row should have blank factory_dir")
        else:
            problems.append(f"[{song}] bad/empty source: {src!r}")

        if r["concert_patch"]:
            if not os.path.isdir(os.path.join(CONCERT_PATCH, r["concert_patch"])):
                problems.append(f"[{song}] concert patch not found: {r['concert_patch']}")
        else:
            problems.append(f"[{song}] empty concert_patch")

        if not r["clip"]:
            problems.append(f"[{song}] empty clip")
        else:
            clips.setdefault(r["clip"], []).append(song)
        if not r["pc_field"]:
            problems.append(f"[{song}] empty pc_field")
        else:
            pcs.setdefault(r["pc_field"], []).append(song)
        if r["clip"] and r["pc_field"]:
            if int(r["pc_field"]) != int(r["clip"]) + 1:
                problems.append(
                    f"[{song}] pc_field {r['pc_field']} != clip {r['clip']} + 1")

    for clip, songs in clips.items():
        if len(songs) > 1:
            problems.append(f"duplicate clip {clip}: {songs}")
    for pc, songs in pcs.items():
        if len(songs) > 1:
            problems.append(f"duplicate pc_field {pc}: {songs}")

    if problems:
        print(f"--- {len(problems)} problem(s) ---")
        for p in problems:
            print(f"  {p}")
        sys.exit(1)
    print(f"manifest OK ({nj} jamzone, {nm} manual)")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true",
                    help="print the resolved table + rows needing attention; write nothing")
    ap.add_argument("--check", action="store_true",
                    help="validate an existing songs.tsv")
    args = ap.parse_args()

    if args.check:
        check()
        return

    rows, problems = discover()
    print_table(rows, problems)
    if not args.dry_run:
        print()
        write_tsv(rows)


if __name__ == "__main__":
    main()
