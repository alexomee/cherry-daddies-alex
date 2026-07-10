---
type: song
updated: 2026-07-10
title: We Found Love
artist: Rihanna & Calvin Harris
set: СЕТ 2 #8
---

# We Found Love

JamZone-песня (стемы `01_Click`…`12_Lead_Vocal`), СЕТ 2 #8. Папка: `/Users/alex/projects/cherry-daddies/music/songs/Rihanna & Calvin Harris - We Found Love/`.

## Сводка

- **bpm 128**, такт 1.875с (из `auto-render/timeline.json`; в `mix.json` ключа `bpm` нет — сетка из JamZone `01_Click.m4a`).
- **pitch_semitones: нет (= 0).** Плейбек в оригинальной тональности. ⚠️ 2026-06-13 ставили `-2` (транспонирование в тональность группы, коммит `fa3e9cb`), в тот же день откатили обратно на 0 (коммит `a81c011`, «pitch обратно 0»). Если группа снова захочет минус в свою тональность — вернуть `pitch_semitones: -2`.
- Спец-полей `cue_step`, `count_in`, `tempo_zone`, `click` в `mix.json` **нет** (ровный темп, дефолтная cue-сетка).

См. [moises-import / jamzone](../pipelines/jamzone-render.md), [cue-система](../pipelines/cue-system.md).

## Плейбек и рендер

- **pb-other:** `04_Noise_effects`. **pb-bass:** `05_Synth_Bass`.
- **Перкуссия вне плейбека:** `03_Percussion.m4a` в микс НЕ идёт (её играет живой барабанщик; в плейбеке только `02_Electronic_Drum_Kit`). Соответствует правилу проекта.
- **layers нет.**
- `auto-render/`: `all.wav`, `click.wav`, `cues.wav`, `pb-other.wav`, `pb-bass.wav`, `cue_preview.mp3`, `timeline.json` (последний рендер 2026-06-20). Плюс `19-lyric-review.mp4` (превью для проверки лирики, см. [lyric-launcher](../pipelines/lyric-launcher.md)).
- **pb-other под потолком громкости** — богатый многоэлементный микс, аттенюатор-потолок его не трогает (нулевая правка).

### Players / practice-миксы

- `steve`: `02_Electronic_Drum_Kit`
- `tanya`: `12_Lead_Vocal`
- `roma`: `06_Organ_1`, `07_Organ_2`, `08_Organ_3`, `09_Synth_Keys_1`, `10_Synth_Keys_2`, `11_Synthesizer`
- Рендерятся `auto-render/practice-steve.mp3`, `practice-tanya.mp3`, `practice-roma.mp3`.
- Alex в этой песне **не играет** (нет его практис-микса) — зафиксировано в памяти players.

См. [practice-mix / players](../pipelines/jamzone-render.md).

## Cue

- **16 cue**, ровная 8-тактовая структура секций (`intro`→`verse`→`chorus`→`break`… по `structure.txt`). Все с `abs_sec` (добавлены при ре-рендере 2026-06-18).
- Стартовый: bar 3 «We Found Love synth in».
- **Стопы (`stop` → «… in 3», отсчёт 3-2-1):** bar 71 «break 2 drum stop», bar 114.4 «end stop».
- Дефолтная скорость (`cue_step` не задан). Счётных входов (`count`) нет.
- Cue вводились/правились вручную в Logic (не автоген) — см. историю.

## История и гочи

- **2026-06-11** — cue для WFL заведены вручную в Logic (батч репетиции); автоген удалён.
- **2026-06-13** — семантика cue `bar 1.1 = музыкальный даунбит`. Поставили `pitch_semitones -2`, затем в тот же день откатили на 0; заданы `pb-other=04_Noise_effects`, `pb-bass=05_Synth_Bass`; де-дефисация cue-текстов (`more synth`, `intro 2`, `verse 2 less synth`, `build up`, `chorus 2/3/4`, `break 2/3`, `verse 3`); `instrumental` тянется на 2 доли.
- **2026-06-18** — новые рендеры + `timeline.json` + `abs_sec` у cue.
- **2026-06-19** — `players` финализированы (SET 2, завершение назначения по всему сетлисту).
- **2026-06-20** — последний рендер `auto-render/` + `19-lyric-review.mp4`.

## Открытое

- Тональность плейбека: сейчас 0 (оригинал). Проверить с группой, не нужен ли `-2` в тональность банды (была попытка и откат 2026-06-13 — причина отката в коммите не указана).
