# Lyric-flow review loop for the vocalist (no Mac)

**Date:** 2026-06-19
**Status:** approved design

## Problem

The vocalist needs to (1) check how the launcher lyrics *flow* on stage and
(2) easily point out edits — from a phone, no Mac. Today the only artifacts are
the `.ass` clip + black `.mp4` (Mac/MainStage-only) and a raw timed text dump.

## Decisions (locked with the user)

- **Review medium = the real clip video.** She watches the actual Now/Next
  stage display in sync with the song audio — most faithful to what she'll see
  on the monitor.
- **Round-trip = messenger reply (text/voice).** She cites a burned-in
  timecode ("0:17 — make these one line"); I translate notes into edits. No
  hosting, no accounts.
- **Scope = reusable script** for any setlist song, not a one-off.
- **Timecode label = `M:SS` song time** (matches the review TSV times exactly).
- **Audio = `all.wav`** (full mix incl. lead vocal) so she hears the sung words
  against the on-screen flow. `--audio cue_preview` swaps in the click variant.

## Why it lines up (verified, not assumed)

`make_song_clip.py` already shifts every line by the render's `offset_sec`
(`auto-render/timeline.json`) so the `.ass` sits on the **same timeline
MainStage plays** — the timeline `click` / `pb-*` / `all.wav` share. For
I Love It both `clips/22.mp4` and `auto-render/all.wav` are exactly 160.000s.
So burning `22.ass` over `all.wav` syncs with zero offset. The script asserts
clip-vs-audio durations match and refuses if they drift (catches a stale
re-render before it produces a misleading review).

## Components

### A. `tools/lyric-launcher/make_review_video.py "<song>"`

- Resolve song → clip `NN` + factory dir via `songs.tsv` (match `song` or
  `factory_dir`). Accepts a song name substring or a folder path.
- Inputs: `clips/NN.ass`, `<factory>/auto-render/all.wav`.
- One ffmpeg call: black `1280x720` bg sized to audio duration →
  `subtitles=NN.ass` (burn Now/Next/Title) → `drawtext` running `M:SS`
  timecode in a corner clear of the centered Now/Next text → mux `all.wav`.
- Output: `<factory>/auto-render/<NN>-lyric-review.mp4`. Local only; I hand
  back the path, the user forwards over messenger. Overwrites on each rebuild
  (disposable iteration artifact, not a promo render).

### B. Edit loop

The editable source is the `time<TAB>line` TSV — the same format
`make_song_clip.py --lines` consumes, and what `<song>/<NN>_lyrics_review.txt`
already is (exported from the live `.ass`). Because exported times are the
already-offset display times and `--lines` uses `offset=0`, a round-trip
reproduces the clip faithfully.

1. She messages notes/voice citing the timecode.
2. I apply edits to the TSV.
3. `make_song_clip.py --lines <TSV>` rebuilds `NN.ass` (+ `NN.mp4`).
4. `make_review_video.py` re-burns → new mp4 → resend. Repeat to sign-off.
5. On sign-off the corrected clip *is* the stage clip → `deploy_clips.sh`
   ships it. No separate apply-to-production step.

Works for JamZone-timed and static clips alike — both have an `.ass`.

## Out of scope (YAGNI)

- No hosting / web player / accounts (messenger handles delivery).
- No automated parsing of her voice notes — manual translation is fine at this
  volume.
- No bar-number overlay (M:SS is enough and matches the TSV).
