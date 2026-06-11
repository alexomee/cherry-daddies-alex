# Статус-борд песен — концерт 26.06.2026

Обновлено: 11.06.2026 (после миграции в репо). Легенда: ✅ есть · ⚠️ требует действия · ❌ нет · 🌐 внешняя (Moises), 🎛 нативная (JamZone).

⭐ = заявлена в афише/анонсе концерта.

| Песня | Тип | Стемы | Структ | Cue | Действие |
|---|---|---|---|---|---|
| ⭐ Alex Gaudino — Destination Calabria | 🎛 | ✅ 9 | ✅ | ⚠️ до-фикса | **Ре-рендер cue** + отслушать |
| ⭐ Cascada — Everytime We Touch | 🎛 | ✅ 14 | ✅ | ❌ | Сделать cue |
| ⭐ Guru Josh — Infinity 2008 | 🎛 | ✅ 10 | ❌ | ❌ | Извлечь structure → cue |
| ⭐ Laurent Wolf — No Stress | 🎛 | ✅ 7 | ✅ | ⚠️ до-фикса | **Ре-рендер cue** + отслушать (конец 3:19.22) |
| ⭐ Rihanna — S&M | 🎛 | ✅ 13 | ✅ | ⚠️ до-фикса | **Ре-рендер cue** + отслушать (конец 4:02.18 ок) |
| ⭐ Rihanna — We Found Love | 🎛 | ✅ 12 | ✅ | ❌ | Сделать cue |
| ⭐ Shakira — Whenever, Wherever | 🎛 | ✅ 14 | ✅ | ⚠️ до-фикса | **Ре-рендер cue** + отслушать |
| ⭐ Yeah Yeah Yeahs — Heads Will Roll | 🎛 | ✅ 13 | ✅ | ⚠️ до-фикса | **Ре-рендер cue** + отслушать (cat_23443, не A-Trak) |
| ⭐ Band'Eros — Pro krasivuju zhizn' | 🌐 | ✅ aligned | — | ✅ | Ок (ext не задет багом) |
| ⭐ Quest Pistols — Я устал | 🌐 | ✅ aligned | — | ✅ | **Отслушать** (старт + bass-окончание, медл. секция ~1:45–2:00) |
| ⭐ SEREBRO — ??? | — | ❌ | ❌ | ❌ | **ПЕСНИ НЕТ ВООБЩЕ** — выбрать трек, извлечь/Moises |
| A Touch of Class — Around the World | 🎛 | ✅ 15 | ✅ | ⚠️ до-фикса | Ре-рендер + отслушать (конец руками 3:37.12) |
| Alexandra Stan — Mr. Saxobeat | 🎛 | ✅ 15 | ✅ | ✅ после фикса | Отслушан в работе 10.06; контрольно прослушать |
| Alice Deejay — Better Off Alone | 🎛 | ✅ 12 | ✅ | ⚠️ до-фикса | Ре-рендер + отслушать |
| Basshunter — Now You're Gone | 🎛 | ✅ 10 | ✅ | ❌ | Сделать cue |
| Beverly Hills (Weezer) | 🌐 | ✅ aligned | — | ✅ 11.06 | **Отслушать** (свежий, ext) |
| Gala — Freed from Desire | 🎛 | ✅ 11 | ✅ | ⚠️ до-фикса | Ре-рендер + отслушать (cat_30111 club) |
| Icona Pop & Charli XCX — I Love It | 🎛 | ✅ 12 | ✅ | ⚠️ до-фикса | Ре-рендер + отслушать (cat_43230) |
| The Weeknd — Blinding Lights | 🎛 | ✅ 13 | ✅ | ⚠️ до-фикса | Ре-рендер + отслушать; **решить конец**: fade 3:20.62 vs последний барабан 3:08 |
| Karen Souza — Every Breath You Take | 🎛 | ❌ (только chart) | ❌ | ❌ | Если нужна в сете — re-extract |
| Yann Muller — Just the Two of Us | 🎛 | ✅ 6 | ✅ | ❌ | Лаунж-версия — вероятно не для этого сета? Решить |

## Батчи (по убыванию приоритета)

1. **Ре-рендер 10 нативных cue до-фикса** (clickgrid-баг): ATC, Destination Calabria, Alice Deejay, Gala, Icona Pop, No Stress, S&M, Shakira, Blinding Lights, Heads Will Roll — `jamzone_cues.py "<песня>"` (cues.json сохраняется). Один батч ~10 мин.
2. **SEREBRO** — единственная заявленная песня без материала. Выбрать трек (Song #1 / Мама Люба?), искать в JamZone, иначе Moises-путь.
3. **Cue с нуля:** Cascada, We Found Love, Basshunter, Infinity 2008 (этой — сначала structure).
4. **Сессия прослушки** всех ⚠️/неотслушанных cue (`--audition`) — после ре-рендера, чтобы слушать один раз.
5. Решения: конец Blinding Lights; судьба Yann Muller и Karen Souza.

## План по репетициям

Шаблон: на каждую репетицию — 3–4 песни доведённые до «готово» (cue отслушан + громкость). Вписывать сюда даты репетиций и закреплённые песни:

| Дата репетиции | Песни | Готовность |
|---|---|---|
| _(заполнить)_ | | |
