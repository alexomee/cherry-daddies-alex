# Lyric-launcher Handover to `cherry-daddies-2000` — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Package the prototyped lyric-launcher into the production `cherry-daddies-2000` MainStage rig so it runs the live show, self-contained, on the keyboardist's laptop.

**Architecture:** `cherry-daddies` stays the *factory* (generates clips from JamZone tiles or a manual `{time,line}` table). `cherry-daddies-2000` gets the *runtime*: `lyrics/` folder with `launcher.py`, double-click bootstrap, pre-built numbered clips, a `songs.tsv` manifest, and a per-set-wired `2000.concert`. Clip number mirrors set number; PC trigger via the one-way `LyricLauncher` virtual port.

**Tech Stack:** Python (`mido`, `python-rtmidi`) in a `uv` venv, `mpv` (IPC), `ffmpeg`/JamZone-AES (factory only), `plutil` for MainStage binary-plist editing, bash `.command` launchers.

**Design:** `docs/plans/2026-06-18-lyric-launcher-handover-design.md`

**Repos touched:** `F` = `/Users/alex/projects/cherry-daddies` (factory). `R` = `/Users/alex/projects/cherry-daddies-2000` (rig). Each task tags which.

**Conventions:** TDD where there's logic; verification steps (screenshots / log greps) where it's MainStage/mpv integration. Commit after every task. MainStage concert edits happen on a **copy**, never the live bundle, until verified.

---

## Phase A — Manifest & numbering  (repo F)

### Task A1: Build `songs.tsv` manifest

**Files:**
- Create: `F: tools/lyric-launcher/songs.tsv`
- Create: `F: tools/lyric-launcher/build_manifest.py`

**Step 1 — discover the data.** Run a one-off script that, for every setlist folder in `R: cherry-daddies-setlist-2026-06-16/`, finds: set number (leading digits of folder name, else blank→assign later), and matches it to (a) a JamZone cat with `tiles.json`, (b) the `F: music/songs/<Artist - Title>/auto-render/` folder (must have `timeline.json`+`all.wav`), (c) the concert `.patch` folder in `R: 2000.concert/Concert.patch/`. Print a table; flag songs with no JamZone tiles as `manual`.

Run: `F/.venv/bin/python tools/lyric-launcher/build_manifest.py --dry-run`
Expected: a printed table of ~23 rows, JamZone vs manual clearly marked, plus any unmatched rows to resolve by hand.

**Step 2 — resolve + write.** Hand-fix unmatched rows / assign numbers to un-numbered sets, then write `songs.tsv` with columns:
```
set	song	clip	pc_field	source	cat	factory_dir	bed_dir	concert_patch
```
`clip` = set number (zero-padded 2). `pc_field` = clip + 1 (MainStage 1-based). `source` ∈ {jamzone, manual}.

**Step 3 — validate.** Run: `F/.venv/bin/python tools/lyric-launcher/build_manifest.py --check`
Expected: every `jamzone` row resolves to a real cat with tiles + a real `timeline.json`+`all.wav`; no duplicate `clip`/`pc_field`; prints "manifest OK (N jamzone, M manual)".

**Step 4 — commit.**
```bash
cd /Users/alex/projects/cherry-daddies
git add tools/lyric-launcher/build_manifest.py tools/lyric-launcher/songs.tsv
git commit -m "lyric-launcher: songs.tsv manifest (set→clip→pc→cat→bed→patch)"
```

---

## Phase B — Generation: manual front-end + renumber  (repo F)

### Task B2.1: Add `--lines` manual front-end to the clip generator

**Files:**
- Modify: `F: tools/lyric-launcher/make_song_clip.py`
- Test: `F: tools/lyric-launcher/tests/test_lines_frontend.py`

**Step 1 — write the failing test.** Parser turns a `{time,line}` TSV into the same `(start_sec, end_sec, text)` line list the JamZone path produces, with times used **directly** (no offset).
```python
# tests/test_lines_frontend.py
from make_song_clip import parse_lines_table
def test_parse_times_and_lines(tmp_path):
    f = tmp_path/"s.tsv"
    f.write_text("0:21.0\tLucky you were born\n0:25.3\tI love a foreign man\n")
    lines = parse_lines_table(str(f))
    assert lines[0][0] == 21.0 and lines[0][2] == "Lucky you were born"
    assert lines[1][0] == 25.3
    assert lines[0][1] == 25.3          # line end = next line start
```

**Step 2 — run, verify fail.**
Run: `cd tools/lyric-launcher && ../../.venv/bin/python -m pytest tests/test_lines_frontend.py -q`
Expected: FAIL (`parse_lines_table` undefined).

**Step 3 — implement.** Add `parse_lines_table(path)` (parse `m:ss.s` or seconds + tab + text; end = next start, last = +3s) and a `--lines FILE` arg that uses it instead of JamZone tiles, with `offset=0` (times already in playback seconds). Keep `--cat` path unchanged.

