---
type: pipeline
updated: 2026-10-02
status: production
---

# lyric-launcher — тексты на сценический монитор

## Самостоятельная работа вокалистки (2026-10-02)

Полный основной репозиторий опубликован как `alexomee/cherry-daddies-alex`.
Актуальные команды: [docs/vocalist-workflow.md](../../docs/vocalist-workflow.md),
инструкции агенту: [AGENTS.md](../../AGENTS.md). `transcribe_lyrics.py` получает
черновой текст/таймкоды из аудио без API-ключа; JamZone использует свои tiles.
`lyric_workflow.py`: sync → build → review → approve → save → deliver.
Preview подмешивает реальные click/cues рига к playback-frame guide. Хеши
связывают проверку с исходниками, клипом и версией аудио рига.

Репозиторный скилл [tanya-texts](../../.agents/skills/tanya-texts/SKILL.md) знает
весь процесс и ведёт Таню по одному шагу. [Старт с нуля](../../docs/tanya-start.md)
содержит принятие обоих приглашений, готовый запрос агенту на клонирование
репозиториев и запуск скилла. Приглашение в риг basbit уже отправил по сообщению Alex.

**Изменение deploy:** `deploy_clips.sh --index NN` — dry-run,
`--index NN --apply` — выбранный клип + строка манифеста + provenance, commit/push
в риг. Предыдущие примеры голого `deploy_clips.sh` ниже исторические.
«Сохрани» отправляет основной репо; «сохрани и отправь клавишнику» — также риг.
Новая песня требует отдельной проверки MIDI-подключения в актуальном концерте.

Синхронные тексты песни на сценический монитор, гонятся с ноута клавишника (MainStage). Без второго GUI-приложения и без лицензий: один постоянный `mpv` в фуллскрине на дисплее 2 (замучен, звук банды остаётся в MainStage), который по MIDI переключает пред-рендеренные клипы. В продакшене с 2026-06-18.

Клавишник — мастер плейбека (см. [mainstage-rig](mainstage-rig.md)); лирик-монитор идёт с той же машины тем же жестом, что и старт бэкинга.

## Два репозитория: фабрика и риг

Пайплайн размазан по ДВУМ репам — это ключевое:

- **Фабрика** — `tools/lyric-launcher/` В ЭТОМ репо (`cherry-daddies`): генераторы клипов, манифест, скрипт проводки концерта, review-видео. Здесь всё собирается.
- **Риг** — `~/projects/cherry-daddies-2000/lyrics/`: рантайм на ноуте клавишника (`launcher.py`, `.command`-бутстрапы, готовые клипы, `songs.tsv`) + проводенный `2000.concert`. Полная картина рантайма — в `cherry-daddies-2000/lyrics/README.md`.

Деплой клипов фабрика→риг — `tools/lyric-launcher/deploy_clips.sh` (копирует `clips/NN.{mp4,ass}` + `songs.tsv`; `.concert` НЕ трогает). План хендовера: `docs/plans/2026-06-18-lyric-launcher-handover.md` (+ `-design.md`).

## Как работает

```
MainStage патч/пэд --MIDI PC--> launcher.py --IPC--> mpv (фуллскрин на мониторе)
                                     |
                                     +-- грузит clips/NN.mp4 (поверхность = часы)
                                     +-- цепляет clips/NN.ass (тайминг строк, libass рендерит вживую)
```

`NN` = номер сета = номер клипа. `mpv` цепляет `.ass` как субтитр-трек и рисует его СВОЕЙ libass — текст остаётся редактируемым субтитром, слова меняются без переэнкода. Почему субтитры, а не burn-in: локальный `ffmpeg` — урезанный билд без `drawtext`/subtitle-фильтров, а `mpv` несёт libass.

Синхронизация внутри песни = клип пред-рендерен на таймлайне песни; и аудио, и лирик-клип — линейная медиа на одной машине, дрейфа нет. Тайтность = насколько точно триггер сработал к старту плейбека. Обязательное условие: темп патча MainStage = bpm песни, иначе бэд/арпы и клип разъезжаются.

## Четыре типа клипов (`source`)

`build_manifest.py` авто-классифицирует каждую песню по тому, какой файл лирики существует (это же задаёт проводку и review-видео). На 2026-07-10 в `songs.tsv`: 18 `jamzone`, 5 `dynamic`, 1 `static` (manual — без клипа).

