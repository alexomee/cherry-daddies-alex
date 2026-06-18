# pb-other auto-leveling — design (2026-06-18)

## Problem
`pb-other` (and `pb-bass`) stems play in the keyboardist's MainStage at a fixed
fader. Their level in the file is whatever Moises gave, with only **peak headroom**
(`jamzone_render.py`, peak>0.99 → attenuate) — no perceived-loudness control. So a
hot stem stays hot: **Better Off Alone noise FX is too loud**. Across songs the two
recurring support roles — **noise/sound FX** (~10 songs) and **backing vocals**
(~9 songs) — sit at inconsistent, mostly-untuned levels. The keyboardist can't set
one fader that works everywhere.

## Goal
Systematically pin fx and back-vox stems to a **consistent per-role loudness** across
all songs, automatically, while leaving **musical** parts (synth lead, arpeggiator,
charango, organ…) alone — "some pb-other should be loud."

## Decisions (brainstorm)
- **Level model:** auto-level to a per-role loudness target (measured, not hand-tuned).
- **Role tagging:** auto-detect by Moises stem name (regex) + per-stem override + a
  re-runnable classification audit ("agent review") to catch regex misses once.
- **Direction:** level both ways, **boost capped at +6 dB** (no pumping sparse stems).
- **Scope:** only `fx` + `back-vox` auto-leveled; `musical` stays on the peak-only path.
- **Calibration:** seed sane target constants, tune once after a listen.

## Mechanism
1. **Classify** each stem/layer by name:
   `noise|sound.?effects?` → `fx`; `back(ing)?.?vocals?|back.?vox` → `back-vox`;
   else `musical`. `"roles": {"<stem>": "musical"}` in mix.json overrides (also the
   opt-out). Audit pass walks every song, flags ambiguous names
   (`Synth_Voice`, `Sample_(sung)`, `Percussion`, `Charango`, `Synth_Brass`) → user
   confirms overrides.
2. **Measure** gated RMS (perceived loudness over active regions): 400 ms windows,
   100 ms hop, mono-sum; keep windows ≥ (loudest window − 20 dB); average power →
   dBFS. Robust to the long silences in sparse FX/back-vox. Pure numpy, no new dep.
   (LUFS/K-weighting can swap in later; gated RMS gives within-role consistency now.)
3. **Auto-gain:** `gain = target − measured`, clamped to ≤ +6 dB boost, no cut limit.
   Measured on the raw stem buffer (before the group pitch pass — pitch doesn't move
   RMS), folded into the `gains` dict `mixdown` already takes.
   - Targets (seed, tuned once): `FX_TARGET`, `BACKVOX_TARGET` dBFS gated-RMS.
   - `gain_db` on an auto-leveled stem = **trim added on top of target** (per-song
     nudge); on a musical stem it stays **absolute** as today.
   - layers classified + leveled the same way (e.g. Я устал `backing-vocal`).

## mix.json schema (additive, back-compatible)
```json
"pb-other": {
  "stems": ["04_Noise_effects"],
  "roles": {"08_Synth_Voice": "musical"},   // optional overrides / opt-out
  "gain_db": {"04_Noise_effects": 1}        // trim vs target for auto roles; absolute for musical
}
```

## Headroom interaction (accepted caveat)
Per-group peak headroom can rescale an auto-leveled group, denting absolute
cross-song consistency. pb-other peaks are moderate so it rarely fires; when it does
on an auto-leveled group, render prints a **warning**. Targets seeded low enough
(peaky FX keeps headroom) that it stays rare. Alternative (drop per-group peak-norm,
trust the fader) rejected as clip-risky.

## Tooling
- `jamzone_render.py --levels [song]` — dry run, writes nothing. Per song: each
  fx/back-vox stem's role · measured loudness · proposed gain (capped?) · final.
  Cross-song summary: per-role measured spread and post-level spread (should flatten).
- classification audit = the same `--levels` listing of detected roles for review.

## Rollout
1. `--levels` dry run across all songs → review proposed gains (THIS step gates everything).
2. Clear/convert manual gains on now-auto stems (Saxobeat fx `+8.9`, Cascada `−2`).
3. Set role overrides from the audit.
4. Re-render all; confirm `--levels` post-level spread ≈ flat (±1–2 dB).
5. One listening pass (Better Off Alone + Blinding Lights) → nudge the two constants.

## Verification
Post-level spread within each role ≈ flat. Spot-listen the trigger song (Better Off
Alone) and a loud-musical song (Blinding Lights) to confirm musical parts untouched.