**Step 4 — run, verify pass.**
Run: same pytest command. Expected: PASS.

**Step 5 — commit.**
```bash
git add tools/lyric-launcher/make_song_clip.py tools/lyric-launcher/tests/test_lines_frontend.py
git commit -m "lyric-launcher: manual {time,line} front-end for non-JamZone songs"
```

### Task B2.2: Generate all JamZone clips at mirrored numbers

**Files:**
- Create: `F: tools/lyric-launcher/build_all_clips.py`
- Output: `F: tools/lyric-launcher/clips/NN.{mp4,ass}` per jamzone row

**Step 1 — script it.** `build_all_clips.py` reads `songs.tsv`, and for each `source=jamzone` row runs the existing `make_song_clip` logic with `--cat`, `--index=clip`, `--song=factory_dir`, `--title`.

**Step 2 — run.**
Run: `F/.venv/bin/python tools/lyric-launcher/build_all_clips.py`
Expected: "wrote NN.mp4 + NN.ass" for each jamzone song; lead-colour/line counts printed.

**Step 3 — verify renders.** Screenshot each clip at a mid-song lyric position (reuse the temp-mpv screenshot harness from this session). Eyeball: title + a real lyric line, no artifacts.
Run: `F/.venv/bin/python tools/lyric-launcher/verify_clips.py`  (loops clips, writes `/tmp/clip_<NN>.png`)
Then Read a few PNGs.