- **`jamzone`** — timed-караоке из JamZone `tiles.json` (`make_song_clip.py`, текущая+следующая строка, сдвиг на `offset_sec` из `timeline.json`). См. [jamzone-render](jamzone-render.md).
- **`dynamic`** — force-aligned timed-клип из `lyrics-timed/NN.tsv` (`make_song_clip.py --lines`). Не-JamZone, но ВСЁ РАВНО timed/караоке — это русские песни (Солнышко, Про красивую жизнь, Мало тебя, Я устал) + Beverly Hills. НЕ static: несёт `factory_dir`, review-видео берёт реальный клип. (Русские сделаны честно dynamic — не путать со static.)
- **`static`** — полный текст на экране из `lyrics-manual/NN.txt` (`make_static_clip.py` + `fetch_lyrics.py`, колонки, повторы → `×N`). Только Мелом (сет 23). На arm показывает весь текст, E1 не нужен.
- **`manual`** — клипа ещё нет → НЕ проводится.

`wire_concert.py` проводит `jamzone|static|dynamic`; `--check` валидирует все четыре.

### Генератор-гочи (`make_song_clip.py`)

- **Дуэт.** JamZone-тайлы хранят лирику по цвету голоса. Дуэт (t.A.T.u. «Я сошла с ума» — оранжевый + зелёный) делит куплеты по цветам, но припевы поёт В УНИСОН → старый одноцветный `lead_color()` ронял целый куплет. Фикс `lead_words()`: мержит каждый цвет с ≥50% слогов самого «занятого» цвета, дедупит одновременные одинаковые слова (унисон-припевы). Одноголосые песни не меняются.
- **Одно-словные вспышки.** JamZone пере-сегментирует, `group_lines` рвёт экран на каждом слове с заглавной → короткие слова мигают <2с. `pack_lines()` мержит однословный экран <2с ВПЕРЁД до ≥2 слов; `collapse_letter_runs()` сворачивает спелл-чант (S&M «S S S M M M» → «S&M»). Только для jamzone-пути (не `--lines`). Было 106 вспышек на 11 песнях → 0.

## MIDI-триггер (сохраняет флоу клавишника)

- **PC на смене сета ARMит клип** (заголовок, пауза).
- Пэд **E1** (Play/Stop экшн глобального транспорта) шлёт MIDI **Start/Stop** → launcher ROLLит с 0 / фризит. Тот же жест стартует и Playback-плагин — тексты и бэкинг стартуют вместе.
- Static-клипы показывают весь текст на arm (E1 не нужен).

### MainStage НЕ отдаёт позицию плейхеда — scrub невозможен (доказано, не пере-обсуждать)

- Нет **Song Position Pointer** — scrub/seek невидим.
- Кнопка Playback Play не эмитит MIDI.
- MIDI-clock свободно бежит на темпе концерта независимо от play/stop — бесполезен для детекта транспорта.
- Нативный дисплей (Parameter Text по Current Marker Name) авто-масштабирует шрифт и абревиатит длинные строки — годен для короткого тега секции, не для полной строки.

Полный scrub-aware sync требовал бы настоящего clock-мастера (Ableton); QLab-как-мастер отвергнут (не может клочить арпы). Поэтому — детерминированный arm/roll + free-run.

## Виртуальный порт + порядок запуска

- Порт = виртуальный **`LyricLauncher`** (one-way CoreMIDI-destination), со **стабильным uniqueID `0x4C595243`** — launcher форсит его, иначе MainStage теряет привязку на каждом рестарте.
- **НЕ IAC** (loopback → петля PC / фантомное пианино играющей клавы).
- **Launcher запускать ДО MainStage** — порт существует только пока launcher жив.
- Триггеры launcher'а: PC N → клип NN, PC 0 → reset на заголовок; опц. GO/STOP-ноты. Музыкальная клавиатура игнорируется.

## Проводка концерта — `wire_concert.py`

Добавляет `Lyrics.cst` External-Instrument-страйп в бинарный `data.plist` каждого сета (idempotent, только на КОПИИ, MainStage закрыт). Маппинг сетов — из `web/songs.json` (позиция в `sets[].songs[]` = номер сета), НЕ из имён папок; `build_manifest.py` → `songs.tsv` (set·clip·pc·source·cat·factory_dir·bed_dir·concert_patch). Все 24 сета проводены (вкл. t.A.T.u. + Мелом, 2026-06-20).

