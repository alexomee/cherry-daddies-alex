---
type: song
updated: 2026-07-10
title: Uptown Funk
artist: Bruno Mars & Mark Ronson
set: "СЕТ 1 #11"
---

# Uptown Funk — Bruno Mars & Mark Ronson

Источник стемов — JamZone (стемы `NN_Name.m4a` + `01_Click.m4a`), не Moises. Позиция в сетлисте: СЕТ 1 #11 (последняя в сете; сверено с `/Users/alex/projects/cherry-daddies/web/songs.json`).

## Сводка

- **bpm:** 115 (доля ≈ 522 мс; в `mix.json` ключа нет — берётся fit'ом из `01_Click.m4a`, значение из `auto-render/timeline.json`).
- **pitch_semitones:** нет ключа → 0, оригинальная тональность.
- **Особые поля `mix.json`:** нет `layers`, `cue_step`, `count_in`, `tempo_zone`, `click` (обычный fit по `01_Click.m4a`). `pb-bass: null` (бас не в плейбеке — играется вживую).
- `mix.json`: `/Users/alex/projects/cherry-daddies/music/songs/Bruno Mars & Mark Ronson - Uptown Funk/mix.json`
- Структура (`structure.txt`): Precount · Intro · Verse · Pre chorus · Chorus · Verse 2 · Pre chorus 2 · Chorus 2 · Bridge · Chorus 3 · Outro.

## Плейбек и рендер

Стемы (JamZone, `/Users/alex/projects/cherry-daddies/music/songs/Bruno Mars & Mark Ronson - Uptown Funk/`):

- **pb-other:** `06_Organ`, `07_Synth_Pad`, `08_Brass_section`, `09_Noise_effects`, `10_Backing_Vocals`.
- **pb-bass:** `null` — бас (`04_Bass`) вживую, в плейбек не идёт.
- **Не в плейбеке:** `02_Drum_Kit` (живой барабанщик Стив), `03_Percussion` (перкуссия — всегда вон из плейбека, правило соблюдено — её нет ни в одной группе), `04_Bass` (живой бас), `05_Electric_Guitar` (живая гитара Алекса), `11_Lead_Vocal` (живой вокал Тани), `01_Click`.
- **layers:** нет.

Рендеры (`auto-render/`): `all.wav`, `click.wav`, `cues.wav`, `pb-other.wav`, `cue_preview.mp3`, `timeline.json`. Плюс `11-lyric-review.mp4` (клип ревью лирики для lyric-launcher, см. [pipelines/lyric-launcher.md](../pipelines/lyric-launcher.md)). Нет `pb-bass.wav` (бас вживую).

**players** (`mix.json`, кто играет вживую):

- **steve** → `02_Drum_Kit` → `practice-steve.mp3`
- **tanya** → `11_Lead_Vocal` → `practice-tanya.mp3`
- **alex** → `05_Electric_Guitar` → `practice-alex.mp3`

Practice-миксы: `practice-alex.mp3`, `practice-steve.mp3`, `practice-tanya.mp3` (см. [pipelines/jamzone-render.md](../pipelines/jamzone-render.md)).

## Cue

19 cue (`mix.json`), с абсолютными секундами `abs_sec`:

| bar.beat | текст | abs_sec |
|---|---|---|
| 2 | Uptown Funk all in ready go | 4.174 |
| 6 | guitar in | 12.522 |
| 10 | verse in | 20.87 |
| 18 | bass in | 37.565 |
| 33 | stop | 68.87 |
| 35.3 | haa | 74.087 |
| 39.3 | haa | 82.435 |
| 46 | stop | 96.0 |
| 53.4 | bass in | 112.174 |
| 62 | kick-vocal only ready go | 129.391 |
| 69 | stop | 144.0 |
| 71.3 | haa | 149.217 |
| 75.3 | haa | 157.565 |
| 82 | bridge in | 171.13 |
| 94 | guitar in | 196.174 |
| 103.4 | haa | 216.522 |
| 107.3 | haa | 224.348 |
| 114 | outro in | 237.913 |
| 129.4 | stop | 270.783 |

Особенности:

- Стартовый cue (bar 2) = название + «all in ready go» (по правилу стартового cue).
- Много `stop` (bars 33, 46, 69, 129.4) → развернутся в «{x} stop in 3» + отсчёт «3 2 1». `kick-vocal only ready go` (bar 62) — вход в редукцию.
- `haa` — короткие хиты/выкрики на beat 3–4 (брейки), 6 штук.
- `kick-vocal only` — дефис = одно слово (по правилу cue-развёртки).
- Нет `cue_step`, `count_in`, счётных входов (`count`), `tempo_zone`. См. [pipelines/cue-system.md](../pipelines/cue-system.md).
- В папке лежат исходники прошлой cue-версии: `cue_track.wav` + `cues.json` (старый Logic-бонс, count_style `readygo`; тексты отличаются от текущих — были оцифрованы/переработаны).

## История и гочи

- **2026-06-18** — новые рендеры (timeline) + обновления `mix.json` + новые песни/layers (пакетный коммит; Uptown в числе новых JamZone-песен).
- **2026-06-19** — проставлены `players` для 7 песен, включая Uptown (steve/tanya/alex).
- **2026-06-20** — последний перерендер (`auto-render/*` и `mix.json` от 20 июня); пакетный коммит «Мелом + t.A.T.u. cleanup».
- **Мультикам концерта** (память `multicam-concert-pipeline.md`): записан operator-OFF `UPTOWN 2664.19` в IMG_2689 (Set 1). Uptown — последняя песня, попадающая под оператора в сете. См. [pipelines/multicam-concert.md](../pipelines/multicam-concert.md).

## Открытое

- Нет зафиксированных TODO по песне.