**Step 4 — clean up stale prototype clips.** Remove the old arbitrary-numbered demo clips (01/02/03 demo, 08/10/11/12 if they don't match final set numbers) so `clips/` only holds the manifest set.

**Step 5 — commit.**
```bash
git add tools/lyric-launcher/build_all_clips.py tools/lyric-launcher/verify_clips.py tools/lyric-launcher/clips
git commit -m "lyric-launcher: generate all JamZone clips at mirrored set numbers"
```

---

## Phase C — Runtime skeleton in the rig  (repo R)

### Task C1: Create `lyrics/` runtime folder

**Files:**
- Create: `R: lyrics/launcher.py` (copy of factory `launcher.py`)
- Create: `R: lyrics/send_pc.py` (copy; backup-machine test helper)
- Modify: `R: .gitignore` (add `lyrics/.venv/`, `lyrics/clips/*.mp4` are committed — keep them)

**Step 1** — `mkdir -p R/lyrics`, copy `launcher.py` + `send_pc.py` from `F/tools/lyric-launcher/`.
**Step 2** — append `lyrics/.venv/` to `R/.gitignore`.
**Step 3 — verify** the copied `launcher.py` is byte-identical: `diff F/tools/lyric-launcher/launcher.py R/lyrics/launcher.py` → no output.
**Step 4 — commit** (in repo R):
```bash
cd /Users/alex/projects/cherry-daddies-2000
git add lyrics/launcher.py lyrics/send_pc.py .gitignore
git commit -m "lyrics: runtime launcher into the rig repo"
```

### Task C2: `setup.command` (one-time bootstrap)

**Files:** Create `R: lyrics/setup.command`

**Step 1 — write it.** Bash, `set -euo pipefail`, `cd "$(dirname "$0")"`:
1. ensure `uv` (`command -v uv || curl -LsSf https://astral.sh/uv/install.sh | sh`),
2. `uv venv --python 3.12 .venv && uv pip install --python .venv mido python-rtmidi`,
3. ensure `mpv` (`command -v mpv || brew install mpv`; if no brew, print clear instructions),
4. verify: `.venv/bin/python -c "import mido; print(mido.get_input_names())"` and `mpv --version | head -1`,
5. print "✅ setup done — double-click Start Lyrics.command".
`chmod +x lyrics/setup.command`.

**Step 2 — run it.** `bash R/lyrics/setup.command`
Expected: venv built, mpv present, prints ✅. (`.venv/` is gitignored.)

**Step 3 — commit.**
```bash
git add lyrics/setup.command
git commit -m "lyrics: setup.command (uv venv + mpv bootstrap)"
```

### Task C3: `Start Lyrics.command` (daily run)

**Files:** Create `R: lyrics/Start Lyrics.command`

**Step 1 — write it.** Bash, `cd "$(dirname "$0")"`; exec:
`.venv/bin/python launcher.py --port "LyricLauncher" --screen 1` (one-way virtual port; fullscreen on display 2). `chmod +x`.
Note in a header comment: the External Instrument MIDI Output in MainStage must target `LyricLauncher`.

**Step 2 — smoke test (windowed override).** Run `.venv/bin/python launcher.py --port "LyricLauncher" --windowed`; in another shell `send_pc.py 3` → window rolls Whenever; Ctrl-C.

**Step 3 — commit.**
```bash
git add "lyrics/Start Lyrics.command"
git commit -m "lyrics: Start Lyrics.command (double-click run)"
```

### Task C4: `deploy_clips.sh` + deploy

**Files:**
- Create: `F: tools/lyric-launcher/deploy_clips.sh`
- Output: `R: lyrics/clips/NN.{mp4,ass}`, `R: lyrics/songs.tsv`

**Step 1 — write it.** Copies `F/tools/lyric-launcher/clips/*.{mp4,ass}` → `R/lyrics/clips/` and `songs.tsv` → `R/lyrics/`, printing what changed.
**Step 2 — run** `bash F/tools/lyric-launcher/deploy_clips.sh`.
**Step 3 — verify** clip count in `R/lyrics/clips/` == jamzone rows in manifest.
**Step 4 — commit (both repos):** the script in F; the clips+manifest in R.
```bash
# F
git add tools/lyric-launcher/deploy_clips.sh && git commit -m "lyric-launcher: deploy_clips.sh"
# R
cd /Users/alex/projects/cherry-daddies-2000
git add lyrics/clips lyrics/songs.tsv && git commit -m "lyrics: deploy JamZone clips + manifest"
```

### Task C5: `README.md` (wiring checklist + add-a-song)

**Files:** Create `R: lyrics/README.md`

Contents: first-time setup (`setup.command`), daily run (`Start Lyrics.command`), the **per-set MainStage wiring checklist** (Playback PLAY FROM Start + play-on-set-change; External Instrument MIDI Output=LyricLauncher + Send Program Change = the row's `pc_field`), the `songs.tsv` mapping, and **"add a Russian song"** (vocalist sends `m:ss line` table → `make_song_clip.py --lines … --index <set#>` in F → `deploy_clips.sh` → set `pc_field` in MainStage). Commit.

---

## Phase D — Concert templating spike  (repo R, on a copy)

### Task D1 — USER ACTION: wire one set by hand

In the live `2000.concert`, fully wire **one** JamZone set (recommend Whenever / `whenever.patch`). Commit in repo R so there's a clean before/after. Tell Claude the set name + the `pc_field` used.

### Task D2: Diff study

**Step 1** — `git show` the commit; for each changed `.cst`/`data.plist`, `plutil -convert xml1 -o - <file>` on the before (`git show HEAD~1:<path>`) and after, and diff the XML.
**Step 2** — Identify: which file is the External Instrument strip, the key holding the MIDI output port name (`LyricLauncher`), the Send-Program-Change value, and the Playback play-on-set-change flag + where it's referenced in the set's `data.plist`.
**Step 3 — decision:** if the strip transplants as a self-contained `.cst` + one `data.plist` registration with only the PC number varying → templating viable. Else → mark templating not viable, jump to the README checklist (Task D4) and stop Phase D.

### Task D3: Templating script (only if D2 viable)

**Files:** Create `F: tools/lyric-launcher/wire_concert.py`

**Step 1 — test on a copy.** Script takes a `.concert` path + `songs.tsv`; for each `source=jamzone` row it copies the wired `.cst` into that set's `concert_patch` folder, sets the PC value to the row's `pc_field`, flips Playback play-on-set-change, registers in `data.plist` (via plutil xml round-trip). Run first against `cp -R 2000.concert /tmp/2000-test.concert`.
**Step 2 — verify** `/tmp/2000-test.concert` opens in MainStage; spot-check 2–3 sets show the External Instrument → LyricLauncher + correct PC, and one live trigger (`Start Lyrics` + select the set → lyrics roll).
**Step 3 — apply to live** only after verification, in a git-clean state. Commit.
**Step 4 — commit** `wire_concert.py` (F) and the wired `2000.concert` (R).

### Task D4: Fallback checklist (if D2 not viable)

Ensure `R: lyrics/README.md` has the exact click-path per set; user wires remaining sets by hand (~2 min each). No code. Commit the README note.

---

## Phase E — End-to-end verification

**Step 1** — On the rig repo, fresh-ish: `setup.command` → `Start Lyrics.command` (windowed) → `send_pc.py <pc>` for 3 different sets → each rolls correct lyrics; `send_pc.py 0` → reset to title; instant `▶ PLAYING` flash shows.
**Step 2** — In MainStage: select 3 different wired sets in a row → each bed starts + correct lyrics roll from 0 (watch launcher log for `[pc N]`). Note any `no clip NN` (off-by-one in that set's field).
**Step 3** — Confirm fullscreen on the stage monitor (`--screen 1`) on the keyboardist laptop.
**Step 4** — Final commit / tag if desired.

---

## Notes
- Russian songs: not built now; README documents the manual path. (Out of scope.)
- Scrub/stop-follow: not possible via MainStage; would need Ableton clock master. (Out of scope.)
- All concert edits on a copy first; reversible via git.
