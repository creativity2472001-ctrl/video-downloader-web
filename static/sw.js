const CACHE_NAME = 'EasyDown-v1';
const ASSETS = [
  '/',
  '/static/logo.png',
  '/static/manifest.json'
];

// 1. التثبيت: حفظ ملفات الواجهة فقط
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(ASSETS);
    })
  );
  self.skipWaiting();
});

// 2. التفعيل: تنظيف الإصدارات القديمة
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

// 3. معالجة الطلبات: ضمان عمل مشغل الفيديو (مثل البوت)
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // استثناء حاسم: أي طلب يحتوي على /files/ أو /download 
  // يجب أن يمر مباشرة للشبكة دون أي تدخل من الكاش لضمان الحفظ في الاستوديو
  if (url.pathname.includes('/download') || url.pathname.includes('/files/')) {
    return; 
  }

  event.respondWith(
    fetch(event.request).catch(() => {
      return caches.match(event.request);
    })
  );
});
