---
type: song
updated: 2026-10-26
title: Кислотный DJ
artist: Акула
set: 28.10 Music Hall SET 2 #1
---

# Кислотный DJ — Акула

Открывашка СЕТ 2 программы 28.10 Music Hall (клип №63 в `lyric-launcher`). Moises-стемы (140.0 BPM, оригинальная тональность `pitch_semitones: 0`), 20 cue. 2026-10-26: в `pb-other` подключён пользовательский синт-арпеджиатор `parts/DJ_arp.wav` (`frame: "render"`, `role: "musical"`, `gain_db: +3.5`) на уровень medium-to-high коридора громкости `pb-other` (−21.52 dBFS gated RMS / −16.1 LUFS, пик −3.21 dBFS).

## Сводка

- **bpm:** 140.0 · **pitch_semitones:** 0
- Источник: Moises-стемы (`bass.wav`, `drums.wav`, `guitars.wav`, `keys.wav`, `metronome.wav`, `other.wav`, `strings.wav`, `vocals.wav`, `wind.wav`, `backing_vocals.wav`), константный клик (540 ударов, `max resid 28.9 мс`).
- `mix.json`: `music/songs/Кислотный DJ/mix.json`

## Плейбек и рендер

- **pb-other:** layer `DJ_arp` (`parts/DJ_arp.wav`, `frame: "render"`, `role: "musical"`, `"gain_db": 3.5`). Пульсирующий 16-ми арпеджиатор звучит в трёх блоках: такты 41–72 (`72.54–127.20 с`, Chorus 1 + Solo 1), такты 86–117 (`149.69–203.88 с`, Build-up / Chorus 2 + Solo 2) и такты 127–135 (`219.97–233.55 с`, финальный блок `all in` до `end in`). Исходный уровень слоя: −25.02 dBFS gated RMS (−22.49 dBFS stereo gated RMS, −19.6 LUFS, пик −6.71 dBFS); после `+3.5 dB` итоговый `pb-other.wav` — **−21.52 dBFS gated RMS** (−18.99 dBFS stereo gated RMS, −16.1 LUFS, пик −3.21 dBFS).
- **pb-bass:** `null` (Alex играет бас живьём).
- **pb-drums:** `drums` (`gain_db: -4.5` → −16.56 dBFS gated RMS).
- **players:** `alex` = guitars, bass; `roma` = keys, strings, wind; `steve` = drums; `tanya` = vocals; `trio` = guitars, drums, vocals, bass.
- Сетка: beat 0.4286 с, такт 1.7143 с, downbeat стема 0.6301 с, `OFF = +2.79846 с` (+1 такт lead), `bar 1.1 = 3.429 с`, полная длина `236.571 с` (138 тактов).

## Cue (20 подсказок)

- `bar 1.1` (3.429 с) — «Кислотный DJ · drums in ready go»
- `bar 8.4` (16.714 с) — «synth in ready go»
- `bar 16.1` (29.143 с) — «stop in 3 · 3 2 1»
- `bar 24.1` (42.857 с) — «drums break ready go»
- `bar 32.1` (56.571 с) — «drums-bass break ready go»
- `bar 38.1` (66.857 с) — «synth in ready go»
- `bar 39.1` (68.571 с) — «build up ready go»
- `bar 41.1` (72.000 с) — «chorus in ready go»
- `bar 56.1` (97.714 с) — «drums-bass break ready go»
- `bar 64.1` (111.429 с) — «bass break ready go»
- `bar 65.1` (113.143 с) — «solo in ready go»
- `bar 72.1` (125.143 с) — «drum break ready go»
- `bar 81.1` (140.571 с) — «long break ready go»
- `bar 85.1` (147.429 с) — «build up ready go»
- `bar 101.1` (174.857 с) — «stop in 3 · 3 2 1»
- `bar 102.1` (176.571 с) — «solo in ready go»
- `bar 117.1` (202.286 с) — «drums bass stop in 3 · 3 2 1»
- `bar 124.1` (214.286 с) — «build up ready go»
- `bar 127.1` (219.429 с) — «all in ready go»
- `bar 135.1` (233.143 с) — «end in 3 · 3 2 1» (`count: true`)

## Риг (MainStage)

Папка сетлиста: `cherry-daddies-2000/cherry-daddies-setlist-2026-06-16/Кислотный DJ/` (`click.wav`, `cues.wav`, `pb-drums.wav`, `pb-other.wav`). В патче `Akula.patch` (`28_10_2.concert` / `2000_1.concert`) новый стем `pb-other.wav` подключается в Playback-плагин вручную в MainStage.
