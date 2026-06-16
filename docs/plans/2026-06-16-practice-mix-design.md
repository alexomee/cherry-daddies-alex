# Practice-mix render — design (2026-06-16)

## Goal

Per-song **practice mix** for a single band member: a combined mp3 = the full mix
**minus the stem(s) that member plays live** + click + cues, so they can practice
their part by playing along to everything else. First user: Alex (guitars / synths,
varies per song). Stored "who plays what" lives in the song config.

## Config — `mix.json` new key `players`

Flat map, player → stem names that player covers live in **this** song:

```json
"players": { "alex": ["guitars", "other"] }
```

- Stem names are validated exactly like `pb-other`/`pb-bass` stems — unknown stem → `sys.exit`.
- Multiple players allowed; code loops the map and emits one mp3 per player.
- **No `players` key → nothing emitted.** Backward-compatible: the existing 23 songs
  render identically until the key is added.
- A player entry may name a `layer` (a part the member recorded) as well as a studio
  stem; both are dropped from that player's minus. (Alex currently = studio stems only.)

Which stem is "mine" is per-song data (Moises splits guitar as `guitars`, synth as
`other`/`keys`, and it varies). That table is curated separately from this code change.

## Render behavior (no flag — emitted on every render)

After `all` / `click` / `cues` are built, for each `player, stem_list` in `players`:

1. `owned = set(stem_list)`.
2. `minus = mixdown([n for n in music if n not in replaced and n not in owned], {})`
   then re-add layers whose name is **not** in `owned`.
3. `minus = pitch_shift(minus, pitch_semitones)` — you play in the band key, so the
   minus must be in band key (same path/engine as `all`). Skip if `pitch_semitones == 0`.
4. Mix at the **same levels as `cue_preview`** so it sounds familiar, your part gone:
   - with cues: `minus*MIX_LVL + click*CLICK_LVL + cues*CUE_LVL` (0.85 / 0.6 / 1.0)
   - no cues:   `minus*MIX_LVL + click*CLICK_LVL`
5. Peak-normalize if > 0.97, write `auto-render/practice-<player>.mp3` @ 192k
   (reuse the exact ffmpeg encode block used for `cue_preview.mp3`).

The practiced part is **fully silent** (level 0), not a faint guide.

`out["click"]` and `out["cues"]` are already built in the run — reused as-is, no rebuild.

## Cost

One extra `rubberband` pitch pass per player per render on pitched songs (~seconds).
Only `alex` is defined now → +1 pass. Unpitched songs → just a sum, no rubberband.

## Validation / edge cases

- Unknown stem in `players[*]` → `sys.exit` (mirrors `pb-other` stem check).
- A stem already in `replaced` and also `owned` → already absent from `all`; intersection
  is harmless (it just stays out).
- Song with no cues → click+minus only (no crash).
- Pitch 0 → minus is unpitched, same as `all`.

## Out of scope (YAGNI)

- No `--practice <player>` flag, no `player:instrument` sub-targeting — flat per-player
  removal only. Adding a band member later = config only (code already loops the map).
- No separate aligned stem set for a rig — single combined mp3 (home/headphone practice).
- Populating `players` across all songs is a follow-up data task, not this code change.
