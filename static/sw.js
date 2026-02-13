const CACHE_NAME = 'easydown-cache-v1';
const ASSETS = [
  '/',
  '/index.html',
  '/manifest.json',
  '/static/logo.png',
  '/static/logo-apple.png',
  '/static/icons/screenshot1.png',
  '/static/style.css',   // إذا لديك CSS خارجي
  '/static/app.js'       // إذا لديك JS خارجي
];

// 1️⃣ التثبيت: حفظ ملفات الواجهة الأساسية
self.addEventListener('install', (event) => {
  console.log('[SW] Installing...');
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS))
  );
  self.skipWaiting();
});

// 2️⃣ التفعيل: تنظيف الكاش القديم فوراً
self.addEventListener('activate', (event) => {
  console.log('[SW] Activating...');
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.filter((key) => key !== CACHE_NAME)
            .map((key) => caches.delete(key))
      );
    })
  );
  self.clients.claim();
});

// 3️⃣ معالجة الطلبات: شبكة أولاً، كاش كاحتياطي
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // استثناء روابط التنزيل من الكاش
  if (url.pathname.includes('/download') || url.pathname.includes('/files/')) {
    return;
  }

  event.respondWith(
    fetch(event.request)
      .then((res) => {
        const resClone = res.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(event.request, resClone));
        return res;
      })
      .catch(() => {
        return caches.match(event.request).then((cachedRes) => {
          if (cachedRes) return cachedRes;
          // Offline fallback: عرض index.html عند طلب صفحة
          if (event.request.destination === 'document') {
            return caches.match('/index.html');
          }
        });
      })
  );
});
