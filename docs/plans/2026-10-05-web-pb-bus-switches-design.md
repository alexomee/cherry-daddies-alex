# Web Playback Bus Switches (pb-other & pb-bass) — Design

**Date:** 2026-10-05  
**Status:** Approved  
**Topic:** Web player multi-track controls for MainStage playback buses (`pb-other` and `pb-bass`) with automatic mutual stem muting.

---

## 1. Overview & Goals

The Cherry & Daddies web dashboard (`web/index.html`) includes a Web Audio multi-track stem player (`vocal`, `back_vox`, `drums`, `keys`, `bass`, `guitars`, `other`, `click`, `cues`).
Band members and keyboardist need to audition and verify the actual stage playback tracks (`pb-other` and `pb-bass`) within the web dashboard.
When `pb-other` or `pb-bass` is turned on, the individual stems that are already included in that bus must be automatically muted so they do not double. Conversely, toggling a muted stem back on or disabling the bus restores normal playback.

---

## 2. Interaction Logic & State Machine

1. **Default State:**
   - Both `pb-other` and `pb-bass` are **OFF** by default when opening a song.
   - All standard stems are **ON** by default (existing behavior).
2. **Turning `pb-other` ON:**
   - Loads and plays `pb-other.mp3` via Web Audio.
   - Automatically sets gain to 0 (mutes) for all constituent stems covered by `pb-other` (e.g. `back_vox` and `keys`).
   - Visually updates the stem buttons to muted state and `pb-other` button to active state.
3. **Turning `pb-other` OFF:**
   - Sets gain of `pb-other` to 0 (or stops its source).
   - Automatically un-mutes (restores to active) the constituent stems that were muted by `pb-other`.
4. **Manual Stem Override while `pb-other` is ON:**
   - If user manually clicks an inactive stem that is part of `pb-other` (e.g. `keys`), the system infers that the user wants individual stem control: `pb-other` is automatically turned **OFF**, and the clicked stem is unmuted.
5. **`pb-bass` Behavior:**
   - Follows identical logic: turning `pb-bass` ON plays `pb-bass.mp3` and mutes `bass`. Turning it OFF restores `bass`. Un-muting `bass` manually turns `pb-bass` OFF.
6. **Badge & Counter:**
   - The mixer badge (`🎛️ N/M`) accounts for active stems/buses cleanly.

---

## 3. Data Model & Pipeline

### 3.1 `tools/setlist_dashboard.py` & `web/songs.json`
* For each song, inspect `mix.json`:
  * Map stems/layers listed in `pb-other` to canonical categories (`back_vox`, `keys`, `other`, `guitars`, `vocal`, `drums`, `bass`) matching `jamzone_render.py` classification.
  * Check existence of `auto-render/pb-other.mp3` and `auto-render/pb-bass.mp3`.
  * Output metadata into `web/songs.json`:
    ```json
    "pb_other": {
      "available": true,
      "mutes": ["back_vox", "keys"]
    },
    "pb_bass": {
      "available": true,
      "mutes": ["bass"]
    }
    ```
  * Compute content hashes for `pb-other` and `pb-bass` and include them in `s.versions` for cache busting (`?v=...`).

### 3.2 Audio Serving (`web/dev.mjs` & `tools/sync_site.py`)
* **Local Dev Server (`web/dev.mjs`):**
  - Allow `/audio?sid=<sid>&p=pb-other` -> `auto-render/pb-other.mp3`.
  - Allow `/audio?sid=<sid>&p=pb-bass` -> `auto-render/pb-bass.mp3`.
* **R2 Sync (`tools/sync_site.py`):**
  - Add `pb-other.mp3` and `pb-bass.mp3` to `desired()` so they are synchronized to R2 (`cherry-dash/<slug>/pb-other.mp3`, etc.).

---

## 4. UI / UX Design

Inside the unfolded track mixer row (`.mixrow`):
* Below or alongside the standard stem buttons, add a dedicated section:
  ```html
  <div class="mix-bus-group">
    <span class="mix-bus-label">Шина плейбека:</span>
    <button class="stem-btn bus-btn pb-other ..." data-bus="pb_other">🎹 pb-other</button>
    <button class="stem-btn bus-btn pb-bass ..." data-bus="pb_bass">🎸 pb-bass</button>
  </div>
  ```
* Buttons are only rendered if the song actually has `pb_other.available` or `pb_bass.available`.
* Styled distinctly with a subtle accent border or badge to distinguish full buses from raw stems.

---

## 5. Web Audio Engine Implementation

* In `playOrToggle(s, plEl, seekTime)`:
  - If `s.pb_other && s.pb_other.available`, include `pb-other` audio fetching in buffer preparation.
  - If `s.pb_bass && s.pb_bass.available`, include `pb-bass` audio fetching.
  - Create GainNodes for `pb-other` and `pb-bass` connected to `master`.
  - Initial gain values set based on stored mix preferences (defaulting to 0 for buses, 1 for stems).
* Click handlers:
  - Clicking a bus button toggles its state, applies `setTargetAtTime`, and updates the gains of muted stems.
  - Clicking a stem button toggles its state, and if turning on, turns off any conflicting active bus.
