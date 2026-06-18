#!/usr/bin/env bash
# Sync rendered playback stems from the source pipeline into the keyboardist's
# MainStage rig repo (cherry-daddies-2000) and optionally commit.
#
# Mechanics:
#   - For each setlist song it copies ONLY the stems that already exist in the
#     target folder (click/cues/pb-other/pb-bass), overwriting in place.
#   - It never adds or removes stem files. MainStage references audio by path;
#     a brand-new or renamed stem needs a manual patch edit in MainStage, so the
#     script deliberately won't introduce one. Same reason it won't delete.
#   - Source = <song>/auto-render/<stem>.wav ; all.wav / cue_preview.mp3 /
#     timeline.json are pipeline-internal and never copied.
#
# Usage:
#   tools/sync_to_mainstage.sh                 # sync every song (dry-run summary first)
#   tools/sync_to_mainstage.sh --apply         # actually copy
#   tools/sync_to_mainstage.sh --apply "S&M"   # only songs whose mapping matches the filter
#   tools/sync_to_mainstage.sh --apply --commit "S&M: re-render cues"
#                                              # copy, then git add+commit in the rig repo (no push)
#
# Default is dry-run: shows what WOULD change. Add --apply to write files.

set -euo pipefail

SRC_ROOT="/Users/alex/projects/cherry-daddies/music/songs"
RIG_ROOT="/Users/alex/projects/cherry-daddies-2000"
SETLIST_DIR="$RIG_ROOT/cherry-daddies-setlist-2026-06-16"

# setlist-folder ||| source-song-folder
MAP=(
  "01 Better Off Alone|||Alice Deejay - Better Off Alone"
  "03 Whenever, Wherever|||Shakira - Whenever, Wherever"
  "04 Infinity 2008|||Guru Josh - Infinity 2008"
  "05 Mr. Saxobeat|||Alexandra Stan - Mr. Saxobeat"
  "07 Adventure of a Lifetime|||Coldplay - Adventure of a Lifetime"
  "08 Blinding Lights|||The Weeknd - Blinding Lights"
  "10 Freed From Desire|||Gala - Freed from Desire"
  "11 Uptown Funk|||Bruno Mars & Mark Ronson - Uptown Funk"
  "12 Солнышко|||Demo - Solnyshko"
  "13 Про красивую жизнь|||Band'Eros - Pro krasivuju zhizn'"
  "15 Я устал|||Quest Pistols - Я устал"
  "16 Now You're Gone|||Basshunter - Now You're Gone"
  "17 S&M|||Rihanna - S&M"
  "18 Beverly Hills|||Beverly Hills"
  "19 We Found Love|||Rihanna & Calvin Harris - We Found Love"
  "20 Everytime We Touch|||Cascada - Everytime We Touch"
  "24 Я сошла с ума|||t.A.T.u. - Ya Soshla S Uma (Я сошла с ума)"
  "A Touch of Class - Around the World (La La La La La)|||A Touch of Class - Around the World (La La La La La)"
  "Alex Gaudino - Destination Calabria|||Alex Gaudino - Destination Calabria"
  "Icona Pop & Charli XCX - I Love It|||Icona Pop & Charli XCX - I Love It"
  "Laurent Wolf & Eric Carter - No Stress|||Laurent Wolf & Eric Carter - No Stress"
  "SEREBRO - Malo tebya|||SEREBRO - Malo tebya"
  "Yeah Yeah Yeahs - Heads Will Roll|||Yeah Yeah Yeahs - Heads Will Roll"
)

STEMS=(click.wav cues.wav pb-other.wav pb-bass.wav)

APPLY=0
COMMIT_MSG=""
FILTER=""
while [ $# -gt 0 ]; do
  case "$1" in
    --apply)  APPLY=1; shift ;;
    --commit) COMMIT_MSG="${2:-}"; shift 2 ;;
    *)        FILTER="$1"; shift ;;
  esac
done

[ -d "$SETLIST_DIR" ] || { echo "ERROR: setlist dir not found: $SETLIST_DIR" >&2; exit 1; }

copied=0; skipped=0; missing=0; songs=0
echo "mode: $([ $APPLY -eq 1 ] && echo APPLY || echo DRY-RUN)${FILTER:+   filter=\"$FILTER\"}"
echo

for entry in "${MAP[@]}"; do
  dst_name="${entry%%|||*}"
  src_name="${entry##*|||}"
  if [ -n "$FILTER" ] && [[ "$dst_name" != *"$FILTER"* && "$src_name" != *"$FILTER"* ]]; then
    continue
  fi
  dst="$SETLIST_DIR/$dst_name"
  src="$SRC_ROOT/$src_name/auto-render"
  [ -d "$dst" ] || { echo "!! target missing, skip: $dst_name"; continue; }
  [ -d "$src" ] || { echo "!! no auto-render, skip:  $src_name"; continue; }

  songs=$((songs+1))
  echo "▸ $dst_name  ←  $src_name"
  for stem in "${STEMS[@]}"; do
    [ -f "$dst/$stem" ] || continue          # only overwrite stems MainStage already references
    if [ ! -f "$src/$stem" ]; then
      echo "    MISSING in render: $stem  (target has it — re-render or fix mix.json)"
      missing=$((missing+1)); continue
    fi
    if cmp -s "$src/$stem" "$dst/$stem"; then
      echo "    = $stem  (identical, skip)"
      skipped=$((skipped+1))
    else
      echo "    ↑ $stem  ($(du -h "$src/$stem" | cut -f1))"
      [ $APPLY -eq 1 ] && cp "$src/$stem" "$dst/$stem"
      copied=$((copied+1))
    fi
  done
done

echo
echo "songs: $songs   changed: $copied   identical: $skipped   missing-in-render: $missing"

if [ $APPLY -eq 1 ] && [ -n "$COMMIT_MSG" ]; then
  echo
  echo "=== committing in $RIG_ROOT (no push) ==="
  git -C "$RIG_ROOT" add -A "cherry-daddies-setlist-2026-06-16"
  git -C "$RIG_ROOT" commit -m "$COMMIT_MSG" || echo "(nothing to commit)"
  echo "Push when ready:  git -C \"$RIG_ROOT\" push"
elif [ $APPLY -eq 1 ]; then
  echo
  echo "Files copied. Review:  git -C \"$RIG_ROOT\" status"
else
  echo
  echo "Dry-run only. Re-run with --apply to copy."
fi
