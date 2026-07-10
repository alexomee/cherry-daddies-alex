---
type: pipeline
updated: 2026-07-10
---

# jamzone-render — главный рендер-пайплайн

`tools/jamzone/jamzone_render.py` — рендерит плейбек-пакет для сцены прямо из стемов, без Logic. На вход — папка песни `music/songs/<Artist - Title>/` с её `mix.json`; на выход — выровненные WAV в `<song>/auto-render/`. Всё выравнивается по построению: `t=0` = тактовая линия, downbeat стема на тактовой линии, целые такты. `auto-render/timeline.json` пишет `{bpm, bar_sec, offset_sec}` — `offset_sec` прибавить к временам стем-таймлайна (`cues.json`/JamZone `structure.json`), чтобы попасть в рендер.

Запуск: `jamzone_render.py "<имя песни или папка>"`. Флаги: `--check` (анализ+проверка, ничего не пишет), `--bpm N` (форс темпа для внешних песен), `--levels [song]` (dry-run аудит громкости pb-other, ничего не пишет), конвертер позиций `--map`/`--logic`/`--bar`/`--at` (см. cue-систему).

Смежные страницы: [Moises-импорт](moises-import.md), [cue-система](cue-system.md), [MainStage-риг](mainstage-rig.md), [lyric-launcher](lyric-launcher.md).

## Что рендерит

