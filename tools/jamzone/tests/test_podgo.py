"""POD Go preset changes: mix.json "podgo" abs_sec write-back (jamzone_render) and the
Stage Traxx tags built from it (stagetraxx_sync): PC on channel 3, changes PODGO_LEAD (1.0 s) early."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import jamzone_render as jr  # noqa: E402
import stagetraxx_sync as st  # noqa: E402

MIX = """{
  "cues": [
    {"bar": 1, "text": "Song all in", "abs_sec": 3.478, "snap_sec": 0.0}
  ],
  "gm800": [
    {"bar": 1,  "scene": 7}
  ],
  "podgo": [
    {"bar": 1,  "preset": "02A"},
    {"bar": 33, "beat": 3, "preset": "03C"}
  ]
}"""


def test_abs_written_only_on_preset_lines(tmp_path):
    p = tmp_path / "mix.json"
    p.write_text(MIX, encoding="utf-8")
    assert jr.write_device_abs_times(str(p), "podgo", "preset", [3.478, 61.2504]) is None
    out = p.read_text(encoding="utf-8")
    assert '{"bar": 1,  "preset": "02A", "abs_sec": 3.478}' in out
    assert '{"bar": 33, "beat": 3, "preset": "03C", "abs_sec": 61.25}' in out
    assert '{"bar": 1,  "scene": 7}' in out                                   # GM-800 line untouched
    assert '"text": "Song all in", "abs_sec": 3.478, "snap_sec": 0.0}' in out  # cue untouched
    # and the GM-800 write-back doesn't pick up the preset lines
    assert jr.write_device_abs_times(str(p), "gm800", "scene", [3.478]) is None


@pytest.mark.parametrize("preset,pc", [("01A", 0), ("01D", 3), ("02A", 4), ("2a", 4),
                                       ("03C", 10), ("32D", 127)])
def test_preset_to_pc(preset, pc):
    assert st.podgo_pc(preset) == pc


@pytest.mark.parametrize("bad", ["00A", "33A", "02E", "2", "A2", 4, None])
def test_preset_rejects(bad):
    with pytest.raises(ValueError, match="01A..32D"):
        st.podgo_pc(bad)


def test_whole_song_preset():
    assert st.device_block(st.parse_device("podgo", "02A"), 3, st.PODGO_LEAD) == [
        "[midi: PC4@3]", "[midi@00:00.000: PC4@3]"]


def test_changes_go_out_a_second_early_and_dedupe():
    ch = st.parse_device("podgo", [
        {"bar": 1, "preset": "02A", "abs_sec": 3.478},
        {"bar": 9, "preset": "02A", "abs_sec": 17.391},     # same preset again -> dropped
        {"bar": 33, "preset": "03C", "abs_sec": 61.25},
    ])
    assert st.device_block(ch, 3, st.PODGO_LEAD) == [
        "[midi: PC4@3]", "[midi@00:00.000: PC4@3]", "[midi@01:00.250: PC10@3]"]


def test_early_change_never_goes_negative():
    assert st.device_block([(0, 4, "02A"), (0.1, 10, "03C")], 3, 0.2)[-1] == "[midi@00:00.000: PC10@3]"


def test_both_devices_in_one_block():
    devices = {"gm800": st.parse_device("gm800", 1), "podgo": st.parse_device("podgo", "02A")}
    assert st.devices_block(devices, {}) == [
        "[midi: PC0@2]", "[midi@00:00.000: PC0@2]", "[midi: PC4@3]", "[midi@00:00.000: PC4@3]"]
    assert st.devices_block({"podgo": devices["podgo"]}, {"podgo": 5})[0] == "[midi: PC4@5]"


@pytest.mark.parametrize("v,msg", [
    ([{"bar": 1, "preset": "02A"}], "no abs_sec"),
    ([{"bar": 1, "preset": "2E", "abs_sec": 1}], "01A..32D"),
    ([{"bar": 1, "scene": 7, "abs_sec": 1}], "01A..32D"),
    ([{"preset": "02A", "abs_sec": 9}, {"preset": "02B", "abs_sec": 1}], "time order"),
    (4, "non-empty"),
    ([], "non-empty"),
])
def test_parse_rejects(v, msg):
    with pytest.raises(ValueError, match=msg):
        st.parse_device("podgo", v)


# --- GM-800 ASSIGN CCs ("gm800_cc") -------------------------------------------------------------

def test_gm800_cc_abs_written_only_on_cc_lines(tmp_path):
    p = tmp_path / "mix.json"
    p.write_text('{\n  "gm800": 27,\n  "gm800_cc": [\n    {"bar": 1,  "cc": 80, "value": 0},\n'
                 '    {"bar": 17, "cc": 80, "value": 127}\n  ],\n'
                 '  "cues": [\n    {"bar": 17, "text": "bass in"}\n  ]\n}', encoding="utf-8")
    assert jr.write_device_abs_times(str(p), "gm800_cc", "cc", [3.489, 31.398]) is None
    out = p.read_text(encoding="utf-8")
    assert '{"bar": 17, "cc": 80, "value": 127, "abs_sec": 31.398}' in out
    assert '{"bar": 17, "text": "bass in"}' in out


def test_cc_block_start_state_then_early_change():
    ev = st.parse_cc([{"bar": 1, "cc": 80, "value": 0, "abs_sec": 3.489},
                      {"bar": 9, "cc": 80, "value": 0, "abs_sec": 17.4},       # no change -> dropped
                      {"bar": 17, "cc": 80, "value": 127, "abs_sec": 31.398}])
    assert st.cc_block(ev, 2) == ["[midi: CC80.0@2]", "[midi@00:00.000: CC80.0@2]",
                                  "[midi@00:30.898: CC80.127@2]"]


def test_cc_tags_follow_the_scene_pc():
    devices = {"gm800": st.parse_device("gm800", 27),
               "gm800_cc": st.parse_cc([{"cc": 80, "value": 0, "abs_sec": 3.5},
                                        {"cc": 80, "value": 127, "abs_sec": 31.4}])}
    assert st.devices_block(devices, {}) == [
        "[midi: PC26@2]", "[midi@00:00.000: PC26@2]",
        "[midi: CC80.0@2]", "[midi@00:00.000: CC80.0@2]", "[midi@00:30.900: CC80.127@2]"]


@pytest.mark.parametrize("v,msg", [
    ([{"cc": 74, "value": 1, "abs_sec": 1}], "not 71..79"),
    ([{"cc": 40, "value": 1, "abs_sec": 1}], "1..31 or 64..95"),
    ([{"cc": 80, "value": 128, "abs_sec": 1}], "0..127"),
    ([{"cc": 80, "value": 1}], "no abs_sec"),
    ([], "non-empty"),
])
def test_parse_cc_rejects(v, msg):
    with pytest.raises(ValueError, match=msg):
        st.parse_cc(v)


def test_switch_leads():
    assert st.SWITCH_LEAD == 0.5
    assert st.GM_CC_LEAD == st.DEVICES["gm800"]["lead"] == st.SWITCH_LEAD
    assert st.PODGO_LEAD == st.DEVICES["podgo"]["lead"] == 1.0


# --- per-switch "lead" exceptions -----------------------------------------------------------------

def test_lead_exception_overrides_one_switch():
    ch = st.parse_device("podgo", [
        {"bar": 1, "preset": "32A", "abs_sec": 3.0},
        {"bar": 9, "preset": "32D", "lead": -1, "abs_sec": 20.0},      # 1 s AFTER the bar
        {"bar": 33, "preset": "32A", "lead": 2, "abs_sec": 60.0},      # 2 s before
        {"bar": 41, "preset": "32D", "abs_sec": 75.0},                 # standard 1 s
    ])
    assert st.device_block(ch, 3, st.PODGO_LEAD)[2:] == [
        "[midi@00:21.000: PC127@3]", "[midi@00:58.000: PC124@3]", "[midi@01:14.000: PC127@3]"]


def test_lead_exception_gm800_scene_and_cc():
    ch = st.parse_device("gm800", [{"scene": 7, "abs_sec": 3.0},
                                   {"scene": 8, "lead": 0, "abs_sec": 31.304}])
    assert st.device_block(ch, 2, st.SWITCH_LEAD)[-1] == "[midi@00:31.304: PC7@2]"
    ev = st.parse_cc([{"cc": 80, "value": 0, "abs_sec": 3.5},
                      {"cc": 80, "value": 127, "lead": -0.5, "abs_sec": 31.4}])
    assert st.cc_block(ev, 2)[-1] == "[midi@00:31.900: CC80.127@2]"


@pytest.mark.parametrize("v,msg", [
    ([{"preset": "02A", "abs_sec": 1}, {"preset": "02B", "lead": "1", "abs_sec": 9}], '"lead" must be'),
    ([{"preset": "02A", "abs_sec": 1}, {"preset": "02B", "lead": 60, "abs_sec": 90}], '"lead" must be'),
    ([{"preset": "02A", "abs_sec": 1}, {"preset": "02B", "lead": -3, "abs_sec": 9},
      {"preset": "02A", "abs_sec": 11}], "out of order"),
])
def test_lead_exception_rejects(v, msg):
    with pytest.raises(ValueError, match=msg):
        st.parse_device("podgo", v)


def test_song_switch_lead():
    assert st.song_lead({}, "podgo") is None
    assert st.song_lead({"switch_lead": 0.3}, "podgo") == st.song_lead({"switch_lead": 0.3}, "gm800_cc") == 0.3
    per = {"switch_lead": {"gm800": 0.2}}
    assert st.song_lead(per, "podgo") is None and st.song_lead(per, "gm800_cc") == 0.2
    ch = st.parse_device("podgo", [
        {"preset": "32A", "abs_sec": 3.694},
        {"preset": "32B", "abs_sec": 11.081},
        {"preset": "32D", "lead": 1, "abs_sec": 40.631},       # an entry's own lead still wins
    ], st.song_lead({"switch_lead": 0.3}, "podgo"))
    assert st.device_block(ch, 3, st.PODGO_LEAD)[2:] == [
        "[midi@00:10.781: PC125@3]", "[midi@00:39.631: PC127@3]"]
    for bad in ({"switch_lead": "0.3"}, {"switch_lead": 60}, {"switch_lead": {"pod": 1}}):
        with pytest.raises(ValueError, match="switch_lead"):
            st.song_lead(bad, "podgo")
