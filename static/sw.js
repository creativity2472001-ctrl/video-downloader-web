const CACHE_NAME = 'EasyDown-v1';
const ASSETS = [
  '/',
  '/static/logo.png',
  '/static/manifest.json',
  '/templates/index.html',
  '/static/icons/icon-192.png',
  '/static/icons/icon-512.png'
];

// 1. التثبيت: حفظ ملفات الواجهة الأساسية
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(ASSETS);
    })
  );
  self.skipWaiting();
});

// 2. التفعيل: تنظيف الكاش القديم فوراً
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
      );
    })
  );
  self.clients.claim();
});

// 3. معالجة الطلبات: استثناء التحميلات + نظام الشبكة أولاً للواجهة
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // استثناء التحميلات المهمة من الكاش
  if (url.pathname.includes('/download') || url.pathname.includes('/files/')) {
    return;
  }

  event.respondWith(
    fetch(event.request)
      .then((res) => {
        // تحديث الكاش تلقائياً عند كل طلب ناجح
        const resClone = res.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(event.request, resClone));
        return res;
      })
      .catch(() => caches.match(event.request)) // في حال انقطاع الإنترنت
  );
});
