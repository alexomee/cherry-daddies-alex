---
type: song
updated: 2026-10-26
title: Такая любовь
artist: 
set: tryout batch 2026-07
---

# Такая любовь

Tryout-батч 2026-07. Страница заведена 2026-09-02 при фиксе хвоста pb-bass; история cue — по git (`Такая любовь: 3 drums cues (bars 27/59/68)`). 2026-10-05: обновление cue (13 cue). 2026-10-11: бэк-вокал убран из pb-other и pb-other-keys; в pb-other добавлен пользовательский слой `sfx-pb`. 2026-10-12: добавлен cue «solo leak ready go» на 174.2с (такт 97, 00:02:54.222), всего 14 cue; обновлён слой `sfx-pb`; в `pb-other` добавлен слой `acoustic-guitar-solo` (акустическая гитара на соло, 165.2–194.8с). 2026-10-26: баланс уровня `gain_db: -3.5`, слой `acoustic-guitar-solo` заглушен после 2:59 (с такта 100, cue «verse in»: `"mute": {"acoustic-guitar-solo": [[100, 138]]}`), чтобы не звучать в куплете; в `pb-other` добавлен аккордовый слой клавиш `takaia_lubov_keys` (`gain_db: -2.5`), а `pb-bass` переведён на слой `takaia_lubov_bass` (`replaces: ["bass"]`, `gain_db: -5.0`).

## Сводка

- **bpm:** 135.0 · **pitch_semitones:** 0
- Источник: Moises-стемы (в корне `.wav`: bass, drums, guitars, keys, metronome, other, strings, vocals, wind, backing_vocals), константный клик (метроном ~ровный, max resid 29мс).
- mix.json: `/Users/alex/projects/cherry-daddies/music/songs/Такая любовь/mix.json`
- `cut_after_last_cue: 2` — рендер обрывается через 2 такта после «end in» (такт 137.1 = 245.33с), студийное аутро выброшено.

## Плейбек и рендер

- **pb-other:** strings + layers `sfx-pb` (роль `fx`, потолок −30 dBFS) + `acoustic-guitar-solo` (роль `musical`, `gain_db: -3.5`, соло-аккомпанемент на тактах 92–99, заглушен с такта 100 / 2:59) + `takaia_lubov_keys` (роль `musical`, `gain_db: -2.5`, аккордовый подклад клавиш с такта 5 до 135; итоговый `pb-other.wav` −24.78 dBFS gated RMS / −21.6 LUFS) · **pb-other-keys:** strings + keys (вариант без живого клавишника) · **pb-bass:** layer `takaia_lubov_bass` (`frame: "render"`, `replaces: ["bass"]`, `gain_db: -5.0` → −20.04 dBFS gated RMS / −18.6 LUFS) · **pb-drums:** drums (−3.1 dB).
- **players:** alex = guitars; roma = keys, strings, wind; steve = drums; tanya = vocals; trio = guitars+drums+vocals.
- Сетка: beat 0.4444с, такт 1.7778с, downbeat стема 0.5601с; OFF рендера +2.99542с, такт 1.1 = 3.556с рендера. Длина 245.333с = 138 тактов.

### Хвост pb-bass (2026-09-02)

Финальный удар банды — «end in» на 135.1 (241.78с). Студийный бас бьёт его вместе со всеми (стаккато, затухает за полдоли), такт 135 молчит, а с **136.1** начинает новую фразу — в 2-тактовом хвосте `cut_after_last_cue` она звучала после того, как банда уже остановилась. Фикс: `"pb-bass": {"stems": ["bass"], "mute": {"bass": [[135.5, 138]]}}` — бас в pb-bass глушится с 135.3 до конца; удар на 135.1 цел, pb-bass побайтно тот же до 242.6с. Только pb-bass: `all`/`cue_preview`/practice-миксы мьюты групп не применяют, там бас в такте 136 остался (по запросу — только pb-bass).

## Cue

14 cue:

- bar 1 — «Такая любовь · synth fade-in ready go» · 3.6с
- bar 5 — «chords in» · 10.7с
- bar 9 — «verse in» · 17.8с
- bar 26 — «drum fill ready go» · 48.0с
- bar 43 — «synth solo ready go» · 78.2с
- bar 51 — «soft verse ready go» · 92.4с
- bar 67 — «drum fill ready go» · 120.9с
- bar 84 — «synth solo ready go» · 151.1с
- bar 92 — «drum stop» («drum stop in 3 · 3 2 1») · 165.3с
- bar 93.4 — «guitar solo ready go» · 168.4с
- bar 97 — «solo leak ready go» · 174.2с
- bar 100 — «verse in» · 179.6с
- bar 111 — «chorus in» · 199.1с
- bar 135 — «end in» (`count: true`) · 241.8с

## Риг (MainStage)

Папка сетлиста: `/Users/alex/projects/cherry-daddies-2000/cherry-daddies-setlist-2026-06-16/Такая любовь/` (click/cues/pb-bass/pb-drums/pb-other/pb-other-keys). Синк 2026-09-02: `pb-bass.wav` (риг-коммит `75b7a5fc`). Синк 2026-10-11: обновление `pb-other.wav`, `pb-other-keys.wav` (бэк-вокал убран), а также свежих `cues.wav` и `pb-bass.wav`.
