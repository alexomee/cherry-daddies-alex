#!/usr/bin/env bash
# JamZone Stem Extractor
# Extracts decrypted audio stems from JamZone after hook capture
#
# Usage: extract_stems.sh <extract_dir> <output_dir>

set -euo pipefail

EXTRACT_DIR="${1:-/tmp/jamzone-extract}"
OUTPUT_DIR="${2:-$HOME/Desktop/jamzone-stems}"

if [ ! -d "$EXTRACT_DIR" ]; then
    echo "Error: Extract directory $EXTRACT_DIR does not exist"
    exit 1
fi

# Find the song.json decrypted file (look for JSON with "title" and "artist")
SONG_FILE=""
TRACKS_FILE=""
for f in "$EXTRACT_DIR"/decrypted_*.bin; do
    [ ! -f "$f" ] && continue
    size=$(wc -c < "$f")
    # song.json is typically 300-600 bytes
    if [ "$size" -gt 200 ] && [ "$size" -lt 1000 ]; then
        if python3 -c "import json; d=json.load(open('$f')); assert 'title' in d and 'artist' in d" 2>/dev/null; then
            SONG_FILE="$f"
        fi
    fi
    # tracks.json is typically 3000-8000 bytes
    if [ "$size" -gt 2000 ] && [ "$size" -lt 20000 ]; then
        if python3 -c "import json; d=json.load(open('$f')); assert isinstance(d, list) and 'descriptions' in d[0]" 2>/dev/null; then
            TRACKS_FILE="$f"
        fi
    fi
done

if [ -z "$SONG_FILE" ]; then
    echo "Warning: Could not find decrypted song.json - stems will have generic names"
    SONG_TITLE="unknown"
    SONG_ARTIST="unknown"
else
    SONG_TITLE=$(python3 -c "import json; print(json.load(open('$SONG_FILE'))['title'])")
    SONG_ARTIST=$(python3 -c "import json; a=json.load(open('$SONG_FILE'))['artist']; print(a if isinstance(a,str) else a.get('en','unknown'))")
    echo "Song: $SONG_TITLE by $SONG_ARTIST"
fi

# Create output directory: ~/Desktop/jamzone-stems/Artist - Title/
SAFE_TITLE=$(echo "$SONG_ARTIST - $SONG_TITLE" | tr '/:*?"<>|' '-')
DEST="$OUTPUT_DIR/$SAFE_TITLE"
mkdir -p "$DEST"

# Find all full-length audio stems (M4A files > 200KB, duration > 60s)
echo "Scanning for audio stems..."
STEM_FILES=()
for f in "$EXTRACT_DIR"/decrypted_*.bin; do
    [ ! -f "$f" ] && continue
    size=$(wc -c < "$f")
    [ "$size" -lt 200000 ] && continue
    # Check if it's a valid M4A with duration > 60s
    dur=$(ffprobe "$f" 2>&1 | grep "Duration:" | sed 's/.*Duration: //' | sed 's/,.*//' | head -1)
    if [ -n "$dur" ]; then
        # Convert to seconds
        secs=$(echo "$dur" | awk -F: '{print ($1 * 3600) + ($2 * 60) + $3}')
        if (( $(echo "$secs > 60" | bc -l) )); then
            STEM_FILES+=("$f")
        fi
    fi
done

echo "Found ${#STEM_FILES[@]} full-length stems"

# Get track names from tracks.json if available
if [ -n "$TRACKS_FILE" ]; then
    TRACK_COUNT=$(python3 -c "import json; print(len(json.load(open('$TRACKS_FILE'))))")
    echo "Track listing has $TRACK_COUNT tracks"

    if [ "${#STEM_FILES[@]}" -eq "$TRACK_COUNT" ]; then
        for i in "${!STEM_FILES[@]}"; do
            name=$(python3 -c "import json; print(json.load(open('$TRACKS_FILE'))[$i]['descriptions']['en'])")
            safe_name=$(echo "$name" | tr '/:*?"<>|' '-')
            idx=$(printf '%02d' $((i+1)))
            dest_file="$DEST/${idx}_${safe_name}.m4a"
            cp "${STEM_FILES[$i]}" "$dest_file"
            echo "  $dest_file"
        done
    else
        echo "Warning: stem count (${#STEM_FILES[@]}) != track count ($TRACK_COUNT), using generic names"
        for i in "${!STEM_FILES[@]}"; do
            idx=$(printf '%02d' $((i+1)))
            cp "${STEM_FILES[$i]}" "$DEST/stem_${idx}.m4a"
            echo "  $DEST/stem_${idx}.m4a"
        done
    fi
else
    echo "No track metadata found, using generic names"
    for i in "${!STEM_FILES[@]}"; do
        idx=$(printf '%02d' $((i+1)))
        cp "${STEM_FILES[$i]}" "$DEST/stem_${idx}.m4a"
        echo "  $DEST/stem_${idx}.m4a"
    done
fi

echo ""
echo "Done! Stems saved to: $DEST"
echo "Total stems: ${#STEM_FILES[@]}"
