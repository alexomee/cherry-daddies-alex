---
type: song
updated: 2026-10-25
title: Destination Calabria
artist: Alex Gaudino
set: "СЕТ 1 #6"
---

# Destination Calabria — Alex Gaudino

Позиция: СЕТ 1 #6 (сверено с `/Users/alex/projects/cherry-daddies/web/songs.json`).
Папка: `/Users/alex/projects/cherry-daddies/music/songs/Alex Gaudino - Destination Calabria/`

## Сводка

- Источник — **JamZone** (стемы `01_Click.m4a` … `09_Lead_Vocal.m4a`), не Moises. См. [../pipelines/jamzone-render.md](../pipelines/jamzone-render.md).
- **bpm ≈ 128.01** (из `auto-render/timeline.json`, `bar_sec 1.874917`, `offset_sec -0.300794`).
- **pitch_semitones нет** — JamZone-стемы уже в тональности группы, питч не применяется.
- **`"click": "follow"`** + **`cut_bars`** (выравнивание сакс-соло и хвоста песни в ровную сетку 4/4):
  - В `click` вырезан полуторадольный сбой такта 71 (`[[71, 1], [71, "2&"]]`, `131.546–132.256 с`, `0.710 с`).
  - В `stems` вырезаны три вставленные восьмые паузы между фразами сакс-соло (`[67.1..67.1&]`, `[69.1&..69.2]`, `[71.2..71.2&]`, в сумме те же `0.710 с`).
  - В результате клик на протяжении всей песни идёт непрерывно в 4/4 (`max_resid = 8.4 мс`), сакс-соло (`Bars 65–72`) образует ровный 8-тактовый квадрат, а все секции после соло начинаются строго на сильной доле (Beat 1).
- Структура (`structure.txt`): Precount, Intro, Instrumental, Verse, Chorus, Instrumental 2, Verse 2, Chorus 2, Instrumental 3, Break, Chorus 3, Chorus 4, Outro.

## Плейбек и рендер

- `pb-other`: `04_Sound_Effects`, `06_Synth_Brass`.
- `pb-bass`: `05_Synth_Bass` (`gain_db -3`).
- Перкуссия `03_Percussion` **не** в миксе (правило: вся перкуссия кроме кита — вон из плейбека, [../pipelines/jamzone-render.md](../pipelines/jamzone-render.md)).
- layers — нет.
- Рендеры в `auto-render/`: `all.wav`, `click.wav`, `cues.wav`, `pb-bass.wav`, `pb-other.wav`, `cue_preview.mp3` (2026-10-25).
- **players** (кто играет живьём): `steve`=`02_Electronic_Drum_Kit`, `tanya`=`09_Lead_Vocal`, `alex`=`07_Baritone_Saxophone`, `roma`=`08_Tenor_Saxophone`. Practice-миксы на всех четверых: `practice-steve.mp3`, `practice-tanya.mp3`, `practice-alex.mp3`, `practice-roma.mp3`. См. [../pipelines/mainstage-rig.md](../pipelines/mainstage-rig.md).
- `tools/lyric-launcher/clips/06.ass` + `06.mp4` — сценические титры (с учётом сдвига `-0.710 с` после соло).

## Cue

15 cue (`mix.json`), все строго на сильной доле (Beat 1):
- Стартовый: bar 3 «Destination Calabria bass in ready go».
- Дальше: `all in` (7, 55, 75), `verse in` (11, 36), `more synths in` (44), `stop` (27, 52, 63), `sax solo in` (65), `crash in` (73), `vocal in` (74), `outro in` (87), `end stop` (96).
- Про раскрытие текста cue — [../pipelines/cue-system.md](../pipelines/cue-system.md).

## История и гочи

- **2026-06-18** — новые рендеры (timeline) + апдейты mix.json (общий проход по песням).
- **2026-06-19** — заведены `players`: alex — баритон-сакс, roma — тенор-сакс (Calabria в проходе по 7 песням).
- **2026-06-20** — ре-рендер `auto-render/`.
- **2026-06-22** — добавлен `06-lyric-review.mp4`.
- **2026-10-25** — выровнена сетка клика и стемов на и после сакс-соло (`cut_bars` `-0.710 с` / `1.5 доли`): соло стало ровным 8-тактовым квадратом (`Bars 65–72`), все cue хвоста (`73, 74, 75, 87, 96`) перенесены с `beat 2` на сильную долю (`beat 1`), обновлены веб, титры `06.ass`/`06.mp4` и риг.

## Открытое

- Нет.
