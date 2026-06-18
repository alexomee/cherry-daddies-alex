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
- **Level model:** measured per-role loudness control (not hand-tuned).
- **Role tagging:** auto-detect by Moises stem name (regex) + per-stem override + a
  re-runnable classification audit ("agent review") to catch regex misses once.
- **Direction:** **ATTENUATE-ONLY, per-role CEILING** (revised — see Balance below). An element
  above its ceiling is pulled down; nothing is ever boosted.
- **Scope:** only `fx` + `back-vox` bounded; `musical` stays on the peak-only path.
- **Calibration:** seed sane ceiling constants, tune once after a listen.

### Balance — why ceiling, not bidirectional target (revised 2026-06-18)
pb-other plays through ONE MainStage fader and never carries the lead — it's all support whose
Moises **internal balance** must be preserved. A bidirectional target *boosts* quiet FX/back-vox
up to the target, which pushes a background swoosh/vocal **forward** against the pads/guitars
sharing the fader — breaking that balance (the first batch did exactly this: I Love It FX +5.9,
Blinding back-vox +6, Coldplay back-vox +5.5…). A **ceiling** only ever pulls *down* an element
that's too loud; a song whose FX already sits below the ceiling is untouched. So the rich
multi-element mixes (Cascada, Blinding, Infinity, S&M, Shakira, Heads, We Found Love, Band'Eros)
get **zero change**, balance preserved, while the genuinely-hot support elements (Better Off FX
−5.7, Я устал back-vox −6.9, …) come down. Fixes "too loud" and bounds loud FX/back-vox across
songs without the boost side-effect.

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
3. **Auto-gain (attenuate-only):** `gain = min(ceiling − measured, 0)` — pull down only if above
   ceiling, never boost. Measured on the raw stem buffer (before the group pitch pass — pitch
   doesn't move RMS), folded into the `gains` dict `mixdown` already takes.
   - Ceilings (seed, tuned once): `FX_CEILING −30`, `BACKVOX_CEILING −23` dBFS gated-RMS.
   - `gain_db` on a bounded stem = **trim added on top** (per-song nudge); on a musical stem it
     stays **absolute** as today.
   - layers classified + bounded the same way (e.g. Я устал `backing-vocal`, −6.9 dB).

## mix.json schema (additive, back-compatible)
```json
"pb-other": {
  "stems": ["04_Noise_effects"],
  "roles": {"08_Synth_Voice": "musical"},   // optional overrides / opt-out
  "gain_db": {"04_Noise_effects": 1}        // trim vs ceiling for bounded roles; absolute for musical
}
```

## Headroom interaction (accepted caveat)
Per-group peak headroom can rescale a bounded group. Attenuate-only never adds energy, so this
is even rarer than under a bidirectional target; when it does fire on a bounded group, render
prints a **warning**. Alternative (drop per-group peak-norm, trust the fader) rejected as clip-risky.

## Tooling
- `jamzone_render.py --levels [song]` — dry run, writes nothing. Per song: each fx/back-vox
  stem's role · measured loudness · attenuate-only gain (≤0; CUT vs ok) · post loudness.
  Cross-song summary: how many exceed the ceiling, measured & post range per role.
- classification audit = the same `--levels` listing of detected roles for review.

## Rollout
1. `--levels` dry run across all songs → review proposed cuts (THIS step gates everything).
2. Clear/convert manual gains on now-bounded stems (Saxobeat fx `+8.9`, Cascada `−2`).
3. Set role overrides from the audit (none needed — audit came back clean).
4. Re-render the songs with a cut; confirm `--levels` shows nothing above ceiling.
5. One listening pass (Better Off Alone + a multi-element mix) → nudge the two ceilings.

## Verification
`--levels` shows no element above its ceiling. Spot-listen the trigger song (Better Off Alone)
and a rich multi-element mix (Cascada/Blinding, which get zero change) to confirm balance held.
