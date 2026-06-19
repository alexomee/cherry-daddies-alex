#!/usr/bin/env python3
"""Burn a song's launcher lyric clip over its audio -> a phone-shareable review mp4.

For the vocalist (no Mac) to check lyric FLOW and point edits by timecode:
the real Now/Next stage display, in sync with the song, plus a running M:SS
timecode (top-right) she can cite ("0:17 -> make these one line").

Default audio = the cue_preview recipe (music + click + cues) with the cues
boosted +3 dB so the in-ear prompts sit clearly over the music, then
peak-normalised to TARGET_DBFS so the boost never clips. Built from the
separate auto-render stems (all/click/cues.wav).

The clip .ass already sits on the render timeline (make_song_clip.py shifts it
by offset_sec), the same timeline the stems use -> no offset. We assert the
clip and all.wav durations match and refuse if they drift (catches a stale
re-render before it makes a misleading review).

Rendering is mpv (this repo's homebrew ffmpeg has no libass/drawtext); the
timecode is baked into a combined .ass as per-second lines.

Usage:
  make_review_video.py "I Love It"                 # name substring (songs.tsv)
  make_review_video.py "I Love It" --cue-db 6      # cues +6 dB instead of +3
  make_review_video.py "I Love It" --audio all     # clean mix, no click/cues
  make_review_video.py "I Love It" --out /tmp/x.mp4
"""
import argparse
import csv
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))           # tools/lyric-launcher -> repo root
TSV = os.path.join(HERE, "songs.tsv")
CLIPS = os.path.join(HERE, "clips")

