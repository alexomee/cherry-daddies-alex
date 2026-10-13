---
type: song
updated: 2026-10-13
title: The Best
artist: Tina Turner
set: "24.10 Lefkara #19"
---

# Tina Turner — The Best

Папка: `/Users/alex/projects/cherry-daddies/music/songs/Tina Turner - The Best/`
Позиция в сетлисте: 24.10 Lefkara, песня #19 (`web/songs.json`).

## Сводка

- **bpm:** 103.9 BPM.
- **Источник стемов:** JamZone HQ-стемы (`cat_5519`).
- **Бас:** живой (Рома играет на бас-гитаре), `pb-bass: null`.
- **Перкуссия:** ручная перкуссия исключена из плейбека (играет барабанщик Стив).
- **pb-other:** `04_Acoustic_Guitar_(clean)`, `05_Rhythm_Electric_Guitar_(muted)`, `06_Rhythm_Electric_Guitar`, `07_Arr._Electric_Guitar`, `08_Distorted_Electric_Guitar`, `09_Digital_Piano`, `10_Hammond_(Hammond)`, `11_Synth_Keys`, `13_Backing_Vocals` (все 5 гитар возвращены в плейбек во всей песне); саксофон (`12_Tenor_Saxophone`) убран из плейбека (играется вживую).
- **cues:**
  - `bar 2.1` — `The Best all in` (4.561s)
  - `bar 5.4` — `verse in` (13.191s)
  - `bar 30.1` — `chorus in` (69.191s)
  - `bar 81.3&` — `sax solo ready go` (188.506s, привязан к первой ноте саксофона)
  - `bar 89.4` — `chorus in ready go` (207.241s, на 1 долю раньше даунбита припева)
  - `bar 106.1` — `end in` (244.791s, финальный хит на ~4:05)

## Задачи (Todo)

- [x] Исправить ending cue (перенесён на bar 106.1 / 244.79s, ~4:05)
- [x] Вернуть гитары в плейбек (`pb-other`) во всей песне
- [x] Убрать саксофон из плейбека (`12_Tenor_Saxophone`)
- [x] Сдвинуть sax solo cue на bar 81.3& под первую ноту саксофона
- [x] Сдвинуть cue припева на bar 89.4 (на 1 долю раньше)