Проводка = добавить строку в `channels` `data.plist`: `Channel_MIDIOutputPort` (DICT, `.name`==`LyricLauncher` + uniqueID), `programChangeNumber`=клип (UI-поле «Send Program Change» = clip+1, 1-based). Проверить провод: `Channel_MIDIOutputPort.name`==LyricLauncher + `programChangeNumber` + `Channel_outputIndex`==-1 через `/usr/bin/python3` plistlib (3.14 сломан).

### Регрессия-гард: НЕ затирать ручной фикс клавишника

Дефолтно Lyrics-страйп — полнодиапазонный ИГРАЕМЫЙ слой на первой клаве (Akai): перехватывает игру и флудит LyricLauncher. Клавишник (Роман) правит это руками per-set и коммитит в риг (`3e08d78 fix layer lirics`). Фикс в ДВУХ местах:

- **`data.plist`:** `Channel_outputIndex = -1` (No Output).
- **Диапазон клавиш слоя живёт в проприетарном OCuA-блобе `Lyrics.cst`, НЕ в `data.plist`** (проверено на 2149 патчах — ни одного key-range поля в plist). После save MainStage пере-авторит `.cst` каждого сета уникально (свой UUID).

Won't-happen-again фикс (`82fe78b` в фабрике): `wire_concert.py` владеет ТОЛЬКО MIDI-проводкой PC. Он (1) НИКОГДА не перезаписывает существующий `.cst` (`--force-cst` чтобы силой), (2) на апдейте трогает только output-port/PC-поля, (3) рождает новый страйп No-Output и сидит его `.cst` из уже-фикснутого сета-донора, (4) `no_output_fix()` двигает страйп только К `-1`, никогда назад. **Повторный прогон по фикснутому концерту = полный no-op** (deep-diff пустой, все `.cst` побайтно те же). Тест: `tools/lyric-launcher/tests/test_wire_preserves_fix.py`.

### MainStage-save молча РЕВЕРТИТ проводку (рецидив)

Если клавишник открывает НЕ-проводенный концерт, редактирует (напр. добавляет бас), сохраняет → MainStage пере-сериализует ~470 файлов из загруженного состояния и ВЫКИДЫВАЕТ любой Lyrics-страйп, которого в том состоянии нет (страйп t.A.T.u. убили save-ы клавишника). Симптом: «тексты не показываются после апдейта клавишника». Фикс — пере-провести поверх ПОСЛЕДНЕГО origin/main: `build_manifest.py` → `wire_concert.py` на свежей копии живого концерта → применить ТОЛЬКО затронутые `<patch>/data.plist`(+`Lyrics.cst`) → коммит → fetch/rebase/push (бинарник → rebase, не merge). **Профилактика: клавишник должен PULL проводенный концерт ДО открытия MainStage.**

pb-рендеры ([sync_to_mainstage.sh](mainstage-rig.md), wav-only) и деплой клипов (`deploy_clips.sh`) `.concert` НЕ трогают → реверта там нет.

## Лирика русских / не-JamZone песен

WebFetch/summarizer ОТКАЗЫВАЕТ (copyright) → брать `tools/lyric-launcher/fetch_lyrics.py` (curl + extract сырого HTML), чистить, класть в `lyrics-manual/NN.txt` (static) или таймить в `lyrics-timed/NN.tsv` (dynamic).

## Вокалистский review-флоу (без Mac)

`make_review_video.py "<song>"` жжёт `NN.ass` поверх music+click+cues микса (cue_preview-рецепт, cues **+3 dB**, peak-norm −1 dBFS) + бегущий M:SS-таймкод. Вся сетлиста как один нумерованный сет → `auto-render/<NN>-lyric-review.mp4`, шарится телефоном. Вокалистка смотрит реальный Now/Next-дисплей в синхроне, отвечает по мессенджеру с таймкодом; правки → в `time<TAB>line` TSV (= `--lines` формат) → пересборка клипа → ре-рендер. Sign-off клип И ЕСТЬ сценический (`deploy_clips.sh`). Рендер — через `mpv` (у homebrew-ffmpeg нет libass/drawtext). `--fit-audio` после trailing-silence trim (перегенерит чёрный canvas под обрезанную длину, `.ass`-тайминг не трогает). Дизайн: `docs/plans/2026-06-19-lyric-flow-review-design.md`.

## См. также

- [mainstage-rig](mainstage-rig.md) — боевой концерт, playback, `sync_to_mainstage.sh`
- [jamzone-render](jamzone-render.md) — источник `tiles.json` / `offset_sec`
- [cue-system](cue-system.md) — cue в review-миксе
