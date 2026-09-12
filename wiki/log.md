# log

Append-only хроника вики. Формат: `## [YYYY-MM-DD] <op> | <заголовок>`.

## [2026-07-10] init | Схема и каркас вики

Заведена вики по Karpathy LLM-wiki паттерну. Решения: скоуп — весь бэнд-опс (песни+гиги+контент+риг), живёт в репо `wiki/`, линки — стандартный markdown (GitHub-читаемо). Схема: `wiki/SCHEMA.md`.

## [2026-07-10] ingest | Первичное наполнение (seed): 24 песни + 7 пайплайнов + 4 людей + 1 гиг + 3 контента

Параллельный сид 32 агентами из источников репо (mix.json, git-история, docs/plans, память агента). Заведён index.md. Открытые противоречия зафиксированы в секциях «Открытое» страниц (см. в т.ч. Beverly Hills бас, Infinity players, No Stress A4/A#4, Mr. Saxobeat «alex vocal in»).

## [2026-07-22] ingest | Беги от меня: полный cue-сет + синк в риг

Новая страница [begi-ot-menya](songs/begi-ot-menya.md) (+ index tryout-секция). 16 cue: старт передвинут на пикап-долю синт-риффа (bar 1 beat 0), остальные позиции — таймстемпы пользователя из Logic. Ключевая находка: его фрейм = нетримленные оригиналы Moises (−8.8с фронт-трима), а сырой индекс клика метронома завышает долю на 2 (варп-даунбит на клике #2) — mapping «клик k = доля k−2» сверен по кик-входу и всем 12 точкам (±50мс на кликах). Риг: только cues.wav (click/pb побайтно те же), коммит в риге не запушен.

## [2026-09-02] fix | Беги от меня: баг фазы варпа → пере-варп, cue перенумерованы, риг обновлён

Пользователь заметил обрезанное начало и сдвиг `moises-orig/keys` относительно `all.wav`. Причина — `jamzone_warp_ext.py`: фаза константной сетки = медиана по всем кликам; при дрейфе +700 → −520 мс варп выбросил первые 700 мс всех стемов, рендер взял клик 2 за такт 1.1 (акцент клика на 3-й доле, все cue на «beat 3»). Фикс инструмента: фаза от старта (dev(0)=0), хвост удлиняется. Пере-варп из `moises-orig/`, cue → на «1» (`bar N.3` → `N+1.1`), рендер = старый +0.96с, синк в риг (cues/pb-other/pb-bass/pb-drums; click тот же), риг-коммит `0cc4f838` не запушен. Страница [begi-ot-menya](songs/begi-ot-menya.md) переписана (правило «k−2» отменено), [moises-import](pipelines/moises-import.md) — примечание про фазу. Побочно: Eva 2.0 тем же багом потеряла 50 мс тишины до первого клика (музыка цела), Солнышко не задето.

## [2026-09-02] fix | Такая любовь: студийный бас после финального удара убран из pb-bass

Бас в pb-bass продолжал фразу с 136.1 в 2-тактовом хвосте `cut_after_last_cue` — после того, как банда остановилась на «end in» 135.1. Штатный `mute` группы: `"pb-bass": {"mute": {"bass": [[135.5, 138]]}}`; удар на 135.1 цел, файл побайтно тот же до 242.6с. В риг ушёл только `pb-bass.wav` (коммит `75b7a5fc`, запушен). Заведена страница [takaya-lyubov](songs/takaya-lyubov.md) (её не было). Попутно: пуш рига с Беги (`0cc4f838`) прошёл после освобождения портов (17 тыс. TIME_WAIT в системе); у основного репо remote не настроен — коммиты локальные.

## [2026-09-03] ingest | Tryout: Медведица, Кукла колдуна, Ту-лу-ла — click + стартовый cue

Три новые песни без плейбека: оригиналы с YouTube (yt-dlp с куками Chrome — brew-версия отдаёт 403/age-gate), bpm по lstsq на beat-треке librosa (130.0 / 148.6 / 130.6), синтетический `metronome.wav` от первой сильной доли (хрома-флакс mod 4), один cue `bar 1` + `count: true` («<Название> in 3» + 3 2 1). Рендер click/cues/all/cue_preview, дашборд «НА ПРОБУ», в риге папки с click+cues (`eb9b74f6`), MAP синка дополнен; сеты в MainStage заводятся руками. Новый пайплайн-page [youtube-click-only](pipelines/youtube-click-only.md).

## [2026-09-03] fix | Tryout-тройка: стартовый cue → стандартный «<Название> … all in ready go»

По правке пользователя: не `count: true` («in 3» + 3 2 1), а обычный стартовый cue — название естественным темпом в такте 1, «all in ready go» по долям такта 2, вход на 1.1. Геометрия рендера та же (click побайтно тот же), в риг ушли только `cues.wav` (`f7b647ec`). Страницы песен, index и [youtube-click-only](pipelines/youtube-click-only.md) поправлены.

## [2026-09-03] ingest | Tryout: Rock & Roll Queen (The Subways) — click + стартовый cue

Тем же пайплайном [youtube-click-only](pipelines/youtube-click-only.md). Гоча: `beat_track` без приора трекал половину долей (197 на 170 с), с `start_bpm` и hop 128 — 400 долей, но темп живой (138–145 по окнам), lstsq по всей песне 141.0 → взято 141. Сильная доля по кик/хрома mod 4 на трекнутых долях (не на константной сетке — она теряет фазу на плывущем темпе). Риг `55091574`, дашборд «НА ПРОБУ» (34 песни).

## [2026-09-11] ingest | Tryout: Pretty Fly (For A White Guy) (The Offspring) — Moises stems + click + cues + pb-drums + backing vocals

Импорт из архива Moises (143 bpm, B minor): выравнивание через `jamzone_warp_ext.py` (`--bpm 143 --downbeat 1`), интро 3 такта отрезано под вход барабанов.
Настроен `mix.json`: стартовый cue (`Pretty Fly drums in`), `pb-other` (backing vocals, auto-leveled до -23 dBFS), `pb-drums` (drums для репетиций), бас живой (Roma).
Сгенерирован полный авто-рендер (click, cues, pb-other, pb-drums, all, cue_preview, pb-drums.mp3, practice-миксы). Песня добавлена в дашборд («НА ПРОБУ», 35 песен).

## [2026-09-11] ingest | Tryout: Медляк (Mr. Credo) — Moises stems + click + cues + pb-drums + pb-other + pb-bass

Импорт из архива Moises (105 bpm, G minor): выравнивание через `jamzone_warp_ext.py` (`--bpm 105.0`), дрейф минимальный (0–36 мс).
Настроен `mix.json`: `pb-other` (backing_vocals + strings), `pb-other-keys` (+keys), `pb-drums`, `pb-bass`.
3 cue: `Медляк synth in` на 1.1, `drums in` на 9.1 (вход барабанов и баса), `verse in` на 17.1 (куплет).
Сгенерирован полный авто-рендер, песня добавлена в дашборд («НА ПРОБУ», 36 песен).

## [2026-09-11] ingest | Tryout: Кукла колдуна (Король и Шут) — Moises stems + click + cues + pb-drums + pb-other (strings скрипка)

Импорт из архива Moises (148.6 bpm, D minor): замена старого youtube-click-only на полный набор стемов.
Выравнивание через `jamzone_warp_ext.py` (`--bpm 148.6`), сетка сведена с плавающей живой записью 1999 года.
Настроен `mix.json`: `pb-other` (backing_vocals + strings со скрипичной темой), `pb-other-keys` (+keys), `pb-drums` (барабаны для репетиций), бас живой (Roma).
3 cue: `Кукла колдуна all in` на 1.1, `drums in` на 8.1 (вход ударных и полного бэнда), `verse in` на 17.1.
Сгенерирован полный авто-рендер со всеми practice-миксами, дашборд обновлён.

## [2026-09-11] ingest | Tryout: Я буду (5sta Family & 23:45) — Moises stems + click + cues + pb-drums + pb-other + pb-bass

Импорт из архива Moises (90 bpm, A minor): выравнивание через `jamzone_warp_ext.py` (`--bpm 90.0`), нулевой дрейф (±6 мс).
Настроен `mix.json`: `pb-other` (backing_vocals + piano), `pb-other-keys` (+keys), `pb-drums`, `pb-bass`.
3 cue: `Я буду all in` на 1.1, `chorus in` на 9.1 (вход припева), `verse in` на 17.1 (рэп-куплет).
Сгенерирован полный авто-рендер, песня добавлена в дашборд («НА ПРОБУ», 37 песен) и синхронизирована в риг MainStage.




