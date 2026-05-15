const CACHE_NAME = 'asl-app-v4';
const urlsToCache = [
  '/',
  '/static/css/style.css',
  '/static/pwa/icon-192x192.png',
  '/static/pwa/icon-512x512.png'
];

// تثبيت وتشغيل الـ service worker
self.addEventListener('install', (event) => {
  console.log('SW: تم التثبيت');
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        return cache.addAll(urlsToCache).catch(err => {
          console.error('فشل في تحميل:', err);
        });
      })
  );
});

self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request)
      .then((response) => {
        return response || fetch(event.request);
      })
  );
});