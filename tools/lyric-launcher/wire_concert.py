#!/usr/bin/env python3
"""Replicate the lyric-trigger wiring from the hand-wired Whenever set across
all jamzone sets of a MainStage concert.

Background (verified against the live concert, see commit message / report):

  * Each song's MainStage *set* is a `.patch` folder under
    `<concert>/Concert.patch/`. Its `data.plist` (Apple binary plist) holds a
    top-level `channels` array — one dict per channel strip.
  * The hand-wired Whenever set has an extra strip appended to `channels`: an
    External-Instrument strip whose `Filename` is `Lyrics.cst`. That strip
    carries the MIDI wiring that fires a Program Change at the LyricLauncher
    virtual port whenever the song's set is selected:

        Channel_MIDIOutputChannel = 1
        Channel_MIDIOutputPort     = { name=LyricLauncher, uniqueID=<UID>,
                                       uniqueIDType=1, isSource=False }
        shouldSendProgramChange    = True
        programChangeNumber        = <clip number for that song>

  * The accompanying `Lyrics.cst` file is the strip's instrument/channel-strip
    setting. It is *set-independent*: the same factory `.cst` files (e.g.
    `Inst 352.cst`) are reused byte-for-byte across every set, while each set's
    `data.plist` gives the strip its own UUID + instID. The UUID embedded in the
    `.cst` (`_WsChannelUUID`/`UUIDBytes`) is therefore authoritative-from-plist,
    not from the `.cst` — so copying `Lyrics.cst` verbatim into another set is
    safe. We just append a strip dict with a fresh per-set-unique UUID + instID.

  * The stable LyricLauncher CoreMIDI uniqueID is 1280922179 (0x4C595243,
    b'LYRC'). Whenever's saved wiring still holds an OLD random uniqueID
    (217740483); this script re-stamps it too.

Idempotent: re-running updates an existing Lyrics strip in place (never
duplicates) and re-copies the `.cst`.

The `programChangeChannel` / `programChangePort` / `sendThruProgramChanges`
keys on `patch.engineNode` are PRE-EXISTING set-level patch-change config (they
are present and identical in the un-wired baseline). They are NOT part of the
Lyrics wiring and are left untouched.

Usage:
    wire_concert.py --concert /tmp/2000-wired.concert --tsv songs.tsv [--template-set whenever.patch]
"""

import argparse
import csv
import os
import plistlib
import shutil
import sys
import uuid as uuidlib

# Stable CoreMIDI uniqueID forced by launcher.py for the "LyricLauncher" port.
LYRIC_UNIQUE_ID = 0x4C595243  # == 1280922179, b'LYRC'
PORT_NAME = "LyricLauncher"
LYRICS_CST = "Lyrics.cst"
INSTID_STRIDE = 4  # observed stride between consecutive Channel_instID values


def load_plist(path):
    with open(path, "rb") as f:
        return plistlib.load(f)


def save_plist(path, obj):
    # plistlib writes Apple binary plist when fmt=FMT_BINARY, matching MainStage.
    with open(path, "wb") as f:
        plistlib.dump(obj, f, fmt=plistlib.FMT_BINARY)


def find_lyrics_strip(channels):
    """Return the existing Lyrics strip dict, or None.

    Identified by Filename == Lyrics.cst (the strip's setting file). We do NOT
    key on Channel_name='Lyrics' alone, since that is a user-visible label."""
    for ch in channels:
        if ch.get("Filename") == LYRICS_CST:
            return ch
    return None


def build_lyrics_strip(template_strip, prog_number, instid, strip_uuid):
    """Clone the template Lyrics strip and stamp the per-set-unique fields."""
    strip = dict(template_strip)  # shallow copy; we replace mutated sub-dicts below

    # Per-set-unique identity.
    strip["UUID"] = strip_uuid
    strip["Channel_instID"] = instid

    # The wiring. Rebuild the output-port dict fresh (don't alias the template's).
    strip["Channel_MIDIOutputChannel"] = 1
    strip["Channel_MIDIOutputPort"] = {
        "name": PORT_NAME,
        "uniqueID": LYRIC_UNIQUE_ID,
        "uniqueIDType": 1,
        "isSource": False,
    }
    strip["shouldSendProgramChange"] = True
    strip["programChangeNumber"] = int(prog_number)

    return strip


