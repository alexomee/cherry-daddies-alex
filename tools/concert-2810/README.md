# Концерт 28.10 → партии Ромы: концерт или стем

Разбор мультитрека с микшера 28.10 Music Hall против стемов песни. Итоги и выводы: `wiki/gigs/2026-10-28-multitrack.md`.

Каналы `08 Guitar LR` / `09 Keys LR` подписаны наоборот: `08` = клавиши Ромы, `09` = гитара Alex, `07` = бас Ромы.

1. `inventory.py` — какие каналы активны в каждой песне, партии Ромы по снимку `4e67c9a`.
2. `align.py` → `concert_align.json` — грубое выравнивание концерта под рендер (огибающие Cues / PB / Click).
3. `analyze.py [песня…]` — запускать через `uv run -q --with librosa --with numpy --python 3.12 python tools/concert-2810/analyze.py`. Точная карта `концерт = a + b·рендер` по онсетам клика (уход часов пульта ≈ −75 ppm; Беги/Медведица шли в другом темпе — растяжка rubberband), ноты (хрома по долям), покрытие, тайминг против сетки 16-х (librosa), шум/клиппинг, громкость. Пишет `analysis/concert-2810/<песня>/{ab-stem,ab-concert,solo-stem,solo-concert}.mp3` и `results.json`.
4. `ab_page.py` + `verdicts.json` → `analysis/concert-2810/index.html` — страница A/B (переключение источника с той же секунды, чипы-переходы к местам).
