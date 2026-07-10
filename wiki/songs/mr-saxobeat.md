---
type: song
updated: 2026-07-10
title: Mr. Saxobeat
artist: Alexandra Stan
set: СЕТ 1 #5
---

# Mr. Saxobeat — Alexandra Stan

Позиция в сетлисте: **СЕТ 1, #5** (сверено с `/Users/alex/projects/cherry-daddies/web/songs.json`).
Папка: `/Users/alex/projects/cherry-daddies/music/songs/Alexandra Stan - Mr. Saxobeat/`

## Сводка

- **Источник — JamZone** (не Moises): нумерованные стемы `01_Click.m4a … 15_Lead_Vocal_♂.m4a` + `01_Click.m4a` для сетки. См. [jamzone-render](../pipelines/jamzone-render.md).
- **bpm / pitch:** в `mix.json` полей `bpm` и `pitch_semitones` **нет** — темп берётся из `01_Click.m4a` (`fit_grid`), питч не применяется (стемы в оригинальной тональности).
- **Особые поля `mix.json`:** только `pb-other`/`pb-bass`/`export_stems`/`players`/`cues`. Нет `cue_step`, `count_in`, `tempo_zone`, `click`, `layers`.
- `structure.txt`: Precount → Intro → Chorus ×2 → Instrumental ×2 → Verse → Chorus 3 → Instrumental 3/4 → Break → Chorus 4/5.

## Плейбек и рендер

Стемы в миксе (`/Users/alex/projects/cherry-daddies/music/songs/Alexandra Stan - Mr. Saxobeat/mix.json`):

- **pb-other:** `04_Noise_effects`, `10_Saxophone_(reverse)` (gain **+8.9 dB**). Реконструкция оригинального бounce, fit 1.000 (коммит `495cc7e`, 2026-06-12).
- **pb-bass:** `05_Synth_Bass`.
- **export_stems** → `auto-render/synths/` (для клавишника, wav в темпе/сетке рендера): `06_Synth_Lead`, `07_Synth_Keys_1`, `08_Synth_Keys_2`, `09_Synth_Keys_3`.
- **Вон из плейбека** (правило «перкуссия/лишнее — вон»): `03_Percussion`, `12_Backing_Vocals`, лид-вокалы и живые синты — не в миксе.
- Нет `layers` и папки `parts/` — живые партии как layer не заводились.

**players** (кто играет живьём):
- **alex** — `06_Synth_Lead`, `11_Saxophone`
- **roma** — `07_Synth_Keys_1`, `08_Synth_Keys_2`, `09_Synth_Keys_3`
- **steve** — `02_Electronic_Drum_Kit`
- **tanya** — `13/14/15` (Lead Vocal Alexandra Stan + ad_lib + Lead Vocal ♂)

**practice-миксы** (`auto-render/`): `practice-alex.mp3`, `practice-roma.mp3`, `practice-steve.mp3`, `practice-tanya.mp3` + `cue_preview.mp3` (all). См. [practice-микс](../pipelines/jamzone-render.md).

Рендеры в `auto-render/` (от 2026-06-20): `all.wav`, `click.wav`, `cues.wav`, `pb-other.wav`, `pb-bass.wav`, `cue_preview.mp3`, `timeline.json`. Также `05-lyric-review.mp4` (проверка лирики для [lyric-launcher](../pipelines/lyric-launcher.md)).

## Cue

**13 cue** (совпадают в `mix.json` и `web/songs.json`). См. [cue-система](../pipelines/cue-system.md).

| bar | text | abs_sec |
|----|------|---------|
| 3 | Mr Saxobeat sax in ready go (стартовый) | 3.78 |
| 11 | bass in | 18.90 |
| 16 | vocal in | 28.35 |
| 33 | alex vocal in | 60.47 |
| 41 | chorus melody in | 75.59 |
| 49 | verse in | 90.71 |
| 57 | stop | 105.83 |
| 66 | alex vocal in | 122.84 |
| 74 | sax solo in | 137.95 |
| 82 | bass in | 153.07 |
| 87 | vocal in | 162.52 |
| 95 | sax in | 177.64 |
| 103 | stop | 192.76 |

- Стартовый cue разворачивается в «Mr Saxobeat sax in ready go».
- Два `stop` (bar 57, 103) → «... stop in 3» + отсчёт 3-2-1.
- Обычный темп — `cue_step` не задан (1). Count-in не форсирован.

## История и гочи

- **2026-06-12** (`64dde1e`, `eaab17b`): каунт-ин такт вырезан — клик-стем `01_Click.m4a` сам даёт 3 такта до музыки; `t=0` = первый даунбит.
- **2026-06-12** (`495cc7e`): песня переведена на авто-бounce `jamzone_render.py`; `pb-other = Noise + Sax(reverse) +8.9 dB`, fit 1.000.
- **2026-06-12** (`20934bd`): `export_stems` — 5 синтов отдельными wav в `auto-render/synths/` для клавишника.
- **2026-06-19** (`265621c`): добавлены `players`.
- **2026-06-20** (`ba99446`): последний ре-рендер (`mix.json` и `auto-render/` от 2026-06-20).
- **Прецедент scope** (память `confirm-scope-first`): пользователь прервал задачу prepend-бара к Saxobeat-стемам — scope не был зафиксирован. Аудио-правки без чёткого scope тратят рендеры.
- **Мультикам** (память `multicam-concert-pipeline`): SET 1, operator OFF `SAXOBEAT 1345.22` (IMG_2689). См. [multicam-concert](../pipelines/multicam-concert.md).

## Открытое

- Cue `alex vocal in` (bar 33, 66): в `players` alex закреплён за `06_Synth_Lead` + `11_Saxophone`, а вокальные стемы (включая `15_Lead_Vocal_♂`) — у tanya. Кто поёт эти вступления живьём — не зафиксировано (возможно alex берёт мужской вокал). Уточнить.