def restamp_uniqueid(strip):
    """Force the LyricLauncher output-port uniqueID to the stable value.

    Returns True if anything changed."""
    changed = False
    port = strip.get("Channel_MIDIOutputPort")
    if isinstance(port, dict) and port.get("name") == PORT_NAME:
        if port.get("uniqueID") != LYRIC_UNIQUE_ID:
            port["uniqueID"] = LYRIC_UNIQUE_ID
            changed = True
        # normalise the companion fields too, so every wired set is identical
        if port.get("uniqueIDType") != 1:
            port["uniqueIDType"] = 1
            changed = True
        if port.get("isSource") is not False:
            port["isSource"] = False
            changed = True
    return changed


def next_instid(channels):
    mx = 0
    for ch in channels:
        v = ch.get("Channel_instID")
        if isinstance(v, int):
            mx = max(mx, v)
    return mx + INSTID_STRIDE


def existing_uuids(channels):
    return {ch.get("UUID") for ch in channels if ch.get("UUID")}


def new_unique_uuid(used):
    while True:
        u = str(uuidlib.uuid4()).upper()
        if u not in used:
            return u


def wire_set(concert, patch_folder, clip_number, template_strip, template_cst_path,
             dry_run=False):
    """Wire one jamzone set. Returns a dict of what happened."""
    patch_dir = os.path.join(concert, "Concert.patch", patch_folder)
    data_plist = os.path.join(patch_dir, "data.plist")
    result = {
        "patch": patch_folder,
        "clip": clip_number,
        "ok": False,
        "action": "",
        "prog_number": None,
        "uuid": None,
        "instid": None,
        "cst_copied": False,
        "note": "",
    }
    if not os.path.isdir(patch_dir):
        result["note"] = "MISSING patch folder"
        return result
    if not os.path.isfile(data_plist):
        result["note"] = "MISSING data.plist"
        return result

    # (a) copy Lyrics.cst into the set (idempotent overwrite).
    # Skip the copy when this set IS the template (src and dest are one file).
    dest_cst = os.path.join(patch_dir, LYRICS_CST)
    is_same = os.path.isfile(dest_cst) and os.path.samefile(template_cst_path, dest_cst)
    if not dry_run and not is_same:
        shutil.copy2(template_cst_path, dest_cst)
    result["cst_copied"] = os.path.isfile(dest_cst)

    # (b) insert/update the strip in data.plist.
    d = load_plist(data_plist)
    channels = d.setdefault("channels", [])
    existing = find_lyrics_strip(channels)

    if existing is not None:
        # idempotent update in place — keep its UUID/instID, restamp wiring.
        existing["Channel_MIDIOutputChannel"] = 1
        existing["Channel_MIDIOutputPort"] = {
            "name": PORT_NAME,
            "uniqueID": LYRIC_UNIQUE_ID,
            "uniqueIDType": 1,
            "isSource": False,
        }
        existing["shouldSendProgramChange"] = True
        existing["programChangeNumber"] = int(clip_number)
        if not existing.get("UUID"):
            existing["UUID"] = new_unique_uuid(existing_uuids(channels))
        if not isinstance(existing.get("Channel_instID"), int):
            existing["Channel_instID"] = next_instid(channels)
        result["action"] = "updated"
        result["uuid"] = existing["UUID"]
        result["instid"] = existing["Channel_instID"]
    else:
        instid = next_instid(channels)
        strip_uuid = new_unique_uuid(existing_uuids(channels))
        strip = build_lyrics_strip(template_strip, clip_number, instid, strip_uuid)
        channels.append(strip)
        result["action"] = "inserted"
        result["uuid"] = strip_uuid
        result["instid"] = instid

    result["prog_number"] = int(clip_number)
    if not dry_run:
        save_plist(data_plist, d)
    result["ok"] = True
    return result


