"""Portable clean all.wav catalogue, publication and single-song download.

No cloud credentials are needed by recipients. Publication is called by
tools/sync_site.py using its existing R2 uploader/credentials.
"""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile
from urllib.parse import urlparse
from urllib.request import Request, urlopen

CATALOG = Path("music/guide-catalog.json")
HOST = "https://releases.agentiqa.com"


def sha(path):
    with Path(path).open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def pcm_fingerprint(path):
    """44.1k stereo PCM identity, ignoring headers and silence below -78 dBFS.

    This does not align/stretch/normalize music. Even a one-sample shift changes
    the hash. The silence floor tolerates tiny dither left in rig WAV tails.
    """
    gate = "|".join(f"if(lte(abs(val({i}))\\,0.0001220703125)\\,0\\,val({i}))" for i in (0, 1))
    command = ["ffmpeg", "-v", "error", "-i", str(path), "-af",
               "aformat=sample_rates=44100:channel_layouts=stereo,aeval=" + gate,
               "-f", "s16le", "-ac", "2", "-ar", "44100", "-"]
    with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as p:
        digest = hashlib.file_digest(p.stdout, "sha256").hexdigest()
        error = p.stderr.read().decode(errors="replace")
        if p.wait():
            raise ValueError(f"cannot fingerprint {path}: {error}")
    return digest


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                     delete=False) as f:
        temp = Path(f.name)
        json.dump(value, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")
    try:
        temp.replace(path)
    finally:
        temp.unlink(missing_ok=True)


def lookup(root, factory):
    path = root / CATALOG
    catalog = json.loads(path.read_text()) if path.is_file() else {}
    entry = catalog.get("songs", {}).get(factory)
    if not entry or entry.get("status") != "available":
        raise ValueError(
            f"Missing guide: {factory or '<factory_dir missing>'}/auto-render/all.wav. "
            "Ask Alex to render this song and run python3 tools/sync_site.py --guides-only, "
            "commit/push music/guide-catalog.json; then sync and retry preview. "
            "A silent clip or pb-other.wav cannot replace the vocal guide.")
    return entry


def discover(root):
    """Include every configured song, including those not in the lyric setlist yet."""
    songs = {}
    for mix in sorted((root / "music/songs").glob("*/mix.json")):
        factory = mix.parent.relative_to(root).as_posix()
        ar = mix.parent / "auto-render"
        audio = ar / "all.wav"
        missing = [n for n in ("all.wav", "click.wav", "timeline.json") if not (ar / n).is_file()]
        if missing:
            songs[factory] = {"status": "missing", "missing": missing}
            continue
        digest = sha(audio)
        slug = hashlib.sha1(mix.parent.name.encode()).hexdigest()[:12]
        key = f"cherry-dash/{slug}/guides/{digest}/all.wav"
        probe = json.loads(subprocess.check_output([
            "ffprobe", "-v", "error", "-show_entries",
            "format=duration:stream=codec_type,sample_rate,channels", "-of", "json", str(audio)]))
        streams = [s for s in probe["streams"] if s["codec_type"] == "audio"]
        if len(streams) != 1:
            raise ValueError(f"expected one audio stream: {audio}")
        songs[factory] = {
            "status": "available", "key": key, "url": f"{HOST}/{key}",
            "sha256": digest, "bytes": audio.stat().st_size,
            "duration_sec": float(probe["format"]["duration"]),
            "sample_rate": int(streams[0]["sample_rate"]), "channels": streams[0]["channels"],
            "timeline": json.loads((ar / "timeline.json").read_text()),
            "mix_sha256": sha(mix),
            "render_audio": {p.name: sha(p) for p in sorted(ar.glob("*.wav"))
                             if p.name in ("click.wav", "cues.wav") or p.name.startswith("pb-")},
            "render_pcm": {name: pcm_fingerprint(ar / name)
                           for name in ("click.wav", "pb-other.wav", "pb-bass.wav") if (ar / name).is_file()},
            "content": "clean full music/vocal render; no added click or cues",
        }
    return {"schema": 1, "songs": songs}


def transfer(entry, output=None):
    """Stream and verify public bytes; never buffer a whole WAV in memory."""
    url = entry["url"]
    parsed = urlparse(url)
    if parsed.scheme != "https" and not (parsed.scheme == "http" and parsed.hostname in ("127.0.0.1", "localhost")):
        raise ValueError("guide URL must use HTTPS")
    digest, count = hashlib.sha256(), 0
    request = Request(url, headers={"User-Agent": "CherryDaddies-Guide/1.0"})
    with urlopen(request, timeout=90) as response:
        if response.headers.get_content_type() not in ("audio/wav", "audio/x-wav", "audio/vnd.wave"):
            raise ValueError(f"guide response is not WAV: {url}")
        while block := response.read(1024 * 1024):
            count += len(block)
            if count > entry["bytes"]:
                raise ValueError(f"guide size mismatch: {url}")
            digest.update(block)
            if output is not None:
                output.write(block)
    if count != entry["bytes"] or digest.hexdigest() != entry["sha256"]:
        raise ValueError(f"guide size/SHA-256 mismatch: {url}; retry / ask Alex to republish")


def download(entry, cache):
    digest = entry["sha256"]
    if not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise ValueError("invalid guide SHA-256")
    target = cache / digest / "all.wav"
    if target.is_file() and target.stat().st_size == entry["bytes"] and sha(target) == digest:
        return target
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=target.parent, suffix=".part", delete=False) as f:
        temp = Path(f.name)
        try:
            transfer(entry, f)
        except Exception:
            temp.unlink(missing_ok=True)
            raise
    temp.replace(target)
    return target


