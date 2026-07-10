---
type: song
updated: 2026-07-10
title: S&M
artist: Rihanna
set: СЕТ 2 #6
---

# S&M — Rihanna

Позиция: СЕТ 2 #6 (сверено с `web/songs.json`, `sid: "Rihanna - S&M"`, slug `3101b8a72732`).
Папка: `/Users/alex/projects/cherry-daddies/music/songs/Rihanna - S&M/`.

## Сводка

- **Источник:** JamZone (нумерованные стемы `NN_Name.m4a`, `01_Click.m4a` даёт сетку). Не Moises. См. [jamzone-render](../pipelines/jamzone-render.md).
- **bpm:** 128.0 (в `mix.json` не задан — берётся из клика; `auto-render/timeline.json`: `bpm 128.0`, `bar_sec 1.875`, `offset_sec 1.578021`).
- **pitch_semitones:** −2 (минус питчится в ключ группы).
- Особых полей нет: `cue_step`, `count_in`, `tempo_zone`, `click:"follow"` отсутствуют — прямая ровная сетка.

## Плейбек и рендер

Стемы в папке: `01_Click`, `02_Electronic_Drum_Kit`, `03_Clap`, `04_Electric_Bass`, `05_Synth_Bass`, `06_Synthesizer`, `07_Synth_Lead`, `08_Synth_Keys`, `09_Arpeggiator`, `10_Noise_effects`, `11_Backing_Vocals_1`, `12_Backing_Vocals_2`, `13_Lead_Vocal` (все `.m4a`).

- **pb-other:** `06_Synthesizer`, `11_Backing_Vocals_1`, `12_Backing_Vocals_2`.
- **pb-bass:** `04_Electric_Bass` (`gain_db` +2).
- **Вне плейбека:** `03_Clap` (перкуссия — играет живой барабанщик, см. правило percussion-out-of-playback), `10_Noise_effects`, `05_Synth_Bass`, `07/08/09` (лид/кис/арп — живьём). `13_Lead_Vocal` — живой вокал Тани.
- **layers:** нет.
- **Рендеры** (`auto-render/`, от 2026-06-25): `all.wav`, `click.wav`, `cues.wav`, `pb-other.wav`, `pb-bass.wav`, `cue_preview.mp3`, `timeline.json`. Плюс `17-lyric-review.mp4` (2026-06-22).

### players / practice-миксы

`players`: `roma` → `07_Synth_Lead`, `09_Arpeggiator`, `08_Synth_Keys`; `steve` → `02_Electronic_Drum_Kit`; `tanya` → `13_Lead_Vocal`; `alex` → `04_Electric_Bass`, `05_Synth_Bass` (оба баса, назначено 2026-06-19).

Practice-миксы присутствуют все: `practice-alex.mp3`, `practice-roma.mp3`, `practice-steve.mp3`, `practice-tanya.mp3`. См. [practice-микс](../pipelines/jamzone-render.md).

## Cue

13 cue (`mix.json`), см. [cue-система](../pipelines/cue-system.md):

- Старт: bar 2 beat 3 — `"S and M vocal in"` со стартовым тоном `chord: ["C#4"]`.
- `all in` (11), `verse in` (19), `chorus in` (35), `bass in` (43), `verse in` (59), `soft chorus` (67), `synth in` (83), `bridge in` (87), `soft chorus` (99), `all in` (107), `outro in` (123).
- Финал: bar 130 `"end in"` с `count: true` (счётный конец «end in 3, 3 2 1»).
- Без `cue_step`/`count_in`/`tempo_zone`.

Секции трека (`structure.txt`): Precount · Intro · Verse · Chorus · Chorus 2 · Verse 2 · Chorus 3 · Chorus 4 · Bridge · Chorus 5 · Chorus 6 · Outro.

## История и гочи

- **2026-06-11/12** — разметка cue (13 позиций), стартовый cue = title + «что вступает» + ready go, счётный конец «end in 3».
- **2026-06-12** — «S&M pb-other = два бек-вокала»; плейбек песни = click + cues; пересобран на ровную сетку 128.0000 (±0.4мс, без каунт-ина, t=0 = первый даунбит).
- **2026-06-18** — общий проход: новые рендеры (timeline) + правки mix.json.
- **2026-06-19** — `players`: alex посажен на оба баса (electric + synth).
- **Гоча (pitch −2):** песня питченая → rubberband недетерминирован между рендерами; при cue-only правке `click/pb-other/pb-bass` в `sync_to_mainstage.sh` покажутся «changed» из-за пайплайн-дрейфа, хотя клик-сетка идентична — тогда катить только `cues.wav` (см. память sync-cue-only-scope; [mainstage-rig](../pipelines/mainstage-rig.md)).
- **Синты Alex/Roma** нигде явно не расписаны кроме `players` этой песни — здесь синты (лид/арп/кис) закреплены за Roma, оба баса за Alex.
- **Lyric-launcher:** особый кейс схлопывания «S S S M M M» → «S&M» реализован (см. память lyric-launcher; [lyric-launcher](../pipelines/lyric-launcher.md)).

## Открытое

- Расхождение: git-заметка 2026-06-12 «pb-other = два бек-вокала», но текущий `mix.json` держит в pb-other ещё и `06_Synthesizer` (три элемента). Похоже добавлено позже — не критично, но не датировано в истории.
