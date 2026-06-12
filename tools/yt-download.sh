#!/usr/bin/env bash
# Download YouTube audio/video into music/youtube/.
#
# Usage:
#   tools/yt-download.sh <url> [audio|video|both]
#
# Default mode: audio (best audio track, native codec, no re-encode).
# Files land in music/youtube/<title> [<video id>].<ext> — id in the name
# keeps versions distinct and makes the source rebuildable.

set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
OUT_DIR="$REPO_DIR/music/youtube"
TEMPLATE="$OUT_DIR/%(title)s [%(id)s].%(ext)s"

URL="${1:?usage: tools/yt-download.sh <url> [audio|video|both]}"
MODE="${2:-audio}"

mkdir -p "$OUT_DIR"

case "$MODE" in
  audio)
    yt-dlp -f bestaudio -o "$TEMPLATE" --no-playlist "$URL"
    ;;
  video)
    yt-dlp -f "bestvideo+bestaudio/best" -o "$TEMPLATE" --no-playlist "$URL"
    ;;
  both)
    yt-dlp -f "bestvideo+bestaudio/best" -o "$TEMPLATE" --no-playlist "$URL"
    yt-dlp -f bestaudio -o "$TEMPLATE" --no-playlist "$URL"
    ;;
  *)
    echo "unknown mode: $MODE (audio|video|both)" >&2
    exit 1
    ;;
esac
