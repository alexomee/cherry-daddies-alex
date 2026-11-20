# parts

## roma-keys-2810.wav — 2026-11-17

Концертная партия Ромы с мультитрека 28.10 Music Hall (`tools/concert-2810/make_layer.py`), render-frame: t=0 = рендер t=0, длина = рендер. Без громкости (gain в mix.json). клавиши Ромы (`08`, Set 2 №3), заменяют Moises `keys`+`other`, `gain_db −4.2`; сдвиг +5.5 мс. **Временно — потом перезаписать** (Alex). Рома не играл в тактах 18–20, 26–40, 70–72 — там сейчас тишина клавиш. Первый A/B был сдвинут на такт — пересобран.
Разбор: `wiki/gigs/2026-10-28-multitrack.md`. При смене cue/OFF пересобрать тем же скриптом.

## synths.notes.json + solnyshko-rusmidi.mid — 2026-11-20

Клавиши песни нотами для GM-800 (вместо концертной партии Ромы). `synths.notes.json` собирает
`tools/jamzone/prep_solnyshko.py notes` из `solnyshko-rusmidi.mid` (MIDI с rusmidi.com, дал Alex) — править в скрипте, не в json.
Тональность группы (Bbm), такты mix.json. Голос `live` (офф-бит стабы 17–24 и 121–127, cue «alex in») играет Alex, в слой не идёт.
Тоны и усиления в `layer.takes` предварительные: на приборе ничего не сыграно, слоя `pb-synths.wav` ещё нет, `mix.json` не тронут.
Разбор и что дальше: `wiki/songs/solnyshko.md`.
