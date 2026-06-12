<!-- STATUS:auto (jamzone_status.py --write) — НЕ редактировать руками -->
_Сгенерировано из артефактов. Сводка: ✅ StageTraxx:2  🎙 cue:16_

```
song                                         stage          stems str cue logic  bounce / ST
Alexandra Stan - Mr. Saxobeat                ✅ StageTraxx    15   Y  13     Y  all,click,cues,other  ▶ST:4tr
Rihanna - S&M                                ✅ StageTraxx    13   Y  13     Y  all,click,cues,other  ▶ST:4tr
A Touch of Class - Around the World (La La L 🎙 cue           15   Y  15     Y  —
Alex Gaudino - Destination Calabria          🎙 cue            9   Y  13     Y  —
Alice Deejay - Better Off Alone              🎙 cue           12   Y   9     Y  —
Band'Eros - Pro krasivuju zhizn'             🎙 cue          ext   -  15     -  —
Basshunter - Now You're Gone                 🎙 cue           10   Y   -     Y  —
Beverly Hills                                🎙 cue          ext   -  19     Y  —
Cascada - Everytime We Touch                 🎙 cue           14   Y   -     Y  —
Gala - Freed from Desire                     🎙 cue           11   Y  15     Y  —
Guru Josh - Infinity 2008                    🎙 cue           10   Y   -     Y  —
Icona Pop & Charli XCX - I Love It           🎙 cue           12   Y  12     -  —
Laurent Wolf & Eric Carter - No Stress       🎙 cue            7   Y  10     Y  —
Quest Pistols - Я устал                      🎙 cue          ext   -  20     Y  —
Rihanna & Calvin Harris - We Found Love      🎙 cue           12   Y   -     Y  —
Shakira - Whenever, Wherever                 🎙 cue           14   Y  13     -  —
The Weeknd - Blinding Lights                 🎙 cue           13   Y  13     Y  —
Yeah Yeah Yeahs - Heads Will Roll            🎙 cue           13   Y  13     Y  —
```
<!-- /STATUS:auto -->

# Статус-борд песен — концерт 26.06.2026

**Фактический статус — выше (авто-блок) или `python3 tools/jamzone/jamzone_status.py`.**
Он выводится из РЕАЛЬНЫХ артефактов (стемы, `cues.json`, `logic-render/`, база StageTraxx) и не протухает.
Регенерация блока: `jamzone_status.py --write`. **НЕ дублировать per-song состояние руками** — именно рукописная таблица соврала новой сессии («в ST 0 песен», хотя S&M там).
Стадии: ❌ none → 🧩 stems → 🎙 cue → 🎚 bounced (`logic-render/`) → ✅ StageTraxx.

Ниже — только то, что НЕ выводится из файлов: докачка, прослушка, решения, выбор на репу.

## Нет в библиотеке (докачать — нужен пользователь)
- **SEREBRO «Мало тебя»** — нет в загруженном JamZone. Докачать в приложении или Moises.
- **Демо «Солнышко»** — Moises-стемы есть (`Demo - Solnyshko/`, варп на 138.000 — брейкдаун плыл до +52мс), auto-render + cue готовы.
(после докачки: extract → cue → довести → bounce в Logic → `stagetraxx_render.py`)

## Прослушка cue (НЕ выводится из файлов — ведём вручную)
Сгенерировано, но НЕ отслушано пользователем:
- S&M (конец 4:02.18) · No Stress (3:19.22) · Alice Deejay (3:33.80) · Quest Pistols (старт + bass-конец, медл. ~1:45–2:00) · Mr. Saxobeat (контрольно) · Демо «Солнышко» (19 cue; `auto-render/cue_preview.mp3`)
Отслушивать: `jamzone_cues.py "<песня>" --audition` (нативные) / `jamzone_cues_ext.py … --audition` (внешние).

## Решения (повисли)
- **Blinding Lights** — конец: fade 3:20.62 vs последний барабан 3:08.
- До-фиксовые cue вне репы (ре-рендер при надобности): ATC, Destination Calabria, Gala, Icona Pop, Shakira, Heads Will Roll.

## Репетиция (выбор — человеческий)
🎯 12 песен: Cascada · Basshunter · We Found Love · S&M · Quest Pistols · Band'Eros · Mr. Saxobeat · Демо «Солнышко» · No Stress · SEREBRO «Мало тебя» · Alice Deejay · Infinity 2008.
Готовность каждой — в авто-блоке. «Готово к репе» = cue отслушан; «готово полностью» = ✅ StageTraxx.

Per-song заметки (cat/end — не из файлов):
- Heads Will Roll: cat_23443 (не A-Trak) · Gala: cat_30111 (club) · Blinding Lights: cat_60088 (не Boyce cover) · ATC: конец руками 3:37.12 · Saxobeat + S&M: в ST играют из `st-render/` (wav на тактовой сетке от `logic_render_rebar.py`; logic-render не тронут, см. arpeggiator-sync.md) · у Saxobeat в logic-render «click.mp3» — дубль cues, настоящего клика в бounce нет (st-render берёт клик из стема, так что не блокер).
