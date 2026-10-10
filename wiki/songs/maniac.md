---
type: song
updated: 2026-10-10
title: Maniac
artist: Michael Sembello
set: "24.10 Lefkara Сет 2 #4"
---

# Michael Sembello — Maniac

Папка: `/Users/alex/projects/cherry-daddies/music/songs/Flashdance (Michael Sembello) - Maniac/`
Позиция в сетлисте: 24.10 Lefkara, Сет 2, песня #4 (`web/songs.json`).

## Сводка

- **bpm:** ~159 BPM (`click: follow`, шаг cue по умолчанию 1 слово на долю).
- **Тональность:** Abm / G#m (оригинальная тональность JamZone, `cat_7662`).
- **Источник стемов:** JamZone HQ-стемы (12 дорожек).
- **Перкуссия:** `03_Percussion` исключена из плейбека (играет живой барабанщик).
- **Бас:** живой (Рома играет на бас-гитаре), `pb-bass: null`.
- **pb-other:** клавиши, синты, струнные и бэки: `06_Electric_Piano_(Rhodes)`, `07_Synthesizer_(disto)`, `08_Synth_Keys_1`, `09_Synth_Keys_2`, `10_String_Section`, `11_Backing_Vocals`.
  - `08_Synth_Keys_1` звучит в плейбеке (в т.ч. в предприпевах и секции Bridge).
  - `09_Synth_Keys_2` заглушен в `pb-other` с такта 1 до такта 141 (`"mute": {"09_Synth_Keys_2": [[1, 141]]}`): лид-партию играет гитара (Alex); на Chorus 3 (такт 141) гитара продолжает играть соло, поэтому `09_Synth_Keys_2` вступает в плейбеке с 141 такта и звучит до конца.
- **players:** roma (`04_Synth_Bass`), steve (`02_Electronic_Drum_Kit`), tanya (`12_Lead_Vocal`), alex (`05_Lead_Electric_Guitar`).

## Cues

- `bar 3.1` (3.040s) — `Maniac drums in` («Maniac drums in ready go») — вступление барабанов на 1 долю 3 такта.
- `bar 11.1` (15.120s) — `main in ready go` — вступление синтов, Rhodes и баса (~0:15).
- `bar 18.4` (26.860s) — `verse in` («verse in ready go», шаг 1 слово/доля) — вокальный вход Тани из-за такта на 4 долю («Just a...»).
- `bar 59.1` (87.590s) — `longer here` (~1:27) — подсказка на 2-тактовом инструментальном тернараунде после Chorus 1 перед Verse 2.
- `bar 101.1` (150.970s) — `bridge in` («bridge in ready go») — секция Bridge JamZone.
- `bar 117.1` (175.120s) — `guitar solo ready go` — секция Instrumental / соло гитары (Alex).
- `bar 133.1` (199.270s) — `prechorus in` («prechorus in ready go») — секция Pre chorus 3 JamZone (~3:15–3:20 JZ time).
- `bar 140.4` (210.990s) — `chorus in ready go` — Chorus 3 на 1 долю раньше (`bar 140 beat 4`), точно под вокальный затакт Тани («She's a...»); гитара продолжает соло, синт keys 2 появляется в плейбеке со 141 такта.
- `bar 171.1` (256.620s) — `end in` («end in 3 · 3 2 1») — финальный удар.

## Задачи (Todo)

- [ ] Вспомнить партию гитары
- [ ] Убрать пианино (`06_Electric_Piano_(Rhodes)`) из плейбека (`pb-other`) — партию будет играть гитара (Alex)
