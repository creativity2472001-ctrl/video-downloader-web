const CACHE_NAME = 'EasyDown-v1';
const ASSETS = [
  '/',
  '/static/logo.png',
  '/static/manifest.json'
];

// 1. مرحلة التثبيت: حفظ الملفات الأساسية في الكاش
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log('Caching assets...');
      return cache.addAll(ASSETS);
    })
  );
  self.skipWaiting();
});

// 2. مرحلة التفعيل: مسح الكاش القديم إذا وجد
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

// 3. استراتيجية (Network First): جلب الجديد من الإنترنت، وإذا انقطع، استخدم الكاش
self.addEventListener('fetch', (event) => {
  // لا نريد تخزين عمليات التحميل (فقط واجهة التطبيق)
  if (event.request.url.includes('/download')) {
    return; 
  }

  event.respondWith(
    fetch(event.request).catch(() => {
      return caches.match(event.request);
    })
  );
});
