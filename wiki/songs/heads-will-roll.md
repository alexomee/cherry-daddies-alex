---
type: song
updated: 2026-07-10
title: Heads Will Roll
artist: Yeah Yeah Yeahs
set: СЕТ 2 #10
---

# Heads Will Roll — Yeah Yeah Yeahs

Папка: `/Users/alex/projects/cherry-daddies/music/songs/Yeah Yeah Yeahs - Heads Will Roll/`
Позиция: **СЕТ 2, #10** (сверено с `/Users/alex/projects/cherry-daddies/web/songs.json`).

## Сводка

- Источник — **JamZone** (нумерованные стемы `NN_*.m4a`, `01_Click.m4a`, легаси `cue_track.wav`/`cues.json`), не Moises. См. [jamzone-render](../pipelines/jamzone-render.md).
- `mix.json` (`.../Yeah Yeah Yeahs - Heads Will Roll/mix.json`): `bpm`, `pitch_semitones`, `cue_step`, `count_in`, `tempo_zone`, `click` — **всех этих полей нет**. bpm/сетка выводятся `fit_grid` из `01_Click.m4a`; питча нет (играется в оригинальной тональности).
- Есть только: `pb-other`, `pb-bass`, `players`, `cues` (16).

## Плейбек и рендер

- **pb-other**: `04_Noise_effects`.
- **pb-bass**: `05_Bass`.
- **Перкуссия вон**: `03_Percussion` есть в папке, но **не входит** ни в одну группу — корректно (её играет живой барабанщик, см. [percussion out of playback](../pipelines/jamzone-render.md)). В плейбек идёт только `02_Drum_Kit`.
- `layers` — нет.
- **players** (кто играет живьём):
  - `steve` → `02_Drum_Kit`
  - `tanya` → `13_Lead_Vocal`
  - `alex` → `06_Electric_Guitar`, `07_Distorted_Electric_Guitar`, `08_Electric_Guitar_(delay)` (3 гитары)
  - `roma` → `09_Synthesizer_(disto)`, `10_Synth_Pad`, `11_Synth_Strings`
- **practice-миксы** (все собраны): `auto-render/practice-{alex,roma,steve,tanya}.mp3` (2026-06-20). См. [practice-mix](../pipelines/jamzone-render.md).
- `auto-render/` содержит полный пакет: `all.wav`, `click.wav`, `cues.wav`, `pb-bass.wav`, `pb-other.wav`, `cue_preview.mp3`, `timeline.json` + `21-lyric-review.mp4` (2026-06-22).

## Cue

- **16 cue**, разметка вручную (не счётные входы, `count` нигде не стоит; `cue_step`/`count_in` нет). См. [cue-system](../pipelines/cue-system.md).
- Стартовый: bar 3 «Heads will roll synth in».
- Входы `... in` → «... ready go»; несколько cue заданы явным текстом: bar 75 «guitar break ready go», bar 109 «guitar solo ready go», bar 117 «drums only ready go».
- Стоп: bar 123 «end stop» → объявление «end stop in 3» + отсчёт 3-2-1.
- Секционные входы на не-первую долю: bar 20.4 «bass in», bar 50.4 «vocal in», bar 100.3 «vocal in».
- Секции песни — `structure.txt` (Precount / Intro / Chorus / Verse ×3 / Pre chorus / Bridge / Instrumental ×2 / Outro).

## История и гочи

- **2026-06-13** — cue (16) добавлены как **черновик по стилю ручной разметки** (в одном коммите с Better Off Alone / I Love It / Around the World / Freed from Desire). В отличие от Infinity 2008 / NYG / Я устал / We Found Love — **НЕ** оцифрованы/сверены транскрипцией со старого cue-трека, а размечены вручную. Тем же коммитом введена семантика `bar 1.1 = музыкальный даунбит`, cue-сетка считается от OFF+db0.
- **2026-06-18** — новые рендеры (timeline) + обновления mix.json.
- **2026-06-19** — финализирован `players` для SET 2: alex = 3 гитары, roma = остальное.
- **2026-06-20** — общий проход players по mix.json; собраны practice-миксы (`auto-render/practice-*.mp3`).
- Легаси `cue_track.wav` / `cues.json` в папке — старый Logic-бонс, оставлен как фоллбек; в глоб стемов external/JamZone-рендера не попадает.
- Упоминаний песни в `CLAUDE.md` и agent-памяти нет.

## Открытое

- Cue — **черновые, не сверены со стемами/старым треком**. Нужен проход прослушивания `auto-render/cue_preview.mp3` и сверка позиций с онсетами стемов (по правилам [cue-system](../pipelines/cue-system.md)); тексты формулировок ещё может править группа.
