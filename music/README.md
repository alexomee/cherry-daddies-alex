# Музыкальный пайплайн — JamZone / стемы / cue

Канонический дом музыкальной подготовки. Скрипты: `../tools/jamzone/` (перенесены из скила `jamzone-stems`; скил теперь ссылается сюда). Симлинк совместимости: `~/Desktop/jamzone-stems` → `music/songs/`.

```
music/
├── songs/<Artist - Title>/   ← по папке на песню (стемы + производные)
│   ├── NN_<Stem>.m4a         ← сырые стемы из JamZone (нативные песни)
│   ├── structure.txt          ← секции песни
│   ├── chart.txt              ← аккорды+структура (jamzone_chart)
│   ├── cues.json              ← редактируемые подсказки
│   ├── cue_track.wav          ← рендер cue-трека
│   ├── <click>.wav            ← клик
│   ├── logic-render/          ← БAUНСЫ ИЗ LOGIC под StageTraxx (см. ниже):
│   │   └── click.mp3 · cues.mp3 · pb-other.mp3 · [pb-bass.mp3] · [all.mp3]
│   └── aligned/ + *-{stem}-…  ← внешние (Moises) песни: выровненные стемы
├── songs/jz_beat.wav, jz_downbeat.wav   ← сэмплы клика (используют click/cues_ext)
├── songs/.loudness_cache.json, .realm-*.bak ← артефакты normalize/setlist (не трогать)
├── setlists/                  ← сет-листы и лирика (booklet из jamzone-lyrics)
├── SONGS.md                   ← СТАТУС-БОРД: что готово, что делать
└── README.md                  ← этот файл
```

## Пайплайн на песню (порядок)

| # | Этап | Команда (из `tools/jamzone/`) | Результат |
|---|---|---|---|
| 1 | Извлечь стемы | `python3 jamzone_extract.py "<запрос>"` (или `--cat cat_N`) | `NN_*.m4a` + `structure.txt` |
| 2 | Чарт | `python3 jamzone_chart.py "<запрос>"` | `chart.txt` (потом руками докурировать) |
| 3 | Громкость | `python3 jamzone_normalize.py …` | per-song master (НЕ per-stem); сначала выставить мьюты, применять по требованию |
| 4 | Cue-трек ЧЕРНОВИК (нативная) | `python3 jamzone_cues.py "<песня>"` | `cues.json` + `cue_track.wav` (+ `--audition` прослушка) |
| 4' | Cue-трек (внешняя/Moises) | `python3 jamzone_cues_ext.py …` | detect + matched click (см. скил-док) |
| 5 | **Кьюрация cue** (вручную) | правка `cues.json` / в Logic → ре-рендер | финальные метки/тайминг (см. правила ниже) |
| 6 | **Бounce в Logic** | вручную в Logic → `logic-render/*.mp3` | click·cues·pb-other·[pb-bass]·[all] (см. ниже) |
| 7 | **Загрузка в StageTraxx** | `python3 stagetraxx_render.py "<песня>" --playlist "Cherry Daddies"` | песня в ST с роутингом Rubix24 |
| — | Сет-лист JamZone в облаке (опц.) | `python3 jamzone_setlist.py …` | reorder/rename (cloud-only, token capture) |

> Старый `jamzone_stagetraxx.py` (заливал ВСЕ стемы + cue, pan R) — устарел для дуо-сетапа; используем `stagetraxx_render.py` (4 канала из Logic).

**🔑 Cue — первичны, и автоген = только ЧЕРНОВИК.** Всегда сначала доводим cue (вручную в Logic + прослушка), и только потом всё ниже по пайплайну (нормализация/экспорт/StageTraxx). `jamzone_cues.py`/`_ext` дают стартовый черновик, не финал.

**Правило счёта:** каждый вход = **«<label> ready go»** — слова метки + «ready» + «go», по слову на долю, часть вступает **на долю ПОСЛЕ «go»**. Метка «<что вступает> in»: `verse/chorus/bridge/outro in`, `all in` (тутти), `synth in` (лид-инструмент), `soft chorus` (тихий). Числовой «3 2 1» только у **END** и **STOP**: «end in»/«stop in» + «3 2 1». **Старт:** название песни + «<что реально вступает> ready go» (vocal in — только если песня с вокала; иначе all in / synth in). **Истина = клик:** вход cue всегда снапится к ближайшему реальному клику (`T=nclick`), DAW-метка — ориентир. Черновик генератора = «<caption секции> in» (старт: vocal in/all in); человек уточняет, убирает лишние, ретаймит. `count_style: readygo|321`.

