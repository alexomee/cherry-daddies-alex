---
type: song
updated: 2026-07-10
title: Солнышко
artist: Demo
set: СЕТ 2 #1
---

# Солнышко (Demo)

Открывает СЕТ 2 (первая песня; сверено с `/Users/alex/projects/cherry-daddies/web/songs.json`).

## Сводка

- **bpm:** 138.0
- **pitch_semitones:** −2 (C minor → Bb minor, тональность группы)
- **count_in:** 1 (принудительный каунт-ин такт спереди — см. Cue)
- Источник: Moises-стемы (`moises-orig/`), варпнуты на константную сетку. См. [moises-import](../pipelines/moises-import.md).
- mix.json: `/Users/alex/projects/cherry-daddies/music/songs/Demo - Solnyshko/mix.json`
- `tempo_zone` нет, `cue_step` нет, `click` нет (константная сетка после варпа).

## Плейбек и рендер

Стемы (Moises, варпнутые, в корне папки): `bass.wav`, `drums.wav`, `guitars.wav`, `keys.wav`, `other.wav`, `vocals.wav`, `metronome.wav`. Оригиналы Moises → `moises-orig/`.

- **pb-other:** `null` (нет).
- **pb-bass:** layer `synth-bass`, frame **render**, `replaces: ["bass"]`, `gain_db: −10`.
  - Источник layer: `/Users/alex/projects/cherry-daddies/music/songs/Demo - Solnyshko/parts/synth-bass.wav` (read-only). Живой синт-бас Alex-а вместо студийного — студийный `bass` выкидывается из `all`/превью. Layer уже в ключе группы → не питчится. См. [jamzone-render](../pipelines/jamzone-render.md).

**players:** `roma`: keys, other · `steve`: drums · `tanya`: vocals · `alex`: bass, synth-bass. Alex играет бас (оба баса), в его practice-миксе бас исключён.

Рендеры в `/Users/alex/projects/cherry-daddies/music/songs/Demo - Solnyshko/auto-render/`: `all.wav`, `click.wav`, `cues.wav`, `pb-bass.wav`, `cue_preview.mp3`, `timeline.json`, practice-миксы `practice-alex.mp3`, `practice-roma.mp3`, `practice-steve.mp3`, `practice-tanya.mp3`. Также `12-lyric-review.mp4` (превью лирики).

## Cue

19 cue (`Солнышко all in` старт + 3 стопа + входы секций). Особенности:

- **Стартовый cue** — «Солнышко all in» на такте 1, лидирует первую ноту внутри каунт-бара.
- **count_in: 1** — принудительный каунт-ин такт спереди. Без него сегодняшний (2026-06-20) рендер сбрасывал передний lead, на который песня рассчитывает.
- **Стопы (3):** bar 7 beat 4, bar 127 beat 4, bar 145.
- `cue_step` нет (темп 138 нормальный), счётных входов (`count`) нет, `tempo_zone` нет.
- См. [cue-system](../pipelines/cue-system.md).

## История и гочи

- **2026-06-12** — импорт: варп Moises-стемов на константную сетку 138.000. Локальный дрейф метронома: брейкдаун 2:06–2:20 уплывал до +52мс, аутро −40мс; после варпа худшая точка ±24мс. Первый клик метронома — НЕ сильная доля (хрома-флакс: смена гармонии на k%4==2 от первого клика) → `--downbeat` при варпе.
- **2026-06-12** — `pitch_semitones: −2` (C minor → Bb minor).
- **2026-06-12** — 19 cue заведены; тогда сверены с аудио были ТОЛЬКО 3 стопа, входы секций — нет.
- **2026-06-18** — новый рендер: offset пересчитался (2.227 с каунт-баром → 0.488), стартовый cue начал «влезать», авто-lead перестал срабатывать → передний lead потерялся.
- **2026-06-20** — фикс выравнивания (коммит `fae0708`): `count_in: 1` + КАЖДЫЙ cue сдвинут на 1 такт раньше. Входы были заведены на 1 такт позже относительно варпнутой записи (12 июня проверяли только стопы). Сверено на слух по `cue_preview.mp3`. Передний offset ЖЁСТКИЙ — двигает музыку+cue+клик вместе, поэтому добавление/удаление каунт-бара НЕ меняет относительное выравнивание cue-vs-музыка; «cue опаздывает» = ошибка авторинга `bar`, не lead. (Память: `cue-alignment-countin.md`.)

## Открытое

- Входы секций были выровнены на слух (2026-06-20), не по пер-стем онсетам. Если всплывёт рассинхрон — мерить онсеты bass/drums/keys/vocals на событии против `abs_sec` (не по RMS полного микса).
