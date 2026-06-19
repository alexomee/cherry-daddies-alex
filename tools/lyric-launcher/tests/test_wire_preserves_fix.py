# tests/test_wire_preserves_fix.py
# Regression guard: re-running wire_concert.py must NOT revert the keyboardist's
# manual Lyrics-layer fix (No-Output routing in data.plist + the per-set .cst
# blob that carries his key/velocity-range fix). See wire_concert.py docstring.
import os
import plistlib
import wire_concert as W


def _strip(prog, output_index=0, with_stereo=True):
    s = {
        "Filename": "Lyrics.cst",
        "Channel_name": "Lyrics",
        "Channel_instID": 100 + prog,
        "Channel_outputIndex": output_index,
        "shouldSendProgramChange": True,
        "programChangeNumber": prog,
        "UUID": f"UUID-{prog}",
    }
    if with_stereo:
        s["Channel_outputIsStereo"] = True
    return s


def _concert(tmp_path):
    """Return (concert_root, concert_patch_dir) with the real bundle layout."""
    base = str(tmp_path / "x.concert")
    cp = os.path.join(base, "Concert.patch")
    os.makedirs(cp)
    return base, cp


def _make_set(concert_patch, name, channels, cst_bytes=None):
    d = os.path.join(concert_patch, name)
    os.makedirs(d)
    W.save_plist(os.path.join(d, "data.plist"), {"channels": channels})
    if cst_bytes is not None:
        with open(os.path.join(d, "Lyrics.cst"), "wb") as f:
            f.write(cst_bytes)
    return d


def _load_strip(patch_dir):
    d = W.load_plist(os.path.join(patch_dir, "data.plist"))
    return W.find_lyrics_strip(d["channels"])


def test_update_preserves_no_output_and_cst(tmp_path):
    """An already-fixed set keeps outputIndex=-1 and its own .cst byte-for-byte."""
    base, cp = _concert(tmp_path)
    fixed_cst = b"OCuA-FIXED-KEYBOARDIST-BLOB"          # his per-set .cst
    fixed = _make_set(cp, "Cascada.patch",
                      [_strip(20, output_index=-1, with_stereo=False)], fixed_cst)
    tmpl = _make_set(cp, "whenever.patch",
                     [_strip(3, output_index=0, with_stereo=True)], b"OCuA-TEMPLATE-OLD")

    res = W.wire_set(base, "Cascada.patch", 20,
                     _load_strip(tmpl), os.path.join(tmpl, "Lyrics.cst"))

    s = _load_strip(fixed)
    assert s["Channel_outputIndex"] == -1               # fix NOT reverted
    assert "Channel_outputIsStereo" not in s            # not re-added
    assert s["programChangeNumber"] == 20               # wiring still applied
    assert s["Channel_MIDIOutputPort"]["uniqueID"] == W.LYRIC_UNIQUE_ID
    assert res["cst_copied"] == "preserved"
    with open(os.path.join(fixed, "Lyrics.cst"), "rb") as f:
        assert f.read() == fixed_cst                    # .cst untouched


def test_force_cst_overwrites(tmp_path):
    """--force-cst is the explicit escape hatch that DOES overwrite the .cst."""
    base, cp = _concert(tmp_path)
    fixed = _make_set(cp, "Cascada.patch",
                      [_strip(20, output_index=-1, with_stereo=False)], b"OCuA-FIXED")
    tmpl = _make_set(cp, "whenever.patch",
                     [_strip(3, output_index=0, with_stereo=True)], b"OCuA-TEMPLATE-OLD")
    res = W.wire_set(base, "Cascada.patch", 20,
                     _load_strip(tmpl), os.path.join(tmpl, "Lyrics.cst"),
                     force_cst=True)
    assert res["cst_copied"] == "forced"
    with open(os.path.join(fixed, "Lyrics.cst"), "rb") as f:
        assert f.read() == b"OCuA-TEMPLATE-OLD"


def test_update_completes_fix_on_old_strip(tmp_path):
    """A strip a previous run left at output 0 is corrected to -1 (never the reverse)."""
    base, cp = _concert(tmp_path)
    old = _make_set(cp, "Demo.patch",
                    [_strip(12, output_index=0, with_stereo=True)], b"OCuA-EXISTING")
    tmpl = _make_set(cp, "whenever.patch",
                     [_strip(3, output_index=0, with_stereo=True)], b"OCuA-TEMPLATE-OLD")
    W.wire_set(base, "Demo.patch", 12,
               _load_strip(tmpl), os.path.join(tmpl, "Lyrics.cst"))
    s = _load_strip(old)
    assert s["Channel_outputIndex"] == -1
    assert "Channel_outputIsStereo" not in s


def test_new_set_born_no_output_and_seeded_from_fixed_donor(tmp_path):
    """A brand-new set gets No-Output + the fixed donor's .cst, not the template's."""
    base, cp = _concert(tmp_path)
    donor_cst = b"OCuA-FIXED-DONOR-BLOB"
    _make_set(cp, "Cascada.patch",
              [_strip(20, output_index=-1, with_stereo=False)], donor_cst)
    tmpl = _make_set(cp, "whenever.patch",
                     [_strip(3, output_index=0, with_stereo=True)], b"OCuA-TEMPLATE-OLD")
    newd = _make_set(cp, "tatu.patch", [])               # no Lyrics strip, no .cst

    seed = W.find_fixed_cst(cp, exclude_dir=tmpl) or os.path.join(tmpl, "Lyrics.cst")
    res = W.wire_set(base, "tatu.patch", 24, _load_strip(tmpl), seed)

    s = _load_strip(newd)
    assert s is not None and res["action"] == "inserted"
    assert s["Channel_outputIndex"] == -1               # born No-Output
    assert "Channel_outputIsStereo" not in s
    assert s["programChangeNumber"] == 24
    assert res["cst_copied"] == "seeded"
    with open(os.path.join(newd, "Lyrics.cst"), "rb") as f:
        assert f.read() == donor_cst                    # seeded from FIXED donor, not template


def test_no_double_strip_on_rerun(tmp_path):
    """Re-wiring never appends a second Lyrics strip."""
    base, cp = _concert(tmp_path)
    fixed = _make_set(cp, "Cascada.patch",
                      [_strip(20, output_index=-1, with_stereo=False)], b"OCuA-FIXED")
    tmpl = _make_set(cp, "whenever.patch",
                     [_strip(3, output_index=0, with_stereo=True)], b"OCuA-TEMPLATE-OLD")
    for _ in range(3):
        W.wire_set(base, "Cascada.patch", 20,
                   _load_strip(tmpl), os.path.join(tmpl, "Lyrics.cst"))
    d = W.load_plist(os.path.join(fixed, "data.plist"))
    lyrics = [c for c in d["channels"] if c.get("Filename") == "Lyrics.cst"]
    assert len(lyrics) == 1
