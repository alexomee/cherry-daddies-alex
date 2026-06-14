#!/usr/bin/env python3
"""
render_audio.py — rebuild the audio track of a promo video from an edl.json recipe.

Pipeline (per project under assets/video/projects/<name>/):
  bed  = song, seeked to `song_seek`, taken for the full video length, fade-out tail
  vo   = voiceover, delayed by `vo_offset` so it lands at its original spot in the cut
  duck = bed is sidechain-compressed by the vo (music drops under speech, recovers in gaps)
  mux  = new stereo audio replaces the original; video stream copied (no re-encode)

Output: auto-render/<out_prefix>_v<N>.mp4  (N auto-increments — never overwrites a render).

Usage:
  tools/video/render_audio.py assets/video/projects/dance2000-promo/edl.json
  tools/video/render_audio.py <edl.json> --version 3      # force a version number
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


def ffprobe_duration(path: Path) -> float:
    out = subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(path),
    ], text=True)
    return float(out.strip())


def next_version(out_dir: Path, prefix: str, forced: int | None) -> int:
    if forced is not None:
        return forced
    existing = []
    for p in out_dir.glob(f"{prefix}_v*.mp4"):
        m = re.search(rf"{re.escape(prefix)}_v(\d+)\.mp4$", p.name)
        if m:
            existing.append(int(m.group(1)))
    return (max(existing) + 1) if existing else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("edl", help="path to edl.json")
    ap.add_argument("--version", type=int, default=None, help="force output version number")
    args = ap.parse_args()

    edl_path = Path(args.edl).resolve()
    proj = edl_path.parent
    edl = json.loads(edl_path.read_text())

    video = (proj / edl["video"]).resolve()
    song = (proj / edl["song"]).resolve()
    vo = (proj / edl["voiceover"]).resolve()
    for f, label in [(video, "video"), (song, "song"), (vo, "voiceover")]:
        if not f.exists():
            print(f"ERROR: {label} not found: {f}", file=sys.stderr)
            return 1

    dur = ffprobe_duration(video)
    song_seek = float(edl.get("song_seek", 0.0))
    vo_offset = float(edl.get("vo_offset", 0.0))
    bed_gain = float(edl.get("bed_gain_db", 0.0))
    vo_gain = float(edl.get("vo_gain_db", 0.0))
    fadeout = float(edl.get("bed_fadeout", 0.0))
    d = edl.get("duck", {})
    thr = d.get("threshold", 0.03)
    ratio = d.get("ratio", 8)
    attack = d.get("attack", 20)
    release = d.get("release", 300)

    vo_ms = int(round(vo_offset * 1000))
    fade_st = max(0.0, dur - fadeout)

    # pad-to-exact-length helper so no stream can drift the mix duration
    pad = f"apad,atrim=duration={dur:.4f},asetpts=N/SR/TB"

    bed_chain = (
        f"[1:a]aformat=sample_rates=44100:channel_layouts=stereo,"
        f"{pad},volume={bed_gain}dB"
    )
    if fadeout > 0:
        bed_chain += f",afade=t=out:st={fade_st:.4f}:d={fadeout}"
    bed_chain += "[bed]"

    # VO is decoded twice (inputs 2 and 3) so the sidechain key and the audible
    # copy are independent — asplit here silently drops the mix branch.
    filtergraph = ";".join([
        bed_chain,
        f"[2:a]aformat=sample_rates=44100:channel_layouts=stereo,"
        f"volume={vo_gain}dB,adelay={vo_ms}|{vo_ms},{pad}[vomix]",
        f"[3:a]aformat=sample_rates=44100:channel_layouts=stereo,"
        f"adelay={vo_ms}|{vo_ms},{pad}[vokey]",
        f"[bed][vokey]sidechaincompress=threshold={thr}:ratio={ratio}:"
        f"attack={attack}:release={release}[bedduck]",
        "[bedduck][vomix]amix=inputs=2:normalize=0:duration=longest[mix]",
    ])

    out_dir = proj / "auto-render"
    out_dir.mkdir(exist_ok=True)
    ver = next_version(out_dir, edl["out_prefix"], args.version)
    out = out_dir / f"{edl['out_prefix']}_v{ver}.mp4"

    cmd = [
        "ffmpeg", "-y",
        "-i", str(video),
        "-ss", f"{song_seek}", "-i", str(song),
        "-i", str(vo),
        "-i", str(vo),
        "-filter_complex", filtergraph,
        "-map", "0:v", "-map", "[mix]",
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "256k",
        "-t", f"{dur:.4f}",
        "-movflags", "+faststart",
        str(out),
    ]
    print("VO onset:", f"{vo_offset}s", "| song from:", f"{song_seek}s",
          "| video:", f"{dur:.3f}s")
    print("render →", out)
    r = subprocess.run(cmd)
    if r.returncode != 0:
        return r.returncode
    print("OK:", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
