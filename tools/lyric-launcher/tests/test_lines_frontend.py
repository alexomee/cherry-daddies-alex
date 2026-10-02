# tests/test_lines_frontend.py
from make_song_clip import parse_lines_table
import pytest
def test_parse_times_and_lines(tmp_path):
    f = tmp_path/"s.tsv"
    f.write_text("0:21.0\tLucky you were born\n0:25.3\tI love a foreign man\n")
    lines = parse_lines_table(str(f))
    assert lines[0][0] == 21.0 and lines[0][2] == "Lucky you were born"
    assert lines[1][0] == 25.3
    assert lines[0][1] == 25.3          # line end = next line start


@pytest.mark.parametrize("text", [
    "nan\tслово\n", "-1\tслово\n", "1\t\n", "1 без таба\n",
    "2\tпервая\n1\tвторая\n", "1\tпервая\n1\tвторая\n", "",
])
def test_invalid_timing_rejected_before_render(tmp_path, text):
    path = tmp_path / "bad.tsv"
    path.write_text(text)
    with pytest.raises(ValueError):
        parse_lines_table(path)


def test_ass_never_extends_beyond_audio(tmp_path):
    from make_song_clip import make_ass
    path = tmp_path / "test.ass"
    make_ass(path, "song", [(9, 12, "last line")], 10, 0)
    for row in path.read_text().splitlines():
        if row.startswith("Dialogue:"):
            assert row.split(",")[2] <= "0:00:10.00"
