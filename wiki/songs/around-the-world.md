---
type: song
updated: 2026-07-10
title: Around the World
artist: A Touch of Class
set: "СЕТ 1 #2"
---

# Around the World (La La La La La)

Папка: `/Users/alex/projects/cherry-daddies/music/songs/A Touch of Class - Around the World (La La La La La)/`
Позиция в сетлисте: СЕТ 1, песня #2 (`web/songs.json`).

## Сводка

- **bpm:** 132 (из `auto-render/timeline.json`; в `mix.json` поле `bpm` не задано).
- **Тональность / pitch_semitones:** поле `pitch_semitones` в `mix.json` отсутствует → питч 0 (нативная тональность JamZone).
- **Источник стемов:** JamZone (нумерованные `NN_*.m4a` + `01_Click.m4a`), не Moises. См. [../pipelines/jamzone-render.md](../pipelines/jamzone-render.md).
- **Особые поля mix.json:** нет `cue_step`, `count_in`, `tempo_zone`, `click`, `layers`. Есть `players`, `pb-other`, `pb-bass` (с `gain_db`), один cue со `squeeze: true` и два со `count: true`.

## Плейбек и рендер

Стемы (все `.m4a`, 15 шт., 01–15):
- **pb-bass:** `05_Synth_Bass` с `gain_db: +3`.
- **pb-other:** `14_Backing_Vocals`.
- Остальные стемы играются живьём (см. players) и не разложены по pb-группам.
- **Перкуссия вон из плейбека:** `03_Clap` и `04_Noise_effects` НЕ включены ни в одну pb-группу (правило «перкуссия вон» соблюдено; в плейбек идёт только `02_Electronic_Drum_Kit` — и то через players/живого барабанщика). См. [../pipelines/jamzone-render.md](../pipelines/jamzone-render.md).

`layers` — нет.

**players** (кто играет живьём):
- **roma:** `13_Vibes`, `11_Synth_Lead`, `06_Digital_Piano`, `12_Synth_Keys`, `09_Synth_Strings_(pizzicato)`
- **alex:** `07_Synth_Pad_1`, `08_Synth_Pad_2`, `10_Synth_Strings`
- **steve:** `02_Electronic_Drum_Kit`
- **tanya:** `15_Lead_Vocal`

**practice-миксы** (`auto-render/`): `practice-alex.mp3`, `practice-roma.mp3`, `practice-steve.mp3`, `practice-tanya.mp3` — есть для всех четырёх игроков.

Рендеры в `auto-render/`: `all.wav`, `click.wav`, `cues.wav`, `pb-bass.wav`, `pb-other.wav`, `cue_preview.mp3`, `timeline.json`. Также `02-lyric-review.mp4` (клип ревью лирики, 2026-06-22 — см. [../pipelines/lyric-launcher.md](../pipelines/lyric-launcher.md)).

## Cue

12 cue в `mix.json` (у каждого `abs_sec`). См. [../pipelines/cue-system.md](../pipelines/cue-system.md).

- **Стартовый cue** (bar 3): `Around the World synth in` → «...ready go».
- **Счётные входы** (`count: true`): bar 79 и bar 112 — `keys-only in` → «keys only in 3, 3 2 1».
- **squeeze** (bar 88): `modulation in` со `squeeze: true` (мягкое ужатие фразы в долю).
- **stop** (bar 120): `end stop` → «end stop in 3», отсчёт 3-2-1.
- Прочие обычные `... in`: vocal in (bar 7, 39), bass-n-beat in (bar 15, дефис = одно слово), solo in (bar 31, 71), piano in (bar 47), keep going (bar 104).

Семантика bar 1.1 = музыкальный даунбит (введена коммитом 2026-06-13).

## История и гочи

- **2026-06-13** — cue оцифрованы/размечены: коммит указывает «черновики по стилю ручной разметки: ... Around the World (16)» — то есть черновик был на **16 cue**. Текущий `mix.json` содержит **12 cue** → черновик впоследствии урезан/переработан. ⚠️ расхождение 16 (черновик) vs 12 (текущее) не задокументировано отдельно.
- **2026-06-18** — новые рендеры (timeline) + обновления mix.json.
- **2026-06-19** — players: alex → pad1, pad2, synth strings (коммит `players: A Touch of Class - Around the World -> alex`).
- **2026-06-20** — последний рендер `auto-render/` (все .wav от 14:04).
- В `CLAUDE.md` и agent-памяти отдельных прецедентов по этой песне нет.

## Открытое

- ⚠️ Черновик cue был на 16 позиций, сейчас 12 — причина сокращения не зафиксирована.
- Тональность нигде не выписана явно (pitch 0 = нативный JamZone-ключ); если группа играет в своём ключе — свериться.
