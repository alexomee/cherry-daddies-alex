# Cherry & Daddies — рабочее пространство

Универсальный хаб группы **Cherry & Daddies** (кавер-бэнд, Кипр): креативы/промо **и** музыкальная подготовка (стемы, cue-треки, сет-листы).
Ближайшая веха: концерт **26 июня** — IG-кампания (`docs/plans/`, `content-calendar.md`) + доводка треков к репетициям (`music/SONGS.md`).

## Работа через ChatGPT / тексты на сцену

GitHub этого **полного** рабочего репозитория: [alexomee/cherry-daddies-alex](https://github.com/alexomee/cherry-daddies-alex).
Начало для Тани и агента: **[памятка по lyrics и сохранению](docs/vocalist-workflow.md)**,
инструкции агенту — [`AGENTS.md`](AGENTS.md), установка на Mac —
`tools/lyric-launcher/setup.command`.

«Сохрани» → проверка + commit/push сюда. «Сохрани и отправь клавишнику» → также
проверенная доставка выбранного клипа в [сценический риг](https://github.com/basbit/cherry-daddies-2000).
JamZone даёт готовые тексты/тайминги; для других песен есть локальная транскрипция
и обязательное превью. Аудио, исключённое `.gitignore`, передаётся отдельно.

---

## Группа

- **Название:** Cherry & Daddies (Cherries & Daddies) — International Party Band, Cyprus
- **Instagram:** [@cherry_and_daddies](https://www.instagram.com/cherry_and_daddies) — 286 подписчиков, 76 постов (на 11.06.2026)
- **Участники:**
  - 🎤 Вокал — Татьяна, [@tatiana__kozinets](https://instagram.com/tatiana__kozinets)
  - 🎸 Гитара — Алекс, [@alexome_](https://instagram.com/alexome_)
  - 🥁 Барабаны — Стив, [@stevechewitt](https://instagram.com/stevechewitt)
  - 🎹 Клавиши — Бас, [@basklass](https://instagram.com/basklass)

## Ближайший концерт

- **Событие:** Cherry & Daddies — 2000s Dance REVOLUTION
- **Дата/время:** 26 июня, 20:00
- **Площадка:** MUSIC HALL Limassol, Georgiou A' 89A, Potamos Germasogeias, 4046
- **Билеты:** от €15 — [Radario](https://lims.radario.ru/events/2721879/tickets#event/2721879)
- **Афтепати:** караоке
- **Посты-события:** [archives/775](https://cherrydaddies.com/archives/775) · [archives/725](https://cherrydaddies.com/archives/725)

## Музыка / сет

Евродэнс и клубные хиты 2000–2010-х. Узнаваемые синты, ностальгия «тех, кому сейчас ~30».

- **Международное:** Rihanna, Shakira, Heads Will Roll, Infinity 2008, Everytime We Touch, No Stress, Destination Calabria
- **CIS/ностальгия:** SEREBRO, Quest Pistols, Band'Eros

---

## Структура воркспейса

```
cherry-daddies/
├── README.md                 ← этот файл (факты, ссылки, индекс ассетов)
├── content-calendar.md       ← 15-дневный план постов + черновики подписей
├── docs/plans/               ← дизайн-доки стратегии и план продакшена
├── assets/                   ← КРЕАТИВ: готовое к публикации
│   ├── posters/              ← афиши (cherry-daddies гранж / neon-2000s)
│   ├── video/                ← 9:16 синемаграфы (15с)
│   └── stories/              ← шаблоны и нарезки под сторис
├── temp-assets/              ← креатив: черновики, исходники, AI-итерации
├── music/                    ← МУЗЫКА: подготовка треков (см. music/README.md)
│   ├── songs/                ← по папке на песню: стемы, structure, chart, cue (1.8 ГБ, вне git)
│   ├── setlists/             ← сет-листы + лирика
│   ├── youtube/              ← загрузки с YouTube (`tools/yt-download.sh`, вне git)
│   └── SONGS.md              ← статус-борд: что готово / что делать к репетициям
└── tools/jamzone/            ← канонические скрипты пайплайна (extract/chart/normalize/click/cues/setlist/stagetraxx)
```

> Симлинк совместимости: `~/Desktop/jamzone-stems` → `music/songs/`. Скил `jamzone-stems` ссылается на `tools/jamzone/`.

## Индекс ассетов (готовое)

| Файл | Что это |
|---|---|
| `assets/posters/cherry-daddies/cd_EN_landscape.*` | Брендовая афиша, EN, горизонт (бэнд справа) |
| `assets/posters/cherry-daddies/cd_RU_landscape.*` | Брендовая афиша, RU, горизонт (тот же дизайн, 5K) |
| `assets/posters/cherry-daddies/cd_RU_landscape_mirror.*` | RU, зеркало (бэнд слева) — для красивой пары в ленте рядом с EN |
| `assets/posters/neon-2000s/neon_{RU,EN}.*` | Альт-афиша в неон-стиле «2000s dance hits» |
| `assets/video/cinemagraph_9x16_*.mp4` | Вертикальные синемаграфы 15с (silent / под Band'Eros / под Infinity 2008) |
| `temp-assets/source/band_photo_real_6k.png` | Реальное фото группы (исходник для лиц) |

## Бренд-заметки

- **Визуальный стиль:** гранж-стикербомб «вишни» — циан + розовый (маджента), рваная бумага, логотип CHERRY DADDIES с вишнями. Это шаблон-«скин» для всех графических постов и сторис.
- **Язык:** подписи двуязычные — сначала RU-блок, ниже EN-блок (разделитель). Текст на видео — короткий/универсальный.
- **Альт-стиль** «неон 2000s» держим как запасной/разнообразящий, основной — гранж «вишни».

## Памятка по генерации ассетов (Higgsfield)

См. память `higgsfield-image-edit`. Кратко: модель `nano_banana_2` (Nano Banana Pro); смену языка/композиции делать ОДНИМ проходом из ИСХОДНИКА (не редактировать уже отредактированное — портит лица); фейс-свопы — `kling_omni_image`; всегда проверять текст по кропам.
