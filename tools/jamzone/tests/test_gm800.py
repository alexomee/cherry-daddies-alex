"""GM-800 scene changes: mix.json "gm800" abs_sec write-back (jamzone_render) and the
Stage Traxx MIDI tags built from it (stagetraxx_sync)."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import jamzone_render as jr  # noqa: E402
import stagetraxx_sync as st  # noqa: E402

MIX = """{
  "bpm": 138,
  "cues": [
    {"bar": 1, "text": "Солнышко all in", "abs_sec": 3.478, "snap_sec": 0.0},
    {"bar": 17, "text": "alex in"}
  ],
  "gm800": [
    {"bar": 1,  "scene": 7},
    {"bar": 17, "beat": 4, "scene": 8, "abs_sec": 99.0}
  ]
}"""


def test_gm800_abs_written_only_on_scene_lines(tmp_path):
    p = tmp_path / "mix.json"
    p.write_text(MIX, encoding="utf-8")
    assert jr.write_device_abs_times(str(p), "gm800", "scene", [3.4781, 31.3]) is None
    out = p.read_text(encoding="utf-8")
    assert '{"bar": 1,  "scene": 7, "abs_sec": 3.478}' in out
    assert '{"bar": 17, "beat": 4, "scene": 8, "abs_sec": 31.3}' in out      # stale value replaced
    assert '{"bar": 17, "text": "alex in"}' in out                            # cue line untouched
    assert jr.write_device_abs_times(str(p), "gm800", "scene", [3.4781, 31.3]) is None           # idempotent
    assert p.read_text(encoding="utf-8") == out


def test_gm800_count_mismatch_writes_nothing(tmp_path):
    p = tmp_path / "mix.json"
    p.write_text(MIX, encoding="utf-8")
    assert "2 gm800 lines vs 1 computed" in jr.write_device_abs_times(str(p), "gm800", "scene", [1.0])
    assert p.read_text(encoding="utf-8") == MIX


def test_cue_write_back_ignores_gm800_lines(tmp_path):
    p = tmp_path / "mix.json"
    p.write_text(MIX, encoding="utf-8")
    assert jr.write_cue_abs_times(str(p), [3.478, 31.304], [0.0, 27.8]) is None
    out = p.read_text(encoding="utf-8")
    assert '"text": "alex in", "abs_sec": 31.304, "snap_sec": 27.8}' in out
    assert '{"bar": 1,  "scene": 7}' in out


def test_block_from_list_dedupes_and_offsets_pc():
    changes = st.parse_device("gm800", [
        {"bar": 1, "scene": 7, "abs_sec": 3.478},
        {"bar": 9, "scene": 7, "abs_sec": 17.391},       # same scene again -> dropped
        {"bar": 17, "scene": 8, "abs_sec": 31.304},
        {"bar": 40, "scene": 1, "abs_sec": 71.3005},
    ])
    assert st.device_block(changes, 2) == [
        "[midi: PC6@2]",
        "[midi@00:00.000: PC6@2]",
        "[midi@00:31.304: PC7@2]",
        "[midi@01:11.300: PC0@2]",
    ]


def test_block_whole_song_scene():
    assert st.device_block(st.parse_device("gm800", 1), 3) == ["[midi: PC0@3]", "[midi@00:00.000: PC0@3]"]
    assert st.parse_device("gm800", None) is None
    assert st.device_block(None, 2) == []


@pytest.mark.parametrize("sec,txt", [(0, "00:00.000"), (61.5, "01:01.500"),
                                     (59.9996, "01:00.000"), (600.25, "10:00.250")])
def test_mmss(sec, txt):
    assert st.mmss(sec) == txt


@pytest.mark.parametrize("gm,msg", [
    ([{"bar": 1, "scene": 7}], "no abs_sec"),
    ([{"bar": 1, "scene": 0, "abs_sec": 1}], "1..128"),
    ([{"bar": 1, "scene": "7", "abs_sec": 1}], "1..128"),
    ([{"scene": 2, "abs_sec": 9}, {"scene": 3, "abs_sec": 1}], "time order"),
    ([], "non-empty"),
    (True, "non-empty"),
])
def test_parse_rejects(gm, msg):
    with pytest.raises(ValueError, match=msg):
        st.parse_device("gm800", gm)


def test_merge_replaces_old_midi_tags():
    old = "[midi: PC6@2]\n[midi@00:03.00: PC7@2]\n[midi: PC12@1]\n[midi@play: START]\n\nverse text"
    block = st.midi_block(12, 1) + st.device_block(st.parse_device("gm800", 1), 2)
    assert st.merge_lyrics(old, block).split("\n") == [
        "[midi: PC12@1]", "[midi@play: START]", "[midi@stop: STOP]",
        "[midi: PC0@2]", "[midi@00:00.000: PC0@2]", "", "verse text"]
