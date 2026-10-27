---
type: song
updated: 2026-10-27
title: Кислотный DJ
artist: Акула
set: 28.10 Music Hall SET 2 #1
---

# Кислотный DJ — Акула

Открывашка СЕТ 2 программы 28.10 Music Hall (клип №63 в `lyric-launcher`). Moises-стемы (140.0 BPM, оригинальная тональность `pitch_semitones: 0`), 22 cue. 2026-10-26: в `pb-other` подключён пользовательский синт-арпеджиатор `parts/DJ_arp.wav` (`frame: "render"`, `role: "musical"`, `gain_db: +3.5`) на уровень medium-to-high коридора громкости `pb-other` (−21.52 dBFS gated RMS / −16.1 LUFS, пик −3.21 dBFS). 2026-10-27: добавлены 2 подсказки — `all in ready go` на вход 2-го припева (`bar 86.1` / `2:29.14`) и `stop in 3 · 3 2 1` на последний удар барабанов перед финальным припевом (`bar 126.1` / `3:37.71`); в `pb-other` добавлен второй слой `parts/wind_part.wav` (`frame: "render"`, `role: "musical"`, `gain_db: -8.0` → `−27.05 dBFS` gated RMS / `−23.0 LUFS`, ниже арпеджиатора; суммарный `pb-other.wav` — `−21.19 dBFS` gated RMS, пик `−2.36 dBFS`).

## Сводка

- **bpm:** 140.0 · **pitch_semitones:** 0
- Источник: Moises-стемы (`bass.wav`, `drums.wav`, `guitars.wav`, `keys.wav`, `metronome.wav`, `other.wav`, `strings.wav`, `vocals.wav`, `wind.wav`, `backing_vocals.wav`), константный клик (540 ударов, `max resid 28.9 мс`).
- `mix.json`: `music/songs/Кислотный DJ/mix.json`

## Плейбек и рендер

- **pb-other:** два слоя (`frame: "render"`, `role: "musical"`):
  1. `DJ_arp` (`parts/DJ_arp.wav`, `"gain_db": 3.5` → `−21.52 dBFS` gated RMS / `−18.99 dBFS` stereo gated RMS / `−16.1 LUFS`, пик `−3.21 dBFS`) — пульсирующий 16-ми арпеджиатор в тактах `41–72` (`72.54–127.20 с`, Chorus 1 + Solo 1), `86–117` (`149.69–203.88 с`, Build-up / Chorus 2 + Solo 2) и `127–135` (`219.97–233.55 с`, финальный блок `all in` до `end in`).
  2. `wind_part` (`parts/wind_part.wav`, `"gain_db": -8.0` → `−27.05 dBFS` gated RMS / `−23.0 LUFS`, пик `−8.12 dBFS`) — духовые/свелл-пэды на разгонах и в припевах в тактах `33–57` (`58.31–99.95 с`), `86–103` (`149.16–179.27 с`) и `127–135` (`219.46–233.77 с`).
  - Итоговый суммарный `pb-other.wav` — **`−21.19 dBFS` gated RMS** (`−18.96 dBFS` stereo gated RMS, пик `−2.36 dBFS`).
- **pb-bass:** `null` (Alex играет бас живьём).
- **pb-drums:** `drums` (`gain_db: -4.5` → −16.56 dBFS gated RMS).
- **players:** `alex` = guitars, bass; `roma` = keys, strings, wind; `steve` = drums; `tanya` = vocals; `trio` = guitars, drums, vocals, bass.
- Сетка: beat 0.4286 с, такт 1.7143 с, downbeat стема 0.6301 с, `OFF = +2.79846 с` (+1 такт lead), `bar 1.1 = 3.429 с`, полная длина `236.571 с` (138 тактов).

## Cue (22 подсказки)

- `bar 1.1` (3.429 с) — «Кислотный DJ · drums in ready go»
- `bar 8.4` (16.714 с) — «synth in ready go»
- `bar 16.1` (29.143 с) — «stop in 3 · 3 2 1»
- `bar 24.1` (42.857 с) — «drums break ready go»
- `bar 32.1` (56.571 с) — «drums-bass break ready go»
- `bar 38.1` (66.857 с) — «synth in ready go»
- `bar 39.1` (68.571 с) — «build up ready go»
- `bar 41.1` (72.000 с) — «chorus in ready go»
- `bar 56.1` (97.714 с) — «drums-bass fill ready go»
- `bar 64.1` (111.429 с) — «bass break ready go»
- `bar 65.1` (113.143 с) — «solo in ready go»
- `bar 72.1` (125.143 с) — «drum fill ready go»
- `bar 81.1` (140.571 с) — «drums-bass break ready go»
- `bar 85.1` (147.429 с) — «build up ready go»
- `bar 86.1` (149.143 с) — «all in ready go»
- `bar 101.1` (174.857 с) — «stop in 3 · 3 2 1»
- `bar 102.1` (176.571 с) — «solo in ready go»
- `bar 117.1` (202.286 с) — «drums bass stop in 3 · 3 2 1»
- `bar 124.1` (214.286 с) — «build up ready go»
- `bar 126.1` (217.714 с) — «stop in 3 · 3 2 1»
- `bar 127.1` (219.429 с) — «all in ready go»
- `bar 135.1` (233.143 с) — «end in 3 · 3 2 1» (`count: true`)

## Риг (MainStage)

Папка сетлиста: `cherry-daddies-2000/cherry-daddies-setlist-2026-06-16/Кислотный DJ/` (`click.wav`, `cues.wav`, `pb-drums.wav`, `pb-other.wav`). В патче `Akula.patch` (`28_10_2.concert` / `2000_1.concert`) новый стем `pb-other.wav` подключается в Playback-плагин вручную в MainStage.
