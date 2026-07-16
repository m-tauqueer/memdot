/* Memdot service worker — ADR-0013 public/static assets only. */
const CACHE = "memdot-shell-v1";
const PRECACHE = ["/manifest.webmanifest", "/icon.svg"];

function mayCache(pathname) {
  if (pathname.startsWith("/api/")) {
    return false;
  }
  if (pathname.startsWith("/_next/static/")) {
    return true;
  }
  return PRECACHE.includes(pathname) || pathname === "/sw.js";
}

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches
      .open(CACHE)
      .then((cache) => cache.addAll(PRECACHE))
      .then(() => {
        /* Do not skipWaiting immediately — wait for client safe point (FSD-OFF-007). */
      }),
  );
  self.clients.matchAll({ type: "window" }).then((clients) => {
    for (const client of clients) {
      client.postMessage({ type: "MEMDOT_SW_UPDATE_READY" });
    }
  });
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(keys.filter((key) => key !== CACHE).map((key) => caches.delete(key))),
      ),
  );
  self.clients.claim();
});

self.addEventListener("message", (event) => {
  if (event.data?.type === "MEMDOT_SKIP_WAITING") {
    self.skipWaiting();
  }
});

self.addEventListener("fetch", (event) => {
  const { request } = event;
  if (request.method !== "GET") {
    return;
  }
  const url = new URL(request.url);
  if (url.origin !== self.location.origin) {
    return;
  }
  if (!mayCache(url.pathname)) {
    return;
  }
  event.respondWith(
    caches.match(request).then((cached) => {
      const network = fetch(request)
        .then((response) => {
          if (response.ok) {
            const copy = response.clone();
            void caches.open(CACHE).then((cache) => cache.put(request, copy));
          }
          return response;
        })
        .catch(() => cached);
      return cached || network;
    }),
  );
});
