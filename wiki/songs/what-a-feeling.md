---
type: song
updated: 2026-10-14
title: What a Feeling
artist: Irene Cara
set: "24.10 Lefkara #12"
---

# Irene Cara — What a Feeling

Папка: `/Users/alex/projects/cherry-daddies/music/songs/Flashdance (Irene Cara) - What a Feeling/`
Позиция в сетлисте: 24.10 Lefkara, песня #12 (`web/songs.json`).

## Сводка

- **bpm:** переменный темп (`click: "follow"`): интро 92.0 BPM (такты 1–18 + даунбит 19.1 на `49.565s`), затем в такте 19 (`50.159s..52.098s`) 4 доли отсчёта `all in ready go` и клик переключаются на 2-й темп **123.8 BPM** (`"lead_tempo": "post"`), ровно подводя к входу барабанов на `bar 20.1` (`52.098s`).
- **Источник стемов:** JamZone HQ-стемы (`cat_10091`).
- **Бас:** живой (Рома играет на бас-гитаре), `pb-bass: null`.
- **Перкуссия:** ручная перкуссия исключена из плейбека (играет барабанщик Стив).
- **pb-other:** 05_Electric_Guitar, 06_Synthesizer, 07_Synth_Voice, 08_Synth_Keys_1, 09_Synth_Keys_2, 10_Backing_Vocals + `11_Lead_Vocal` в припевах и аутро с автоуровнем `back-vox` (-23 dBFS, -5.4 dB) и мьютом вне припевов (`mute: [[1, 31.58], [48.5, 63.59], [82.5, 87.55]]`).
- **cues (10 подсказок):**
  - `bar 2.1` — `What a Feeling guitars in` (5.218s)
  - `bar 6.1` — `verse in` (15.652s, секция Verse JamZone)
  - `bar 20.1` — `all in` (52.098s, вход барабанов; отсчёт `all in ready go` и клик в такте 19 с `50.159s` уже идут во 2-м темпе 123.8 BPM)
  - `bar 48.1` — `solo in ready go` (106.379s, 1-я секция Instrumental JamZone)
  - `bar 55.4` — `vocal in` (121.403s, 4-я доля под затакт «Now» перед 3-м куплетом)
  - `bar 80.1` — `bridge in` (168.414s, 2-я секция Instrumental JamZone)
  - `bar 88.1` — `chorus variation ready go` (183.923s, 3-й припев JamZone)
  - `bar 96.1` — `outro in ready go` (199.432s, секция Outro JamZone)
  - `bar 104.1` — `keep going` (214.941s, продолжение аутро)
  - `bar 114.1` — `end in` (234.327s, count: true, финальный аккорд Gm)

## Задачи (Todo)

- [x] Исправить подсказки (cues) — verse in и остальные, выровнять клик интро
- [ ] Убрать соло из плейбека (`05_Electric_Guitar`) — его должна играть гитара (Alex)