def validate_rig(entry, bed):
    """Click is the timeline anchor; changed cue wording is deliberately allowed.

    Shared playback stems must still match the reference render. New rig-only
    rehearsal tracks (e.g. pb-drums with cues) are not guide sources.
    This fingerprint check is not a substitute for measuring a new render's
    musical alignment or the vocalist's review.
    """
    expected = entry.get("render_audio", {})
    for name in ("click.wav", "cues.wav"):
        if not (bed / name).is_file():
            raise ValueError(f"rig audio missing: {bed / name}; fetch the selected song first")
    for name in ("click.wav", "pb-other.wav", "pb-bass.wav"):
        p = bed / name
        if name == "click.wav" or (p.is_file() and name in expected):
            if name not in expected or sha(p) != expected[name]:
                pcm = entry.get("render_pcm", {}).get(name)
                if not pcm or pcm_fingerprint(p) != pcm:
                    raise ValueError(f"guide does not match rig {name}: {bed / name}; "
                                     "ask Alex to align all.wav against current stage audio and republish")


def publish(root, catalog, upload):
    """Only advertise a version after upload + public HTTP SHA verification."""
    path = root / CATALOG
    previous = json.loads(path.read_text()).get("songs", {}) if path.is_file() else {}
    changed = {k: v for k, v in catalog["songs"].items()
               if v["status"] == "available" and previous.get(k, {}).get("sha256") != v["sha256"]}
    print(f"Guides: {len(changed)} new WAV version(s); "
          f"{sum(v['status'] == 'available' for v in catalog['songs'].values())} available", flush=True)
    if changed:
        upload([{"file": str(root / factory / "auto-render/all.wav"), "key": e["key"]}
                for factory, e in changed.items()])
        with ThreadPoolExecutor(max_workers=4) as pool:
            list(pool.map(transfer, changed.values()))
        for factory, entry in changed.items():
            if sha(root / factory / "auto-render/all.wav") != entry["sha256"]:
                raise ValueError(f"all.wav changed during publication: {factory}; retry")
    write_json(path, catalog)
    for factory, entry in catalog["songs"].items():
        if entry["status"] != "available":
            print(f"MISSING guide: {factory}/auto-render/ — {', '.join(entry['missing'])}")
    print(f"Published catalogue: {path}; commit/push it so recipients can sync.", flush=True)
