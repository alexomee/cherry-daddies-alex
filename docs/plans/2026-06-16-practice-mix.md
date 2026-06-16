# Practice-Mix Render Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Emit a per-member `auto-render/practice-<player>.mp3` = full mix minus that member's live stems + click + cues, so a player can practice their part by playing along.

**Architecture:** One new `mix.json` key `players` (flat `player -> [stem/layer names]`). In `jamzone_render.py:main()`, after `all`/`click`/`cues`/layers/pitch are all built, loop the map: build a fresh `mixdown` of the music subset that drops the player's stems, pitch it to the band key, re-add the layers the player does **not** play, then mix at the `cue_preview` levels and encode mp3. No new flag; emitted on every full render. Backward-compatible (absent key → no-op).

**Tech Stack:** Python 3 + numpy, ffmpeg/rubberband CLIs. No test framework in repo — validation is an end-to-end render with numeric assertions on output WAV/MP3 plus a final ear-check (project rule: cues/practice are audio).

**Reference:** design doc `docs/plans/2026-06-16-practice-mix-design.md`. Target file `tools/jamzone/jamzone_render.py` (single script, `main()` spans lines ~506-806). Levels constant: `CLICK_LVL, MIX_LVL, CUE_LVL = 0.6, 0.85, 1.0` (line 57). `mixdown(names, gains, mutes)` line 612. `pitch_shift(buf, semitones)` line 120. cue_preview encode block lines 779-787.

---

## Task 1: Validate the `players` map

**Files:**
- Modify: `tools/jamzone/jamzone_render.py` (after the pb-other/pb-bass stem-validation loop, currently ending ~line 543, before `click_st = decode(...)` ~line 545)

**Step 1: Add the validation block**

Insert immediately after the existing `for grp in ("pb-other", "pb-bass"):` validation loop (the one ending with the `replaces` check), before `click_st = decode(stems[click_name])`:

```python
    players = mix.get("players") or {}                  # member -> stems/layers they play live;
    for who, owned in players.items():                  # practice mix per player = all minus these
        for nm in owned:
            if nm not in stems and not glob.glob(os.path.join(folder, "parts", nm + ".*")):
                sys.exit(f"mix.json: player '{who}' lists unknown stem/layer '{nm}'")
```

**Step 2: Verify it rejects a bad stem**

Pick any external song with a `mix.json` (e.g. `SEREBRO - Malo tebya`). Temporarily add a bad players key and run `--check`:

Run:
```bash
cd /Users/alex/projects/cherry-daddies/tools/jamzone
python3 - <<'PY'
import json, subprocess, os
p = os.path.expanduser("~/projects/cherry-daddies/music/songs/SEREBRO - Malo tebya/mix.json")
orig = open(p).read()
m = json.loads(orig); m["players"] = {"alex": ["nonsense"]}
open(p, "w").write(json.dumps(m))
r = subprocess.run(["python3","jamzone_render.py","Malo tebya","--check"], capture_output=True, text=True)
open(p, "w").write(orig)                       # always restore
print("RC", r.returncode); print(r.stdout[-200:]); print("ERR", r.stderr[-200:])
PY
```
Expected: non-zero RC, message `mix.json: player 'alex' lists unknown stem/layer 'nonsense'`. (Script restores the original `mix.json`.)

**Step 3: Verify a valid stem passes**

Run the same harness but with `{"alex": ["guitars"]}`. Expected: RC 0, normal `--check` grid output, no error.

**Step 4: Commit**

```bash
cd /Users/alex/projects/cherry-daddies
git add tools/jamzone/jamzone_render.py
git commit -m "practice-mix: validate players map (stems/layers must exist)"
```

---

## Task 2: Capture placed layer buffers for reuse

