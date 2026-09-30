/* Retired root service worker — self-destruct.
   An early build registered a service worker at /sw.js for the whole site and
   served marketing pages cache-first, so returning visitors saw new HTML with
   stale CSS after a deploy. Browsers that still have it fetch this file on their
   next update check; it clears the old caches, unregisters itself and reloads
   open pages from the network. The phone app keeps its own worker at /app/sw.js
   (scope /app/), which re-caches its shell on next launch.
   Safe to delete this file once no browsers are expected to hold the old worker. */
self.addEventListener('install', () => self.skipWaiting());

self.addEventListener('activate', event => {
  event.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys.map(k => caches.delete(k)));
    await self.registration.unregister();
    const clients = await self.clients.matchAll({ type: 'window' });
    clients.forEach(c => c.navigate(c.url));
  })());
});
