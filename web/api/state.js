// Backend for the setlist dashboard. One endpoint, whole-state document.
//   GET  /api/state        -> { global:[...], songs:{ sid:{notes,todos} } }
//   PUT  /api/state  body=^ -> { ok:true }   (last-write-wins)
//
// Storage adapter, chosen at runtime:
//   - DATABASE_URL set  -> Neon Postgres (prod, e.g. on Vercel)
//   - else              -> local SQLite file via built-in node:sqlite (dev)
//
// Exported helpers getState/putState are reused by the local dev server (dev.mjs).
import { fileURLToPath } from "node:url";
import { mkdirSync } from "node:fs";
import path from "node:path";

const DEFAULT_STATE = { global: [], songs: {} };

function normalize(s) {
  s = s || {};
  return {
    global: Array.isArray(s.global) ? s.global : [],
    songs: s.songs && typeof s.songs === "object" && !Array.isArray(s.songs) ? s.songs : {},
  };
}

let _backend = null;
function backend() {
  if (_backend) return _backend;
  _backend = process.env.DATABASE_URL ? neonBackend() : sqliteBackend();
  return _backend;
}

// ---- Neon (Postgres) ----
function neonBackend() {
  let sqlPromise = null;
  async function sql() {
    if (!sqlPromise) {
      sqlPromise = (async () => {
        const { neon } = await import("@neondatabase/serverless");
        const q = neon(process.env.DATABASE_URL);
        await q`CREATE TABLE IF NOT EXISTS app_state (id INT PRIMARY KEY, data JSONB NOT NULL)`;
        return q;
      })();
    }
    return sqlPromise;
  }
  return {
    async get() {
      const q = await sql();
      const rows = await q`SELECT data FROM app_state WHERE id = 1`;
      return rows.length ? normalize(rows[0].data) : { ...DEFAULT_STATE };
    },
    async put(state) {
      const q = await sql();
      const json = JSON.stringify(normalize(state));
      await q`INSERT INTO app_state (id, data) VALUES (1, ${json}::jsonb)
              ON CONFLICT (id) DO UPDATE SET data = EXCLUDED.data`;
    },
  };
}

// ---- SQLite (local dev, zero npm deps via node:sqlite) ----
function sqliteBackend() {
  let dbPromise = null;
  async function db() {
    if (!dbPromise) {
      dbPromise = (async () => {
        const { DatabaseSync } = await import("node:sqlite");
        const file =
          process.env.SQLITE_PATH ||
          fileURLToPath(new URL("../data/dashboard.db", import.meta.url));
        mkdirSync(path.dirname(file), { recursive: true });
        const d = new DatabaseSync(file);
        d.exec("CREATE TABLE IF NOT EXISTS app_state (id INTEGER PRIMARY KEY, data TEXT NOT NULL)");
        return d;
      })();
    }
    return dbPromise;
  }
  return {
    async get() {
      const d = await db();
      const row = d.prepare("SELECT data FROM app_state WHERE id = 1").get();
      return row ? normalize(JSON.parse(row.data)) : { ...DEFAULT_STATE };
    },
    async put(state) {
      const d = await db();
      const json = JSON.stringify(normalize(state));
      d.prepare(
        "INSERT INTO app_state (id, data) VALUES (1, ?) " +
          "ON CONFLICT(id) DO UPDATE SET data = excluded.data"
      ).run(json);
    },
  };
}

export async function getState() {
  return backend().get();
}
export async function putState(state) {
  return backend().put(state);
}

async function readBody(req) {
  if (req.body && typeof req.body === "object") return req.body;
  if (typeof req.body === "string" && req.body) return JSON.parse(req.body);
  let raw = "";
  for await (const chunk of req) raw += chunk;
  return raw ? JSON.parse(raw) : {};
}

// Vercel Node serverless handler.
export default async function handler(req, res) {
  res.setHeader("content-type", "application/json; charset=utf-8");
  try {
    if (req.method === "GET") {
      res.end(JSON.stringify(await getState()));
    } else if (req.method === "PUT" || req.method === "POST") {
      await putState(await readBody(req));
      res.end(JSON.stringify({ ok: true }));
    } else {
      res.statusCode = 405;
      res.end(JSON.stringify({ error: "method not allowed" }));
    }
  } catch (e) {
    res.statusCode = 500;
    res.end(JSON.stringify({ error: String((e && e.message) || e) }));
  }
}
