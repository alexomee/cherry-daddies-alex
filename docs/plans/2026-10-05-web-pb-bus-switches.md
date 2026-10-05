# Web Playback Bus Switches (pb-other & pb-bass) Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add `pb-other` and `pb-bass` playback bus controls in the web dashboard multi-track mixer with mutual exclusion that automatically mutes constituent individual stems.

**Architecture:** 
1. `tools/setlist_dashboard.py` maps `pb-other` and `pb-bass` from `mix.json` to canonical stem IDs (`back_vox`, `keys`, `other`, `guitars`, `bass`, etc.) and writes `pb_other` / `pb_bass` availability and mute mappings into `web/songs.json`.
2. `web/dev.mjs` and `tools/sync_site.py` support serving and synchronizing `pb-other.mp3` and `pb-bass.mp3`.
3. `web/index.html` renders a dedicated "Шины плейбека" block in the mixer row and manages Web Audio GainNodes with two-way mutual exclusion logic.

**Tech Stack:** Python 3, Node.js (HTTP / dev server), Web Audio API, Vanilla JavaScript, HTML5/CSS3.

---

### Task 1: Data Model in `tools/setlist_dashboard.py`

**Files:**
- Modify: `tools/setlist_dashboard.py`
- Output: `web/songs.json`

**Step 1: Inspect and implement canonical stem categorization for `pb-other` and `pb-bass`**
Add helper function `covered_categories(group_items, is_bass=False)` in `tools/setlist_dashboard.py` that maps stems and layers in `pb-other` / `pb-bass` to canonical categories using rules:
- `back_vox`: regex `back(ing)?.?vocals?|back.?vox`
- `vocal`: regex `lead.?vocal|^vocals?$`
- `drums`: regex `drum`
- `bass`: regex `bass`
- `guitars`: regex `guitar`
- `keys`: regex `keys|piano|organ|synth|clav|rhodes|accord|vibe`
- `other`: any other sound/effect/horn/noise/string

Check file existence of `auto-render/pb-other.mp3` and `auto-render/pb-bass.mp3`.
Add version hashes for `pb-other` and `pb-bass` in `versions` dictionary.
Output `pb_other` and `pb_bass` objects in each song record in `web/songs.json`.

**Step 2: Run `python3 tools/setlist_dashboard.py` and inspect `web/songs.json`**
Run: `python3 tools/setlist_dashboard.py`
Verify songs like `5sta Family & 23:45 - Я буду`, `Mr. Credo - Медляк`, `The Offspring - Pretty Fly (For A White Guy)` have correct `pb_other` and `pb_bass` entries.

**Step 3: Commit data model changes**
```bash
git add tools/setlist_dashboard.py web/songs.json
git commit -m "feat(web): export pb_other and pb_bass mute mapping to songs.json"
```

---

### Task 2: Audio Serving in `web/dev.mjs` & R2 Sync in `tools/sync_site.py`

**Files:**
- Modify: `web/dev.mjs:60-67`
- Modify: `tools/sync_site.py:63-94`

**Step 1: Update `web/dev.mjs`**
Allow `player` parameter to accept `pb-other` and `pb-bass`:
```javascript
if (!/^(all|drums|alex|steve|roma|tanya|trio|pb-other|pb-bass)$/.test(player)) return send(res, 400, "bad player");
fp = player === "all"
  ? path.join(MUSIC, sid, "auto-render", "cue_preview.mp3")
  : player === "drums"
  ? path.join(MUSIC, sid, "auto-render", "pb-drums.mp3")
  : player === "pb-other"
  ? path.join(MUSIC, sid, "auto-render", "pb-other.mp3")
  : player === "pb-bass"
  ? path.join(MUSIC, sid, "auto-render", "pb-bass.mp3")
  : path.join(MUSIC, sid, "auto-render", `practice-${player}.mp3`);
```

