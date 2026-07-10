---
type: song
updated: 2026-07-10
title: Blinding Lights
artist: The Weeknd
set: "СЕТ 1 #8"
---

# Blinding Lights — The Weeknd

Источник стемов — JamZone (стемы `NN_Name.m4a` + `01_Click.m4a`), не Moises. Позиция в сетлисте: СЕТ 1 #8 (сверено с `/Users/alex/projects/cherry-daddies/web/songs.json`, `sid: "The Weeknd - Blinding Lights"`, `slug: ce6a8891a4b7`).

## Сводка

- **bpm:** 171 (доля ≈ 351 мс — быстрый темп; из `mix.json`/`timeline.json`).
- **pitch_semitones:** нет ключа → 0, оригинальная тональность.
- **Особые поля `mix.json`:** `cue_step: 2` (растяжка cue под быстрый темп). Нет `layers`, `players`-live-записей, `count_in`, `tempo_zone`, `click` (обычный fit по `01_Click.m4a`).
- `mix.json`: `/Users/alex/projects/cherry-daddies/music/songs/The Weeknd - Blinding Lights/mix.json`
- Структура (`structure.txt`): Precount · Intro · Verse · Pre chorus · Chorus · Instrumental · Verse 2 · Pre chorus 2 · Chorus 2 · Bridge · Chorus 3 · Instrumental 2 · Chorus 4.

## Плейбек и рендер

Стемы (JamZone, `/Users/alex/projects/cherry-daddies/music/songs/The Weeknd - Blinding Lights/`):

- **pb-other:** `04_Noise_effects`, `09_Synth_Keys`, `10_Arpeggiator`, `11_Synth_Ambiant`, `12_Backing_Vocals`.
- **pb-bass:** `05_Synth_Bass`.
- **Не в плейбеке:** `02_Electronic_Drum_Kit` (живой барабанщик), `03_Electronic_Percussion` (перкуссия — всегда вон из плейбека, правило соблюдено — её нет ни в одной группе), `06_Synthesizer`, `07_Synth_Pad_1`, `08_Synth_Pad_2` (живые синты Ромы), `13_Lead_Vocal` (живой вокал Тани), `01_Click`.
- **layers:** нет (живые партии играются вживую, не записаны в плейбек).

Рендеры (`auto-render/`): `all.wav`, `click.wav`, `cues.wav`, `pb-bass.wav`, `pb-other.wav`, `cue_preview.mp3`, `timeline.json`. Плюс `08-lyric-review.mp4` (клип ревью лирики).

**players** (`mix.json`, кто играет вживую):

- **steve** → `02_Electronic_Drum_Kit` → `practice-steve.mp3`
- **tanya** → `13_Lead_Vocal` → `practice-tanya.mp3`
- **roma** → `06_Synthesizer`, `07_Synth_Pad_1`, `08_Synth_Pad_2` → `practice-roma.mp3`
- Alex в этой песне НЕ играет (коммит 2026-06-19: «Alex sits out Blinding/Gala»).

Practice-миксы: `practice-steve.mp3`, `practice-roma.mp3`, `practice-tanya.mp3` (см. [pipelines/jamzone-render.md](../pipelines/jamzone-render.md)).

## Cue

8 cue (`mix.json`), с абсолютными секундами `abs_sec`:

| bar.beat | текст | abs_sec |
|---|---|---|
| 3 | Blinding Lights synth in ready go (`step: 1`) | 2.807 |
| 11 | drums in | 14.035 |
| 15.2 | melody in | 20.0 |
| 22 | verse in | 29.474 |
| 63 | keys in | 87.018 |
| 70.3 | verse in | 97.544 |
| 119 | keys in | 165.614 |
| 135 | drums stop | 188.07 |

Особенности:

- **`cue_step: 2`** на уровне песни — быстрый темп (171 bpm): каждое размеренное слово блока занимает 2 доли (≈700 мс), `go` за 2 доли до события, блок «{x} in ready go» = 8 долей (2 такта). См. [pipelines/cue-system.md](../pipelines/cue-system.md).
- **Стартовый cue (bar 3) переопределён `step: 1`** — идёт в естественном темпе (название песни не ужимается). При `cue_step: 2` длинный стартовый блок обычно перестаёт влезать спереди → рендер может добавить count-in такт; структура начинается с «Precount».
- `drums stop` (bar 135) → развернётся в «drums stop in 3» + отсчёт «3 2 1».
- Нет счётных входов (`count`), нет `tempo_zone`.

## История и гочи

- **2026-06-18** — новые рендеры (timeline) + обновления `mix.json` + новые песни/layers (пакетный коммит).
- **2026-06-19** — проставлены `players`: Blinding — roma играет синты; Alex сидит вне песни.
- **2026-06-20** — последний перерендер (`auto-render/*` от 20 июня); в этом же коммите — пакетный players-проход и правки других песен.
- Blinding Lights — эталонный пример `cue_step` в `CLAUDE.md` (быстрая песня 171 bpm).

## Открытое

- Нет зафиксированных TODO по песне.