MIX_LVL, CLICK_LVL, CUE_LVL = 0.85, 0.6, 1.0            # cue_preview recipe (jamzone_render)
TARGET_DBFS = -1.0                                       # peak after the cue boost
MEAS_PAD_DB = 12.0                                       # headroom so the true peak is readable

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
    Returns (clip_NN:int, title:str, factory_dir:abs_or_None, source:str)."""
    rows = list(csv.DictReader(open(TSV, encoding="utf-8"), delimiter="\t"))
    q = song.strip().lower()
    base = os.path.basename(song.rstrip("/")).lower()
    hits = []
    for r in rows:
        names = [r["song"].lower(), os.path.basename(r["factory_dir"]).lower()]
        if q in names[0] or (names[1] and (q in names[1] or base == names[1])):
            hits.append(r)
    uniq = {r["clip"]: r for r in hits}
    if not uniq:
        sys.exit(f"no song in songs.tsv matches {song!r}")
    if len(uniq) > 1:
        opts = ", ".join(f"{r['song']} (clip {r['clip']})" for r in uniq.values())
        sys.exit(f"{song!r} is ambiguous: {opts}")
    r = next(iter(uniq.values()))
    fac = r["factory_dir"].strip()
    fac = (fac if os.path.isabs(fac) else os.path.join(REPO, fac)) if fac else None
    return int(r["clip"]), r["song"], fac, r["source"]


def _maxvol(filterchain, inputs):
    args = ["ffmpeg", "-hide_banner"]
    for i in inputs:
        args += ["-i", i]
    args += ["-filter_complex", filterchain, "-f", "null", "-"]
    err = subprocess.run(args, capture_output=True, text=True).stderr
    m = re.search(r"max_volume:\s*(-?[\d.]+) dB", err)
    if not m:
        sys.exit("could not read peak level from ffmpeg volumedetect")
    return float(m.group(1))


def cuemix_wav(ar, cue_db, tmp):
    """music + click + cues (cues +cue_db dB), peak-normalised to TARGET_DBFS."""
    allw = os.path.join(ar, "all.wav")
    clk = os.path.join(ar, "click.wav")
    cue = os.path.join(ar, "cues.wav")
    for p in (allw, clk, cue):
        if not os.path.exists(p):
            sys.exit(f"missing stem for cue mix: {p} (use --audio all)")
    cg = CUE_LVL * (10 ** (cue_db / 20.0))
    base = (f"[0:a]volume={MIX_LVL}[a];[1:a]volume={CLICK_LVL}[c];"
            f"[2:a]volume={cg:.4f}[q];[a][c][q]amix=inputs=3:normalize=0")
    peak = _maxvol(base + f",volume=-{MEAS_PAD_DB}dB,volumedetect", [allw, clk, cue]) + MEAS_PAD_DB
    g = TARGET_DBFS - peak
    out = os.path.join(tmp, "cuemix.wav")
    subprocess.run(
        ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
         "-i", allw, "-i", clk, "-i", cue,
         "-filter_complex", base + f",volume={g:.3f}dB[m]",
         "-map", "[m]", out],
        check=True)
    return out, f"cues +{cue_db:g}dB, peak {peak:+.1f}->{TARGET_DBFS:+.0f}dBFS (gain {g:+.1f}dB)"


def combined_ass(src_ass, dur, tmp):
    """src .ass + a TC style + one M:SS line per second -> .ass path in tmp."""
    lines = open(src_ass, encoding="utf-8").read().splitlines()
    last_style = max(i for i, l in enumerate(lines) if l.startswith("Style:"))
    lines.insert(last_style + 1, TC_STYLE)
    tc = [f"Dialogue: 0,{ass_t(i)},{ass_t(i + 1)},TC,,0,0,0,,{i // 60}:{i % 60:02d}"
          for i in range(int(dur) + 1)]
    path = os.path.join(tmp, "review.ass")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines + tc) + "\n")
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("song", help="song name substring or factory-dir name")
    ap.add_argument("--audio", default="mix", choices=["mix", "all", "cue_preview"],
                    help="mix = music+click+cues, cues boosted (default); "
                         "all = clean mix; cue_preview = the raw preview file")
    ap.add_argument("--cue-db", type=float, default=3.0,
                    help="cue boost for --audio mix (default +3 dB)")
    ap.add_argument("--out", help="default <factory>/auto-render/<NN>-lyric-review.mp4")
    ap.add_argument("--song-dir", help="override the audio folder (for static songs "
                    "whose songs.tsv factory_dir is blank; expects <dir>/auto-render/)")
    args = ap.parse_args()

    nn, title, fac, source = resolve(args.song)
    if args.song_dir:
        fac = args.song_dir if os.path.isabs(args.song_dir) else os.path.join(REPO, args.song_dir)
    if not fac:
        sys.exit(f"clip {nn:02d} '{title}' has no factory_dir in songs.tsv -> pass --song-dir")
    ass = os.path.join(CLIPS, f"{nn:02d}.ass")
    mp4 = os.path.join(CLIPS, f"{nn:02d}.mp4")
    ar = os.path.join(fac, "auto-render")
    allw = os.path.join(ar, "all.wav")
    for p in (ass, allw):
        if not os.path.exists(p):
            sys.exit(f"missing: {p}")

    da = duration(allw)
    out = args.out or os.path.join(ar, f"{nn:02d}-lyric-review.mp4")

    with tempfile.TemporaryDirectory() as tmp:
        # canvas: timed clips reuse the stage mp4 (same render timeline; guard drift);
        # static clips are a 6s still -> make a black canvas at song length instead.
        if source == "static":
            canvas = os.path.join(tmp, "canvas.mp4")
            subprocess.run(
                ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                 "-f", "lavfi", "-i", f"color=c=black:s=1280x720:d={da:.3f}:r=30",
                 "-c:v", "libx264", "-pix_fmt", "yuv420p", "-an", canvas], check=True)
        else:
            if not os.path.exists(mp4):
                sys.exit(f"missing: {mp4}")
            dv = duration(mp4)
            if abs(da - dv) > 0.25:
                sys.exit(f"clip {nn:02d}.mp4 ({dv:.3f}s) and all.wav ({da:.3f}s) differ by "
                         f"{abs(da - dv):.3f}s -> timelines drifted; re-render the clip "
                         f"(make_song_clip.py) before reviewing.")
            canvas = mp4

        if args.audio == "mix":
            audio, note = cuemix_wav(ar, args.cue_db, tmp)
        elif args.audio == "all":
            audio, note = allw, "all.wav (clean mix)"
        else:
            audio, note = os.path.join(ar, "cue_preview.mp3"), "cue_preview.mp3"
            if not os.path.exists(audio):
                sys.exit(f"missing: {audio}")
        comb = combined_ass(ass, da, tmp)
        subprocess.run(
            ["mpv", canvas, "--audio-file=" + audio, "--aid=1",
             "--sub-files=" + comb,
             "--o=" + out, "--ovc=libx264", "--oac=aac",
             "--no-config", "--really-quiet"],
            check=True)

    print(f"clip {nn:02d}  {title}")
    print(f"audio {note}  {da:.2f}s")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
