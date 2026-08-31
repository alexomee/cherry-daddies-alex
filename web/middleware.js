// Basic HTTP auth for the DEPLOYED board (Vercel Routing Middleware, edge runtime).
// Runs before the cache on every request → index.html, songs.json, cue-lab/, lyric-review/.
// Local dev (dev.mjs) does NOT go through this file — localhost stays open.
//
// Creds: BASIC_AUTH_USER / BASIC_AUTH_PASS env vars on Vercel, else the defaults below.

const USER = process.env.BASIC_AUTH_USER || "cherry";
const PASS = process.env.BASIC_AUTH_PASS || "lovetospooch";
const REALM = 'Basic realm="Cherry & Daddies", charset="UTF-8"';

// constant-time-ish compare (no early return on first differing byte)
function eq(a, b) {
  if (typeof a !== "string" || typeof b !== "string") return false;
  let diff = a.length ^ b.length;
  const n = Math.max(a.length, b.length);
  for (let i = 0; i < n; i++) diff |= (a.charCodeAt(i) || 0) ^ (b.charCodeAt(i) || 0);
  return diff === 0;
}

function authorized(request) {
  const header = request.headers.get("authorization") || "";
  const sp = header.indexOf(" ");
  if (sp < 0) return false;
  if (header.slice(0, sp).toLowerCase() !== "basic") return false;
  let decoded;
  try {
    decoded = atob(header.slice(sp + 1).trim());
  } catch {
    return false;
  }
  const i = decoded.indexOf(":");
  if (i < 0) return false;
  return eq(decoded.slice(0, i), USER) && eq(decoded.slice(i + 1), PASS);
}

export default function middleware(request) {
  if (authorized(request)) return; // no response = pass through to the static asset

  return new Response("401 — Cherry & Daddies: authentication required\n", {
    status: 401,
    headers: {
      "WWW-Authenticate": REALM,
      "content-type": "text/plain; charset=utf-8",
      "cache-control": "no-store, must-revalidate",
    },
  });
}

export const config = {
  runtime: "edge",
  matcher: "/(.*)",
};
