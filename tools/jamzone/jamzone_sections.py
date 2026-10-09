#!/usr/bin/env python3
"""Quick JamZone section analyzer for song cues.

Usage:
    tools/jamzone/jamzone_sections.py "<song name or query>"

Prints all JamZone sections mapped to:
  - stem seconds (t_stem)
  - render seconds (render_t / abs_sec, exactly accounting for rendered click / count-in lead offset)
  - Logic ruler bar.beat
  - mix.json bar and beat
  - ready-to-paste mix.json cue snippets
  - opening lyric preview
"""
import sys, os, subprocess

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: jamzone_sections.py \"<song name or query>\"")
        sys.exit(1)
    here = os.path.dirname(os.path.abspath(__file__))
    render_py = os.path.join(here, "jamzone_render.py")
    cmd = [sys.executable, render_py, sys.argv[1], "--sections"]
    sys.exit(subprocess.run(cmd).returncode)