**Why:** the practice minus must re-add layers the player does NOT play (e.g. someone else's live bass), in the band key, unpitched — exactly as `all` gets them. The existing layer loop already builds each placed buffer `lb`; capture them in a list instead of recomputing.

**Files:**
- Modify: `tools/jamzone/jamzone_render.py` layer loop (currently ~lines 727-738, the `for grp in ("pb-other", "pb-bass"):` loop that adds `lb` to `out[grp]` and `out["all"]`)

**Step 1: Initialize the list before the loop**

Immediately before that `for grp in ("pb-other", "pb-bass"):` layer loop, add:

```python
    placed_layers = []                             # (name, placed band-key buffer) for practice minus
```

**Step 2: Append inside the loop**

Inside the loop, right after `lb = load_layer(nm, start) * 10**(g/20)` and before `out[grp] = out.get(...) + lb`, add:

```python
            placed_layers.append((nm, lb))
```

**Step 3: Verify nothing changed for existing renders**

Render a song that HAS a layer (`SEREBRO - Malo tebya` has `malo-bass`). Confirm output unchanged vs before (same `layer:` log line, same files):

Run:
```bash
cd /Users/alex/projects/cherry-daddies/tools/jamzone
python3 jamzone_render.py "Malo tebya" --check
```
Expected: RC 0, prints the existing `layer: malo-bass -> pb-bass + all (...)` line, grid green. `--check` writes no audio, so this just confirms no exception from the new code path.

**Step 4: Commit**

```bash
cd /Users/alex/projects/cherry-daddies
git add tools/jamzone/jamzone_render.py
git commit -m "practice-mix: capture placed layer buffers"
```

---

## Task 3: Build and write the practice mp3s

**Files:**
- Modify: `tools/jamzone/jamzone_render.py` — insert AFTER the `cue_preview.mp3` block (ends ~line 787, after the `extra = " + cue_preview.mp3"` and its print at ~788) and BEFORE the `export_stems` block (`exp = mix.get("export_stems")` ~line 792). This location is past the `--check` early-return (~line 768) and past `adir = ...` creation (~line 770), so practice files are written only on a real render and land in `auto-render/`.

**Step 1: Insert the practice-mix block**

```python
    for who, owned in players.items():             # practice mix: all MINUS this member's stems,
        owned = set(owned)                          # pitched to band key, + click + cues (cue_preview
        minus = mixdown([n for n in music if n not in replaced and n not in owned], {})
        if semi: minus = pitch_shift(minus, semi)   # member plays in band key -> minus is pitched;
        for nm, lb in placed_layers:                # layers are already band-key (never pitched): add
            if nm not in owned: minus = minus + lb  # back the ones this member does NOT play live
        pm = minus*MIX_LVL + out["click"]*CLICK_LVL
        if "cues" in out: pm = pm + out["cues"]*CUE_LVL
        pk = float(np.abs(pm).max())
        if pk > 0.97: pm *= 0.97/pk
        subprocess.run(["ffmpeg","-v","quiet","-y","-f","f32le","-ar",str(SR),"-ac","2","-i","-",
                        "-b:a","192k",os.path.join(adir, f"practice-{who}.mp3")],
                       input=pm.astype(np.float32).tobytes())
        print(f"✓ auto-render/practice-{who}.mp3 (all minus {sorted(owned)} + click + cues)")
```

**Step 2: Add first real data + render the test song**

`SEREBRO - Malo tebya` start cue is "Мало тебя guitar in" → Alex plays guitar there. Add the players key (this is both the test fixture and the first real datum the user confirmed):

```bash
cd /Users/alex/projects/cherry-daddies/tools/jamzone
python3 - <<'PY'
import json, os
p = os.path.expanduser("~/projects/cherry-daddies/music/songs/SEREBRO - Malo tebya/mix.json")
m = json.load(open(p)); m["players"] = {"alex": ["guitars"]}
json.dump(m, open(p,"w"), ensure_ascii=False, indent=2)
print("added players")
PY
python3 jamzone_render.py "Malo tebya"
```
Expected: among the output, `✓ auto-render/practice-alex.mp3 (all minus ['guitars'] + click + cues)`, and the file exists.

**Step 3: Assert practice mp3 exists, matches timeline, and differs from cue_preview**

The practice mix is `cue_preview` with the guitar removed → it must (a) exist, (b) be the same duration as `cue_preview.mp3`, (c) differ from it by a non-trivial amount (proves a stem was actually dropped).

Run:
```bash
cd "/Users/alex/projects/cherry-daddies/music/songs/SEREBRO - Malo tebya/auto-render"
python3 - <<'PY'
import subprocess, numpy as np, os
def dec(p):
    raw = subprocess.run(["ffmpeg","-v","quiet","-i",p,"-ac","2","-ar","44100","-f","f32le","-"],
                         capture_output=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1,2)
assert os.path.exists("practice-alex.mp3"), "practice-alex.mp3 missing"
pa, cp = dec("practice-alex.mp3"), dec("cue_preview.mp3")
n = min(len(pa), len(cp))
assert abs(len(pa)-len(cp)) < 44100*0.05, f"duration mismatch: {len(pa)} vs {len(cp)}"
diff = np.sqrt(((cp[:n]-pa[:n])**2).mean())
print(f"len pa={len(pa)} cp={len(cp)}  rms(cue_preview - practice) = {diff:.5f}")
assert diff > 1e-3, "practice == cue_preview -> no stem was removed"
print("OK: practice mix exists, aligned, guitar removed")
PY
```
Expected: prints `OK: ...` with a clearly non-zero RMS diff. (The diff ≈ the removed guitar stem at 0.85 gain, pitched.)

**Step 4: Backward-compat check — no `players` → no practice file**

Run:
```bash
cd /Users/alex/projects/cherry-daddies/tools/jamzone
ls "../../music/songs/Gala - Freed from Desire/auto-render/" 2>/dev/null | grep -c practice- || true
python3 jamzone_render.py "Freed from Desire" >/tmp/fd.log 2>&1; tail -1 /tmp/fd.log
ls "../../music/songs/Gala - Freed from Desire/auto-render/" | grep practice- && echo "FAIL: practice file leaked" || echo "OK: no players key, no practice file"
```
Expected: `OK: no players key, no practice file` (Gala has no `players` key). Pick any song whose `mix.json` lacks `players` if Gala already has one.

**Step 5: Ear-check (final gate, project rule)**

Listen to `music/songs/SEREBRO - Malo tebya/auto-render/practice-alex.mp3`: guitar fully gone, everything else + click + cues present, in band key, in time. Report; do not claim done before this passes.

**Step 6: Commit**

```bash
cd /Users/alex/projects/cherry-daddies
git add tools/jamzone/jamzone_render.py "music/songs/SEREBRO - Malo tebya/mix.json"
git commit -m "practice-mix: emit practice-<player>.mp3 (all minus player's stems)"
```

---

## Task 4: Document the feature

**Files:**
- Modify: `CLAUDE.md` (add a short section), and `music/README.md` if the per-song pipeline table should mention it.

**Step 1: Add a `## Practice-микс` section to CLAUDE.md**

Describe: `players` key shape (`{"alex": ["guitars","other"]}`, stem/layer names), that every render emits `auto-render/practice-<player>.mp3` = all minus that player's stems + click + cues at cue_preview levels, fully silent (not a guide), pitched to band key, layers the player doesn't play stay in. No flag; absent key = nothing. Match the file's terse Russian style.

**Step 2: Commit**

```bash
cd /Users/alex/projects/cherry-daddies
git add CLAUDE.md music/README.md
git commit -m "practice-mix: document players key + practice render"
```

---

## Notes / gotchas

- **Do not upload** anything — practice mp3s stay local in `auto-render/` (CLAUDE.md rule).
- **Per-song data follow-up (not this code change):** which stem(s) are Alex's varies per song — Moises splits guitar as `guitars`, synth usually as `other`/`keys`. Only `Malo tebya` is wired here (guitar). The rest of `players` across the 23 songs is a separate curated pass (draft a table, user confirms) — out of scope for this plan.
- **Cost:** one extra `rubberband` pass per player per render on pitched songs (~seconds). Unpitched songs: pure sum, no rubberband.
- If a song's `players` lists a stem already in `replaced` (e.g. a studio bass swapped for a live-bass layer), it's already absent from `all`; the set intersection is harmless.
