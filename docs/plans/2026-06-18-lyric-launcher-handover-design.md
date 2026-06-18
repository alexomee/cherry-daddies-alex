# Lyric-launcher handover to the `cherry-daddies-2000` rig — design

**Date:** 2026-06-18
**Status:** approved (brainstorming) → next: writing-plans

## Goal

The lyric-launcher (synced lyrics on a stage monitor) was prototyped in
`cherry-daddies/tools/lyric-launcher/`. Hand it over to the **production
MainStage rig** in the separate repo `cherry-daddies-2000/` so it runs the live
show on the keyboardist's laptop (and the user's as backup).

## Decisions (from brainstorming)

- **Deployment target:** `cherry-daddies-2000` lives on the **keyboardist's
  laptop** (primary) + user's (backup). Runtime must be **self-contained** and
  keyboardist-operable there. Both Macs are **Apple Silicon**.
- **Start mechanism:** double-click. `setup.command` (one-time per Mac) +
  `Start Lyrics.command` (daily).
- **Bootstrap:** fully self-bootstrapping with **internet once at home** (then
  offline at gigs). Runtime deps are only **mpv** + a Python venv (`mido`,
  `python-rtmidi`); ffmpeg is generation-only and stays in `cherry-daddies`.
- **Coverage:** JamZone songs now; documented path for Russian/Moises songs
  later via a vocalist-supplied `{time, line}` table.
- **Numbering:** clip number **mirrors the set number**; `songs.tsv` manifest is
  the single source of truth (incl. the MainStage Program-Change off-by-one).
- **MainStage wiring:** **template/script the concert** by studying the diff of
  one hand-wired set; hand-wiring checklist as fallback.

## Architecture — two repos, split by role

- **`cherry-daddies/` (factory):** keeps the *generation* tools
  (`make_song_clip.py`, `embed_markers.py`) — they need JamZone decryption +
  ffmpeg. Clips are **built here**.
- **`cherry-daddies-2000/` (rig):** gets the *runtime* — `launcher.py`,
  pre-built `clips/`, bootstrap scripts, manifest, wired `2000.concert`.
  Self-contained; no JamZone / ffmpeg / Python knowledge needed.
- **Deploy = copy built clips** factory → rig and commit (same pattern as beds).

### Layout in `cherry-daddies-2000`

```
lyrics/
  launcher.py
  setup.command           # one-time per Mac: uv venv + mpv (internet once)
  "Start Lyrics.command"  # double-click → mpv on stage monitor, listening on LyricLauncher
  songs.tsv               # manifest: set# · song · clip · PC-field · bed-folder · source(jamzone|manual)
  clips/  01.mp4 01.ass  03.mp4 03.ass …   # numbered to mirror set numbers
  .venv/                  # gitignored; built by setup.command
  README.md               # per-set wiring checklist + "how to add a song"
2000.concert/             # wired per-set
cherry-daddies-setlist-2026-06-16/   # beds (already present)
```

`songs.tsv` maps set 03 → clip `03` → MainStage Send-Program-Change field `04`
→ launcher plays `03.mp4`. Un-numbered setlist entries get a number assigned.

## Runtime & bootstrap

- `setup.command`: ship/curl `uv` → `uv venv` + `uv pip install mido
  python-rtmidi` (prebuilt arm64 wheels); install mpv via `brew` (fallback:
  drop a static mpv binary into the repo); verify mpv + MIDI port. Internet
  needed once.
- `Start Lyrics.command`: run `launcher.py` from `.venv`, fullscreen on the
  stage monitor (`--screen 1`), listening on the one-way `LyricLauncher` virtual
  port (no IAC loopback).
- Trigger model (already built): Program Change N → play clip N from 0; PC 0 /
  STOP note → reset to title; debounce; instant `▶ PLAYING` OSD flash.

## Clip pipeline — two front-ends, same output

- **A. JamZone:** `make_song_clip.py --cat <cat_id> --index <set#>` (existing).
- **B. Manual:** `make_song_clip.py --lines <song>.tsv --index <set#>` (new).
  Vocalist table is `m:ss.s   <line>` in **playback seconds** (used directly, no
  offset). Same `.ass` renderer/look.
- `deploy_clips.sh`: copy built clips → `cherry-daddies-2000/lyrics/clips/`,
  refresh `songs.tsv`.

## Concert templating ("wire one, script the rest")

1. User wires ONE set by hand (Playback PLAY FROM Start + play-on-set-change;
   External Instrument MIDI Output = LyricLauncher + Send Program Change). Commit.
2. Diff: `plutil -convert xml1` the set's `.cst` / `data.plist` before/after,
   diff to find the changed files/keys.
3. Templating move: the wired External Instrument `.cst` is identical across sets
   except the PC number → **copy that `.cst` into each JamZone set's `.patch`,
   patch the PC number from `songs.tsv`, flip Playback play-on-set-change,
   register in that set's `data.plist`.** Safer than synthesizing strips.
4. Verify in MainStage: spot-check 2–3 sets + one live trigger.

**Risk + fallback:** MainStage assigns internal IDs when a strip is added; if
they don't transplant cleanly, scripting breaks. The step-2 diff reveals
viability in ~1h. Fallback = README per-set checklist (~2 min/set). Work is done
on a **copy/worktree**, never the live concert until verified; reversible via git.

## Testing

- Generate + deploy clips for all JamZone setlist songs; verify each renders at a
  lyric moment (screenshot).
- `setup.command` on a clean-ish state → `Start Lyrics.command` → trigger via
  `send_pc`/MainStage → lyrics roll, reset works.
- Concert spike: diff one set; if scriptable, apply + verify a few sets live.

## Out of scope (now)

- Russian/Moises songs (manual front-end documented, not built per-song yet).
- Scrub/stop-follow (needs Ableton as clock master — separate project).
