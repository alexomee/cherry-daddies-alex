// Offline copy of the stage page ONLY (stage.html is self-contained and open without the password).
// The worker is registered from /stage.html at the site root, so it controls every page of the origin; it must not
// touch anything else: the board (index.html, songs.json, ...) is behind basic auth, and a fetch re-issued from the
// worker goes out WITHOUT the browser's saved credentials (mobile Chrome, 2026-11-21: songs.json -> 401, the board
// showed «не удалось загрузить songs.json», and the old worker cached the 401). v4 drops the v3 cache with those 401s.
const CACHE = 'stage-28-oct-v4';
const STAGE = '/stage.html';
self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll([STAGE])));
  self.skipWaiting();
});
self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});
self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);
  if (url.origin !== self.location.origin || url.pathname !== STAGE) return;   // everything else: the browser's own fetch
  e.respondWith(
    fetch(e.request).then(res => {
      if (res.ok) {
        const clone = res.clone();
        caches.open(CACHE).then(c => c.put(e.request, clone));
      }
      return res;
    }).catch(() => caches.match(e.request))
  );
});