def restamp_template(concert, template_folder, dry_run=False):
    """Re-stamp the template (Whenever) set's saved wiring to the stable uniqueID."""
    data_plist = os.path.join(concert, "Concert.patch", template_folder, "data.plist")
    d = load_plist(data_plist)
    strip = find_lyrics_strip(d.get("channels", []))
    if strip is None:
        return {"patch": template_folder, "restamped": False,
                "note": "no Lyrics strip in template!"}
    old = strip.get("Channel_MIDIOutputPort", {}).get("uniqueID")
    changed = restamp_uniqueid(strip)
    if changed and not dry_run:
        save_plist(data_plist, d)
    return {"patch": template_folder, "restamped": changed,
            "old_uniqueID": old,
            "new_uniqueID": LYRIC_UNIQUE_ID,
            "prog_number": strip.get("programChangeNumber")}


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--concert", required=True,
                    help="path to the .concert bundle to wire (NEVER the live one)")
    ap.add_argument("--tsv", required=True, help="songs.tsv manifest")
    ap.add_argument("--template-set", default="whenever.patch",
                    help="the hand-wired set whose Lyrics strip + .cst is the template")
    ap.add_argument("--dry-run", action="store_true",
                    help="report what would change without writing")
    ap.add_argument("--skip-clips", default="",
                    help="comma-separated clip numbers to NOT wire (e.g. 24 for tatu)")
    ap.add_argument("--allow-live", action="store_true",
                    help="deliberately permit writing the live concert "
                         "(only after a copy has been verified in MainStage)")
    args = ap.parse_args()

    concert = os.path.abspath(args.concert)
    # Hard guard: refuse to touch the live concert unless explicitly allowed.
    if os.path.realpath(concert).rstrip("/").endswith(
            "cherry-daddies-2000/2000.concert") and not args.allow_live:
        sys.exit("REFUSING to write to the live concert. Run against a copy, "
                 "or pass --allow-live once a copy has been verified.")

    base = os.path.join(concert, "Concert.patch")
    if not os.path.isdir(base):
        sys.exit(f"not a concert bundle (no Concert.patch): {concert}")

    # Load template strip + .cst from the template set inside THIS concert copy.
    tmpl_dir = os.path.join(base, args.template_set)
    tmpl_plist = os.path.join(tmpl_dir, "data.plist")
    tmpl_cst = os.path.join(tmpl_dir, LYRICS_CST)
    if not os.path.isfile(tmpl_plist) or not os.path.isfile(tmpl_cst):
        sys.exit(f"template set incomplete: {tmpl_dir}")
    tmpl = load_plist(tmpl_plist)
    template_strip = find_lyrics_strip(tmpl.get("channels", []))
    if template_strip is None:
        sys.exit(f"template set has no Lyrics strip: {tmpl_dir}")

    # Parse manifest -> jamzone rows.
    with open(args.tsv, newline="") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    jz = [r for r in rows if r.get("source") in ("jamzone", "static")]
    skip = {int(x) for x in args.skip_clips.split(",") if x.strip()}
    if skip:
        jz = [r for r in jz if int(r["clip"]) not in skip]
        print(f"skipping clips: {sorted(skip)}")

    print(f"concert: {concert}")
    print(f"template set: {args.template_set}  (strip instID stride {INSTID_STRIDE})")
    print(f"LyricLauncher uniqueID: {LYRIC_UNIQUE_ID} ({hex(LYRIC_UNIQUE_ID)})")
    print(f"jamzone sets to wire: {len(jz)}")
    print()

    # 1) re-stamp template's own saved wiring.
    rt = restamp_template(concert, args.template_set, dry_run=args.dry_run)
    print(f"[template restamp] {rt['patch']}: "
          f"old uniqueID {rt.get('old_uniqueID')} -> {rt.get('new_uniqueID')} "
          f"(changed={rt.get('restamped')}) prog={rt.get('prog_number')}")
    print()

    # 2) wire every jamzone set (template included — it's idempotent there).
    results = []
    for r in jz:
        clip = int(r["clip"])  # zero-padded string -> int
        res = wire_set(concert, r["concert_patch"], clip,
                       template_strip, tmpl_cst, dry_run=args.dry_run)
        results.append(res)
        flag = "OK " if res["ok"] else "ERR"
        print(f"[{flag}] clip={clip:>2} {res['action']:>8} "
              f"prog={res['prog_number']} instID={res['instid']} "
              f"uuid={res['uuid']} cst={res['cst_copied']} "
              f"{res['patch']} {res['note']}")

    bad = [r for r in results if not r["ok"]]
    print()
    print(f"done: {len(results) - len(bad)}/{len(results)} sets wired"
          + (f", {len(bad)} FAILED" if bad else ""))
    if bad:
        sys.exit(2)


if __name__ == "__main__":
    main()
