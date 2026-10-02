#!/usr/bin/env bash
# Selected delivery only. Dry-run by default; --apply commits and pushes.
# bash deploy_clips.sh --index 14 --rig /path/to/cherry-daddies-2000 [--apply]
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
PY="${PYTHON:-$HERE/.venv/bin/python}"
if [ ! -x "$PY" ] && [ -z "${PYTHON:-}" ]; then PY=python3; fi
"$PY" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else "Python 3.11+ required; run setup.command first")'
exec "$PY" "$HERE/deploy_clips.py" "$@"
