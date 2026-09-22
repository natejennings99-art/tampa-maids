/* Tampa Maids Cleaning service worker.
   App shell is cached so the app opens instantly and still works offline;
   API calls are network-first with a cache fallback so a crew member in a
   basement or a client on bad LTE still sees their last-known jobs. */
// Bump this on every rebrand or shell change: it invalidates the cached app
// shell on phones that already installed the app, so they pick up the new
// name, icons and markup on next launch instead of serving stale files.
const VERSION = 'tm-v2';
const SHELL = 'shell-' + VERSION;
const DATA = 'data-' + VERSION;

const SHELL_FILES = [
  '/app/', '/app/index.html', '/app/app.css', '/app/app.js',
  '/app/manifest.webmanifest', '/js/api.js',
  '/icons/icon-192.png', '/icons/icon-512.png', '/icons/favicon.svg',
];

self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(SHELL)
      .then(c => Promise.allSettled(SHELL_FILES.map(f => c.add(f))))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(
        keys.filter(k => !k.endsWith(VERSION)).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', e => {
  const { request } = e;
  if (request.method !== 'GET') return;                 // never cache writes
  const url = new URL(request.url);
  if (url.origin !== location.origin) return;

  if (url.pathname.startsWith('/api/')) {
    // network-first, fall back to the last good response
    e.respondWith(
      fetch(request)
        .then(res => {
          const copy = res.clone();
          caches.open(DATA).then(c => c.put(request, copy));
          return res;
        })
        .catch(() => caches.match(request).then(hit => hit || new Response(
          JSON.stringify({ error: "You're offline. Showing the last data we had." }),
          { status: 503, headers: { 'Content-Type': 'application/json' } })))
    );
    return;
  }

  // shell: cache-first, refresh in the background
  e.respondWith(
    caches.match(request).then(hit => {
      const net = fetch(request).then(res => {
        if (res.ok) caches.open(SHELL).then(c => c.put(request, res.clone()));
        return res;
      }).catch(() => hit);
      return hit || net;
    })
  );
});