**Step 2: Update `tools/sync_site.py`**
In `desired()`: check `s.get("pb_other", {}).get("available")` and `s.get("pb_bass", {}).get("available")`.
Collect `cherry-dash/<slug>/pb-other.mp3` and `cherry-dash/<slug>/pb-bass.mp3` if their files exist and versions are present.

**Step 3: Test audio serving via curl**
Start or verify server, curl: `curl -I "http://localhost:5173/audio?sid=5sta%20Family%20%26%2023%3A45%20-%20%D0%AF%20%D0%B1%D1%83%D0%B4%D1%83&p=pb-other"`
Expected: HTTP 200 OK with `audio/mpeg` content-type.

**Step 4: Commit audio serving updates**
```bash
git add web/dev.mjs tools/sync_site.py
git commit -m "feat(web): support pb-other and pb-bass in local dev server and R2 sync"
```

---

### Task 3: Frontend UI and Web Audio Engine in `web/index.html`

**Files:**
- Modify: `web/index.html`

**Step 1: UI Rendering in `mixRowHtml`**
Add a dedicated `.mix-bus-group` below `.stem-buttons` when `s.pb_other?.available` or `s.pb_bass?.available`:
```html
<div class="mix-bus-group">
  <span class="mix-bus-label">Шина плейбека:</span>
  <!-- pb-other button if available -->
  <!-- pb-bass button if available -->
</div>
```
Add CSS styling for `.mix-bus-group`, `.mix-bus-label`, and `.bus-btn`.

**Step 2: Audio Loading in `playOrToggle`**
If `s.pb_other?.available`, fetch and decode `audioSrc(s, "pb-other")` alongside stems.
If `s.pb_bass?.available`, fetch and decode `audioSrc(s, "pb-bass")` alongside stems.
Create GainNodes `gains["pb_other"]` and `gains["pb_bass"]` connected to `master`.
Initial gains: 0.0 (off by default) or according to stored `prefs["pb_other"]` / `prefs["pb_bass"]`.

**Step 3: Event handling and mutual exclusion**
In `setupToggles`:
- Click on `.bus-btn`:
  - Toggle bus active state.
  - If activating:
    - Set bus gain to 1.0.
    - For each stem category ID in `bus.mutes`:
      - Set stem gain to 0.0.
      - Mark stem button as muted (`stemBtn.classList.remove("active")`, `stemBtn.classList.add("muted")`).
      - Set `prefs[stId] = false`.
  - If deactivating:
    - Set bus gain to 0.0.
    - For each stem category ID in `bus.mutes`:
      - Set stem gain to 1.0.
      - Mark stem button as active (`stemBtn.classList.add("active")`, `stemBtn.classList.remove("muted")`).
      - Set `prefs[stId] = true`.
  - Save prefs to localStorage and update badges.
- Click on `.stem-btn`:
  - Standard toggle.
  - If user is turning stem ON:
    - If `s.pb_other?.available && prefs["pb_other"] && s.pb_other.mutes.includes(stemId)`:
      - Turn `pb_other` OFF: set its gain to 0.0, update button class, set `prefs["pb_other"] = false`.
    - If `s.pb_bass?.available && prefs["pb_bass"] && s.pb_bass.mutes.includes(stemId)`:
      - Turn `pb_bass` OFF: set its gain to 0.0, update button class, set `prefs["pb_bass"] = false`.
  - Save prefs to localStorage and update badges.

**Step 4: Commit frontend changes**
```bash
git add web/index.html
git commit -m "feat(web): add pb-other and pb-bass bus buttons with mutual stem muting in mixer"
```

---

### Task 4: Verification & Browser Testing

**Step 1: Verify on "Я буду"**
- `pb_other` covers `keys` (piano).
- Turning on `pb-other` mutes `keys`. Turning on `keys` deactivates `pb-other`.
- Turning on `pb-bass` mutes `bass`. Turning on `bass` deactivates `pb-bass`.

**Step 2: Verify on song with backing vocals + keys, e.g. "Adventure of a Lifetime" or "Blinding Lights"**
- Turning on `pb-other` mutes both `back_vox` and `keys` (and `other`).
