---
type: song
updated: 2026-07-10
title: Adventure of a Lifetime
artist: Coldplay
set: СЕТ 1 #7
---

# Adventure of a Lifetime — Coldplay

СЕТ 1, позиция #7 (сверено с `web/songs.json`, slug `369f5f6cb7e3`).

## Сводка

- **Источник — JamZone** (не Moises): нумерованные стемы `NN_*.m4a`, `01_Click.m4a`, `cue_track.wav`, `cues.json`, `structure.txt`. См. [pipelines/jamzone-render.md](../pipelines/jamzone-render.md).
- **bpm 112.0** (из `auto-render/timeline.json`; в `mix.json` поле не задано — темп берётся из `01_Click.m4a`).
- **pitch_semitones не задан** (нет в `mix.json`) → минус в оригинальной тональности, без питча.
- Нет полей `cue_step`, `count_in`, `tempo_zone`, `click` — ровная сетка, всё по дефолту.
- Файлы: `music/songs/Coldplay - Adventure of a Lifetime/mix.json`, `.../structure.txt` (16 секций: Precount → Intro → … → Outro).

## Плейбек и рендер

Полный пакет в `music/songs/Coldplay - Adventure of a Lifetime/auto-render/`: `all.wav`, `click.wav`, `cues.wav`, `pb-other.wav`, `cue_preview.mp3`, `timeline.json` + practice-миксы. `pb-bass` = `null`.

- **Бас — живой** (`"note": "live bass"`; в `songs.json` `bass.who = "Roma (real bass-guitar)"`). `05_Bass.m4a` в плейбек НЕ идёт.
- **pb-other стемы:** `04_Noise_effects`, `09_Piano`, `10_Synth_Pad`, `11_Sample_(sung)`, `12_Backing_Vocals`, `13_Backing_Vocals`.
- **Перкуссия вон:** `03_Percussion.m4a` присутствует в папке, но НЕ включён в pb-other (правило «вся перкуссия кроме кита — из плейбека»). В плейбеке только `02_Drum_Kit`.
- **layers** — нет.

### players и practice-миксы

`players`: `steve` → `02_Drum_Kit`, `tanya` → `14_Lead_Vocal`, `alex` → `06_Acoustic_Guitar`, `07_Electric_Guitar`, `08_Electric_Guitar_(right)` (три гитары; из коммита 2026-06-19). Roma играет живой бас — отдельного practice-микса для него нет.

Practice-миксы: `practice-alex.mp3`, `practice-steve.mp3`, `practice-tanya.mp3` (каждый = весь микс без своих стемов + клик + cue). См. [pipelines/jamzone-render.md](../pipelines/jamzone-render.md).

## Cue

13 cue (сверено с `mix.json` и `songs.json`), обычные `in`/`stop`, без счётных входов и без `cue_step`:

- b2 «Adventure guitar in ready go» (стартовый), b9.3 «all in», b18 «verse in», b40 «stop», b50 «verse in», b64 «stop», b65.3 «all in», b74 «drums stop», b86 «drums in», b88 «guitar in», b95.3 «vocal in», b112 «guitar melody ready go», b119.4 «stop».

Разворот текста по общим правилам — см. [pipelines/cue-system.md](../pipelines/cue-system.md).

## История и гочи

- **2026-06-18** — новые рендеры (timeline) + правки mix.json + новые песни + layers (общий коммит).
- **2026-06-19** — заполнены `players`: alex = 3 гитары на Adventure (пакетный проход по 7 песням Saxobeat/Calabria/Adventure/Blinding/No Stress/Gala/Uptown).
- **2026-06-20** — последняя правка `mix.json` (общий коммит энкора/t.A.T.u.).
- **Мультикам гига (набор памяти):** ADVENTURE снят оператором, operator OFF = 1737.83с в `IMG_2689` (Set 1). См. [pipelines/multicam-concert.md](../pipelines/multicam-concert.md).
- `auto-render/07-lyric-review.mp4` — клип для ревью лирики (номер сета 7).

## Открытое

- Тональность песни не документирована явно в `mix.json` (питч 0 = оригинал); подтвердить, что живой басист/вокал играют в оригинальной тональности.
