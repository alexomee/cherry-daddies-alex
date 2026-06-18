#!/bin/zsh
# Compress a video (.MOV/.mp4/...) to HEVC using Apple hardware encoder.
# Fast, keeps resolution + fps, ~3x smaller for typical 1080p60 phone footage.
# Original is never touched — output is a new file.
#
# Usage: compress-mov.sh <input> [bitrate] [output]
#   bitrate default 4M (good for 1080p60). lower = smaller (e.g. 2M, 1.5M).
#   output  default <input dir>/<name>_h265_<bitrate>.mp4
#
# Examples:
#   tools/compress-mov.sh ~/Downloads/IMG_2621.MOV
#   tools/compress-mov.sh ~/Downloads/IMG_2621.MOV 2M
#   tools/compress-mov.sh in.MOV 4M /tmp/out.mp4
set -euo pipefail

in="${1:?usage: compress-mov.sh <input> [bitrate] [output]}"
bv="${2:-4M}"
out="${3:-${in:r}_h265_${bv}.mp4}"

[[ -f "$in" ]] || { echo "no such file: $in" >&2; exit 1; }

insize=$(stat -f '%z' "$in")
echo ">>> compressing $in  ($((insize/1024/1024)) MB)  @ $bv HEVC -> $out" >&2

ffmpeg -nostdin -hide_banner -v warning -stats -i "$in" \
  -c:v hevc_videotoolbox -b:v "$bv" -tag:v hvc1 \
  -c:a aac -b:a 128k -movflags +faststart "$out" -y

outsize=$(stat -f '%z' "$out")
echo "<<< done: $out  ($((outsize/1024/1024)) MB, $((100*outsize/insize))% of original)" >&2
echo "$out"
