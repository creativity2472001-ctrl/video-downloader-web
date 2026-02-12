const CACHE_NAME = 'EasyDown-v1';
const ASSETS = [
  '/',
  '/static/logo.png',
  '/static/manifest.json'
];

// 1. التثبيت: حفظ الملفات الأساسية
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(ASSETS);
    })
  );
  self.skipWaiting();
});

// 2. التفعيل: تنظيف الكاش القديم
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

// 3. جلب البيانات: ذكاء التعامل مع الملفات الكبيرة
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // استثناء ملفات التحميل والـ API تماماً من الـ Service Worker
  // لضمان سرعة التحميل وعدم استهلاك ذاكرة الهاتف
  if (url.pathname.includes('/download') || url.pathname.includes('/files/')) {
    return; // اتركه يذهب للإنترنت مباشرة بدون تدخل
  }

  event.respondWith(
    fetch(event.request).catch(() => {
      return caches.match(event.request);
    })
  );
});