Стадии готовности: стемы → структура/чарт → **cue доведён+отслушан** → бounce в Logic → выгружено в StageTraxx. «Готово к репетиции» ≥ cue отслушан; «готово полностью» = в StageTraxx.

## Logic-бounce + StageTraxx (финальная стадия)

**Бounce из Logic → `<song>/logic-render/`** (все из абсолютного 0 до конца, ОДИН диапазон → сэмпл-в-сэмпл синхрон, одинаковая длина):
- `click.mp3` — клик
- `cues.mp3` — голосовые подсказки (доведённый cue из Logic)
- `pb-other.mp3` — плейбек-минус: всё, что НЕ играется живьём и не бас
- `pb-bass.mp3` — бас (ОПЦИОНАЛЬНО; для песен, где бас играешь живьём синтгитарой-слоем — НЕ баунсить, ch4 пуст)
- `all.mp3` — полный микс (ОПЦИОНАЛЬНО; чтобы послушать всю песню в ST; грузится **muted**)

**Загрузка:** `python3 stagetraxx_render.py "<песня>" --playlist "Cherry Daddies"` (ST должен быть ЗАКРЫТ — скрипт его гасит). Что делает:
- роутинг под Rubix24, ОДИН трек на дискретный выход (в ST это bus=стерео-пара + pan L/R):

  | выход | трек | bus | pan | по умолч. |
  |---|---|---|---|---|
  | ch1 | Click | 0 | −1 | вкл |
  | ch2 | Cues | 0 | +1 | вкл |
  | ch3 | PB Other | 1 | −1 | вкл |
  | ch4 | PB Bass | 1 | +1 | вкл |
  | ch3 | **All** | 1 | −1 | **muted** (как PB Other) |

- метроном OFF, всё unmuted кроме All; чтобы послушать всю песню — анмьют All + мьют PB Other (тот же ch3).
- **регионы = структура JamZone** (`structure.json`: Intro/Verse/Chorus/Bridge/Outro), НЕ метки cue (кьюшки живут на аудио-дорожке Cues). Для внешних песен — fallback на cues.json.
- плейлист «Cherry Daddies».

## Известные грабли (из боевого опыта)

1. **Clickgrid-баг (исправлен 10.06.2026):** старый `jamzone_cues.py` масштабировал время кликов на +0.227% → счёт «3-2-1» уезжал до полудоли к ~1:46. **Все нативные cue-треки, отрендеренные ДО фикса, требуют ре-рендера**: `jamzone_cues.py "<песня>"` без `--regen` (cues.json сохраняется, пересобирается только рендер). Список — в SONGS.md. Внешний `jamzone_cues_ext.py` не был подвержен.
2. **Тайм-привязка:** нативные треки — song-time = Logic-time − 1ч, без lead-офсета; внешние (Moises) несут lead. `click_grid` декодировать на 44.1k.
3. **Нормализация** — мастер на песню, не на стем; mute-конфиг до применения.
4. **Сет-листы JamZone — только в облаке**; правки через `jamzone_setlist.py` + перехват токена.
5. Пути в скриптах захардкожены на `~/projects/cherry-daddies/music/songs` (обновлены при переезде 11.06.2026).
6. **Мастер StageTraxx −21 dB** — это ГЛОБАЛЬНАЯ настройка приложения `audio_masterVolumeOffset` в `~/Library/Containers/de.dikant.StageTraxx4/Data/Library/Preferences/de.dikant.StageTraxx4.plist`, общая для всех песен, НЕ из загрузчика (он пишет все громкости на 0 dB unity). Чинится мастер-фейдером в ST.
7. **Дискретные выходы Rubix24** в ST адресуются через `bus` (стерео-пара) + `pan` (L/−1 = нечётный канал, R/+1 = чётный): bus0→1-2, bus1→3-4. Если ST нумерует/маппит выходы иначе — поправить таблицу ROUTING в `stagetraxx_render.py`.
8. **Cue-генератор:** вокальный вход детектится по ВСЕМ вокальным стемам (вкл. бэк-вокал — открывающий «na-na» в S&M = backing, а lead вступает позже); `song_mix` берёт только `NN_` стемы (иначе подмешивает прошлые превью → наложения); скорость счёта масштабируется от bpm (слово влезает в долю).

## Подготовка к репетиции (рабочий цикл)

1. Открыть `SONGS.md`, выбрать 2–4 песни на репетицию (колонка «Действие»).
2. Догнать пайплайн по каждой (см. таблицу этапов).
3. **Отслушать cue** (`--audition`) — не пропускать, см. список неотслушанных.
4. Отметить статус в SONGS.md, собрать сет в StageTraxx.
