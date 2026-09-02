---
type: song
updated: 2026-09-02
title: Такая любовь
artist: 
set: tryout batch 2026-07
---

# Такая любовь

Tryout-батч 2026-07. Страница заведена 2026-09-02 при фиксе хвоста pb-bass; история cue — по git (`Такая любовь: 3 drums cues (bars 27/59/68)`).

## Сводка

- **bpm:** 135.0 · **pitch_semitones:** 0
- Источник: Moises-стемы (в корне `.wav`: bass, drums, guitars, keys, metronome, other, strings, vocals, wind, backing_vocals), константный клик (метроном ~ровный, max resid 29мс).
- mix.json: `/Users/alex/projects/cherry-daddies/music/songs/Такая любовь/mix.json`
- `cut_after_last_cue: 2` — рендер обрывается через 2 такта после «end in» (такт 137.1 = 245.33с), студийное аутро выброшено.

## Плейбек и рендер

- **pb-other:** backing_vocals + strings · **pb-other-keys:** backing_vocals + strings + keys (вариант без живого клавишника) · **pb-bass:** bass · **pb-drums:** drums (−3.1 dB).
- **players:** alex = guitars; roma = keys, strings, wind; steve = drums; tanya = vocals; trio = guitars+drums+vocals.
- Сетка: beat 0.4444с, такт 1.7778с, downbeat стема 0.5601с; OFF рендера +2.99542с, такт 1.1 = 3.556с рендера. Длина 245.333с = 138 тактов.

### Хвост pb-bass (2026-09-02)

Финальный удар банды — «end in» на 135.1 (241.78с). Студийный бас бьёт его вместе со всеми (стаккато, затухает за полдоли), такт 135 молчит, а с **136.1** начинает новую фразу — в 2-тактовом хвосте `cut_after_last_cue` она звучала после того, как банда уже остановилась. Фикс: `"pb-bass": {"stems": ["bass"], "mute": {"bass": [[135.5, 138]]}}` — бас в pb-bass глушится с 135.3 до конца; удар на 135.1 цел, pb-bass побайтно тот же до 242.6с. Только pb-bass: `all`/`cue_preview`/practice-миксы мьюты групп не применяют, там бас в такте 136 остался (по запросу — только pb-bass).

## Cue

15 cue:

- bar 1 — «Такая любовь synth in» · 3.6с
- bar 5 — «chords in» · 10.7с
- bar 9 — «verse in» · 17.8с
- bar 21 — «strings in» · 39.1с
- bar 27 — «drums in» · 49.8с
- bar 43 — «solo in» · 78.2с
- bar 51 — «soft verse ready go» · 92.4с
- bar 59 — «light drums ready go» · 106.7с
- bar 68 — «drums in» · 122.7с
- bar 84 — «solo in» · 151.1с
- bar 92 — «stop» · 165.3с
- bar 93.4 — «guitar in» · 168.4с
- bar 100 — «verse in» · 179.6с
- bar 111 — «chorus in» · 199.1с
- bar 135 — «end in» (`count: true`) · 241.8с

## Риг (MainStage)

Папка сетлиста: `/Users/alex/projects/cherry-daddies-2000/cherry-daddies-setlist-2026-06-16/Такая любовь/` (click/cues/pb-bass/pb-drums/pb-other/pb-other-keys). Синк 2026-09-02: только `pb-bass.wav` (pb-other/pb-other-keys с тем же контентом — откачены, чтобы не тащить дизеринг-дрейф). Риг-коммит `75b7a5fc`, запушен.
