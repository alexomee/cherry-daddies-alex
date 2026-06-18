#!/bin/zsh
set -e
cd /tmp/reels
mkdir -p asr
MODEL=mlx-community/whisper-large-v3-mlx
n=0
for f in audio/IMG_*_*.mp3; do
  base=$(basename "$f" .mp3)
  out="asr/${base}.json"
  if [ -f "$out" ]; then echo "skip $base (done)"; continue; fi
  n=$((n+1))
  echo ">>> [$n] transcribing $base"
  uvx --python 3.12 --from mlx-whisper mlx_whisper "$f" \
    --model "$MODEL" --word-timestamps True \
    --output-format json --output-dir asr --language ru 2>&1 | tail -1
  echo "<<< $base done"
done
echo "ALL ASR DONE"
