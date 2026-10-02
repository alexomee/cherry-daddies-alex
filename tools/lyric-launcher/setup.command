#!/bin/bash
# One-time macOS setup. Run again after dependency changes.
set -euo pipefail
export PATH="/opt/homebrew/bin:/usr/local/bin:$HOME/.local/bin:$PATH"
HERE="$(cd "$(dirname "$0")" && pwd)"
if [ "$(uname -s)" != Darwin ]; then
  echo 'This installer targets macOS (JamZone). See docs/vocalist-workflow.md.'
  exit 1
fi
if ! command -v brew >/dev/null; then
  echo 'Install Homebrew from https://brew.sh, then run this file again.'
  exit 1
fi
missing=()
for tool in uv ffmpeg mpv gh; do
  command -v "$tool" >/dev/null || missing+=("$tool")
done
if [ "${#missing[@]}" -gt 0 ]; then
  HOMEBREW_NO_AUTO_UPDATE=1 brew install "${missing[@]}"
fi
if [ ! -x "$HERE/.venv/bin/python" ]; then
  uv venv --python 3.12 "$HERE/.venv"
fi
backend=faster-whisper
if [ "$(uname -m)" = arm64 ]; then backend=mlx-whisper; fi
uv pip install --python "$HERE/.venv/bin/python" "$backend"
"$HERE/.venv/bin/python" -c 'import sys; assert sys.version_info >= (3, 11), "Python 3.11+ required"'
ffmpeg -version >/dev/null
ffprobe -version >/dev/null
mpv --version >/dev/null
echo "Tools installed. Transcription backend: $backend (model downloads on first use)."
echo 'Next: open the repository in ChatGPT/Codex and ask it to read AGENTS.md.'
echo 'Check both clones and GitHub identity with lyric_workflow.py doctor.'
