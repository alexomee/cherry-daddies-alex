# Cherry Daddies — дашборд сетлиста

Интерактивная доска: сетлист со статусом плейбека (Cues / bass / pb-other из `mix.json`)
плюс редактируемые todo и заметки. Данные пользователя хранятся в БД на сервере
(общие для всех), справочные данные песен — в `songs.json`.

## Структура

- `index.html` — страница (рендерит из `songs.json`, тянет/пишет `/api/state`).
- `songs.json` — справочные данные песен. **Генерируется**, не править руками.
- `api/state.js` — бэкенд (одна функция). Хранилище выбирается на рантайме:
  - есть `DATABASE_URL` → **Neon Postgres** (прод);
  - нет → локальный **SQLite** (`data/dashboard.db`, через встроенный `node:sqlite`).
- `dev.mjs` — локальный dev-сервер (статика + `/api/state`).

## Локально

```bash
# 1) перегенерировать данные песен после правок mix.json
python3 ../tools/setlist_dashboard.py     # пишет web/songs.json

# 2) поднять дашборд (Node >= 22.5; нужен встроенный node:sqlite)
cd web
npm install        # ставит @neondatabase/serverless (для прода)
npm run dev        # → http://localhost:5173
```

Локальные правки todo/заметок лежат в `web/data/dashboard.db` (в .gitignore).

## Хостинг на Vercel + Neon

1. Создать БД в Neon, скопировать connection string.
2. В Vercel: проект из этого репо, **Root Directory = `web`**.
3. Env var `DATABASE_URL` = строка Neon (для Production и Preview).
4. Deploy. `api/state.js` сам создаст таблицу `app_state` при первом запросе.

Тот же код, что локально: при наличии `DATABASE_URL` адаптер уходит в Postgres,
переписывать ничего не нужно. После правок `mix.json` — перегенерировать
`songs.json` и задеплоить заново.

## Модель данных

Один документ: `{ global: [{id,text,done}], songs: { <sid>: {notes, todos:[...]} } }`.
`<sid>` = имя папки песни (или `NOFOLDER:<title>`). GET отдаёт весь документ,
PUT перезаписывает (last-write-wins). Для редкого совместного редактирования ок;
если понадобится — позже разнести на строки и слать PATCH.
