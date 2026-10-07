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

## [2026-09-12] tune | Pretty Fly (For A White Guy): транспонирование на 1 тон вниз (B minor → A minor, pitch_semitones: -2)

По запросу группы песня переведена на 1 тон ниже оригинала (B minor → A minor, `"pitch_semitones": -2` в `mix.json`).
Выполнен полный перерендер (`jamzone_render.py` с флагом `--practice`):
- `all.wav`, `pb-other.wav` (бэк-вокал), а также мультитрековые стемы (`auto-render/stems/`) и practice-миксы для участников (`alex`, `roma`, `steve`, `tanya`) спитчены на -2 полутона через Rubberband R3 `-3 -F` с сохранением формант;
- `pb-drums.wav` и барабанный стем оставлены без питча;
- Сетка, клик и стартовый cue («Pretty Fly drums in») не изменились;
- Риг MainStage синхронизирован через `sync_to_mainstage.sh --apply "Pretty Fly"`.

## [2026-09-12] fix | Кукла колдуна: исправление плавающего строя скрипки (варпинг через RubberBand timemap вместо varispeed-интерполяции)

- Обнаружено, что наивный линейный ресемплинг (`np.interp`) в `jamzone_warp_ext.py` при выравнивании живой записи 1999 года (дрейф сетки до 270 мс) работал как ленточный вариспид: локальная скорость менялась на ±3.5–4%, вызывая девиацию питча скрипки от -60 до +62 центов (больше полутона размаха!).
- `tools/jamzone/jamzone_warp_ext.py` модернизирован: для всех аудиостемов теперь используется `rubberband` (CLI R2 с посекундным `--timemap`), сохраняющий исходную высоту тона независимо от локальных сжатий и растяжений темпа. Метроном остаётся на линейной интерполяции для сохранения импульсных атак клика.
- Скрипт теперь автоматически поддерживает повторный варп из папки `moises-orig/` без необходимости ручного переноса файлов.
- Все стемы переварплены из `moises-orig/` и заново отрендерены через `jamzone_render.py --practice` (включая `pb-other.wav`, `pb-other-keys.wav`, мультитрековые стемы и practice-миксы).
- Риг MainStage синхронизирован через `sync_to_mainstage.sh --apply "Кукла колдуна"`.

## [2026-09-12] feat | Интерактивный мультитрековый микшер на дашборде (100% песен репертуара)

- В `jamzone_render.py` добавлен параллельный экспорт выровненных mp3-стемов (vocal, back_vox, drums, keys, bass, guitars, other, click, cues) в `auto-render/stems/`.
- Выполнен экспорт стемов для всех 37 песен всех сетов (СЕТ 1, СЕТ 2, НА БИС, НА ПРОБУ, АРХИВ).
- В `web/index.html` реализован Web Audio мультитрековый плеер со строгим каноническим порядком дорожек и независимым мгновенным мьютом/анмьютом на лету (с сохранением состояния в `localStorage`).

## [2026-09-24] cues | Медведица: 3 cue на интро + ренейм вкладки «28.10 new songs»

- По запросу группы в `Мумий Тролль - Медведица/mix.json` настроены 3 подсказки:
  1. `bar 1.1` (3.692 с): `Медведица drums in` («Медведица» в lead-такте + «drums in ready go»);
  2. `bar 3.1` (7.385 с): `all in` («all in ready go» на 4 долях такта 2, вступает гитара и банда);
  3. `bar 19.1` (36.923 с): `verse in` («verse in ready go» на 4 долях такта 18, сильная доля перед входом вокала «В слезах парнишка...»).
- Исправлен баг отсутствия `abs_sec` для Медведицы (многострочный JSON мешал регулярке `is_cue` в `jamzone_render.py`).
- Полный перерендер: обновлены `click.wav`, `cues.wav`, `all.wav`, `cue_preview.mp3` и стемы.
- Секция «НА ПРОБУ» / «New» в дашборде и сетлисте переименована в «28.10 new songs». `web/songs.json` обновлён.
- Настроен `tools/sync_site.py` и `tools/r2_upload_mixes.cjs`: 410 файлов мультитреков залиты в Cloudflare R2 (`cherry-dash/<slug>/stems/`), деплой на Vercel Production.

## [2026-09-29] analysis | Rock & Roll Queen: JamZone-клик тоже переменный

По запросу Alex извлечены 7 HQ-стемов cat_67531 в `music/songs/The Subways - Rock and Roll Queen/`. Измерены 377 импульсов исходного `01_Click.m4a`: precount ~155.28 BPM, вступление/первый куплет ~144, припевы ~139.4–139.6, финальные 10 с ~146.05; 141 в метаданных — номинальный темп. Переменность подтверждена несколькими RMS-порогами и независимым измерением максимумов волн (расхождение интервалов <0.046 мс). Сохранена CSV импульсов, дополнена [страница песни](songs/rock-and-roll-queen.md). Текущий YouTube-рендер и риг ещё не переключены: сырой JZ требует follow-сетки, строго ровные 141 — общего варпа стемов. Исправлено прежнее предположение в разговоре, что JamZone автоматически даст ровную версию.

## [2026-09-29] render | Rock & Roll Queen: ровный JamZone-плюс + клик 141 для репетиций

По подтверждению Alex применён метод «Куклы колдуна»: шесть музыкальных стемов через общую сглаженную карту RubberBand R2, pitch сохранён. Быстрый JZ-precount удалён; новый ровный клик и стандартный стартовый cue, музыка на 3.404 с. Версия `The Subways - Rock and Roll Queen/warped-141-v1/`, рецепт `analysis/warp_141_v1.py`; канонический рендер в папке с `&` обновлён, прежний целиком сохранён в `youtube-before-jamzone-2026-09-29/`. Клик 140.999997 BPM (остаток <0.303 мс), барабанный выход следует карте с лагом 2–6 мс в 11 окнах по песне. Плюс `all.wav`, плюс+клик+cue `cue_preview.mp3`, раздельные stems. Локальный дашборд обновлён, аплоада нет. Sync рига dry-run: click/cues уже побайтно идентичны, копирование не требуется.

