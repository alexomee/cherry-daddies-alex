import build_manifest


def test_static_song_keeps_its_factory_for_guide_lookup():
    row = build_manifest._row(23, "Мелом", "static", None, "Мелом", "beds/23", "melom.patch", [])
    assert row["factory_dir"] == "music/songs/Мелом"
