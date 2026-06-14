# Video "create iteration" pipeline — design

**Date:** 2026-06-14
**Status:** approved, pilot rendered

## Goal

A repeatable home for **advertising / promo video** iteration, mirroring the music
pipeline (`music/songs/<song>/` + `mix.json` + `auto-render/`). Each promo lives in a
per-project folder with a committed recipe; heavy media stays out of git and every render
is rebuildable from the recipe.

First task (pilot): rebuild the audio of the June-26 event promo
`~/Downloads/DANCE2000 рус1.mp4` — replace its baked-in Shakira-mix soundtrack with a new
song bed while keeping the existing ElevenLabs voiceover at its original position.

## Layout

Per-project folder under `assets/video/`:

```
assets/video/projects/<name>/
  src/            inputs as symlinks (no heavy-media copies)
  edl.json        recipe — committed, rebuildable
  auto-render/    versioned outputs <prefix>_vN.mp4 — gitignored
```

Tooling: `tools/video/render_audio.py` (json-driven). Inputs symlinked so source files
(Downloads, music/youtube) are never duplicated. Only `edl.json` + the renderer are in git;
`.mp4` is already gitignored, so renders never bloat the repo.

## Pilot: dance2000-promo

`assets/video/projects/dance2000-promo/`

- **bed** = SEREBRO — Мало тебя (`music/youtube/Мало тебя [VsLGqtzAdic].webm`), seeked to
  `0:30`, taken for the full 22.04s video length, 0.8s fade-out tail.
- **vo** = `ElevenLabs_…Dmitry…v3 (1).mp3` (20.19s), delayed to **1.771s** — its original
  onset in the source, measured by cross-correlating the separate VO against the source
  mixed track. Verified: VO in render lands at 1.771s exactly.
- **duck** = bed sidechain-compressed by the VO (threshold 0.03, ratio 8, attack 20,
  release 300) → music drops ~-12 dB under speech, recovers in gaps. "Match original feel"
  (VO sits clearly on top), per user.
- **mux** = audio replaced only; `-c:v copy` (HEVC 1080×1920 untouched, no re-encode).

### render_audio.py mechanics / gotchas learned

- VO is decoded **twice** (two `-i` of the same file → sidechain key + audible copy). Using
  `asplit` to fork one decoded VO silently dropped the audible branch (bed ducked but no VO).
- Every stream is `apad,atrim=duration=<video>` padded to the exact video length so the mix
  duration cannot drift (first attempt produced 21.68s audio under a 22.04s video).
- Output version auto-increments (`_v1`, `_v2`, …) — never overwrites a render
  (see memory: version every render).

### Iteration knobs (edit `edl.json`, re-run)

`song_seek`, `vo_offset`, `bed_gain_db`, `vo_gain_db`, `bed_fadeout`,
`duck.{threshold,ratio,attack,release}`.

## Run

```bash
python3 tools/video/render_audio.py assets/video/projects/dance2000-promo/edl.json
# → assets/video/projects/dance2000-promo/auto-render/dance2000-promo_v<N>.mp4
```
