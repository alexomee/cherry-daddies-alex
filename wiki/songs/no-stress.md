---
type: song
updated: 2026-07-10
title: No Stress
artist: Laurent Wolf & Eric Carter
set: СЕТ 1 #9
---

# No Stress

Позиция: **СЕТ 1 #9** (сверено с `/Users/alex/projects/cherry-daddies/web/songs.json`, slug `39c9137c546c`).
Папка: `/Users/alex/projects/cherry-daddies/music/songs/Laurent Wolf & Eric Carter - No Stress/`.

## Сводка

- **bpm 130** (`timeline.json`: `bar_sec 1.846154`, `offset_sec 1.549152`).
- **pitch_semitones — нет** в `mix.json`. Это JamZone-песня (стемы `01_Click`..`07_Lead_Vocal`), уже в тональности группы, питч не применяется. См. [jamzone-render](../pipelines/jamzone-render.md).
- Особые поля `mix.json`: `"note": "live bass"` (басовая партия живая, `pb-bass: null`).
- Структура (`structure.txt`): Precount → Verse → Pre chorus → Chorus → Instrumental → Bridge → Verse 2 → Pre chorus 2 → Chorus 2 → Outro.

## Плейбек и рендер

Стемы (JamZone, `.m4a`): `01_Click`, `02_Electronic_Drum_Kit`, `03_Synth_Bass`, `04_Piano`, `05_Synthesizer`, `06_Synth_Ambiant`, `07_Lead_Vocal`.

- **pb-other**: `06_Synth_Ambiant` с `gain_db -12`.
- **pb-bass**: `null` — бас играет Alex живьём (`note: "live bass"`).
- **layers**: нет. **parts/**: нет.
- Рендеры в `.../auto-render/`: `all.wav`, `click.wav`, `cues.wav`, `pb-other.wav`, `cue_preview.mp3`, `timeline.json`, плюс `09-lyric-review.mp4`.

**players** (кто играет живьём):
- `steve` → `02_Electronic_Drum_Kit`
- `tanya` → `07_Lead_Vocal`
- `alex` → `03_Synth_Bass` (живой бас)
- `roma` → `04_Piano`, `05_Synthesizer`

**practice-миксы** (все 4): `practice-alex.mp3`, `practice-roma.mp3`, `practice-steve.mp3`, `practice-tanya.mp3` — каждый = микс минус свои партии + клик + cue. См. [практика-миксы в jamzone-render](../pipelines/jamzone-render.md). Синты живьём делят Alex/Roma (в этой песне Roma: piano+synth); бас = Alex (нетипично, обычно бас Roma).

## Cue

8 cue (`ready: true`). См. [cue-система](../pipelines/cue-system.md).

| bar | текст | abs_sec |
|-----|-------|---------|
| 3   | No Stress vocal in | 5.538 |
| 11  | beat in | 20.308 |
| 29  | main in | 53.538 |
| 33  | synth in | 60.923 |
| 53  | verse piano in | 97.846 |
| 57  | vocal in | 105.231 |
| 85  | main in | 156.923 |
| 109 | end in (`count: true`) | 201.231 |

Особенности:
- Первый cue несёт `"chord": ["A#4"]` — тональный тон в ухо вокалисту за такт до входа (как в S&M). Рендер фронт-падит count-in такт под этот тон, `abs_sec` пересчитаны.
- `end in` со `"count": true` → счётный конец «end in 3, 3 2 1».
- `cue_step`, `count_in` (в mix.json), `tempo_zone`, `click` — не заданы.

## История и гочи

- **2026-06-16** (`bbb29aa`): добавлен A4-тон в ухо вокалисту на первый cue — «measured first sung note (441Hz)», мягкий синт-тон за такт до блока, только в cue-треке (тональность группы, без питча), фронт-пад count-in такта.
- **2026-06-18**: новые рендеры (timeline) + правки mix.json.
- **2026-06-19** (`b826a9b`, `265621c`): players назначены — Alex на бас (исключён из его practice-микса), Roma piano+synth. Alex на басу в No Stress/Solnyshko/Beverly Hills — нетипично (обычно бас у Roma).
- **2026-06-11** (`57985b3`-эпоха): общая cue-конвенция — вокальный/verse-вход = «ready go», инструментал = «3 2 1».

## Открытое

- ⚠️ **Тональный тон: A#4 vs A4.** `mix.json` первого cue содержит `"chord": ["A#4"]`, а коммит `bbb29aa` и его сообщение говорят A4 / 441 Гц (A440 = A4; A#4 ≈ 466 Гц). Расхождение на полутон между записанным chord и заявленным намерением — уточнить, какой тон реально нужен вокалисту.