## [2026-09-29] cues | Rock & Roll Queen: pb-other, живой бас Ромы, 4 cue

По указаниям Alex: pb-other = `06_Backing_Vocals` + `05_Lead_Electric_Guitar`, бас живой (Рома на гитаре), `players.roma = [03_Bass]`. Cue: 1 guitar in, 13 all in (первый припев), 69 solo in (Break), 77 chorus in (выход из Break). Точки сверены через исходную структуру/клики и warp-map, активность lead guitar подтверждает такты 69–76. Полный рендер + practice Ромы без баса; pb-other проверен как точная сумма двух назначенных стемов. Версия сохранена в `The Subways - Rock and Roll Queen/arrangement-v2/`; локальный web отдаёт новый плюс, cue и practice. В риг синхронизирован cues.wav; нового pb-other там пока нет, подключение в MainStage вручную.

## [2026-09-29] cues | Rock & Roll Queen: Verse 2/3 и guitar only после Chorus 2

Добавлены 3 cue по структуре JamZone/warp-map: bar 33 Verse 2 (57.872 с) «verse in ready go»; bar 57 Intro 3 после Chorus 2 (98.723 с) «guitar only ready go» (полный текст + raw:true); bar 61 Verse 3 (105.532 с) «verse in ready go». Всего 7 cue. Пересобраны плюс/прослушка pb-other/practice Ромы/стем cues, проверены актуальные HTTP-файлы локального web; cues.wav синхронизирован в риг. Версия сохранена как `The Subways - Rock and Roll Queen/arrangement-v3/`.

## [2026-09-29] cues | Ту-лу-ла: 10 cue и укороченный финал

По заданию Alex измерены события по уже имевшимся Moises-WAV: drums 1.1, guitar 4.4, verse 13.1, solo 32.4, verse 41.1, drums only 51.1, all 53.1, keep going (фраза около 2:00, точка 65.1), solo 68.4, end 77.1 / 2:23.338. Alex отдельно выбрал обрезать оригинальный хвост после финального удара: fade +80…260 мс, последующие музыкальные WAV обнулены, один такт хвоста клика. Старые источники/рендер в `versions/2026-09-29-before-cues-v1/`, новый в `versions/2026-09-29-cues-v2/`, рецепт `analysis/ending_v2.py`. Проверены сохранность PCM до fade, тишина после, все 10 cue и текущие HTTP-файлы web. Пересобраны все четыре practice; в риг синхронизированы click/cues/pb-drums. Восстановлены отсутствовавшие ~/1,2,3.aiff из идентичных по PCM копий Logic-проектов. Страница песни обновлена: прежнее описание YouTube-click-only уже не соответствовало имевшимся стемам.

## [2026-09-29] cues | Rock & Roll Queen: отсчёт к последнему удару

По стему барабанов найден финальный удар около 2:40 (пик атаки ~160.08 с), cue привязан к ближайшей доле 93.1 / 160.000 с. Добавлен `end in` + count:true → «end in 3 … 3 2 1», всего 8 cue. Пересобраны preview/pb-other-прослушка/practice Ромы/стем cues; локальные HTTP-файлы проверены хешами, cues.wav синхронизирован в риг. Версия сохранена в `The Subways - Rock and Roll Queen/arrangement-v4/`.

## [2026-09-29] cues | Pretty Fly: первый бэк, общий вход, вокальный затакт басового куплета

По измеренным стемам добавлены cue: vocal in на 2.1 / 5.035 с (Alex отдельно подтвердил первый бэк «Give it to me baby», а не lead около 15 с); all in на 10.1 / 18.462 с; bass verse ready go на 73.4 / 125.455 с — вокальный затакт на долю раньше баса 74.1 / 125.874 с. Последняя фраза целиком с raw:true. Всего 4 cue с прежним drums in на старте. Предыдущая версия сохранена в `Pretty Fly/versions/2026-09-29-before-cues-v1/` (в канонической папке The Offspring).

Полный рендер с pitch −2 завершён, плюс/прослушки плейбека/4 practice/web-стемы обновлены; текущие локальные HTTP-файлы проверены хешами. Музыка/клик/pb-other/pb-drums WAV побайтно совпали с предыдущей версией. Снимок `versions/2026-09-29-cues-v2/`, измерения `analysis/cue-anchors-2026-09-29.json`; cues.wav синхронизирован в риг.

## [2026-09-29] import | Медведица: Moises ZIP → стемы в локальном web

По запросу Alex импортирован архив `Мумии_ Тролль _ Медведица _3uDFkM8FH_E_-E minor-130bpm-443hz.zip`: 8 музыкальных стемов + метроном + служебный count-in. Сглаженный дрейф −19.7…+3.2 мс выровнен общей картой RubberBand R2 на 130 BPM без pitch shift. Male/female vocals сохранены отдельно (оба нужны), в web объединены как Вокал; lead/rhythm guitars — Гитары. Ещё Барабаны/Бас/Клавиши/Остальное + Click/Cues. Новый плюс собран только из стемов, старый цельный источник и рендер перенесены в `versions/2026-09-29-before-stems-v1/`; сырьё/рецепт/манифест в `imports/moises-2026-09-29/`. Прежние три cue на 3.692 / 7.385 / 36.923 с. Локальные 8 дорожек + preview проверены HTTP-хешами, seeking 206; cues.wav синхронизирован в риг. Аплоада нет.

## [2026-09-29] transcription | Кукла колдуна: два MIDI-голоса скрипок для Logic

По подтверждению Alex разобран корневой `strings.wav` через Basic Pitch ONNX, затем фундаментальные частоты/гармоники: убраны многие октавные дубли, вибрато-фрагменты и короткие хвостовые перекрытия. `transcription/violin-v1/kukla-violins-2voices.mid` — 752 ноты (456/296), 148.6 BPM, render-frame +3.057926 с, без квантизации и pitch-bend. MIDI перечитан двумя библиотеками (ошибка сериализации <0.46 мс), просмотрены спектральные наложения, выполнен обратный синтез. Аудиогайд и source-left/MIDI-right для слуховой правки; 152 ноты отмечены менее уверенными, особенно тихая зона/финал. Статус — черновая транскрипция, не выверенная партитура и не готовый playback-layer. Сохранены рецепт, CSV, отчёт и инструкция импорта; обновлены страница песни и index.

