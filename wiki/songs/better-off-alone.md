---
type: song
updated: 2026-07-10
title: Better Off Alone
artist: Alice Deejay
set: "СЕТ 1 #1"
---

# Better Off Alone — Alice Deejay

Открывашка программы: СЕТ 1, песня #1 (сверено с `/Users/alex/projects/cherry-daddies/web/songs.json`).
Папка: `/Users/alex/projects/cherry-daddies/music/songs/Alice Deejay - Better Off Alone/`.

## Сводка

- Источник — **JamZone** (нативные стемы `NN_Name.m4a`), не Moises. См. [../pipelines/jamzone-render.md](../pipelines/jamzone-render.md).
- **bpm ≈ 136.98** — в `mix.json` поля `bpm` НЕТ; темп/сетка выводятся из `01_Click.m4a` (`fit_grid`). Значение из `auto-render/timeline.json` (`bar_sec 1.752081`, `offset_sec −0.297038`).
- **pitch_semitones — не задан** (в оригинальной тональности, без питча).
- Особых полей `mix.json` нет: `cue_step`, `count_in`, `tempo_zone`, `click`, `layers` отсутствуют.

## Плейбек и рендер

Стемы JamZone (12 шт., `01_Click`…`12_Lead_Vocal`, `.m4a`). Мэппинг для плейбека в `mix.json`:

- `pb-other`: `04_Noise_effects` (задано 2026-06-13; уровень ограничен потолком pb-other, см. ниже).
- `pb-bass`: `null` (бас не в плейбеке).
- `layers`: нет.
- **Перкуссия вне плейбека:** стем `03_Percussion` присутствует в папке, но в `pb-other` НЕ включён — корректно по правилу «вся перкуссия кроме основного кита вон из плейбека».

Рендеры в `/Users/alex/projects/cherry-daddies/music/songs/Alice Deejay - Better Off Alone/auto-render/`: `all.wav`, `click.wav`, `cues.wav`, `pb-other.wav`, `cue_preview.mp3`, `timeline.json`. Плюс `01-lyric-review.mp4` (lyric-launcher review, см. [../pipelines/lyric-launcher.md](../pipelines/lyric-launcher.md)).

### players и practice-миксы

Живьём 4-piece (`mix.json` → `players`):

- **roma** — `07_Synth_Pad`, `11_Arpeggiator`, `08_Synth_Strings`, `10_Synth_Lead_2`.
- **alex** — `09_Synth_Lead_1` (задано 2026-06-19).
- **steve** — `02_Electronic_Drum_Kit`.
- **tanya** — `12_Lead_Vocal`.

Practice-миксы (весь микс минус свои стемы + клик + cue): `practice-roma.mp3`, `practice-alex.mp3`, `practice-steve.mp3`, `practice-tanya.mp3`. См. [../pipelines/jamzone-render.md](../pipelines/jamzone-render.md).

## Cue

16 cue (`mix.json`), везде bar-позиции в темпе песни. Особенности:

- **Счётные входы (`"count": true`)** — 2 шт.: `bass-only in` (bar 75) и `end in` (bar 123). Произносятся как «{текст} 3» + отсчёт «3 2 1» вместо «ready go». Такие cue получают лишний пустой count-in такт.
- **Cue на доле 2/3** (не только даунбит): `vocal in` bar 43 beat 2, `outro in` bar 114 beat 3. См. память «cue sections at beat resolution».
- Стартовый cue: `Better Off Alone all in` (bar 3).
- `cut off in` (bar 32) — 2026-06-13 переименован из `cut-off in`: дефис убран, чтобы слова легли по разным долям (иначе дефис = одно слово).
- Дефис-слова как одно слово: `bass-only`, `lead-and-pad`.
- `cue_step` не задан (дефолт 1) — темп ~137 не считается быстрым.

Общая cue-система: [../pipelines/cue-system.md](../pipelines/cue-system.md).

## История и гочи

- **2026-06-13** — оцифрован черновик cue (song #15 в той нумерации) в общем проходе разметки; семантика `bar 1.1 = музыкальный даунбит`.
- **2026-06-13** — `pb-other = 04_Noise_effects`; `cut-off in` → `cut off in`.
- **2026-06-18** — новые рендеры (timeline) + обновления mix.json.
- **2026-06-19** — `players`: alex играет `09_Synth_Lead_1`.
- **pb-other loudness ceiling** (память): именно шум-FX этой песни спровоцировал потолок уровня pb-other — noise FX был слишком громкий (−24.3 → −30 dBFS, −5.7 dB). Дизайн: `/Users/alex/projects/cherry-daddies/docs/plans/2026-06-18-pb-other-autolevel-design.md`.
- **BOA-рилс** (память `reels-better-off-alone-pipeline`): контент-рилс, где каждая нота синт-лида (`09_Synth_Lead_1`) триггерит позу банды; крыша `~/Downloads/IMG_2655.MOV`, рабочая папка `/tmp/boa_demo/` (в репо не коммичено). Ноты — спектральный флюкс (`flux_notes.py`), НЕ бит-сетка (рифф синкопирован против 137 bpm). См. [../pipelines/content-reels.md](../pipelines/content-reels.md).
- **Мультикам** (память `multicam-concert-pipeline`): BOA — якорь калибровки часов оператор-камеры (`DIMAS0222-019` op t0 = IMG_2689 287.36s → clock +1h00m16.6s). Set 1 operator OFF для BOA = 287.36 (первые 3с дропнуты — оговорка). См. [../pipelines/multicam-concert.md](../pipelines/multicam-concert.md).

## Открытое

- В `mix.json` нет `bpm` — темп полностью на `fit_grid` из клика (норма для JamZone, но значение bpm живёт только в `timeline.json`).
- BOA-рилс не закоммичен в репо (живёт в `/tmp/boa_demo/`, том может быть очищен).
