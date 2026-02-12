const CACHE_NAME = 'EasyDown-v1';
const ASSETS = [
  '/',
  '/static/logo.png',
  '/static/manifest.json'
];

// 1. التثبيت: حفظ ملفات الواجهة الأساسية
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      // إشعار: نستخدم 'force-cache' لضمان تحديث الملفات عند التغيير
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

// 3. معالجة الطلبات: استثناء التحميلات + نظام (الشبكة أولاً) للواجهة
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // استثناء حاسم: الروابط الحيوية لا تُلمس نهائياً
  if (url.pathname.includes('/download') || url.pathname.includes('/files/')) {
    return; 
  }

  event.respondWith(
    // نحاول جلب الملف من الشبكة أولاً لتحديث الواجهة دائماً
    fetch(event.request).catch(() => {
      // إذا انقطع الإنترنت، نستخدم الملفات المخزنة (Offline Mode)
      return caches.match(event.request);
    })
  );
});
