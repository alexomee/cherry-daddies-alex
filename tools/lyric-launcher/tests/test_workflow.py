import csv
import importlib
import json
import os
import shutil
import subprocess
import sys
import wave
from pathlib import Path

import pytest


def git(root, *args):
    return subprocess.run(["git", "-C", str(root), *args], check=True,
                          capture_output=True, text=True).stdout.strip()


def init_repo(path):
    path.mkdir()
    git(path, "init", "-b", "main")
    git(path, "config", "user.name", "Test Singer")
    git(path, "config", "user.email", "singer@example.test")
    remote = path.with_name(path.name + ".git")
    subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True)
    git(path, "remote", "add", "origin", str(remote))
    return remote


FIELDS = "set song clip pc_field source cat factory_dir bed_dir concert_patch".split()


def row(n, title):
    return dict(zip(FIELDS, [str(n), title, f"{n:02}", str(n + 1), "dynamic", "",
                            f"music/songs/{title}", f"beds/{n:02}", f"{title}.patch"]))


def manifest(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


@pytest.fixture
def env(tmp_path, monkeypatch):
    workflow = importlib.import_module("lyric_workflow")
    root, rig = tmp_path / "main", tmp_path / "rig"
    init_repo(root)
    rig_remote = init_repo(rig)
    here = root / "tools/lyric-launcher"
    manifest(here / "songs.tsv", [row(1, "Песня"), row(2, "Другая")])
    manifest(rig / "lyrics/songs.tsv", [row(1, "Песня"), row(2, "Другая"), row(3, "Rig only")])
    (root / ".gitignore").write_text("*.wav\n*.mp4\n.local/\n")
    audio = root / "reference.wav"
    with wave.open(str(audio), "wb") as w:
        w.setparams((1, 2, 8000, 0, "NONE", "not compressed"))
        w.writeframes(b"\0\0" * 8000 * 4)
    bed = rig / "beds/01"
    bed.mkdir(parents=True)
    (bed / "click.wav").write_bytes(audio.read_bytes())
    (rig / "lyrics/clips").mkdir()
    (rig / "lyrics/clips/02.ass").write_text("colleague's current clip")
    timed = here / "lyrics-timed/01.tsv"
    timed.parent.mkdir()
    timed.write_text("1\tПервая строка\n2\tВторая строка\n")
    for repo in [root, rig]:
        git(repo, "add", ".")
        git(repo, "commit", "-m", "initial")
        git(repo, "push", "-u", "origin", "main")
    # Rendering itself is exercised separately with real mpv; Git race tests
    # don't need repeated video encoding. Build still uses real ffmpeg/ffprobe.
    def render(canvas, ass, audio, output):
        output.write_bytes(b"preview" + ass.read_bytes())
    monkeypatch.setattr(workflow, "render_review", render)
    ws = workflow.Workspace(root, rig)
    ws.build(1, audio)
    ws.review(1)
    ws.approve(1, "Татьяна")
    return ws, root, rig, rig_remote, audio


def test_save_and_selected_delivery_are_remotely_persisted(env):
    ws, root, rig, _, _ = env
    (root / "unrelated.txt").write_text("unfinished work")
    source_commit = ws.save(1, "lyrics: Песня")
    assert git(root, "ls-remote", "origin", "refs/heads/main").split()[0] == source_commit
    before = (rig / "lyrics/clips/02.ass").read_bytes()
    rig_commit = ws.deliver(1, apply=True, message="deliver Песня")
    assert git(rig, "ls-remote", "origin", "refs/heads/main").split()[0] == rig_commit
    assert (rig / "lyrics/clips/02.ass").read_bytes() == before
    assert len(list(csv.DictReader((rig / "lyrics/songs.tsv").open(), delimiter="\t"))) == 3
    assert source_commit in git(rig, "log", "-1", "--format=%B")
    assert "unrelated.txt" not in git(root, "ls-tree", "-r", "--name-only", "HEAD")


@pytest.mark.parametrize("target", ["text", "ass", "audio", "new-override"])
def test_edits_after_approval_require_new_review(env, target):
    ws, root, _, _, audio = env
    p = {"text": ws.here / "lyrics-timed/01.tsv", "ass": ws.here / "clips/01.ass",
         "audio": audio, "new-override": ws.here / "overrides/01.tsv"}[target]
    p.parent.mkdir(exist_ok=True)
    with p.open("ab") as f:
        f.write(b"changed")
    with pytest.raises(ValueError, match="changed|stale"):
        ws.save(1, "must fail")


def test_review_cannot_bless_an_outdated_build(env):
    ws, *_ = env
    (ws.here / "lyrics-timed/01.tsv").write_text("1\tEdited after build\n")
    with pytest.raises(ValueError, match="changed|stale"):
        ws.review(1)


def test_save_does_not_include_someone_elses_staging(env):
    ws, root, *_ = env
    (root / "other.txt").write_text("other change")
    git(root, "add", "other.txt")
    with pytest.raises(ValueError, match="staged"):
        ws.save(1, "must fail")


def test_selected_rig_audio_changed_after_review_blocks_delivery(env):
    ws, _, rig, _, _ = env
    ws.save(1, "save")
    with (rig / "beds/01/click.wav").open("ab") as f:
        f.write(b"new audio")
    git(rig, "add", ".")
    git(rig, "commit", "-m", "new audio")
    git(rig, "push")
    with pytest.raises(ValueError, match="rig.*changed|changed.*rig"):
        ws.deliver(1, apply=True)


def test_other_song_remote_update_is_preserved(env, tmp_path):
    ws, _, rig, remote, _ = env
    ws.save(1, "save")
    other = tmp_path / "colleague"
    subprocess.run(["git", "clone", "-b", "main", str(remote), str(other)], check=True, capture_output=True)
    git(other, "config", "user.name", "Colleague")
    git(other, "config", "user.email", "colleague@example.test")
    (other / "lyrics/clips/02.ass").write_text("NEW colleague lyrics")
    git(other, "add", ".")
    git(other, "commit", "-m", "other song")
    git(other, "push")
    ws.deliver(1, apply=True)
    assert (rig / "lyrics/clips/02.ass").read_text() == "NEW colleague lyrics"


def test_rejected_rig_push_keeps_commit_and_can_retry(env):
    ws, _, rig, remote, _ = env
    ws.save(1, "save")
    hook = remote / "hooks/pre-receive"
    hook.write_text("#!/bin/sh\nexit 1\n")
    hook.chmod(0o755)
    with pytest.raises(ValueError, match="push"):
        ws.deliver(1, apply=True)
    pending = git(rig, "rev-parse", "HEAD")
    hook.unlink()
    assert ws.deliver(1, apply=True) == pending
    assert git(rig, "ls-remote", "origin", "refs/heads/main").split()[0] == pending


def test_dry_run_copies_nothing(env):
    ws, _, rig, _, _ = env
    ws.save(1, "save")
    before = git(rig, "rev-parse", "HEAD")
    ws.deliver(1)
    assert not (rig / "lyrics/clips/01.mp4").exists()
    assert git(rig, "rev-parse", "HEAD") == before


def test_delivery_requires_pushed_source(env):
    ws, *_ = env
    with pytest.raises(ValueError, match="save|commit"):
        ws.deliver(1, apply=True)


def test_manifest_collision_cannot_rename_a_rig_song(env):
    ws, _, rig, _, _ = env
    ws.save(1, "save")
    rows = [row(1, "Different song"), row(2, "Другая")]
    manifest(rig / "lyrics/songs.tsv", rows)
    git(rig, "add", ".")
    git(rig, "commit", "-m", "renumber")
    git(rig, "push")
    with pytest.raises(ValueError):
        ws.deliver(1, apply=True)


def test_repeat_delivery_detects_new_audio_even_when_clips_match(env):
    ws, _, rig, _, _ = env
    ws.save(1, "save")
    ws.deliver(1, apply=True)
    with (rig / "beds/01/click.wav").open("ab") as f:
        f.write(b"new arrangement")
    git(rig, "add", ".")
    git(rig, "commit", "-m", "new playback")
    git(rig, "push")
    with pytest.raises(ValueError, match="rig.*changed|changed.*rig"):
        ws.deliver(1, apply=True)


def test_rejected_source_push_is_not_reported_as_saved(env):
    ws, root, _, _, _ = env
    remote = Path(git(root, "remote", "get-url", "origin"))
    hook = remote / "hooks/pre-receive"
    hook.write_text("#!/bin/sh\nexit 1\n")
    hook.chmod(0o755)
    with pytest.raises(ValueError, match="push NOT confirmed"):
        ws.save(1, "save")
    pending = git(root, "rev-parse", "HEAD")
    hook.unlink()
    assert ws.save(1, "retry") == pending


def test_real_preview_contains_video_audio_and_matching_duration(tmp_path):
    workflow = importlib.import_module("lyric_workflow")
    from make_song_clip import make_ass, make_black
    audio, canvas, ass = tmp_path / "tone.wav", tmp_path / "canvas.mp4", tmp_path / "clip.ass"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i",
                    "sine=frequency=440:duration=2", str(audio)], check=True)
    make_black(str(canvas), 2)
    make_ass(ass, "Проверка", [(0, 1, "Первая строка"), (1, 2, "Вторая строка")], 2, 0)
    output = tmp_path / "review.mp4"
    workflow.render_review(canvas, ass, audio, output)
    result = json.loads(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(output)]))
    assert {s["codec_type"] for s in result["streams"]} == {"video", "audio"}
    assert abs(float(result["format"]["duration"]) - 2) < .1


