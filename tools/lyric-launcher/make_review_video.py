#!/usr/bin/env python3
"""Burn a song's launcher lyric clip over its audio -> a phone-shareable review mp4.

For the vocalist (no Mac) to check lyric FLOW and point edits by timecode:
the real Now/Next stage display, in sync with the song, plus a running M:SS
timecode (top-right) she can cite ("0:17 -> make these one line").

The clip .ass already sits on the render timeline (make_song_clip.py shifts it
by offset_sec), the same timeline all.wav uses -> burning lyrics over all.wav
needs no offset. We assert the clip and audio durations match and refuse if
they drift (catches a stale re-render before it makes a misleading review).

Rendering is mpv (this repo's homebrew ffmpeg has no libass/drawtext); the
timecode is baked into a combined .ass as per-second lines, so mpv burns
lyrics + clock in one pass.

Usage:
  make_review_video.py "I Love It"            # name substring (from songs.tsv)
  make_review_video.py "Icona Pop & Charli XCX - I Love It"   # folder name
  make_review_video.py "I Love It" --audio cue_preview        # +click/cues
  make_review_video.py "I Love It" --out /tmp/x.mp4
"""
import argparse
import csv
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))           # tools/lyric-launcher -> repo root
TSV = os.path.join(HERE, "songs.tsv")
CLIPS = os.path.join(HERE, "clips")

# top-right (alignment 9), white, thick outline (canvas is black -> always legible)
TC_STYLE = ("Style: TC,Arial,40,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,"
            "1,0,0,0,100,100,0,0,1,3,1,9,30,30,24,1")


def ass_t(sec):
    sec = max(0.0, sec)
    cs = int(round(sec * 100))
    h, cs = divmod(cs, 360000)
    m, cs = divmod(cs, 6000)
    s, cs = divmod(cs, 100)
    return f"{h:d}:{m:02d}:{s:02d}.{cs:02d}"


def duration(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", path],
        capture_output=True, text=True).stdout.strip()
    return float(out)


def resolve(song):
    """song = substring of the 'song' column, or a factory-dir basename/path.
    Returns (clip_NN:int, title:str, factory_dir:abs)."""
    rows = list(csv.DictReader(open(TSV, encoding="utf-8"), delimiter="\t"))
    q = song.strip().lower()
    base = os.path.basename(song.rstrip("/")).lower()
    hits = []
    for r in rows:
        names = [r["song"].lower(), os.path.basename(r["factory_dir"]).lower()]
        if q in names[0] or q in names[1] or base == names[1]:
            hits.append(r)
    uniq = {r["clip"]: r for r in hits}
    if not uniq:
        sys.exit(f"no song in songs.tsv matches {song!r}")
    if len(uniq) > 1:
        opts = ", ".join(f"{r['song']} (clip {r['clip']})" for r in uniq.values())
        sys.exit(f"{song!r} is ambiguous: {opts}")
    r = next(iter(uniq.values()))
    fac = r["factory_dir"]
    if not os.path.isabs(fac):
        fac = os.path.join(REPO, fac)
    return int(r["clip"]), r["song"], fac


def combined_ass(src_ass, dur):
    """src .ass + a TC style + one M:SS line per second -> temp .ass path."""
    lines = open(src_ass, encoding="utf-8").read().splitlines()
    last_style = max(i for i, l in enumerate(lines) if l.startswith("Style:"))
    lines.insert(last_style + 1, TC_STYLE)
    tc = [f"Dialogue: 0,{ass_t(i)},{ass_t(i + 1)},TC,,0,0,0,,{i // 60}:{i % 60:02d}"
          for i in range(int(dur) + 1)]
    body = "\n".join(lines + tc) + "\n"
    fd, path = tempfile.mkstemp(suffix=".ass", prefix="review-")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(body)
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("song", help="song name substring or factory-dir name")
    ap.add_argument("--audio", default="all", choices=["all", "cue_preview"],
                    help="all = full mix incl. vocal (default); cue_preview = +click/cues")
    ap.add_argument("--out", help="default <factory>/auto-render/<NN>-lyric-review.mp4")
    args = ap.parse_args()

    nn, title, fac = resolve(args.song)
    ass = os.path.join(CLIPS, f"{nn:02d}.ass")
    mp4 = os.path.join(CLIPS, f"{nn:02d}.mp4")
    audio = os.path.join(fac, "auto-render",
                         "all.wav" if args.audio == "all" else "cue_preview.mp3")
    for p in (ass, mp4, audio):
        if not os.path.exists(p):
            sys.exit(f"missing: {p}")

    da, dv = duration(audio), duration(mp4)
    if abs(da - dv) > 0.25:
        sys.exit(f"clip {nn:02d}.mp4 ({dv:.3f}s) and audio ({da:.3f}s) differ by "
                 f"{abs(da - dv):.3f}s -> timelines drifted; re-render the clip "
                 f"(make_song_clip.py) before reviewing.")

    out = args.out or os.path.join(fac, "auto-render", f"{nn:02d}-lyric-review.mp4")
    comb = combined_ass(ass, da)
    try:
        subprocess.run(
            ["mpv", mp4, "--audio-file=" + audio, "--aid=1",
             "--sub-files=" + comb,
             "--o=" + out, "--ovc=libx264", "--oac=aac",
             "--no-config", "--really-quiet"],
            check=True)
    finally:
        os.unlink(comb)
    print(f"clip {nn:02d}  {title}")
    print(f"audio {os.path.basename(audio)}  {da:.2f}s")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
