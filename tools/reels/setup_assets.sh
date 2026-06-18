#!/bin/zsh
# Регенерирует ассеты рилсов (gitignored: png/wav) в content/rehearsal-reels/assets/.
# Запуск один раз на новой машине / после чистки: zsh tools/reels/setup_assets.sh
set -e
REPO="$HOME/projects/cherry-daddies"
ASSETS="$REPO/content/rehearsal-reels/assets"
mkdir -p "$ASSETS/badges" "$ASSETS/emoji"

echo "1/3 бейджи (PIL через uv)…"
BADGE_OUT="$ASSETS/badges" uv run --with pillow python "$REPO/tools/reels/make_badges.py"

echo "2/3 эмодзи (Noto 512px)…"
for cp in 1f914 1f928 1f605 1f3b6; do
  curl -fsSL "https://cdn.jsdelivr.net/gh/googlefonts/noto-emoji/png/512/emoji_u${cp}.png" -o "$ASSETS/emoji/${cp}.png"
done

echo "3/3 whoosh-SFX (ffmpeg)…"
ffmpeg -nostdin -v error -f lavfi -i "anoisesrc=d=0.34:c=pink:r=48000" \
  -af "highpass=f=220,lowpass=f=4800,afade=t=in:st=0:d=0.05,afade=t=out:st=0.10:d=0.24,volume=0.55" \
  -ac 2 -ar 48000 "$ASSETS/whoosh.wav" -y

echo "OK → $ASSETS"
ls "$ASSETS" "$ASSETS/badges" "$ASSETS/emoji"
