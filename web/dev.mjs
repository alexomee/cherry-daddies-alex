// Local dev server: serves static files from web/ and routes /api/state to the
// same handler logic used in production (api/state.js). Uses node:sqlite locally.
//   node dev.mjs      (needs Node >= 22.5; you have 24)
import http from "node:http";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { getState, putState } from "./api/state.js";

const ROOT = path.dirname(fileURLToPath(import.meta.url));
const PORT = process.env.PORT || 5173;
const MIME = {
  ".html": "text/html; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".svg": "image/svg+xml",
};

function send(res, code, body, ct = "text/plain; charset=utf-8") {
  res.statusCode = code;
  res.setHeader("content-type", ct);
  res.end(body);
}

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, "http://localhost");

  if (url.pathname === "/api/state") {
    try {
      if (req.method === "GET") {
        send(res, 200, JSON.stringify(await getState()), MIME[".json"]);
      } else if (req.method === "PUT" || req.method === "POST") {
        let raw = "";
        for await (const chunk of req) raw += chunk;
        await putState(raw ? JSON.parse(raw) : {});
        send(res, 200, JSON.stringify({ ok: true }), MIME[".json"]);
      } else {
        send(res, 405, JSON.stringify({ error: "method not allowed" }), MIME[".json"]);
      }
    } catch (e) {
      send(res, 500, JSON.stringify({ error: String((e && e.message) || e) }), MIME[".json"]);
    }
    return;
  }

  // static files
  const rel = url.pathname === "/" ? "/index.html" : url.pathname;
  const fp = path.join(ROOT, decodeURIComponent(rel));
  if (!fp.startsWith(ROOT)) return send(res, 403, "forbidden");
  try {
    const buf = await readFile(fp);
    send(res, 200, buf, MIME[path.extname(fp)] || "application/octet-stream");
  } catch {
    send(res, 404, "not found");
  }
});

server.listen(PORT, () => console.log(`dev dashboard → http://localhost:${PORT}`));
