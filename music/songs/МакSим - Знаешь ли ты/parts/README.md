# parts

## keys.notes.json + znaesh-rusmidi.mid — 2026-11-21

Клавиши плейбека нотами (вместо Moises-стемов `piano`, `keys`, `other`, `strings`). `keys.notes.json` собирает
`tools/jamzone/prep_znaesh_li_ty.py notes` из `znaesh-rusmidi.mid` (MIDI с rusmidi.com, дал Alex) — править в скрипте, не в json.
Alex после страницы сравнения «запись против MIDI» (2026-11-21): «Да, берём MIDI» — ноты как в MIDI, без правок по записи.
MIDI в 128 bpm (наши 64 вдвое): наш такт 1.1 = доля 4 MIDI; онсеты квантованы до 1/8 нашей доли. Тональность оригинала
(C#m) = тональность группы (`pitch_semitones` 0); если тональность сменится, ноты транспонировать.

Голоса: `piano` (дорожка 3, ноты держатся до тактовой черты — педаль), `arp` (5), `low` (4, держанные корни),
`strings` (6), `lead` (7: мелодия 48–55, октавные пары + квинта сверху, как в записи), `lead_acc` (аккорды дорожки 6
в 44–59: аккомпанемент стема other), `horn` (9, тромбон 39–59, в записи слышна половина нот), `hits` (10, 43–46).
Не взяты: колокольчики MIDI (дорожка 8) и одиночные шестнадцатые дорожки 7 — в записи их нет. Живых голосов нет (вся песня в плейбеке, `gm800` 1). Звук — ZENOLOGY, выбирает Alex (выбор — на странице песни в вики); слоя ещё нет.
Разбор: `wiki/songs/maksim-znaesh-li-ty.md`.

## pb-keys.wav, keys.gains.json — 2026-11-21

`pb-keys.wav` — слой клавиш: дубли плагина ZENOLOGY на тонах, выбранных Alex (`zenology_render.py record`), + колокольчики
тактов 8 и 10, вырезанные из минуса mp3 (`analysis/.../bells-mp3/bells-cut.wav`). Stem-фрейм, тональность оригинала, не в git (wav).
Пересборка: `prep_znaesh_li_ty.py notes` → `zr record` → `calibrate` → `notes` → `layer`. `keys.gains.json` — усиления голосов
по стемам (`calibrate`). В `mix.json` с 2026-11-21: `pb-other.layers`, `derived` от piano / keys / strings / other, `gain_db −2.3`.

