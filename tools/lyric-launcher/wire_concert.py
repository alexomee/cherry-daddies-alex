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
    setting. At first wiring it is *set-independent*: the same blob is copied
    into every set, while each set's `data.plist` gives the strip its own UUID +
    instID. The UUID embedded in the `.cst` (`_WsChannelUUID`/`UUIDBytes`) is
    non-authoritative (the per-set `data.plist` UUID wins) — so seeding a new
    set from another set's `.cst` is safe. We append a strip dict with a fresh
    per-set-unique UUID + instID.

    !! IMPORTANT (regression guard): once MainStage SAVES a set, it re-authors
    that set's `Lyrics.cst` per-set, and the keyboardist's manual fix — the
    Lyrics layer's key/velocity range + "No Output" routing, so the strip stops
    acting as a playable layer on his top keyboard (Akai) — lives partly in this
    proprietary OCuA blob and partly in `data.plist` (`Channel_outputIndex=-1`,
    no `Channel_outputIsStereo`). So re-running this script must NEVER overwrite
    an existing set's `.cst` (default behaviour; `--force-cst` to override) and
    must touch only the MIDI patch-change wiring in `data.plist`, leaving output
    routing / ranges intact. Brand-new sets are seeded from an already-fixed
    set's `.cst` when one exists, and stamped `Channel_outputIndex=-1`.

  * The stable LyricLauncher CoreMIDI uniqueID is 1280922179 (0x4C595243,
    b'LYRC'). Whenever's saved wiring still holds an OLD random uniqueID
    (217740483); this script re-stamps it too.

Idempotent: re-running updates an existing Lyrics strip's MIDI wiring in place
(never duplicates) and PRESERVES the set's existing `.cst` + output/range fix.

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

    # Born "No Output": the Lyrics strip is a MIDI-only patch-change sender, not
    # an audible keyboard layer. The keyboardist's manual fix sets the strip's
    # audio output to none (Channel_outputIndex = -1, no Channel_outputIsStereo)
    # so it never grabs an output bus / shows up as a playable layer on his Akai.
    # Stamp that here so a NEW set is born correct instead of cloning whatever
    # the (possibly un-fixed) template carries. See no_output_fix() / the
    # idempotent update path, which preserve this for already-wired sets.
    no_output_fix(strip)

    return strip


def no_output_fix(strip):
    """Force the keyboardist's 'No Output' state on a Lyrics strip.

    Only ever moves a strip TOWARD No Output (audio output = none); it never
    re-routes a strip back to an audio bus, so it can't revert his fix — it only
    completes it on a strip a previous run left routed to Output 1-2.
    Returns True if anything changed."""
    changed = False
    if strip.get("Channel_outputIndex") != -1:
        strip["Channel_outputIndex"] = -1
        changed = True
    if "Channel_outputIsStereo" in strip:
        del strip["Channel_outputIsStereo"]
        changed = True
    return changed


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


def find_fixed_cst(base, exclude_dir=None):
    """Find a set whose Lyrics strip already carries the keyboardist's fix
    (Channel_outputIndex == -1) and return that set's Lyrics.cst path.

    Used to seed BRAND-NEW sets: their .cst is then a copy of a real, fixed
    set's blob (which carries his per-set layer/key-range fix in the OCuA data)
    rather than the possibly-un-fixed template's .cst. Returns None if no fixed
    set exists yet. The .cst's embedded UUID is non-authoritative (the per-set
    data.plist UUID wins), so copying one set's .cst to another is safe."""
    if not os.path.isdir(base):
        return None
    for name in sorted(os.listdir(base)):
        patch_dir = os.path.join(base, name)
        if exclude_dir and os.path.abspath(patch_dir) == os.path.abspath(exclude_dir):
            continue
        dp = os.path.join(patch_dir, "data.plist")
        cst = os.path.join(patch_dir, LYRICS_CST)
        if not (os.path.isfile(dp) and os.path.isfile(cst)):
            continue
        try:
            strip = find_lyrics_strip(load_plist(dp).get("channels", []))
        except Exception:
            continue
        if strip is not None and strip.get("Channel_outputIndex") == -1:
            return cst
    return None


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
             dry_run=False, force_cst=False):
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
        "cst_copied": "",
        "note": "",
    }
    if not os.path.isdir(patch_dir):
        result["note"] = "MISSING patch folder"
        return result
    if not os.path.isfile(data_plist):
        result["note"] = "MISSING data.plist"
        return result

    # (a) Seed Lyrics.cst into the set — but PRESERVE an existing one.
    # Once MainStage saves a set, it re-authors that set's Lyrics.cst per-set
    # (its own embedded UUID, and the keyboardist's layer/key-range fix lives in
    # this proprietary OCuA blob). Overwriting it from the template would REVERT
    # that fix — exactly the regression we are guarding against. So we only copy
    # the template .cst when the set has NONE yet (brand-new wiring), or when the
    # operator explicitly asks with --force-cst. An existing .cst is left intact.
    dest_cst = os.path.join(patch_dir, LYRICS_CST)
    dest_exists = os.path.isfile(dest_cst)
    is_same = dest_exists and os.path.samefile(template_cst_path, dest_cst)
    if is_same:
        result["cst_copied"] = "is-template"
    elif dest_exists and not force_cst:
        result["cst_copied"] = "preserved"          # keyboardist's per-set .cst — never clobber
    else:
        if not dry_run:
            shutil.copy2(template_cst_path, dest_cst)
        result["cst_copied"] = "forced" if dest_exists else "seeded"

    # (b) insert/update the strip in data.plist.
    d = load_plist(data_plist)
    channels = d.setdefault("channels", [])
    existing = find_lyrics_strip(channels)

    if existing is not None:
        # Idempotent update in place — touch ONLY the MIDI patch-change wiring
        # this tool owns. Everything else (audio output routing, key/velocity
        # range, MIDITransform, filters) is the keyboardist's domain and is left
        # exactly as he saved it, so re-running never reverts his fix.
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
        # Complete (never revert) the No-Output fix: -1 stays -1; only an
        # older-run strip still routed to an audio bus gets corrected.
        no_output_fix(existing)
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
    ap.add_argument("--force-cst", action="store_true",
                    help="overwrite each set's existing Lyrics.cst from the template. "
                         "DEFAULT IS OFF: a set's saved .cst carries the keyboardist's "
                         "per-set layer/key-range fix and is preserved. Only use this to "
                         "deliberately reset every set's strip setting.")
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

    # Seed source for the .cst of BRAND-NEW sets: prefer an already-fixed set's
    # blob (carries the keyboardist's layer/key-range fix) over the template's.
    seed_cst = find_fixed_cst(base, exclude_dir=tmpl_dir) or tmpl_cst
    print(f"new-set .cst seed: {os.path.relpath(seed_cst, base)}"
          + ("  (fixed donor)" if seed_cst != tmpl_cst else "  (template — no fixed set found)"))

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
                       template_strip, seed_cst, dry_run=args.dry_run,
                       force_cst=args.force_cst)
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