## [2026-10-01] analysis | Кукла колдуна: громкость пользовательского pb-other

Найден `/Users/alex/Documents/kukla_kolduna_pb_other.mp3` (бэки/скрипки/гитары по описанию Alex). Измерены он и 26 текущих pb-other: новый −15.4 LUFS, −0.1 dBTP, активный stereo RMS −18.25; плотные музыкальные референсы около −17.6…−18.1 LUFS, старая Кукла −18.9. Рекомендован общий trim **−2.5 dB**: отдельный измерительный проход без сохранения аудио подтвердил −17.9 LUFS / −2.6 dBTP. Активные фрагменты остаются немного громче большинства выбранных музыкальных референсов. Результаты и рецепт в `Король и Шут - Кукла колдуна/analysis/2026-10-01-pb-other-loudness/`; исходник не правили и в playback пока не подключали.

## [2026-10-01] level | Кукла колдуна: пользовательский pb-other −2.5 dB

По просьбе Alex сохранён `/Users/alex/Documents/kukla_kolduna_pb_other_minus2p5dB.wav`: простой gain −2.5 dB, PCM 24 bit / 48 kHz stereo. Проверка готового файла: −17.9 LUFS, true peak −2.6 dBTP, длительность 206.784 с. Исходный MP3 сохранён, mix/риг ещё не обновлены.

## [2026-10-01] deploy | Кукла колдуна: пользовательский pb-other в проекте и риге

По просьбе Alex WAV −2.5 dB импортирован в `parts/kukla-pb-other-v1.wav`, закреплён как единственный render-layer pb-other в mix.json. В canonical WAV перенесена tempo-метка 148.6 при побайтно идентичном PCM; обновлена pb-other MP3-прослушка. Старая версия сохранена в `versions/2026-10-01-before-custom-pb-other/`. Sync изменил только `Кукла колдуна/pb-other.wav` в риге, SHA256 factory/риг совпал. Коммит `be489c2a` успешно запушен в `basbit/cherry-daddies-2000`, `origin/main`.

## [2026-10-01] import | Медведица: обновление файлов, две отдельные гитары

По просьбе Alex импортирован новый Moises ZIP с суффиксом `(1)` (MP3 48 kHz); после уточнения «только файлы» обновлены 8 музыкальных WAV и метроном в корне песни. `lead_guitars.wav` и `rhythm_guitars.wav` — отдельные проверенные партии. Подготовка прежним рецептом: 44.1 kHz stereo float, общий warp 130 BPM без питча; карта совпадает с прежней, все файлы по 235.721519 с, онсеты метронома отличаются максимум на один сэмпл. Сырьё/хеши/рецепт/проверка — `imports/moises-2026-10-01/`, прежние файлы — `versions/2026-10-01-before-stems-update/`. Web, auto-render и риг остаются на предыдущем импорте согласно выбранному объёму задачи.

## [2026-10-02] workflow | Самостоятельные lyrics, сохранение и доставка в риг

Полный репозиторий группы подключён к `alexomee/cherry-daddies-alex`, `tkozinets` приглашена с write-доступом. Добавлены AGENTS.md, русская памятка `docs/vocalist-workflow.md`, setup.command, локальная MLX/faster-whisper транскрипция, build/review/approve/check/save/deliver. Превью использует сценический ASS и реальные click/cues рига; хеши связывают подтверждение с исходниками и версией плейбека. «Сохрани» = проверенный commit/push сюда; «сохрани и отправь клавишнику» = также выбранная пара клипов и строка манифеста в риг. Доставка сохраняет чужие песни, проверяет удалённый source commit, обнаруживает устаревшее ревью и поддерживает повтор после отказа push. 44 теста, реальный mpv-рендер и транскрипция русского фрагмента прошли; доступ в приватный риг Тане должен выдать basbit. Новая песня требует проверки подключения MainStage; Push не равен Pull на ноуте клавишника. Основная реализация: `ab4fddd`.

## [2026-10-02] skill | tanya-texts: запуск Тани с нуля

По просьбе Alex добавлен repo-scoped скилл `.agents/skills/tanya-texts/SKILL.md` с UI-метаданными ChatGPT/Codex: настройка, два репо, JamZone/ASR, preview, человеческая проверка, save и deliver. `docs/tanya-start.md` обращается к Тане и содержит ссылки на оба приглашения и готовые сообщения агенту для клонирования и запуска скилла. Alex сообщил, что basbit уже отправил приглашение в риг; принятие и реальные write-права агент проверяет на её машине. Нативный вызов: `@` в ChatGPT, `$`/`/skills` в Codex; запрос `/tanya-texts` также описан в AGENTS.md, доступен прямой запуск по пути SKILL.md. YAML и локальные ссылки проверены.

## [2026-10-03] render | Я буду: бэк-вокал убран из всех шин плейбека

По запросу Alex `backing_vocals` исключён из всех шин в `music/songs/5sta Family & 23:45 - Я буду/mix.json`:
- `pb-other`: остался только `piano`;
- `pb-other-keys`: остались `piano`, `keys`, `other`.
Выполнен полный перерендер через `jamzone_render.py`: обновлены `pb-other.{wav,mp3}`, `pb-other-keys.{wav,mp3}`, `all.wav`, `cue_preview.mp3` и `web/songs.json`. Скорректированы страницы вики `wiki/songs/ya-budu.md` и `wiki/index.md`.

## [2026-10-03] workflow | Общая библиотека all.wav и превью Тани по одной песне

По согласованию Alex опубликованы 37 чистых WAV (1.406 ГБ) в существующем R2,
вне Git; проверены полным HTTP-скачиванием и SHA-256. Каталог версий/таймлайнов
в `music/guide-catalog.json`, публикация включена в `tools/sync_site.py` и
`--guides-only`. Workflow получает один guide и только выбранные sparse-файлы
рига, собирает полное вокальное review командой `preview NN`. Проверены
отпечатки 24/24 песен lyric-сетлиста; для clip 13 измерен реальный синхрон по
восстановленному сигналу (0 мс в начале/середине/конце). Обновлены скилл и
инструкции Intel Mac без Homebrew. Подтверждение текста остаётся за Таней,
сценический риг и доставка клипов не менялись. [Процесс и измерения](pipelines/lyric-guide-library.md).

