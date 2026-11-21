---
type: song
updated: 2026-11-21
title: Медляк
artist: Mr. Credo
set: tryout batch 2026-09
---

# Медляк (Mr. Credo)

Tryout 2026-09. Moises стемы (G minor, 105 bpm). В плейбеке: `pb-other` (`backing_vocals`, `strings`, `keys`), `pb-drums` (drums для репетиций), `pb-bass` (`bass`).

## Сводка

- **bpm:** 105.0 — Moises стемы выровнены через `jamzone_warp_ext.py` (`--bpm 105.0`), дрейф оригинальной записи минимальный (0–36 мс за 4.5 мин).
- **pitch_semitones:** 0 (G minor).
- **pb-other:** `backing_vocals` (+0.5 dB), `keys` (+0.5 dB), `strings` (+2.5 dB) — `keys` объединены в `pb-other`, уровень поднят на +4 dB (итоговый `auto-render/pb-other.wav` −20.69 dBFS gated RMS, пик −0.4 dBFS).
- **pb-drums:** `drums` (барабаны для репетиций без барабанщика).
- **pb-bass:** `bass` (`gain_db: -2.0`).
- **players:** steve: `drums`; tanya: `vocals`.
- **mix.json:** `music/songs/Mr. Credo - Медляк/mix.json`
- **Рендер:** OFF +4.229 с, lead +2 такта под стартовую фразу, длина 269.7 с (118 тактов).

## Cue

6 cue:
1. `bar 1.1` (4.571 с) — `"Медляк synth in"` → «Медляк» + «synth in ready go», на 1.1 вступает аккордеонный синт.
2. `bar 9.1` (22.857 с) — `"drums in"` → «drums in ready go», на 9.1 вступают барабаны и бас.
3. `bar 17.1` (41.143 с) — `"verse in"` → «verse in ready go», на 17.1 вступает куплет («Сегодня в белом танце кружимся...»).
4. `bar 81.1` (187.429 с / 3:07.43) — `"stop"` → «stop in 3 · 3 2 1», отсчёт «3 2 1» на долях `80.2–80.4`, событие на последнем ударе бочки `81.1` перед брейкдауном без барабанов.
5. `bar 96.1` (221.714 с / 3:41.71) — `"drum in"` → «drum in ready go», на `96.1` возвращаются барабаны после брейкдауна.
6. `bar 113.1` (260.571 с / 4:20.57) — `"end in"` (`count: true`) → «end in 3 · 3 2 1», отсчёт «3 2 1» на долях `112.2–112.4`, событие на последнем финальном ударе барабанов `113.1`.

## Файлы рендера (`auto-render/`)

- `click.wav`, `cues.wav`, `all.wav`
- `pb-other.wav`, `pb-drums.wav`, `pb-bass.wav`
- `cue_preview.mp3`, `pb-drums.mp3`, `pb-other.mp3`, `pb-bass.mp3`
- `practice-steve.mp3`, `practice-tanya.mp3`

## Клавиши нотами (с 2026-11-21)

Задача Alex: «помоги снять песню Медляк». Решено Alex: всё в плейбек (вживую гитара на POD Go, GM-800 на MUTE), звук — тонами ZENOLOGY без прибора ([zenology](../pipelines/zenology.md)). MIDI нашёл Alex: `parts/medlyak-midifind.mid` (midifind, 105 bpm, только такты 1–32: интро, проигрыш, куплет; такт MIDI = наш такт, сверено по дорожке 0 на стеме keys).

Скрипт: `tools/jamzone/prep_medlyak.py` (`bp` → `notes` → `preview`), ноты: `parts/keys.notes.json`, MIDI как есть для A/B: `analysis/gm800-match/Mr. Credo - Медляк/keys-midi.notes.json`. `mix.json` не тронут: в плейбеке пока Moises keys + strings.

Что в записи (стемы keys + strings):

