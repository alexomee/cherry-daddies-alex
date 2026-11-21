# parts

## roma-keys-2810.wav — 2026-11-17

Концертная партия Ромы с мультитрека 28.10 Music Hall (`tools/concert-2810/make_layer.py`), render-frame: t=0 = рендер t=0, длина = рендер. Без громкости (gain в mix.json). клавиши Ромы (`08`, Set 2 №3), заменяют Moises `keys`+`other`, `gain_db −4.2`; сдвиг +5.5 мс. **Временно — потом перезаписать** (Alex). Рома не играл в тактах 18–20, 26–40, 70–72 — там сейчас тишина клавиш. Первый A/B был сдвинут на такт — пересобран.
Разбор: `wiki/gigs/2026-10-28-multitrack.md`. При смене cue/OFF пересобрать тем же скриптом.

## synths.notes.json + solnyshko-rusmidi.mid — 2026-11-20

Клавиши песни нотами для GM-800 (вместо концертной партии Ромы). `synths.notes.json` собирает
`tools/jamzone/prep_solnyshko.py notes` из `solnyshko-rusmidi.mid` (MIDI с rusmidi.com, дал Alex) — править в скрипте, не в json.
Тональность группы (Bbm), такты mix.json. Голос `live` (офф-бит стабы 17–24 и 121–127, cue «alex in») играет Alex, в слой не идёт.
Тоны выбрал Alex на слух (2026-11-20), усиления — `synths.gains.json` (`prep_solnyshko.py calibrate`).
Разбор и что дальше: `wiki/songs/solnyshko.md`.

## pb-synths.wav, pb-fx.wav — 2026-11-20

`pb-synths.wav` — слой клавиш, записанный с GM-800 (25 дублей, `gmp record` → `gmp layer`), stem-фрейм, тональность группы. `pb-fx.wav` — реверс-тарелка из стема `other` (такты 8, 24, 120, 128, выше 3 кГц, транспонирована −2), `prep_solnyshko.py fx`. Оба не в git (wav), пересобираются командами из шапки скрипта; дубли лежат в `analysis/gm800-match/Demo - Solnyshko/rec-synths-*.wav`.
В `mix.json` с 2026-11-20: `pb-other.layers`, оба `derived` от `keys` + `other`, `gain_db +0.4`. `roma-keys-2810.wav` больше не используется (оставлен как ориентир по звуку).

### 2026-11-21: рифф — плагин ZENOLOGY

Голос `riff` в `pb-synths.wav` сыгран плагином ZENOLOGY, тон `PRST_A Factory Presets/32{p1.level=0,p*.release=450}` («Sunrise полусухой», выбор Alex), вместо дублей GM-800 330 + 1024. Остальные голоса — прежние дубли прибора. Пересборка: `prep_solnyshko.py notes` → `zenology_render.py record` → `prep_solnyshko.py calibrate` → `notes` → `gm800_part.py layer`.