def test_review_mix_includes_actual_rig_click_when_guide_is_silent(tmp_path):
    workflow = importlib.import_module("lyric_workflow")
    bed = tmp_path / "bed"
    bed.mkdir()
    guide = tmp_path / "guide.wav"
    for path, source in [(guide, "anullsrc=r=16000:cl=mono"),
                         (bed / "click.wav", "sine=frequency=880:sample_rate=16000")]:
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", source,
                        "-t", "2", str(path)], check=True)
    output = tmp_path / "mixed.wav"
    workflow.mix_review_audio(guide, bed, output)
    decoded = subprocess.check_output(["ffmpeg", "-v", "error", "-i", str(output),
                                       "-f", "s16le", "-ac", "1", "-"])
    assert any(decoded), "rig click must be audible over a silent guide"
    assert abs(workflow.duration(output) - 2) < .1


def test_build_rejects_sources_changed_during_encoding(env, monkeypatch):
    ws, _, _, _, audio = env
    workflow = importlib.import_module("lyric_workflow")
    original = workflow.maker.make_black
    def edit_during_encode(path, dur):
        original(path, dur)
        (ws.here / "lyrics-timed/01.tsv").write_text("1\tNew words during encoding\n")
    monkeypatch.setattr(workflow.maker, "make_black", edit_during_encode)
    with pytest.raises(ValueError, match="changed|stale"):
        ws.build(1, audio)


