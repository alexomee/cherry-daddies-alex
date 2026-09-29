"""CLI source selection/archiving: real files, no renderer or audio tools invoked."""
from pathlib import Path
import subprocess

import numpy as np
import pytest

import jamzone_warp_ext as W


def source(folder, name, level=0.1):
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / name
    # Tiny float payloads stand in for encoded audio at the codec boundary.
    path.write_bytes(np.full((8, 2), level, dtype=np.float32).tobytes())
    return path


@pytest.fixture
def run_cli(monkeypatch, tmp_path):
    def decode(path):
        return np.frombuffer(Path(path).read_bytes(), np.float32).reshape(-1, 2).copy()

    def encode(cmd, *, input, check):
        assert cmd[0] == "ffmpeg" and check
        out = Path(cmd[-1])
        assert out.is_relative_to(tmp_path)
        out.write_bytes(input)

    monkeypatch.setattr(W, "decode", decode)
    monkeypatch.setattr(W, "grid_dev", lambda audio, bpm: (
        np.array([0., 1.]), np.zeros(2), np.array([0., 1.]), np.arange(2)))
    monkeypatch.setattr(W, "warp_interp", lambda audio, *args: audio * 0.5)
    monkeypatch.setattr(W, "warp_rubberband", lambda audio, *args, **kw: audio * 0.5)
    monkeypatch.setattr(W.shutil, "which", lambda name: "/test/rubberband")
    monkeypatch.setattr(W.subprocess, "run", encode)

    def run(folder, *args):
        monkeypatch.setattr(W.sys, "argv", ["jamzone_warp_ext.py", str(folder), "--bpm", "120", *args])
        W.main()

    return run


@pytest.mark.parametrize("name", [
    "02_Drum_Kit.wav", "female_lead_vocal.wav", "lead_guitars.wav", "Wind Pad.wav",
])
def test_keeps_numbered_and_custom_stems_with_canonical_metronome(tmp_path, run_cli, name):
    originals = tmp_path / "moises-orig"
    source(originals, "metronome.wav")
    source(originals, "bass.wav")
    custom = source(originals, name)  # even identical bytes do not make custom parts aliases
    untouched = custom.read_bytes()

    run_cli(tmp_path)

    assert (tmp_path / name).is_file()
    assert (tmp_path / name).read_bytes() != untouched
    assert custom.read_bytes() == untouched


@pytest.mark.parametrize("role,short", [("Bass", "bass"), ("Background Vocals", "backing_vocals")])
def test_deduplicates_byte_identical_raw_import_alias(tmp_path, run_cli, role, short):
    originals = tmp_path / "moises-orig"
    source(originals, "metronome.mp3")
    source(originals, short + ".mp3", 0.2)
    alias = source(originals, f"Song _video_-{role}-D minor-149bpm-442hz.mp3", 0.2)
    untouched = alias.read_bytes()

    run_cli(tmp_path)

    assert (tmp_path / (short + ".wav")).is_file()
    assert not (tmp_path / (alias.stem + ".wav")).exists()
    assert alias.read_bytes() == untouched
    assert len(list(tmp_path.glob("*.wav"))) == 2


def test_initial_import_archives_duplicate_instead_of_leaving_it_in_root(tmp_path, run_cli):
    source(tmp_path, "metronome.mp3")
    source(tmp_path, "bass.mp3", 0.2)
    alias = source(tmp_path, "Song _video_-Bass-D minor-149bpm-442hz.mp3", 0.2)
    untouched = alias.read_bytes()

    run_cli(tmp_path)

    assert not alias.exists()  # the renderer must not pick up the raw duplicate
    assert (tmp_path / "moises-orig" / alias.name).read_bytes() == untouched
    assert sorted(p.name for p in tmp_path.glob("*.wav")) == ["bass.wav", "metronome.wav"]


@pytest.mark.parametrize("from_orig", [False, True], ids=["first-import", "rewarp"])
@pytest.mark.parametrize("name", [
    "count-in.mp3", "count_in.mp3",
    "Ту-лу-ла _gLe11ZntDCs_-Count-in-D major-131bpm-442hz.mp3",
])
def test_service_count_in_stays_outside_renderer_root(tmp_path, run_cli, from_orig, name):
    originals = tmp_path / "moises-orig"
    folder = originals if from_orig else tmp_path
    source(folder, "metronome.mp3")
    source(folder, "bass.mp3", 0.2)
    count_in = source(folder, name, 0.3)
    untouched = count_in.read_bytes()

    run_cli(tmp_path)

    assert sorted(p.name for p in tmp_path.iterdir() if p.is_file()) == ["bass.wav", "metronome.wav"]
    assert (originals / name).read_bytes() == untouched


@pytest.mark.parametrize("counterpart", ["different_bytes", "missing", "wrong_role"])
def test_keeps_raw_named_stem_without_an_identical_same_role_alias(tmp_path, run_cli, counterpart):
    originals = tmp_path / "moises-orig"
    source(originals, "metronome.mp3")
    raw = source(originals, "Song _video_-Bass-D minor-149bpm-442hz.mp3", 0.2)
    if counterpart == "different_bytes":
        source(originals, "bass.mp3", 0.3)
    elif counterpart == "wrong_role":
        source(originals, "guitars.mp3", 0.2)

    run_cli(tmp_path)

    assert (tmp_path / (raw.stem + ".wav")).is_file()


def test_initial_wav_preserves_original_and_leaves_warped_root_on_rerun(tmp_path, run_cli):
    source(tmp_path, "metronome.wav")
    bass = source(tmp_path, "bass.wav", 0.2)
    untouched = bass.read_bytes()

    run_cli(tmp_path)

    assert (tmp_path / "moises-orig/bass.wav").read_bytes() == untouched
    assert bass.is_file()
    warped = bass.read_bytes()
    assert warped != untouched
    run_cli(tmp_path)
    assert bass.read_bytes() == warped  # rerun reads the original, not already-warped audio
    assert (tmp_path / "moises-orig/bass.wav").read_bytes() == untouched


def test_failed_encode_does_not_overwrite_initial_wav(tmp_path, run_cli, monkeypatch):
    source(tmp_path, "metronome.wav")
    bass = source(tmp_path, "bass.wav", 0.2)
    untouched = bass.read_bytes()

    def fail_encode(cmd, **kwargs):
        Path(cmd[-1]).write_bytes(b"incomplete output")
        raise subprocess.CalledProcessError(1, cmd)

    monkeypatch.setattr(W.subprocess, "run", fail_encode)
    with pytest.raises(subprocess.CalledProcessError):
        run_cli(tmp_path)

    assert bass.read_bytes() == untouched


def test_check_mode_leaves_sources_in_place(tmp_path, run_cli):
    metro = source(tmp_path, "metronome.wav")
    bass = source(tmp_path, "bass.wav", 0.2)
    before = {p.name: p.read_bytes() for p in (metro, bass)}

    run_cli(tmp_path, "--check")

    assert {p.name: p.read_bytes() for p in tmp_path.iterdir()} == before
