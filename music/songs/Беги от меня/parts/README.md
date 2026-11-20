# parts

## roma-keys-2810.wav — 2026-11-17

Концертная партия Ромы с мультитрека 28.10 Music Hall (`tools/concert-2810/make_layer.py`), render-frame: t=0 = рендер t=0, длина = рендер. Без громкости (gain в mix.json). клавиши Ромы **с биса** (`08`, Set 2 №17), заменяют Moises `keys`, `gain_db −1.1`; на бисе темп был 123 → растянуто rubberband'ом до 125 с сохранением тона; вход пульта был перегружен (207 срезанных вершин) → `adeclip` + `alimiter` −1 dBFS, в слое срезов нет; сдвиг −10 мс. В pb-other рядом strings (+3.5).
Разбор: `wiki/gigs/2026-10-28-multitrack.md`. При смене cue/OFF пересобрать тем же скриптом.

## synths.notes.json + begi-midifind.mid + pb-fx.wav — 2026-11-20

Клавиши песни нотами для GM-800 (вместо концертной партии Ромы и стема strings). `synths.notes.json` собирает
`tools/jamzone/prep_begi_ot_menya.py notes` из `begi-midifind.mid` (MIDI с midifind.com, дал Alex) — править в скрипте, не в json.
До-диез минор (pitch 0), такты mix.json. Голоса: `lead`, `lead_lo`, `lead_echo`, `whistle`, `stab`, `arp`, `pad`.
`pb-fx.wav` — обратные свеллы перед припевами (такты 42 и 83, доли 3–4), вырезаны из стемов keys/strings, stem-фрейм
(`prep_begi_ot_menya.py fx`); в mix.json пойдёт слоем `derived` вместе с `pb-synths`.
Тоны и усиления в `layer.takes` предварительные: на приборе ничего не сыграно, слоя `pb-synths.wav` ещё нет, `mix.json` не тронут.
Alex 2026-11-20: «всё в плейбек» — все голоса идут в слой, живых нет. Разбор и что дальше: `wiki/songs/begi-ot-menya.md`.