## [2026-10-05] cues | Такая любовь: правка cue-сета (13 cue)

По запросу Alex обновлены подсказки в `music/songs/Такая любовь/mix.json`:
1. Стартовый cue bar 1.1 переведён в `Такая любовь synth fade-in ready go` (3.556 с, название в естественном темпе + блок из 4 слов «synth fade-in ready go» по долям такта 0);
2. Убран cue `strings in` (бывший bar 21);
3. Оба `drums in` переведены в `drum fill ready go` и сдвинуты на 1 такт раньше (bar 27 → 26 / 48.0 с и bar 68 → 67 / 120.9 с) под реальные барабанные сбивки перед входом грува;
4. Оба `solo in` заменены на `synth solo ready go` (bar 43 / 78.2 с и bar 84 / 151.1 с);
5. Убран cue `light drums` (бывший bar 59);
6. Стоп 2:45 (bar 92 / 165.3 с) заменён на `drum stop` («drum stop in 3 · 3 2 1») — останавливаются только барабаны, гитара и другие партии продолжают звучать;
7. `guitar in` заменён на `guitar solo ready go` на затакте соло (bar 93.4 / 168.4 с).
Всего 13 cue. Выполнен полный рендер (`jamzone_render.py`): обновлены `click.wav`, `cues.wav`, `all.wav`, `cue_preview.mp3`, `pb-*.wav`, practice-миксы и `web/songs.json`.

## [2026-10-05] render | Я буду: pb-other объединён с pb-other-keys, pb-other-keys удалён

По запросу Alex состав `pb-other` в `music/songs/5sta Family & 23:45 - Я буду/mix.json` изменён на `["piano", "keys", "other"]` (включены все клавиши и вступительный синт-хук), отдельная шина `pb-other-keys` удалена. Выполнен полный перерендер через `jamzone_render.py`: обновлены `pb-other.{wav,mp3}`, `all.wav`, `cue_preview.mp3`, `web/songs.json`. Файлы `pb-other-keys.*` удалены из `auto-render/` и из рига (`cherry-daddies-setlist-2026-06-16/Я буду/pb-other-keys.wav`), `pb-other.wav` скопирован в риг. Скорректированы страницы вики `wiki/songs/ya-budu.md` и `wiki/index.md`.

## [2026-10-05] import | Я буду: сборка pb-other из оригинальных стемов + караоке бэк-вокал (redacted)

По указанию Alex состав `pb-other` скомпонован заново:
- `backing_vocals`: взят `redacted`-вариант из караоке-минусовки, точно сфазирован с таймлайном оригинала (компенсированы задержка энкодера и смещение);
- `guitars`, `piano`, `keys`: возвращены из оригинального импорта (лучшее разделение);
- `other`: взят из оригинала и заглушен с 0:13 (13.0 сек);
- `bass`: взят из караоке-минусовки (скомпенсирован на 20 мс и отварплен под 90.0 BPM, глубокий суб-бас 30–80 Гц);
- `drums`, `metronome`, `vocals`: из оригинального импорта.

В `tools/jamzone/jamzone_render.py` убран баг подмешивания click/cues в `pb-*.mp3`. Выполнен переварп (`jamzone_warp_ext.py`) и полный рендер (`jamzone_render.py --practice`): `pb-other.{wav,mp3}`, `pb-bass.{wav,mp3}`, `all.wav`, practice-миксы и `web/songs.json` обновлены. В риг синхронизированы `pb-other.wav`, `pb-bass.wav`, `pb-drums.wav`. Скорректированы `wiki/songs/ya-budu.md` и `wiki/index.md`.

## [2026-10-06] web | Раздел «24.10 lefkara» для сборки нового плейлиста

По запросу Alex добавлен новый раздел/таб «24.10 lefkara» в веб-дашборд (`web/index.html` и `tools/setlist_dashboard.py`):
- Вкладка «24.10 lefkara» выведена первой в навигации с фиолетовым акцентом (`--lefkara:#9d5bf0`) и выставлена активной по умолчанию.
- Поддерживает отображение как единого списка (`cls: "lefkara"`), так и разбивки по сетам (`cls: "lefkara1"`, `"lefkara2"`).
- При пустом списке корректно выводится плейсхолдер «Плейлист пока пуст — собираем треки».
- Перегенерирован `web/songs.json`. Сетлист готов к наполнению треками.

## [2026-10-06] render | 24.10 Lefkara: импорт 5 JamZone-треков, pb-other, живой бас Ромы, стартовые cues

По предоставленному Alex списку из 10 песен проверена локальная библиотека JamZone:
- 5 песен скачаны в JamZone и полностью собраны:
  1. `Shocking Blue — Venus` (cat_12674, 128 BPM, `click: follow`): pb-other = Wurlitzer + Backing Vocals, стартовый cue `Venus guitar in ready go`.
  2. `Modern Talking — Cheri, Cheri Lady` (cat_37357, 114 BPM): pb-other = все синты, Orchestra Hit, Synth Brass, Synth Flute, Backing Vocals; стартовый cue `Cheri Cheri Lady all in ready go`.
  3. `Ricchi e Poveri — Sarà perché ti amo` (cat_18179, 120.6 BPM): pb-other = Piano, Synthesizer, Synth Pad, String Section; стартовый cue `Sarà perché ti amo all in ready go`.
  4. `Modern Talking — Brother Louie` (cat_38978, 109 BPM): pb-other = Piano, Synthesizer 1/2, Synth Pad, Synth Strings, Orchestra Hit, Synth Brass, Backing Vocals; стартовый cue `Brother Louie all in ready go`.
  5. `Donna Summer — Hot Stuff (12" Version)` (cat_5408, 120.3 BPM, `click: follow`): `03_Percussion` исключена (играет барабанщик), pb-other = Piano, Synthesizer, Synth Keys, Backing Vocals; стартовый cue `Hot Stuff all in ready go`.
