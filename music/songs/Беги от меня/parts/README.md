# parts

## roma-keys-2810.wav — 2026-11-17

Концертная партия Ромы с мультитрека 28.10 Music Hall (`tools/concert-2810/make_layer.py`), render-frame: t=0 = рендер t=0, длина = рендер. Без громкости (gain в mix.json). клавиши Ромы **с биса** (`08`, Set 2 №17), заменяют Moises `keys`, `gain_db −1.1`; на бисе темп был 123 → растянуто rubberband'ом до 125 с сохранением тона; вход пульта был перегружен (207 срезанных вершин) → `adeclip` + `alimiter` −1 dBFS, в слое срезов нет; сдвиг −10 мс. В pb-other рядом strings (+3.5).
Разбор: `wiki/gigs/2026-10-28-multitrack.md`. При смене cue/OFF пересобрать тем же скриптом.
