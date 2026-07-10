---
type: song
updated: 2026-07-10
title: Whenever, Wherever
artist: Shakira
set: СЕТ 1 #3
---

# Shakira — Whenever, Wherever

Папка: `/Users/alex/projects/cherry-daddies/music/songs/Shakira - Whenever, Wherever/`

## Сводка

- **Источник:** JamZone (нумерованные стемы `01_Click.m4a` … `14_Lead_Vocal.m4a`), см. [../pipelines/jamzone-render.md](../pipelines/jamzone-render.md).
- **bpm:** в `mix.json` не задан; из рендера (`auto-render/timeline.json`) — **≈109** (108.9984), длина такта 2.2019с, offset 1.901с.
- **pitch_semitones:** отсутствует → **0** (оригинальная тональность, без питча).
- **click:** `"follow"` — клик/cue-сетка строится с переменным темпом, фаза перезахватывается по онсетам метронома (см. [../pipelines/cue-system.md](../pipelines/cue-system.md)).
- **Особых полей нет:** `cue_step`, `count_in`, `tempo_zone`, `layers` — отсутствуют.
- Структура (`structure.txt`): Precount · Intro · Verse · Pre chorus · Chorus · Instrumental · Verse 2 · Pre chorus 2 · Chorus 2 · Instrumental 2 · Bridge · Chorus 3 · Outro.

## Плейбек и рендер

Группы (`mix.json`):
- **pb-bass:** `04_Bass`.
- **pb-other:** `13_Female_Backing_Vocals`, `08_Charango_(left)`, `09_Charango_(right)`.
- **Перкуссия вон из плейбека:** стем `03_Percussion.m4a` есть в папке, но НЕ в одной из групп — корректно выкинут (живой барабанщик), см. правило в [../pipelines/jamzone-render.md](../pipelines/jamzone-render.md). В плейбеке из ударных только `02_Drum_Kit` (через players/клик).
- В плейбек не идут: `11_Pan_Flute`, `12_Backing_Vocals`, `14_Lead_Vocal`, `10_Synth_Pad`, гитары — это живые партии (players) либо вокал.
- **layers:** нет.

**players** (кто играет живьём) → practice-миксы в `auto-render/`:
- `roma` → `10_Synth_Pad` (`practice-roma.mp3`)
- `steve` → `02_Drum_Kit` (`practice-steve.mp3`)
- `tanya` → `14_Lead_Vocal` (`practice-tanya.mp3`)
- `alex` → `05_Rhythm_Electric_Guitar`, `06_Distorted_Electric_Guitar_(left)`, `07_Distorted_Electric_Guitar_(right)` (`practice-alex.mp3`)

Рендеры в `music/songs/Shakira - Whenever, Wherever/auto-render/`: `all.wav`, `click.wav`, `cues.wav`, `pb-bass.wav`, `pb-other.wav`, `cue_preview.mp3`, четыре practice-микса, `timeline.json`. Есть `all_marked.wav` (маркированный), `03-lyric-review.mp4` и `lyrics-ctrl.mid` — материалы lyric-launcher (клип №3), см. [../pipelines/lyric-launcher.md](../pipelines/lyric-launcher.md).

## Cue

**12 cue** (`mix.json`), все с `abs_sec`; счётных входов/стопов с `"count"` нет — обычные `in`/`stop`:

| bar | текст |
|-----|-------|
| 2  | Shakira guitar in ready go (стартовый) |
| 5  | all in ready go |
| 9  | verse in |
| 20 | stop |
| 29 | flute in |
| 34 | verse in |
| 45 | stop |
| 58 | bridge in |
| 66 | stop |
| 67 | all in ready go |
| 78 | keep going |
| 86 | end stop |

`cue_step`/`count_in` не заданы (темп ~109 — слово-на-долю разборчиво). Развёртка `in`/`stop` — по общим правилам ([../pipelines/cue-system.md](../pipelines/cue-system.md)).

## История и гочи

- **2026-06-18** — новые рендеры (timeline), обновления `mix.json`, новые песни и layers (пакетный коммит).
- **2026-06-19** — проставлены players: Shakira → `alex` = 3 электрогитары (`05`/`06`/`07`).
- **2026-06-20** — пакетный проход players по остальным `mix.json`; финальные practice-миксы (файлы в `auto-render/` от 2026-06-20 14:28).
- **pb-other loudness ceiling** (память): Shakira — один из «богатых» многоэлементных миксов, уже НИЖЕ потолка → аттенюатор pb-other его не трогает (0 изменений).
- **lyric-launcher** (память `wire-concert-preserves-layer-fix`): фигурирует шаблон `whenever.patch` strip в MainStage-риге — наивный ре-wire мог откатить ручной фикс клавишника; см. [../pipelines/mainstage-rig.md](../pipelines/mainstage-rig.md).

## Открытое

- `bpm` в `mix.json` не прописан (берётся из клика JamZone). При переносе/сверке ориентир — `timeline.json` (≈109).
- `click: "follow"` задан без явного `tempo_zone` — реальной смены темпа в песне не отмечено; флаг, вероятно, для точной фазировки клика по метроному JamZone. Не подтверждено, что в песне есть темповая зона.
