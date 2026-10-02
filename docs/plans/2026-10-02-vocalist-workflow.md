# Vocalist Workflow Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Enable Tatiana to prepare, review, save and deliver lyrics conversationally using the full band repository.

**Architecture:** Keep the existing generators and stage format. Add portable transcription and a small workflow CLI with hash-bound review receipts; selective deployment merges one manifest row and uses normal Git commits/pushes with remote verification.

**Tech Stack:** Python 3.12, pytest, ffmpeg/ffprobe, mpv, uv, mlx-whisper/faster-whisper, Git, GitHub CLI.

---

### Task 1: Portable generation and transcription

Files: modify `tools/lyric-launcher/make_song_clip.py`; create
`tools/lyric-launcher/transcribe_lyrics.py`; test
`tools/lyric-launcher/tests/test_transcribe.py` and `test_lines_frontend.py`.

1. Add failing tests for invalid/unsorted/nonfinite times and transcription offset,
   repeats, empty speech and low-confidence diagnostics.
2. Run `uv run --python 3.12 --with pytest pytest tools/lyric-launcher/tests -q`.
3. Make generator accept explicit reference audio/duration and JamZone path;
   preserve the old CLI. Validate before rendering and bound ASS events to duration.
4. Add local ASR CLI, raw JSON provenance and editable TSV, using word timestamps
   where available. Require an explicit stem-to-playback offset.
5. Run tests and a short real Russian transcription.

### Task 2: Review, save and selective rig delivery

Files: create `tools/lyric-launcher/lyric_workflow.py`,
`tools/lyric-launcher/deploy_clips.py`, `tools/lyric-launcher/tests/test_workflow.py`;
modify `tools/lyric-launcher/deploy_clips.sh`.

1. Add temporary main/rig/bare-remote fixtures; assert only the selected clip and
   manifest row change and source provenance is recoverable.
2. Test stale audio/clips/sources/rig row, dirty index, concurrent remote updates,
   rejected push and retry. Use real Git subprocesses, not mocked push success.
3. Implement doctor/sync/review/approve/check/save/deliver commands. Resolve paths
   portably. Record input hashes at review, validate again at approval/delivery.
4. Selectively merge the chosen row, retaining rig-only rows. Refuse renumbering
   an existing song and collisions. Require source commit reachable from remote.
5. Replace bulk shell copier with a compatibility entry point requiring a song
   selection and explicit apply; default to a dry-run.
6. Run `uv run --python 3.12 --with pytest pytest tools/lyric-launcher/tests -q`.
7. Exercise actual generation/review on short synthetic audio via ffmpeg/mpv.

### Task 3: Onboarding and publishing

Files: create `AGENTS.md`, `docs/vocalist-workflow.md`,
`tools/lyric-launcher/setup.command`; modify `.gitignore`, `README.md`,
`tools/lyric-launcher/README.md` and relevant wiki pipeline pages.

1. Describe user commands, both repositories, media prerequisites, new-song wiring,
   human review and accurate saved/delivered/pulled statuses.
2. Add setup for macOS dependencies with selectable ASR backend; models install on
   first transcription. Ignore environments, local audio/preview state and secrets.
3. Invite `tkozinets` to the main repository. Check rig permission and report any
   owner action required.
4. Inspect tracked/history payload before first publication to the supplied remote,
   then push the full repository history and verify remote SHA if publication is clear.
5. Review diff, run required checks, commit only task files. Preserve pre-existing
   user changes in the original working directory.
