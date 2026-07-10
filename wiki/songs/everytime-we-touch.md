---
type: song
updated: 2026-07-10
title: Everytime We Touch
artist: Cascada
set: СЕТ 2 #9
---

# Everytime We Touch — Cascada

Позиция: **СЕТ 2, #9** (`web/songs.json`, slug `cadd346666dc`).
Источник — **JamZone** (нумерованные стемы `NN_Name.m4a`, есть `01_Click.m4a`), не Moises.

## Сводка

- **bpm 142.0** (из `auto-render/timeline.json`; в `mix.json` поля `bpm` нет — темп берётся из `01_Click.m4a` через `fit_grid`).
- **pitch_semitones нет** — JamZone-стемы уже в тональности группы, питч не нужен (см. [moises-import](../pipelines/moises-import.md) про питч внешних песен).
- **bar_sec 1.690**, offset_sec -0.297 (`timeline.json`).
- Особых полей нет: `cue_step`, `count_in`, `tempo_zone`, `click` в `mix.json` отсутствуют.
- Структура (`structure.txt`): Precount / Verse / Chorus / Break / Instrumental / Verse 2 / Chorus 2 / Instrumental 2 / Chorus 3.

Файлы: `music/songs/Cascada - Everytime We Touch/mix.json`, `.../structure.txt`, `.../auto-render/timeline.json`.

## Плейбек и рендер

Стемы в папке `music/songs/Cascada - Everytime We Touch/` (14 стемов JamZone + click).

- **pb-other** (6 стемов): `03_Sound_effects_(Crowd)`, `13_Backing_Vocals`, `04_Noise_effects`, `08_Synth_Voice`, `07_Synth_Pad`, `11_Synth_Ambiant`.
  - **mute**: `13_Backing_Vocals` заглушены в диапазоне `[1, 18.2]` (интро до вступления бэков).
- **pb-bass**: `null` (баса в плейбеке нет — бас играет живой, `05_Synth_Bass`/`06_Synth_Bass_(crunch)` не в миксе).
- **layers / parts**: нет (`parts/` отсутствует).
- Перкуссии-стемов нет — вопрос чистки перкуссии не стоит (см. [jamzone-render](../pipelines/jamzone-render.md)).

**players** (кто играет живьём) → practice-миксы в `auto-render/`:

- `steve` → `02_Electronic_Drum_Kit` → `practice-steve.mp3`
- `tanya` → `14_Lead_Vocal` → `practice-tanya.mp3`
- `alex` → `09_Synth_Lead` → `practice-alex.mp3`
- `roma` → `10_Synth_Keys_(Bells)`, `12_Bells` → `practice-roma.mp3`

Рендеры: `all.wav`, `click.wav`, `cues.wav`, `pb-other.wav`, `cue_preview.mp3`, 4×`practice-*.mp3`, `timeline.json`, плюс `20-lyric-review.mp4` (клип ревью текста лаунчера).

## Cue

**13 cue** (`ready: true` в `songs.json`). Разрешение по долям (несколько на beat 3/4). См. [cue-system](../pipelines/cue-system.md).

Особенности:

- `bar 59.4 "vocal ready go"` помечен `"raw": true` — текст берётся дословно, без разворота в «ready go» (стоит сразу после стопа bar 59, чтобы не сталкивался с ним).
- `bar 91.3 "solo in"`, `99.3 "keep going"`, `107.3 "vocal in"` — на долю 3.
- Счётных входов (`count`), `cue_step`, `count_in`, `tempo_zone` — нет. Cue-заголовок влезает спереди без лишнего count-in такта (проверено при снижении порога lead-такта, коммит 2026-06-13).

## История и гочи

- **2026-06-11** — cue Cascada делались вручную в Logic (автоген удалён): «Борд: cue Cascada/Basshunter/WFL/Infinity ручные в Logic, автоген удалён».
- **2026-06-13** — оцифровка старых cue-треков в `mix.json`; pb-other собран из 6 стемов, убран дубль; при снижении порога lead-такта Cascada перестала получать лишний пустой count-in такт (cue и так влезает).
- **2026-06-18** — pb-other авто-левелинг: back-vox **-2 dB** (auto-level fx/back-vox под per-role loudness target, см. [jamzone-render](../pipelines/jamzone-render.md)).
- **2026-06-19** — назначены players (SET 2): `alex` = lead (`09_Synth_Lead`).
- **2026-06-21** — добавлен cue `vocal ready go` на bar 59.4 (после стопа bar 59); последний ре-рендер.
- Память [pb-other-loudness-ceiling](../pipelines/mainstage-rig.md): Cascada в списке «богатых многослойных миксов ниже потолка → ноль изменений от ceiling».

## Открытое

- Нет открытых TODO по песне.
