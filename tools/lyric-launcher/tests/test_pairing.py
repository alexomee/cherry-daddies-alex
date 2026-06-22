# tests/test_pairing.py
# Two-line page-flip: build_pairs groups consecutive lines two-at-a-time but never
# pairs across a gap > max_gap (a section boundary), so a new section starts clean.
from make_song_clip import build_pairs

A = (0.0, 1.0, "a")
B = (1.5, 2.5, "b")
C = (3.0, 4.0, "c")
D = (4.5, 5.5, "d")


def texts(pairs):
    return [[p[2] for p in pr] for pr in pairs]


def test_basic_pairs():
    assert texts(build_pairs([A, B, C, D])) == [["a", "b"], ["c", "d"]]


def test_odd_tail_is_singleton():
    assert texts(build_pairs([A, B, C])) == [["a", "b"], ["c"]]


def test_gap_breaks_pair_and_realigns():
    # big interval before 'b' (start 10 vs a.start 0 = 10s > 6, an instrumental):
    # 'a' shows alone, then b+c pair on the new section, 'd' trails as a singleton.
    far_b = (10.0, 11.0, "b")
    far_c = (11.5, 12.5, "c")
    far_d = (13.0, 14.0, "d")
    assert texts(build_pairs([A, far_b, far_c, far_d])) == [["a"], ["b", "c"], ["d"]]


def test_gap_threshold_is_inclusive():
    # start-to-start interval exactly == max_gap (6.0) still pairs (<=), just over not.
    on = (6.0, 7.0, "b")          # interval 6.0 == max_gap -> pair
    off = (6.01, 7.0, "b")        # interval 6.01 > max_gap -> singleton
    assert texts(build_pairs([A, on])) == [["a", "b"]]
    assert texts(build_pairs([A, off])) == [["a"], ["b"]]
