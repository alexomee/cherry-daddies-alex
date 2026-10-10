---
type: song
updated: 2026-10-10
title: "Hot Stuff (12\" Version)"
artist: Donna Summer
set: "24.10 Lefkara #10"
---

# Donna Summer — Hot Stuff (12" Version)

Папка: `/Users/alex/projects/cherry-daddies/music/songs/Donna Summer - Hot Stuff/`
Позиция в сетлисте: 24.10 Lefkara, песня #10 (`web/songs.json`).

## Сводка

- **bpm:** ~120.3 BPM (`click: follow`, живой диско-грув).
- **Тональность:** Gm (оригинальная тональность JamZone, `cat_5408`).
- **Источник стемов:** JamZone HQ-стемы (13 дорожек).
- **Перкуссия:** `03_Percussion` полностью исключена из плейбека и превью (играет живой барабанщик).
- **Бас:** живой (Рома играет на бас-гитаре), `pb-bass: null`. `05_Synth_Bass` полностью исключён из проекта (`exclude_stems: ["05_Synth_Bass"]`, стем удалён).
- **pb-other:** `09_Piano`, `10_Synthesizer`, `11_Synth_Keys_(theme)`, `12_Backing_Vocals`.
- **players:** roma (`04_Bass`), steve (`02_Drum_Kit`), tanya (`13_Lead_Vocal`).
- **Форма и купюры:**
  - `cut_bars: [130, 140]` — вырезаны Chorus 4 и Instrumental 4 (10 тактов / 19.97 с): после Verse 3 трек идёт сразу в 2 финальных припева (Chorus 5 и Chorus 6).
  - Вырезано студийное аутро: финальный удар перенесён на окончание Chorus 6 (`bar 146.1`, 291.32 с).
  - `10_Synthesizer` полностью заглушен в финале (`pb-other.fade_out`: bar 145 beat 4.5 → bar 146 beat 1.0, в 146 такте строго 0.0), чтобы громкий пульсирующий суб-басовый секвенсор (49 Гц) не звучал после финального удара.
  - `fade_out` на остальных музыкальных стемах: финальный аккорд и вокал «to-night!» звучат весь 146 такт (~1 такт ring-out), плавно затухая к началу 147 такта (bar 146 beat 3.5 → bar 147 beat 1.0, спад 0.74 с в ноль). Начиная со 147 такта плейбек в абсолютном нуле (0.0).
  - `cut_after_last_cue: 1` — рендер завершается через 1 такт клика после финального удара (295.13 с / 148 тактов).
- **cues:**
  - `bar 2.1` (4.114s) — `Hot Stuff all in` («Hot Stuff · all in ready go») — вступление всей банды на 2 такт (lead +1 такт count-in).
  - `bar 17.4` (35.574s) — `verse in ready go`.
  - `bar 74.1` (147.764s) — `guitar solo ready go`.
  - `bar 98.1` (195.624s) — `chorus in ready go`.
  - `bar 146.1` (291.324s) — `end in` («end in 3 · 3 2 1») — финальный аккорд/удар на долю 1 («to-night!») после счёта на «Gonna need your love».