- **Гармония:** Gm E♭ Cm D (интро, проигрыши, куплеты), припев Gm E♭ B♭ D, брейкдаун 81–88 | Gm Cm | F | E♭ | F | Gm Cm | F | E♭ | Dm B♭ |, конец Gm.
- **Секции:** интро 1–8, проигрыш 9–16 / 41–48 / 105–112, куплет 17–32 / 49–64, припев 33–40 / 65–80 / 89–104 (89–96 без барабанов), брейкдаун 81–88, конец 113.
- **arp** (дорожка 0 MIDI): арпеджио на 1 1& 2 — интро, проигрыши, куплеты. На D F♯3 A3 C4 (в MIDI D3 F♯3 A3); в проигрышах оно тоже есть (в MIDI нет); в интро и проигрышах тянется весь такт, в куплете гаснет к 3-й доле.
- **lead**: второй голос куплета (дорожка 2 MIDI) — и он же мелодия интро (Alex: «в интро 4 аккорд точно не тот, вроде так же как в куплете»; по стему A♯4 на 4& такта 1, D4 на 4 такта 2, на D G4 F♯4 G4 A4). Правки: на 4& Gm A♯4 (MIDI F4), на Cm D4 C4 A♯4 (MIDI C4 D4 D♯4).
- **hookline**: подголосок проигрыша (дорожка 0 MIDI, такты 9–16: C5 A♯4 на 2& 3…), по стему верен.
- Сначала arp, lead и hookline были одним голосом, и перебор играл на тоне обе партии сразу — Alex: «две разные партии пытаемся в одну запихнуть». Разделены.
- **strings**: стем strings, тянущиеся трезвучия; в проигрыше расклад как в MIDI.
- **Припев** (нет в MIDI) — подложка и над ней мелодия или фигура (Alex: «в оригинале звучит мелодия и подложка»; первый черновик сложил онсеты всех 10 проходов в «аккорды восьмыми» `stab` — убран):
  - **cpad** — трезвучия D4 G4 A♯4 | D♯4 G4 A♯4 | D4 F4 A♯4 | D4 F♯4 A4 с медленной атакой (отсюда казалось, что аккорд меняется позже доли);
  - **mel** — во фразах 65–72 и 89–96: A♯5 … A♯5 A5 G5 D5 | F5 D♯5 . D♯5 . D5 | D5 . D5 C5 | . C5 C5 D5 C5 | … (линия вокала A♯ A G F D♯ D, свой ритм);
  - **mel_lo** — низкий ответ под мелодией: C4 (3&) A♯3 (4) A3 (4&) | A♯3 (2) C4 (2&) | A♯3 (2), такты 3–5 фразы, C4 на 2 восьмого;
  - **fig** — во фразах 33–40, 73–80, 97–104: восьмые, на 1 и 3 A5, на 2 и 4 нота аккорда (G5 / D♯5 / F5), на каждой «и» A♯5; на D сбег C6 A♯5 A5 G5 . F♯5 F♯5 A♯5, в 8-м такте D5 D6 A5 D6 F♯5.
- **brk + brk_pad** (нет в MIDI): брейкдаун — арпеджио шестнадцатыми (онсеты, совпавшие в обоих проходах 81–84 / 85–88) и аккорды под ним. В 82–88 стемы keys и strings одинаковые (корреляция 0.995): текущий плейбек играет брейкдаун вдвое громче.
- **Нет в записи:** дорожка 1 MIDI (Bright) — мелодия интро в стеме не слышна, с такта 9 она дублирует вокал.
- **Ждёт слуха Alex:** ноты припева и брейкдауна.

Страница нот (простой синт, вся песня, оригинал / мои ноты / как в MIDI, с группой): `analysis/gm800-match/Mr. Credo - Медляк/preview-part/index.html`, локальный сервер, порт 8733.

## Вокализ — записать вокалистку (2026-11-21)

Alex, работая над «Солнышком»: вокализ там синтом не получился, его надо записать вживую с вокалисткой, и «похожее место есть в медляке». Где именно в песне, он не назвал: найти по вокальному стему и уточнить. Дело в [todo](../todo.md), запись вместе с вокализом [«Солнышка»](solnyshko.md).