- **click.wav** — клик. Без манифеста. Для JamZone-песен = стем `01_Click`; для внешних (Moises) строится чистый константный клик из лифтнутых JamZone-сэмплов (`jz_downbeat`/`jz_beat`) на bpm песни, акцент на долю 1. Grid-фаза = первый онсет метронома.
- **cues.wav** — вокальные подсказки в ухо (`cue_track.wav`). Без манифеста, строится из списка `cues` в `mix.json`. Правила разворота текста — см. [cue-систему](cue-system.md).
- **pb-other.wav** — support-плейбек через ОДИН MainStage-фейдер (FX, бэк-вокал, пэды, синты). Стемы/лейеры задаются в `mix.json` ключом `pb-other`.
- **pb-bass.wav** — бас-плейбек (аналогично, ключ `pb-bass`; часто `null`).
- **all.wav** — превью-микс всех музыкальных стемов.
- **cue_preview.mp3** — прослушка для утверждения cue: `all*0.85 + click*0.6 + cues*1.0` (при `MIX_LVL`/`CLICK_LVL`/`CUE_LVL`, см. ниже). Пишется только если есть cues.
- **practice-\<player\>.mp3** — минус партии игрока для разучивания (см. Practice-миксы).
- **timeline.json** — служебное (offset/bar/bpm). Не превью.
- **synths/** — опциональный `export_stems`: отдельные стемы в том же выровненном/темпо-лейбленном формате (отдать синты клавишнику).

## Уровни

Константы в шапке `jamzone_render.py`:

- `MIX_LVL = 0.85` — уровень музыки в `all`-превью и practice-миксах.
- `CUE_DB = 5.0`, `CLICK_DB = 10.0` — над бандой: cue **+5 dB**, клик **+10 dB** (клик на 5 dB громче cue). Базовые `CLICK_LVL=0.6`, `CUE_LVL=1.0` домножаются на эти dB. Клик/cue boosted, чтобы пробиваться сквозь полный микс.
- Пик-нормализация (клип до 0.97) двигает весь микс вместе — сохраняет именно эти РАЗНИЦЫ.

Эти уровни действуют в `cue_preview.mp3` (all-превью) и `practice-*.mp3`.

### pb-other loudness ceiling (attenuate-only)

pb-other идёт через ОДИН фейдер и никогда не несёт lead/мелодию — это чистый support, чей внутренний Moises-баланс надо сохранить. Две повторяющиеся support-роли ограничены per-role ПОТОЛКОМ, **только вниз**: элемент ГРОМЧЕ потолка притягивается вниз, ничего не бустится (буст тихого support толкал бы его вперёд против музыкальных партий на том же фейдере → ломает баланс).

- `FX_CEILING = -30.0`, `BACKVOX_CEILING = -23.0` dBFS gated-RMS (seed, тюнится на слух).
- Роль = regex по имени Moises: `noise|sound effects` → fx; `backing vocals` → back-vox; иначе musical (не трогается — часть pb-other должна быть громкой: synth lead, арп, чаранго). Override/opt-out через `"roles": {"<stem>": "musical"}` в `mix.json`.
- `gain_db` на bounded-стеме = трим ПОВЕРХ потолка; на musical-стеме — абсолютный.
- Мера = gated RMS по активным регионам (400мс окна, дропает тишину) → редкие FX читаются по громкости эффекта, не размываются паузами.
- Аудит: `jamzone_render.py --levels [song]` — dry-run (роль · measured · CUT/ok · post). Гонять ДО правок громкости. Прецедент: Better Off Alone noise FX −24.3 → −30 (−5.7 dB). Дизайн: `docs/plans/2026-06-18-pb-other-autolevel-design.md`.

## Перкуссия — вон из плейбека

ВСЯ перкуссия КРОМЕ основной установки (drum kit) **никогда** не идёт в плейбек/превью — её играет живой барабанщик, в миксе она с ним конфликтует. Перкуссия дропается из стем-вселенной один раз → отсутствует в `music`/`all`/`pb-other`/`pb-bass`/`cue_preview`/`practice`. Regex `is_percussion` ловит `percussion|conga|bongo|shaker|tambour|cowbell|clap|claves|guiro|cabasa|woodblock`, но kit (`drum`) всегда остаётся. Оставляем: `drums` (Moises), `Drum_Kit`/`Electronic_Drum_Kit` (JamZone). Прецедент-нарушение для чистки: t.A.T.u. `03_Percussion`.

## Layers участников (`layers`)

Когда участник (клавишник/гитарист/басист) присылает СВОЮ записанную партию для плейбека — это **layer**, а не стем. Партия ВСЕГДА уже в тональности группы (её играют под живую банду) → **layer НИКОГДА не питчится**. Меняется только временной ФРЕЙМ. Задаётся полем `"layers": [...]` рядом со `"stems"` в `pb-other`/`pb-bass`. Источник = сам layer, обработки ноль; оригинал → `<song>/parts/<name>.{wav,mp3,aif}` (read-only, вне стем-glob → не станет авто-стемом). Кладётся ПОСЛЕ питч-пасса, ДО хедрум-нормализации; подмешивается в свою группу И в `all`.

- **frame `render`** (дефолт, entry = `"name"`): запись слушала мой `auto-render`/`all` → уже несёт каунт-ин lead и темп рендера → кладётся 1:1 с индекса 0 (без offset).
- **frame `stem`** (entry = `{"file":"name","frame":"stem"}`): запись слушала сырые Moises-стемы → нативный таймлайн без lead → кладётся на `OFF`, где сидят стемы.
- **`replaces`**: если layer ПЕРЕ-записывает moises-стем (живой бас вместо студийного) → `"replaces":["bass"]`, иначе в `all`/превью два баса. Рендер выкидывает эти стемы из `all`.
- Опции entry: `offset_ms` (остаточный сдвиг латентности/фила), `gain_db`.
- **ФРЕЙМ И КЛЮЧ — НЕ ПРЕДПОЛАГАТЬ, А МЕРИТЬ.** Фрейм: широкая кросс-кор огибающей layer vs `drums` → пик ~0мс = stem, пик ~+OFF = render. Ключ: хрома-профиль layer vs `bass`/`keys`, лучший круговой сдвиг = транспозиция (0 = ориг.ключ; совпал с `pitch_semitones` = уже в ключе группы). Медиана f0 не годится. Фазу баса-vs-баса доверять уху.
- Валидность только против того, подо что писали: переписал cue (изменился OFF) → render-фрейм layer невалиден. Layers — ПОСЛЕ заморозки cue.
- Прецеденты: Band'Eros «Pro krasivuju zhizn'» — `parts/keys-noise.wav`, render-фрейм, lag +0мс. SEREBRO «Malo tebya» (`pitch_semitones:-2`) — `parts/malo-bass.aif`, stem-фрейм, хрома −2 = уже в ключе → без питча, на OFF.

## Practice-миксы (ключ `players`)

`mix.json` ключ `players` — кто что играет ЖИВЬЁМ: `{"alex": ["guitars"], "roma": [...]}` (точные имена стемов/лейеров; native = `NN_Name`, Moises = `guitars`/`keys`/`other`). На каждый полный рендер для каждого игрока пишется `auto-render/practice-<player>.mp3` = весь микс БЕЗ его стемов + клик + cue, на уровнях cue_preview (`all*0.85 + click*0.6 + cues*1.0`). Партия игрока — в ноль (не тихий гайд, играешь сам поверх). Минус питчится в ключ группы (`pitch_semitones`); layers уже в ключе — те, что игрок НЕ играет, добавляются в минус (напр. чужой живой бас остаётся). Нет ключа `players` → ничего не пишется (обратно совместимо).

Заполнение `players` — знание банды, не выводится из стемов: живые синты СПЛИТЯТСЯ между Alex и Roma per-song, спрашивать. Весь сетлист назначен (SET 1 + SET 2). Alex сидит без партии: Blinding Lights, Gala, We Found Love, t.A.T.u. Alex на басу (исключён из его practice): No Stress, Solnyshko, Beverly Hills, S&M. Уоркшит: `docs/plans/2026-06-19-players-worksheet.md`. Дизайн: `docs/plans/2026-06-16-practice-mix*.md`.

## Версионирование рендеров

Никогда не перезаписывать превью/промо-рендеры (правило [version-every-render] в памяти агента). Каждую версию под НОВЫЙ файл (`preview_v{N}`, `-v2` и т.д.), EDL/srt тоже версионировать/документировать, чтобы любую версию можно было пересобрать. Перезапись теряла работу дважды. Совпадает с граблей edge-cache при шаринге через R2 (новый key = свежая ссылка).

## Смежное

- **Никакого аплоада без явной просьбы** — по умолчанию рендерить локально в `auto-render/` и давать путь к файлу (полный, от корня репо).
- **Каунт-ин** (`"count_in": N`, `cue_step`) и cue-математика — см. [cue-систему](cue-system.md).
- **Обновление рига** после ре-рендера — `tools/sync_to_mainstage.sh`, см. [MainStage-риг](mainstage-rig.md).
- **Гочи Moises** (локальный дрейф, первый клик ≠ сильная доля, реальная смена темпа, tempo_zone/subdiv) — см. [Moises-импорт](moises-import.md).