@pytest.mark.parametrize("action", ["check", "save"])
def test_check_and_save_reject_stale_rig_audio(env, action):
    ws, _, rig, _, _ = env
    with (rig / "beds/01/click.wav").open("ab") as f:
        f.write(b"changed playback")
    git(rig, "add", ".")
    git(rig, "commit", "-m", "new playback")
    git(rig, "push")
    with pytest.raises(ValueError, match="rig.*changed|changed.*rig"):
        if action == "check":
            ws.check(1)
        else:
            ws.save(1, "save")


def test_save_after_own_delivery_does_not_invalidate_review(env):
    ws, *_ = env
    source = ws.save(1, "save")
    ws.deliver(1, apply=True)
    ws.check(1)
    assert ws.save(1, "already saved") == source


def test_deploy_wrapper_uses_setup_python(tmp_path):
    here = Path(__file__).resolve().parents[1]
    for p in here.glob("*.py"):
        shutil.copy2(p, tmp_path / p.name)
    shutil.copy2(here / "deploy_clips.sh", tmp_path / "deploy_clips.sh")
    venv = tmp_path / ".venv/bin"
    venv.mkdir(parents=True)
    (venv / "python").symlink_to(sys.executable)
    wrong = tmp_path / "wrong-bin"
    wrong.mkdir()
    (wrong / "python3").write_text("#!/bin/sh\nexit 99\n")
    (wrong / "python3").chmod(0o755)
    environ = dict(os.environ, PATH=f"{wrong}:/usr/bin:/bin")
    environ.pop("PYTHON", None)
    result = subprocess.run(["/bin/bash", str(tmp_path / "deploy_clips.sh"), "--help"],
                            env=environ, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert "--index" in result.stdout
