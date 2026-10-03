import functools
import hashlib
import http.server
import importlib
import json
import threading
from pathlib import Path

import pytest


@pytest.fixture
def audio_module():
    return importlib.import_module("guide_audio")


@pytest.fixture
def http_audio(tmp_path):
    served = tmp_path / "served"
    served.mkdir()
    requests = []

    class Handler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            if self.headers.get("User-Agent", "").startswith("Python-urllib"):
                self.send_error(403, "Cloudflare 1010: default urllib user agent")
                return
            requests.append(self.path)
            super().do_GET()

        def log_message(self, *args):
            pass

    server = http.server.ThreadingHTTPServer(
        ("127.0.0.1", 0), functools.partial(Handler, directory=str(served)))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    data = b"selected song audio"
    (served / "all.wav").write_bytes(data)
    entry = {"status": "available", "url": f"http://127.0.0.1:{server.server_port}/all.wav",
             "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}
    yield served, requests, entry, data
    server.shutdown()
    thread.join()
    server.server_close()


def test_download_only_selected_audio_and_reuse_verified_cache(audio_module, http_audio, tmp_path):
    _, requests, entry, data = http_audio
    cache = tmp_path / "cache"
    p = audio_module.download(entry, cache)
    assert p.read_bytes() == data
    assert audio_module.download(entry, cache) == p
    assert requests == ["/all.wav"]
    assert list(cache.rglob("*.wav")) == [p]


def test_corrupt_download_never_becomes_usable_cache(audio_module, http_audio, tmp_path):
    served, _, entry, _ = http_audio
    (served / "all.wav").write_bytes(b"wrong version")
    cache = tmp_path / "cache"
    with pytest.raises(ValueError, match="SHA|size"):
        audio_module.download(entry, cache)
    assert not list(cache.rglob("*.wav"))
    assert not list(cache.rglob("*.part"))


def test_damaged_cache_is_repaired_from_published_bytes(audio_module, http_audio, tmp_path):
    _, requests, entry, data = http_audio
    p = audio_module.download(entry, tmp_path)
    p.write_bytes(b"broken")
    assert audio_module.download(entry, tmp_path).read_bytes() == data
    assert len(requests) == 2


def test_missing_catalogue_names_exact_source_and_publisher_command(audio_module, tmp_path):
    with pytest.raises(ValueError, match=r"music/songs/Test/auto-render/all.wav.*sync_site.py --guides-only"):
        audio_module.lookup(tmp_path, "music/songs/Test")


def test_discover_reports_missing_song_and_versions_by_content(audio_module, tmp_path):
    import subprocess
    for name in ("Ready", "Missing"):
        song = tmp_path / "music/songs" / name
        song.mkdir(parents=True)
        (song / "mix.json").write_text('{}')
    ar = tmp_path / "music/songs/Ready/auto-render"
    ar.mkdir()
    subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i",
                    "sine=frequency=440:duration=1", str(ar / "all.wav")], check=True)
    (ar / "click.wav").write_bytes((ar / "all.wav").read_bytes())
    (ar / "timeline.json").write_text('{"offset_sec": 1.25}')
    cat = audio_module.discover(tmp_path)
    ready = cat["songs"]["music/songs/Ready"]
    assert ready["sha256"] in ready["url"]
    assert ready["timeline"]["offset_sec"] == 1.25
    assert ready["render_audio"]["click.wav"] == ready["sha256"]
    assert cat["songs"]["music/songs/Missing"]["status"] == "missing"


def test_rig_check_uses_click_and_playback_but_current_cues_can_differ(audio_module, tmp_path):
    bed = tmp_path / "bed"
    bed.mkdir()
    for n in ("click.wav", "cues.wav", "pb-other.wav"):
        (bed / n).write_bytes(n.encode())
    entry = {"render_audio": {n: audio_module.sha(bed / n)
                              for n in ("click.wav", "cues.wav", "pb-other.wav")}}
    (bed / "cues.wav").write_bytes(b"new spoken prompts on the same timeline")
    audio_module.validate_rig(entry, bed)
    (bed / "click.wav").write_bytes(b"shifted stage timeline")
    with pytest.raises(ValueError, match="click.wav.*republish"):
        audio_module.validate_rig(entry, bed)


def test_no_available_catalogue_is_written_after_failed_publication(audio_module, tmp_path):
    catalog = {"schema": 1, "songs": {"music/songs/Test": {
        "status": "available", "sha256": "a" * 64, "bytes": 10,
        "url": "https://example.test/all.wav", "key": "test/all.wav"}}}
    def fail(items):
        raise ValueError("upload failed")
    with pytest.raises(ValueError, match="upload failed"):
        audio_module.publish(tmp_path, catalog, fail)
    assert not (tmp_path / "music/guide-catalog.json").exists()


def test_timeline_fingerprint_ignores_headers_and_subaudible_silence_but_not_shift(audio_module, tmp_path):
    import array
    import wave
    samples = array.array("h", [0] * 100 + [1000, -2000, 3000, -4000] * 100 + [0] * 100)
    paths = []
    variants = [samples, samples + array.array("h"), array.array("h", [0]) + samples[:-1]]
    variants[1][-10] = 3  # -80.8 dBFS dither in the silent tail
    for i, data in enumerate(variants):
        p = tmp_path / f"{i}.wav"
        with wave.open(str(p), "wb") as f:
            f.setparams((1, 2, 44100, 0, "NONE", "not compressed"))
            f.writeframes(data.tobytes())
        paths.append(p)
    assert audio_module.pcm_fingerprint(paths[0]) == audio_module.pcm_fingerprint(paths[1])
    assert audio_module.pcm_fingerprint(paths[0]) != audio_module.pcm_fingerprint(paths[2])
