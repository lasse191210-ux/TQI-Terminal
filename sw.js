/* TQI Terminal Service Worker: Netzwerk zuerst (immer aktuell), Cache nur als Offline-Rückfall. Börsendaten werden nie abgefangen. */
const C = "tqi-v2";
const CORE = ["./", "./index.html", "./manifest.webmanifest", "./icons/icon-192.png", "./icons/icon-512.png", "./icons/apple-touch-icon.png"];
self.addEventListener("install", e => { e.waitUntil(caches.open(C).then(c => c.addAll(CORE)).then(() => self.skipWaiting())); });
self.addEventListener("activate", e => { e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== C).map(k => caches.delete(k)))).then(() => self.clients.claim())); });
self.addEventListener("fetch", e => {
  const u = new URL(e.request.url);
  if (e.request.method !== "GET" || u.origin !== self.location.origin) return;
  const req = (e.request.mode === "navigate" || /\.html$|\/$|\.json$/.test(u.pathname)) ? new Request(e.request, { cache: "no-store" }) : e.request;
  e.respondWith(fetch(req).then(r => { if (r && r.ok) { const cp = r.clone(); caches.open(C).then(c => c.put(e.request, cp)); } return r; })
    .catch(() => caches.match(e.request).then(r => r || caches.match("./index.html"))));
});