### Звук: перебор ZENOLOGY (2026-11-21)

Страница вариантов: `analysis/gm800-match/Mr. Credo - Медляк/zenology/page/index.html` (порт 8733, путь `/zenology/page/`), по 12 тонов на голос, весь каталог (3756) через отпечатки, чистые дубли. Перебор шёл против одного стема: голоса keys — против `keys`, strings — против `strings` (копии нот `keys-k` / `keys-s` в той же папке). Первые места (близость):

- **poly** (интро 1–4, исправленные ноты): F/711 Brightness Cho 0.921, E/504 Unearthly, D/985 OSC-SyncLd 7, A/13 Kaihou Keys, F/710 Brightness — все в пределах 0.01.
- **stab** (припев 89–92): E/507 Shadows 0.859, J/54 Dusk Harp, D/223 LFO Saw 2, F/582 Fantasy 2, L/219 Liquid Desert.
- **strings** (89–92, только пэды/струнные/хоры): ZEZ003/7 Mercurial 0.856, E/328 JP-8Haunting, K/61 Lifesines, E/327 JP-8 Hollow, F/624 Hollow Pad.
- **brk** (брейкдаун 82–85): J/6 Dreamer Keys 0.920, A/24 AnalogAtmosphere, L/219 Liquid Desert, D/511 Pipe Chatter.
- **counter** (куплет 17–20): рейтинг шумовой (0.82 и обрыв до 0.59, наверху FX и хиты) — в куплете голос звучит не один. Тот же голос играет мелодию интро внутри `poly`, разумно брать ему тон `poly`.

**Круг 2–3 (2026-11-21):** голоса переделаны (arp / lead / hookline, mel / fig / cpad), перебор заново; во втором круге у lead, hookline и mel наверх вышли шумовые FX и хиты (голос в тактах не один, мерка награждает тоны, заполняющие спектр) — третий круг только по мелодическим категориям (`sweeps3.sh`). Первые места: arp — I/33 Into the dreams, J/35 Grains, ZEZ001/1 Rocket Pad; lead — I/33 Into the dreams, I/1 ZenoPoly, D/536 Tower Bell; hookline — D/536 Tower Bell, A/29 Heliosphere, L/192 Horn Blast 2; mel — ZEZ003/9 Ionic Atmosphere, F/712 Vox Key, A/32 Sunrise; fig — F/712 Vox Key, D/491 Dreaming 6, D/520 Bell 7; cpad — ZEZ003/9 Ionic Atmosphere, B/184 Tuned Nz 2, D/191 Glass Forest. Страница дополняется `prep_medlyak.py tonepage`: под каждым голосом — что слушать в оригинале, выбор Alex отмечен ✓.

**Выбрано Alex (2026-11-21):** strings — ZEZ003/7 Mercurial, brk — J/6 Dreamer Keys, arp — ZEZ001/1 Rocket Pad, cpad — D/490 Dreaming 5, fig — A/38 AX Analog Dream «но не хватает жирка, saw базовой в унисон» (`ZEN` в `prep_medlyak.py`). Не подошло (круг 3): lead — «много грязи, там обычная мягкая пила с эффектами»; hookline — «ближе к brass/trumpet с делеем»; mel — «что-то типа magic piano / dreamy». Круг 4 по этим описаниям: `sweeps4.sh` (копия нот `keys-r4`) + `prep_medlyak.py round4` → `zenology/page/round4.html` (эффекты pedalboard на чистых дублях, смеси AX + пила). Перебор poly / counter / stab отменён (голоса переделаны), второй круг: mel, fig, arp, lead, hookline, cpad.

Ждёт: Alex выбирает тон на остальные голоса (brk_pad — по умолчанию Mercurial, как струнные?); затем дубли плагином (`zen` в `layer.takes`), слой в `pb-other` вместо Moises keys + strings, рендер, Stage Traxx.

