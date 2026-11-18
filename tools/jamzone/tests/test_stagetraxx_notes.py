"""Dashboard notes -> the Stage Traxx lyrics area (stagetraxx_sync)."""
import json
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import stagetraxx_sync as st  # noqa: E402

BLOCK = ["[midi: PC62@1]", "[midi@play: START]", "[midi@stop: STOP]"]


def _db(tmp_path, songs):
    p = tmp_path / "dashboard.db"
    con = sqlite3.connect(p)
    con.execute("CREATE TABLE app_state (id INTEGER PRIMARY KEY, data TEXT NOT NULL)")
    con.execute("INSERT INTO app_state VALUES (1, ?)", (json.dumps({"global": {}, "songs": songs}),))
    con.commit()
    con.close()
    return str(p)


def test_clean_note_like_stage_sheet():
    assert st.clean_note("32B <-> 32D\n\n  Gm Bb Eb (Cm D)  \n\nGm Bb Eb (Cm D)\n") == \
        "32B <-> 32D\nGm Bb Eb (Cm D)"
    assert st.clean_note("[midi: PC1@1]\nreal") == "real"          # can't smuggle a MIDI tag in
    assert st.clean_note(None) == ""


def test_load_merges_nofolder_record(tmp_path):
    p = _db(tmp_path, {
        "Мелом": {"notes": "A, I START"},
        "NOFOLDER:Мелом": {"notes": "Am F C G"},
        "Солнце": {"notes": "32B <-> 32D\n\nGm"},
        "Пусто": {"notes": "  \n"},
        "Без поля": {},
    })
    assert st.load_web_notes(p) == {"Мелом": "A, I START\nAm F C G", "Солнце": "32B <-> 32D\nGm"}


def test_load_missing_db_is_none(tmp_path):
    assert st.load_web_notes(str(tmp_path / "nope.db")) is None


def test_note_replaces_old_text_and_keeps_tags_first():
    old = "[midi: PC62@1]\n[midi@play: START]\n\nold hand-typed text"
    assert st.merge_lyrics(old, BLOCK, "32B <-> 32D\nGm").split("\n") == BLOCK + ["", "32B <-> 32D", "Gm"]
    assert st.merge_lyrics(old, BLOCK, "") == "\n".join(BLOCK)               # note removed on the board
    assert st.merge_lyrics(old, BLOCK, None).split("\n") == BLOCK + ["", "old hand-typed text"]


def test_resync_is_stable():
    once = st.merge_lyrics("", BLOCK, "a\nb")
    assert st.merge_lyrics(once, BLOCK, "a\nb") == once
    assert st.lyrics_text(once) == "a\nb"


def test_practice_tracks_route_to_pb_other_bus_and_start_muted(tmp_path):
    bus = {stem: b for stem, _fn, _nm, b, _p in st.ROUTING}
    assert bus["drums"] == bus["vocal"] == bus["pb-other"]
    assert {"drums", "vocal"} <= st.MUTED
    assert st.stem_src("/r", "drums") == "/r/stems/drums.mp3"
    assert st.stem_src("/r", "vocal") == "/r/stems/vocal.mp3"
    assert st.stem_src("/r", "pb-other") == "/r/pb-other.wav"


def test_all_track_and_mute_groups():
    bus = {stem: b for stem, _fn, _nm, b, _p in st.ROUTING}
    assert bus["all"] == bus["pb-other"] and "all" in st.MUTED
    assert st.stem_src("/r", "all") == "/r/all.wav"
    g = st.MUTE_GROUPS
    assert g["all"] == 0                                              # All is never group-muted
    assert g["click"] == g["cues"] == 0                               # click/cues never group-muted
    assert {s for s in bus if g.get(s, 0) & 1} == {"pb-other", "pb-bass", "drums", "vocal"}
    assert not any(g.get(s, 0) & ~1 for s in bus)                     # one group only
