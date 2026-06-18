# tests/test_lines_frontend.py
from make_song_clip import parse_lines_table
def test_parse_times_and_lines(tmp_path):
    f = tmp_path/"s.tsv"
    f.write_text("0:21.0\tLucky you were born\n0:25.3\tI love a foreign man\n")
    lines = parse_lines_table(str(f))
    assert lines[0][0] == 21.0 and lines[0][2] == "Lucky you were born"
    assert lines[1][0] == 25.3
    assert lines[0][1] == 25.3          # line end = next line start
