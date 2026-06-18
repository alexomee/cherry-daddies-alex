#!/usr/bin/env bash
# deploy_clips.sh — copy built lyric clips + manifest from the factory (this
# repo) into the rig repo's runtime folder.
#
#   factory:  cherry-daddies/tools/lyric-launcher/clips/NN.{mp4,ass}  +  songs.tsv
#   rig:      cherry-daddies-2000/lyrics/clips/NN.{mp4,ass}           +  songs.tsv
#
# The mp4s are gitignored in the FACTORY (cherry-daddies) but committed in the
# RIG (cherry-daddies-2000) — they're the runtime payload there. After running
# this, commit lyrics/clips + lyrics/songs.tsv in the rig repo.
#
# Usage:  bash deploy_clips.sh [RIG_REPO_PATH]
#   RIG_REPO_PATH defaults to /Users/alex/projects/cherry-daddies-2000
set -euo pipefail

SRC_DIR="$(cd "$(dirname "$0")" && pwd)"          # F/tools/lyric-launcher
RIG="${1:-/Users/alex/projects/cherry-daddies-2000}"
DST_CLIPS="$RIG/lyrics/clips"
DST_TSV="$RIG/lyrics/songs.tsv"

if [ ! -d "$RIG/lyrics" ]; then
  echo "❌ rig lyrics dir not found: $RIG/lyrics" >&2
  echo "   (pass the rig repo path as arg 1 if it lives elsewhere)" >&2
  exit 1
fi

mkdir -p "$DST_CLIPS"

echo "== deploy clips: $SRC_DIR/clips -> $DST_CLIPS =="
mp4_n=0
ass_n=0
for f in "$SRC_DIR"/clips/*.mp4; do
  [ -e "$f" ] || continue
  base="$(basename "$f")"
  ass="${f%.mp4}.ass"
  cp "$f" "$DST_CLIPS/$base"
  echo "  + $base"
  mp4_n=$((mp4_n + 1))
  if [ -e "$ass" ]; then
    cp "$ass" "$DST_CLIPS/$(basename "$ass")"
    echo "  + $(basename "$ass")"
    ass_n=$((ass_n + 1))
  else
    echo "  ! WARNING: no .ass for $base" >&2
  fi
done

echo "== deploy manifest: songs.tsv =="
cp "$SRC_DIR/songs.tsv" "$DST_TSV"
echo "  + songs.tsv"

echo
echo "summary: $mp4_n mp4 + $ass_n ass copied to $DST_CLIPS, songs.tsv refreshed"
echo "next: in the rig repo, commit  lyrics/clips  lyrics/songs.tsv"