- Для всех 5 песен: бас живой (`pb-bass: null`, Рома на бас-гитаре), сгенерированы `all.wav`, `cue_preview.mp3`, `pb-other.mp3`, `pb-drums.mp3`, practice-миксы на четверых и поканальные stems.
- 5 остальных песен добавлены в список сетлиста `24.10 Lefkara` (Heart of Glass, Ghostbusters, Stumblin' In, Sweet Dreams, Personal Jesus) в статусе ожидания загрузки/источников.
- `web/songs.json`, страницы `wiki/songs/`, `wiki/gigs/2026-10-24-lefkara.md` и `wiki/index.md` обновлены.

## [2026-10-06] render | 24.10 Lefkara: остальные 5 треков скачаны в JamZone и собраны на 100%

После докачки Alex недостающих треков в JamZone:
- Извлечены HQ-стемы, настроен `mix.json`, собраны starter cues и practice-миксы для оставшихся 5 песен:
  1. `Blondie — Heart of Glass` (cat_12447, ~114.7 BPM, `click: follow`): `03_Percussion` исключена, pb-other = Organ, Pad, Strings, Backing Vocals; стартовый cue `Heart of Glass all in ready go`.
  2. `Ray Parker Jr. — Ghostbusters` (cat_11300, 115 BPM): pb-other = Piano, Clavinet, синты (Strings, Keys 1/2, Lead, Brass), Brass section, Backing Vocals; стартовый cue `Ghostbusters all in ready go`.
  3. `Suzi Quatro & Chris Norman — Stumblin' In` (cat_22836, ~129.3 BPM, `click: follow`): `01_Intro_Count` отделен от основного `02_Click`, pb-other = Rhodes, String Section; стартовый cue `Stumblin In all in ready go`.
  4. `Eurythmics — Sweet Dreams (Are Made of This)` (cat_69124, ~125.2 BPM): `03_Percussion` исключена, pb-other = Noise effects, Piano, синты, Strings, Lead, Backing Vocals; стартовый cue `Sweet Dreams all in ready go`.
  5. `Depeche Mode — Personal Jesus` (cat_12804, 130 BPM): `03_Percussion` исключена, pb-other = Breath FX, Guitar Synth, Piano, Organ, Pad, Lead, Arp 1/2, Backing Vocals; стартовый cue `Personal Jesus all in ready go`.
- Для всех 10 песен сета: бас играет Рома (`pb-bass: null`), сформированы `auto-render` (all, cue_preview, pb-other, pb-drums, practice, stems).
- Все 10 песен в разделе `24.10 lefkara` на дашборде получили 10/10 готовность данных и полный интерактивный плеер.
- Созданы страницы в `wiki/songs/` для всех 10 песен, обновлены `wiki/gigs/2026-10-24-lefkara.md` и `wiki/index.md`.

## [2026-10-06] lyrics | 24.10 Lefkara: сценические тексты (клипы 34–43) для всех 10 песен

По запросу Alex созданы сценические тексты и видеоклипы для сценического вокального монитора:
- Сгенерированы сценические субтитры ASS с двухстрочным page-flip отображением (`clips/34.ass` .. `clips/43.ass`) и фоновые видео MP4 (`clips/34.mp4` .. `clips/43.mp4`).
- Экспортированы тайм-кодированные TSV-таблицы в `tools/lyric-launcher/lyrics-timed/34.tsv` .. `43.tsv` с точным смещением `offset_sec` под финальный таймлайн плейбека.
- В дуэтах (`Stumblin' In`, `Sarà perché ti amo`) учтены оба ведущих голоса.
- В `tools/lyric-launcher/songs.tsv` зарегистрированы 10 новых строк: клипы 34–43, Program Change 35–44.

## [2026-10-06] cues | Heart of Glass: фикс стартового кью + полный набор из 14 подсказок

По замечаниям и таймкодам Alex:
- **Причина раннего стартового кью:** в JamZone клике первый такт — прекаунт клика в тишине; барабаны и музыка на самом деле вступают на такте 2 (`bar 2.1`, 4.254 с). Стартовый cue переведён на `bar 2`: теперь «Heart of Glass all in ready go» идеально выровнен по входу барабанов.
- Настроены все запрошенные подсказки (всего 14 cue):
  - `bar 2.1` — `Heart of Glass all in ready go`
  - `bar 6.1` — `verse in ready go` (вход куплета 1)
  - `bar 14.1` — `keep going` (окончание куплета 1, сквозной ход к куплету 2)
  - `bar 17.1` — `verse in ready go` (куплет 2)
  - `bar 26.1` — `chorus in ready go` (припев 1)
  - `bar 38.1` — `verse in ready go` (куплет 3, ~1:21)
  - `bar 47.1` — `chorus in ready go` (припев 2, ~1:41)
  - `bar 55.1` — `instrumental with-beat-offset ready go` (инструментал с 2-долевым оффсетом)
  - `bar 70.2` — `voice in ready go` (вокал в бридже, ~2:29)
  - `bar 78.2` — `break in ready go` (брейк, ~2:46)
  - `bar 82.2` — `guitar in ready go` (гитара после брейка, ~2:54)
  - `bar 86.1` — `verse in ready go` (куплет 4, ~3:02)
  - `bar 95.1` — `chorus in ready go` (припев 3, ~3:21)
  - `bar 119.2` — `end in` (`count: true` → «end in 3 · 3 2 1», финал ~4:12).
- Выполнен перерендер: обновлены `all.wav`, `click.wav`, `cues.wav`, `cue_preview.mp3`, `pb-*.mp3`, practice-миксы и `web/songs.json`.
- Пересобран сценический lyric-клип 34 (`clips/34.ass`, `clips/34.mp4`, `lyrics-timed/34.tsv`) под новый таймлайн.

## [2026-10-06] cues | Heart of Glass: 5-дольный instrumental, точное выравнивание куплета 3:00 и припева 3:18

По замечаниям Alex:
1. `instrumental with-beat-offset ready go` развёрнут на 5 долей:
   - `instrumental`: 1 доля (доля -5)
   - `with-beat-offset`: 2 доли натуральным темпом без сжатия (доли -4 и -3)
   - `ready`: 1 доля (доля -2)
   - `go`: 1 доля (доля -1)
   В `jamzone_render.py` (`_metric_clips`) добавлена поддержка натурального многодолевого растяжения для длинных слов внутри фразы без агрессивного `_atempo` сжатия.
2. Куплет 4 (`verse in` около 3:00) сдвинут с доли 1 на долю 2 (`bar 86.2` = 180.564 с): точно под вход фразы «Once I had a love».
3. Припев 3 (`chorus in` около 3:18) сдвинут с доли 1 на долю 2 (`bar 95.2` = 199.394 с): точно под вход фразы «In between...».
4. Перерендер `all.wav`, `cue_preview.mp3`, `click.wav`, `cues.wav`, stems и `web/songs.json`.

## [2026-10-06] cues | Ghostbusters: добавлены 11 cue по сетке песни

По запросу Alex сформирован и добавлен полный набор cue для `Ray Parker Jr. — Ghostbusters`:
- `bar 1.1` (4.174s) — `Ghostbuster playback in` («Ghostbuster · playback in ready go»)
- `bar 2.1` (6.261s) — `guitar bass ready go` (вступление живой гитары и баса, 0:06)
- `bar 6.1` (14.609s) — `drums in` («drums in ready go», барабанный грув, 0:14)
- `bar 7.1` (16.696s) — `main in` («main in ready go», главная тема, 0:17)
- `bar 59.1` (125.217s) — `break-one in` («break-one in ready go», первый брейк, 2:05)
- `bar 75.1` (158.609s) — `break-two in` («break-two in ready go», второй брейк, 2:38)
- `bar 83.1` (175.304s) — `chorus in` («chorus in ready go», припев / главная тема, 2:55)
- `bar 103.1` (217.043s) — `keep going` (звучит на 3:36 перед новым 4-тактовым циклом)
- `bar 115.1` (242.087s) — `keep going` (звучит на 4:02 перед новым 4-тактовым циклом)
- `bar 123.1` (258.783s) — `keep going` (звучит на 4:18 перед новым 4-тактовым циклом)
- `bar 128.1` (269.217s) — `end in` («end in 3 · 3 2 1», финальный удар барабанов на 4:29)

Выполнен локальный рендер через `jamzone_render.py "Ghostbusters"`: обновлены `mix.json`, `click.wav`, `cues.wav`, `all.wav`, `cue_preview.mp3`, `pb-*.wav`, `pb-*.mp3`, `timeline.json` и `web/songs.json`.

## [2026-10-06] cues | Venus, Cheri Cheri Lady, Stumblin' In: обновление подсказок и обрезка интро Cheri

По запросу Alex обновлены cue и таймлайны трёх песен:
1. **Venus (Shocking Blue):**
   - Ранний стартовый cue на 1-м такте удалён.
   - `bar 9.1` (19.066s) — `Venus all in` («Venus · all in ready go», вступление банды).
   - `bar 13.1` (26.656s) — `verse in` («verse in ready go», вступление вокала на даунбит).
   - `bar 103.1` (195.666s = 3:15.7) — `end in` (`count: true` → «end in 3 · 3 2 1» на последний барабанный удар).
   - Зафиксирован `count_in: 2` для сохранения стабильного таймлайна (+3.450с).

2. **Cheri, Cheri Lady (Modern Talking):**
   - В `jamzone_render.py` добавлена поддержка `cut_bars`: физическая вырезка диапазона тактов из стемов и клика с de-click фейдами.
   - Вырезаны 4 вступительных такта флейты (`cut_bars: [2, 6]`), трек начинается сразу с главной темы клавиш:
     - `bar 2.1` (4.211s) — `Cheri Cheri Lady all in` («Cheri Cheri Lady · all in ready go» на вступление клавишной темы).
     - `bar 105.1` (221.053s = 3:41.1) — `end fill in` (`count: true` → «end fill in 3 · 3 2 1» под финальную сбивку барабанов).
   - Таймлайн сценических lyrics пересчитан под новый трек: `37.tsv` сдвинут на 5 тактов (-10.53с), перегенерированы `clips/37.ass` и `clips/37.mp4`.

3. **Stumblin' In (Suzi Quatro & Chris Norman):**
   - Добавлены 13 cue строго под вокал, соло и стопы барабанов:
     - `bar 1.3` (4.654s) — `Stumblin In vocal in` («Stumblin In · vocal in ready go» под вступление голосов на 3-й доле).
     - `bar 17.3` (34.414s) — `alex sing ready go` (вход Alex «Wherever you go»).
     - `bar 25.3` (49.214s) — `tanya sing ready go` (вход Tanya «I'm fallin' for you»).
     - `bar 37.2` (70.994s = 1:11.0) — `stop` («stop in 3 · 3 2 1» на стоп барабанов).
     - `bar 54.1` (102.094s = 1:42.1) — `guitar solo ready go` (гитарное соло).
     - `bar 61.3` (116.014s = 1:56.0) — `alex sing ready go` (Alex «You were so young»).
     - `bar 65.2` (123.034s = 2:03.0) — `tanya sing ready go` (Tanya «I may have been young»).
     - `bar 69.3` (130.914s = 2:10.9) — `alex sing ready go` (Alex «Well you were the one»).
     - `bar 81.2` (152.734s = 2:32.7) — `stop` («stop in 3 · 3 2 1» на стоп барабанов).
     - `bar 105.2` (197.314s = 3:17.3) — `alex sing ready go` (Alex «Oh stumblin' in»).
     - `bar 113.2` (212.154s = 3:32.2) — `tanya sing ready go` (Tanya «Oh stumblin' in»).
     - `bar 121.1` (226.494s = 3:46.5) — `tanya sasha sing go` (дуэт Tanya & Sasha).
     - `bar 128.1` (239.414s = 3:59.4) — `end in` (`count: true` → «end in 3 · 3 2 1» на финальный удар).

Выполнены рендеры всех трёх песен в `auto-render/` (`all.wav`, `click.wav`, `cues.wav`, `cue_preview.mp3`, `pb-*.wav`, `pb-*.mp3`), обновлён `web/songs.json`.

## [2026-10-06] cues | Sarà perché ti amo, Sweet Dreams, Personal Jesus, Brother Louie, Hot Stuff: фикс ранних стартовых cue и добавление "end in 3 2 1"

По замечаниям Alex обновлены стартовые и финальные кью для 5 песен сетлиста Lefkara:

1. **Ricchi e Poveri — Sarà perché ti amo:**
   - Стартовый cue перенесён с `bar 1` на `bar 3.1` (3.978s): `Sarà perché ti amo all in` («Sarà perché ti amo · all in ready go»); 2 такта precount теперь корректно содержат объявление и отсчёт перед вступлением всей банды на такте 3.
   - Добавлен финальный cue на последний барабанный удар: `bar 91.2` (179.520s) — `end in` (`count: true` → «end in 3 · 3 2 1»).

2. **Eurythmics — Sweet Dreams (Are Made of This):**
   - Стартовый cue перенесён с `bar 1` на `bar 3.1` (3.834s): `Sweet Dreams all in` («Sweet Dreams · all in ready go»); музыка вступает на такте 3 после 2 тактов precount.
   - Добавлен финальный cue на последний барабанный удар: `bar 113.1` (214.709s) — `end in` (`count: true` → «end in 3 · 3 2 1»).

3. **Depeche Mode — Personal Jesus:**
   - Стартовый cue перенесён с `bar 1` на `bar 3.1` (3.692s) и заменён на гитару: `Personal Jesus guitar in` («Personal Jesus · guitar in ready go») — вступление гитары на такте 3 после 2 тактов precount.
   - Добавлен финальный cue на последний барабанный удар перед клавишным хвостом: `bar 117.4` (215.538s) — `end in` (`count: true` → «end in 3 · 3 2 1»).

4. **Modern Talking — Brother Louie:**
   - Стартовый cue перенесён с `bar 1.1` на первую ноту клавиш `bar 1.3` (3.303s): `Brother Louie playback in` («Brother Louie · playback in ready go»); автоматически добавлен 1 такт count-in lead, чтобы фраза чисто отзвучала перед нотой.
   - Добавлен финальный cue на orchestra hit и финальный удар барабанов: `bar 105.4` (232.844s) — `end in` (`count: true` → «end in 3 · 3 2 1»).

5. **Donna Summer — Hot Stuff (12" Version):**
   - Стартовый cue перенесён с `bar 1` на `bar 2.1` (4.114s): `Hot Stuff all in` («Hot Stuff · all in ready go»); вся банда вступает на такте 2 (lead +1 такт count-in для чистого звучания).
   - Добавлен финальный cue на последний барабанный удар: `bar 160.1` (319.254s) — `end in` (`count: true` → «end in 3 · 3 2 1»).

Для всех 5 песен выполнен локальный рендер через `jamzone_render.py` (`mix.json`, `all.wav`, `click.wav`, `cues.wav`, `cue_preview.mp3`, `pb-*.wav`, `pb-*.mp3`, `timeline.json`), актуализирован `web/songs.json`.

## [2026-10-07] fix | Stumblin' In: стартовый cue сдвинут на «&» (bar 1 beat 2&, 4.419s)

- В `jamzone_render.py` добавлена поддержка дробных долей `beat: 2.5` и `"2&"` (парсинг `_parse_beat`, формат отображения `_disp_beat`).
- **Синкопированный вход:** вокальная фраза «Our love is alive» начинается со слова «Our» на синкопе 2& (4.419s). Чтобы подсказка звучала в том же синкопированном ритме и приходила точно в долю:
  - `vocal` на 2& прекаунта (2.55s)
  - `in` на 3& прекаунта (3.02s)
  - `ready` на 4& прекаунта (3.48s)
  - `go` на 1& такта 1 (3.95s)
  - ровно через 1 долю (на 2&, 4.419s) чисто и в ритме вступает голос: «Our» (2&) → «love» (доля 3, 4.65s).
- **Стопы барабанов (bar 37 и 81):** оба cue были сдвинуты на 1 долю позже (`beat 2`). Исправлено на `bar 37 beat 1` (70.514s) и `bar 81 beat 1` (152.254s) — отсчёт «3 2 1» теперь звучит на долях 2, 3, 4 предыдущего такта, и стоп приходится точно на сильную долю 1.
- **Гитарное соло (bar 53):** соло начиналось на `bar 53 beat 3` (во время прежнего «ready»), а cue целился в `bar 54 beat 1`. Cue перенесён на `bar 53 beat 3` (101.174s) — теперь «ready» на 53.1, «go» на 53.2, и соло начинается ровно на следующей доле после «go».
- Выполнен перерендер `jamzone_render.py`, обновлены `auto-render/*`, `mix.json`, `web/songs.json`, `wiki/songs/stumblin-in.md`.

## [2026-10-07] web | Добавлен сет «07.10 rehearsal» (10 песен) в веб-дашборд

- По запросу Alex сформирован репетиционный список на 7 октября 2026:
  1. `Smells Like Teen Spirit — Nirvana` (черновой слот без папки / hasData: false)
  2. `Кукла колдуна — Король и Шут`
  3. `Pretty Fly (For A White Guy) — The Offspring`
  4. `Rock & Roll Queen — The Subways`
  5. `Heads Will Roll — Yeah Yeah Yeahs`
  6. `I Love It — Icona Pop`
  7. `Медведица — Мумий Тролль`
  8. `Мелом — Пропаганда`
  9. `Я сошла с ума — ТАТУ`
  10. `Мама Люба — SEREBRO`
- Создана выделенная вкладка «07.10 rehearsal» в `web/index.html` с акцентным цветом `--rehearsal:#38bdf8`.
- В `tools/setlist_dashboard.py` добавлен блок сета `07.10 rehearsal`, перегенерирован `web/songs.json`.
- Существующие заметки и todo для всех 9 готовых треков сохранены и подтянуты по `sid` без дублирования.
- Создана страница `wiki/gigs/2026-10-07-rehearsal.md`, обновлён `wiki/index.md`.

## [2026-10-07] cues | Sarà perché ti amo: финальный cue перенесён на такт 91.1 ("end fill in 3 · 3 2 1")

- Финальный cue перенесён с `bar 91.2` (179.520s, последний удар) на 1 долю раньше: `bar 91.1` (179.023s = 2:59.02).
- Текст изменён на `end fill in` (`count: true` → «end fill in 3 · 3 2 1»):
  - Анонс «end fill in 3» звучит в конце такта 89 / начале такта 90 (~2:56.2 – 2:57.1s).
  - Отсчёт «3» (2:57.5s, такт 90.2), «2» (2:58.0s, такт 90.3), «1» (2:58.5s, такт 90.4) звучит во время барабанной сбивки.
  - На 2:59.02s (такт 91.1) отсчёт завершён, и точно в долю звучат три финальных акцента keys: «pa pa pa» (такт 91 доли 1, 1-и, 2 с финальным крэшем).
- Выполнен перерендер `jamzone_render.py` (`mix.json`, `cues.wav`, `cue_preview.mp3`, `all.wav`, стемы), обновлены `web/songs.json`, `wiki/index.md`, `wiki/songs/sara-perche-ti-amo.md`, `wiki/gigs/2026-10-24-lefkara.md`.

## [2026-10-07] cues | Brother Louie: финальный cue перенесён на такт 105.3 ("end fill in 3 · 3 2 1")

- Финальный cue перенесён с `bar 105.4` (232.844s) на 1 долю раньше: `bar 105.3` (232.294s = 3:52.29).
- Текст изменён на `end fill in` (`count: true` → «end fill in 3 · 3 2 1»):
  - Анонс «end fill in 3» звучит в конце такта 104 (~3:49.3 – 3:50.2s).
  - Отсчёт «3» (3:50.6s, такт 104.4), «2» (3:51.2s, такт 105.1), «1» (3:51.7s, такт 105.2).
  - На 232.294s (такт 105.3) отсчёт завершён, и точно в долю звучат финальные удары orchestra hit / барабанов (такт 105 доли 3 и 4).
- Выполнен перерендер `jamzone_render.py` (`mix.json`, `cues.wav`, `cue_preview.mp3`, `all.wav`, стемы), обновлены `web/songs.json`, `wiki/index.md`, `wiki/songs/brother-louie.md`, `wiki/gigs/2026-10-24-lefkara.md`.

## [2026-10-07] level | Кукла колдуна: замена pb-other на более громкий рендер v2 без трима

На репетиции выяснилось, что предыдущая версия с тримом −2.5 dB (−17.9 LUFS) звучала слишком тихо.
По запросу Alex получен новый файл `/Users/alex/Downloads/кукла колдуна other.mp3` (Logic Pro bounce, 48 kHz / 320 kbps stereo, 206.784 с).
- **Уровни:** −14.9 LUFS-I, −0.1 dBTP, активный stereo RMS −18.22 dBFS, mono −19.19 dBFS, LRA 8.6 LU (на ~3 dB громче прежнего v1).
- **Тайминг:** точное посемпловое совпадение с v1 (лаг 0 мс, 9 925 632 семплов при 48 kHz).
- **Пайплайн:** файл импортирован в `parts/kukla-pb-other-v2.wav` (PCM 24 bit / 48 kHz stereo); в `mix.json` обновлена привязка на `kukla-pb-other-v2`. В canonical `auto-render/pb-other.wav` добавлена tempo-метка 148.6 (SHA256: `95220a9f10812855e9a3ff2c672638f8fb60280f1d1d9713761d6416b5c7b7fa`). Обновлена прослушка `auto-render/pb-other.mp3` (pb-other + click + cues) и `web/songs.json`.
- Предыдущая версия сохранена в `versions/2026-10-07-before-louder-pb-other/`.
- Выполнен `sync_to_mainstage.sh --apply "Кукла колдуна"`: обновлён `pb-other.wav` в риге `cherry-daddies-2000`.

## [2026-10-07] ingest | Smells Like Teen Spirit: базовый плейбек (intro cue + click) из JamZone

- По запросу Alex подготовлен базовый плейбек для репетиции (`07.10 rehearsal`).
- Исходник: JamZone **cat_11775**, 13 HQ M4A-стемов распакованы через `jamzone_extract.py`.
- **Сетка и темп:** в оригинальной дорожке темп интро ~110–111 BPM, с такта 5 (вход барабанов) ускоряется до ~117.6 BPM. Использован `"click": "follow"` (BPM 118.0) — рендер следует реальной сетке клика с максимальной ошибкой <4.2 мс.
- **Плейбек:** базовый живой состав (`pb-other: null`, `pb-bass: null`). Стволы распределены по игрокам в `players`: Alex (все электрогитары), Roma (бас), Steve (барабаны), Tanya (вокал).
- **Cue:** 1 стартовая подсказка `bar 2.1` (4.221s) — `"Smells Like Teen Spirit guitar in"`:
  - Lead-такт 0 (0.00–2.03s, JZ count-in сэмплы клика): название песни **«Smells Like Teen Spirit»** в естественном темпе.
  - Такт 1 (2.03–4.22s, прекаунт JamZone): слова **«guitar in ready go»** точно на долях клика.
  - Такт 2.1 (4.221s): вступает гитарный рифф Курта Кобейна (`05_Electric_Guitar_(intro)`).
- Выполнен рендер через `jamzone_render.py` с флагом `--practice`: сгенерированы `all.wav`, `click.wav`, `cues.wav`, `cue_preview.mp3`, `timeline.json`, раздельные mp3 в `stems/`, а также practice-миксы для всех 4 участников.
- Обновлён `tools/setlist_dashboard.py` (привязка к папке `Nirvana - Smells Like Teen Spirit`), перегенерирован `web/songs.json` (57/57 песен с данными, hasData: true).
- Создана страница `wiki/songs/nirvana-smells-like-teen-spirit.md`, обновлены `wiki/gigs/2026-10-07-rehearsal.md` и `wiki/index.md`.
