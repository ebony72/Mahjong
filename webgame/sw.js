/* Offline cache for the PWA build. Precaches the app shell + engine sources
   at install time (so a second visit works fully offline); Pyodide's own
   CDN runtime files are cached opportunistically the first time they're
   fetched (they're versioned/immutable URLs, safe to cache indefinitely).
   Bump CACHE_NAME whenever any precached file's content changes. */
const CACHE_NAME = 'xuezhan-pwa-v3';

const APP_SHELL = [
  './app.html', './style.css', './game.js', './transport_pyodide.js',
  './worker.js', './manifest.webmanifest',
  './icons/icon-192.png', './icons/icon-512.png', './icons/icon-180.png',
  // Python sources the worker fetches into its virtual filesystem
  '../dfncy/block_dfncy.py', '../hytreekong.py', '../strategy_defense.py',
  '../strategy_huev.py', '../strategy_initial21_7attr.py', '../strategyz0614.py',
  '../utils/constants.py', '../utils/daque.py', '../utils/hutype.py',
  '../utils/hysolx.py', '../utils/pusolx.py', '../utils/xzcard.py',
  '../utils/xzscore.py', '../utils/xzutils.py',
  '../xzdealer.py', '../xzjudger.py', '../xzplayer.py', '../xzround.py',
  './game_core.py', './pwa_bridge.py',
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(APP_SHELL))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then(names =>
      Promise.all(names.filter(n => n !== CACHE_NAME).map(n => caches.delete(n)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  if(event.request.method !== 'GET') return;
  event.respondWith(
    caches.match(event.request).then(cached => {
      if(cached) return cached;
      return fetch(event.request).then(resp => {
        if(resp && resp.ok){
          const copy = resp.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(event.request, copy));
        }
        return resp;
      }).catch(() => cached);
    })
  );
});
