---
type: song
updated: 2026-07-10
title: Freed From Desire
artist: Gala
set: СЕТ 1 #10
---

# Gala — Freed from Desire

Позиция в сетлисте: **СЕТ 1, песня #10** (сверено с `/Users/alex/projects/cherry-daddies/web/songs.json`).

Папка: `/Users/alex/projects/cherry-daddies/music/songs/Gala - Freed from Desire/`

## Сводка

- Источник — **JamZone** (стемы `01_Click`…`11_Lead_Vocal`, `.m4a`), не Moises. См. [../pipelines/jamzone-render.md](../pipelines/jamzone-render.md).
- **bpm ≈ 129.0**, bar ≈ 1.860465 c, offset_sec ≈ −0.297046 — из `auto-render/timeline.json` (в `mix.json` bpm НЕ задан; сетка от `01_Click.m4a` через `fit_grid`).
- `pitch_semitones` в `mix.json` отсутствует — JamZone-стемы уже в ключе группы, питч не применяется.
- Особых полей `mix.json` нет: **нет** `cue_step`, `count_in`, `tempo_zone`, `click`, `layers`.
- `mix.json`: `pb-other: null`, `pb-bass` со стемом `03_Synth_Bass`.

## Плейбек и рендер

- **pb-bass:** `03_Synth_Bass`.
- **pb-other:** `null` (ничего не подмешивается отдельной группой).
- Стем `10_Noise_effects.m4a` в папке есть, но **ни в одну группу не заведён** — в плейбек/`all` не попадает.
- **layers** нет.
- Рендеры в `auto-render/`: `all.wav`, `click.wav`, `cues.wav`, `pb-bass.wav`, `cue_preview.mp3`, `timeline.json`; плюс `10-lyric-review.mp4` (клип на ревью лирики, см. [../pipelines/lyric-launcher.md](../pipelines/lyric-launcher.md)).

### players и practice-миксы

`mix.json` `players` (кто играет ЖИВЬЁМ):

- **steve** — `02_Electronic_Drum_Kit` → `auto-render/practice-steve.mp3`
- **tanya** — `11_Lead_Vocal` → `auto-render/practice-tanya.mp3`
- **roma** — все синты: `04_Piano`, `05_Organ`, `06_Synth_Strings`, `07_Synth_Strings_(treble)`, `08_Synth_Lead`, `09_Arpeggiator` → `auto-render/practice-roma.mp3`
- **alex** партии не назначено — в этой песне **не играет** (подтверждено в памяти practice-mix-players и коммите 2026-06-19). См. [../pipelines/mainstage-rig.md](../pipelines/mainstage-rig.md).

## Cue

16 cue (см. [../pipelines/cue-system.md](../pipelines/cue-system.md)). Стартовый: **«Freed from desire keys in»** (bar 3).

- Секционные входы: `vocal in`, `drums in`, `piano in` (×2), `keep going`, `chorus in` (×3), `solo in` (×2), `verse in`, `break in`, `bridge in`.
- **`chorus in` на bar 98 beat 3** — вход на 3-ю долю (не на 1). Остальные cue на доле 1.
- Две остановки в финале: **`bass stop`** (bar 107) и **`end stop`** (bar 114) → разворачиваются в «… stop in 3» + отсчёт «3 2 1».
- Счётных входов (`count: true`) нет; `cue_step`/`count_in` не заданы.

## История и гочи

- **2026-06-13** — черновик cue (16 позиций) размечен по стилю ручной разметки при оцифровке старых cue-треков (коммит `bd3fbed`). Тогда же введена семантика `bar 1.1 = музыкальный даунбит`.
- **2026-06-18** — новые рендеры (`timeline`) + правки `mix.json`.
- **2026-06-19** — назначены `players`: roma = все синты, alex сидит вне (коммит `265621c`).
- **2026-06-20** — последний рендер (`auto-render/*` от 2026-06-20 14:16); `10-lyric-review.mp4` от 2026-06-22.

## Открытое

- Cue помечены как **черновик** при разметке 2026-06-13 (наравне с Better Off Alone, Heads Will Roll, I Love It, Around the World) — статус финальной сверки cue со стемами по этой песне в истории явно не зафиксирован.
