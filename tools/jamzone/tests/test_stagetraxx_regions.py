"""Stage Traxx regions built from mix.json cues (stagetraxx_sync.cue_regions)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import stagetraxx_sync as st  # noqa: E402


def test_regions_tile_song_from_snap_points():
    cues = [
        {"bar": 1, "text": "Солнышко all in", "abs_sec": 3.478, "snap_sec": 0.0},
        {"bar": 7, "beat": 4, "text": "stop", "abs_sec": 15.217, "snap_sec": 11.304},
        {"bar": 17, "text": "alex in", "abs_sec": 31.304, "snap_sec": 27.826},
    ]
    assert st.cue_regions(cues, 260.0) == [
        ("1 · Солнышко all in", 0.0, 11.304),
        ("7.4 · stop", 11.304, 27.826),
        ("17 · alex in", 27.826, 260.0),
    ]


def test_count_in_region_and_fallbacks():
    cues = [
        {"bar": 1, "text": "all in", "abs_sec": 5.0},                       # no snap -> abs
        {"bar": 2, "text": "not rendered"},                                 # no abs_sec -> skipped
        {"bar": 3, "text": "late snap", "abs_sec": 9.0, "snap_sec": 4.0},   # snap goes back -> abs
        {"bar": 3, "text": "same spot", "abs_sec": 9.0},                    # no progress -> skipped
    ]
    assert st.cue_regions(cues, 20.0) == [
        ("count-in", 0.0, 5.0),
        ("1 · all in", 5.0, 9.0),
        ("3 · late snap", 9.0, 20.0),
    ]


def test_no_cues_no_regions():
    assert st.cue_regions([], 100.0) == []
    assert st.cue_regions([{"bar": 1, "text": "x", "abs_sec": 120.0}], 100.0) == []
