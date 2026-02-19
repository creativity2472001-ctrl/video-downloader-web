from flask import Flask, render_template, request, send_file, jsonify, session
import os
import yt_dlp
import uuid
import time
import threading
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'easydown_secret_key_2026'

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

ALLOWED_DOMAINS = [
    "youtube.com", "youtu.be",
    "tiktok.com", "vm.tiktok.com",
    "instagram.com", "www.instagram.com",
    "facebook.com", "fb.watch",
    "twitter.com", "x.com"
]

# قائمة اللغات المدعومة
LANGUAGES = {
    'ar': {
        'name': 'العربية',
        'flag': '🇸🇦',
        'app_name': 'EasyDown',
        'tagline': 'أسرع وأسهل طريقة لتحميل الفيديوهات',
        'paste_link': 'الصق الرابط هنا',
        'video': 'فيديو',
        'audio': 'صوت',
        'download': 'تحميل',
        'quality_480p': '480p',
        'quality_720p': '720p',
        'quality_1080p': '1080p',
        'quality_best': 'أفضل جودة',
        'select_quality': 'اختر جودة التحميل',
        'downloading': 'جاري التحميل والمعالجة...',
        'ready': 'جاهز للتحميل!',
        'save': 'اضغط هنا للحفظ',
        'error': '❌ حدث خطأ في التحميل',
        'connection_error': '❌ خطأ في الاتصال بالخادم',
        'enter_link': '⚠️ يرجى إدخال رابط الفيديو',
        'help_title': 'طريقة الاستخدام',
        'help_1': '1️⃣ الصق رابط الفيديو في الحقل أعلاه',
        'help_2': '2️⃣ اختر صيغة التحميل (فيديو أو صوت)',
        'help_3': '3️⃣ اختر الجودة المناسبة',
        'help_4': '4️⃣ اضغط على زر "تحميل"',
        'help_5': '5️⃣ انتظر حتى تجهيز الملف',
        'help_6': '6️⃣ اضغط على رابط التحميل',
        'iphone_help': 'لأجهزة الآيفون: اضغط مطولاً على الفيديو ثم اختر Save Video',
        'add_to_home': '📱 لإضافة التطبيق للشاشة الرئيسية: اضغط على زر المشاركة ثم اختر "إضافة إلى الشاشة الرئيسية"',
        'supported_sites': 'المواقع المدعومة',
        'footer': 'جميع الحقوق محفوظة'
    },
    'en': {
        'name': 'English',
        'flag': '🇺🇸',
        'app_name': 'EasyDown',
        'tagline': 'Fastest way to download videos',
        'paste_link': 'Paste link here',
        'video': 'Video',
        'audio': 'Audio',
        'download': 'Download',
        'quality_480p': '480p',
        'quality_720p': '720p',
        'quality_1080p': '1080p',
        'quality_best': 'Best Quality',
        'select_quality': 'Select quality',
        'downloading': 'Downloading and processing...',
        'ready': 'Ready to download!',
        'save': 'Click here to save',
        'error': '❌ Download error',
        'connection_error': '❌ Connection error',
        'enter_link': '⚠️ Please enter video link',
        'help_title': 'How to use',
        'help_1': '1️⃣ Paste video link above',
        'help_2': '2️⃣ Choose format (Video/Audio)',
        'help_3': '3️⃣ Select quality',
        'help_4': '4️⃣ Click "Download" button',
        'help_5': '5️⃣ Wait for processing',
        'help_6': '6️⃣ Click download link',
        'iphone_help': 'For iPhone: Long press on video then tap Save Video',
        'add_to_home': '📱 Add to home screen: Share button → Add to Home Screen',
        'supported_sites': 'Supported sites',
        'footer': 'All rights reserved'
    },
    'tr': {
        'name': 'Türkçe',
        'flag': '🇹🇷',
        'app_name': 'EasyDown',
        'tagline': 'Video indirmenin en hızlı yolu',
        'paste_link': 'Linki yapıştır',
        'video': 'Video',
        'audio': 'Ses',
        'download': 'İndir',
        'quality_480p': '480p',
        'quality_720p': '720p',
        'quality_1080p': '1080p',
        'quality_best': 'En iyi kalite',
        'select_quality': 'Kalite seç',
        'downloading': 'İndiriliyor...',
        'ready': 'İndirmeye hazır!',
        'save': 'İndirmek için tıkla',
        'error': '❌ İndirme hatası',
        'connection_error': '❌ Bağlantı hatası',
        'enter_link': '⚠️ Lütfen video linkini girin',
        'help_title': 'Kullanım',
        'help_1': '1️⃣ Linki yapıştır',
        'help_2': '2️⃣ Format seç (Video/Ses)',
        'help_3': '3️⃣ Kalite seç',
        'help_4': '4️⃣ "İndir" butonuna bas',
        'help_5': '5️⃣ İşlemin bitmesini bekle',
        'help_6': '6️⃣ İndirme linkine tıkla',
        'iphone_help': 'iPhone: Videoya uzun bas → Save Video',
        'add_to_home': '📱 Ana ekrana ekle: Paylaş → Ana Ekrana Ekle',
        'supported_sites': 'Desteklenen siteler',
        'footer': 'Tüm hakları saklıdır'
    },
    'ru': {
        'name': 'Русский',
        'flag': '🇷🇺',
        'app_name': 'EasyDown',
        'tagline': 'Быстрая загрузка видео',
        'paste_link': 'Вставьте ссылку',
        'video': 'Видео',
        'audio': 'Аудио',
        'download': 'Скачать',
        'quality_480p': '480p',
        'quality_720p': '720p',
        'quality_1080p': '1080p',
        'quality_best': 'Лучшее качество',
        'select_quality': 'Выберите качество',
        'downloading': 'Загрузка...',
        'ready': 'Готово к загрузке!',
        'save': 'Нажмите для сохранения',
        'error': '❌ Ошибка загрузки',
        'connection_error': '❌ Ошибка соединения',
        'enter_link': '⚠️ Введите ссылку на видео',
        'help_title': 'Инструкция',
        'help_1': '1️⃣ Вставьте ссылку выше',
        'help_2': '2️⃣ Выберите формат',
        'help_3': '3️⃣ Выберите качество',
        'help_4': '4️⃣ Нажмите "Скачать"',
        'help_5': '5️⃣ Подождите',
        'help_6': '6️⃣ Нажмите ссылку',
        'iphone_help': 'iPhone: Нажмите и удерживайте видео → Save Video',
        'add_to_home': '📱 На главный экран: Поделиться → На экран «Домой»',
        'supported_sites': 'Поддерживаемые сайты',
        'footer': 'Все права защищены'
    },
    'fr': {
        'name': 'Français',
        'flag': '🇫🇷',
        'app_name': 'EasyDown',
        'tagline': 'Téléchargement rapide',
        'paste_link': 'Collez le lien',
        'video': 'Vidéo',
        'audio': 'Audio',
        'download': 'Télécharger',
        'quality_480p': '480p',
        'quality_720p': '720p',
        'quality_1080p': '1080p',
        'quality_best': 'Meilleure qualité',
        'select_quality': 'Choisir qualité',
        'downloading': 'Téléchargement...',
        'ready': 'Prêt!',
        'save': 'Cliquez pour sauvegarder',
        'error': '❌ Erreur',
        'connection_error': '❌ Erreur connexion',
        'enter_link': '⚠️ Entrez le lien',
        'help_title': 'Comment utiliser',
        'help_1': '1️⃣ Collez le lien',
        'help_2': '2️⃣ Choisissez le format',
        'help_3': '3️⃣ Choisissez la qualité',
        'help_4': '4️⃣ Cliquez "Télécharger"',
        'help_5': '5️⃣ Attendez',
        'help_6': '6️⃣ Cliquez sur le lien',
        'iphone_help': 'iPhone: Appuyez longuement → Save Video',
        'add_to_home': '📱 Ajouter à l\'écran d\'accueil',
        'supported_sites': 'Sites supportés',
        'footer': 'Tous droits réservés'
    },
    'de': {
        'name': 'Deutsch',
        'flag': '🇩🇪',
        'app_name': 'EasyDown',
        'tagline': 'Schneller Video-Download',
        'paste_link': 'Link einfügen',
        'video': 'Video',
        'audio': 'Audio',
        'download': 'Herunterladen',
        'quality_480p': '480p',
        'quality_720p': '720p',
        'quality_1080p': '1080p',
        'quality_best': 'Beste Qualität',
        'select_quality': 'Qualität wählen',
        'downloading': 'Lade herunter...',
        'ready': 'Bereit!',
        'save': 'Hier klicken',
        'error': '❌ Fehler',
        'connection_error': '❌ Verbindungsfehler',
        'enter_link': '⚠️ Link eingeben',
        'help_title': 'Anleitung',
        'help_1': '1️⃣ Link einfügen',
        'help_2': '2️⃣ Format wählen',
        'help_3': '3️⃣ Qualität wählen',
        'help_4': '4️⃣ "Download" klicken',
        'help_5': '5️⃣ Warten',
        'help_6': '6️⃣ Link klicken',
        'iphone_help': 'iPhone: Lange drücken → Save Video',
        'add_to_home': '📱 Zum Home-Bildschirm',
        'supported_sites': 'Unterstützte Seiten',
        'footer': 'Alle Rechte vorbehalten'
    }
}

def get_text(key, lang='ar'):
    return LANGUAGES.get(lang, LANGUAGES['ar']).get(key, key)

def cleanup():
    while True:
        now = time.time()
        for f in os.listdir(DOWNLOAD_DIR):
            path = os.path.join(DOWNLOAD_DIR, f)
            if os.path.isfile(path) and os.stat(path).st_mtime < now - 3600:
                try: os.remove(path)
                except: pass
        time.sleep(1800)

threading.Thread(target=cleanup, daemon=True).start()

@app.route('/')
def index():
    lang = request.args.get('lang', 'ar')
    session['lang'] = lang
    return render_template('index.html', lang=lang, texts=LANGUAGES[lang], languages=LANGUAGES)

@app.route('/set_language/<lang>')
def set_language(lang):
    if lang in LANGUAGES:
        session['lang'] = lang
    return index()

@app.route('/api/info', methods=['POST'])
def video_info():
    data = request.get_json()
    url = data.get('url')
    try:
        ydl_opts = {'quiet': True, 'no_warnings': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
        return jsonify({
            'success': True,
            'title': info.get('title', 'Video'),
            'duration': info.get('duration', 0)
        })
    except:
        return jsonify({'error': '❌ خطأ'}), 400

@app.route('/api/download', methods=['POST'])
def download():
    data = request.get_json()
    url = data.get('url')
    mode = data.get('mode', 'video')
    quality = data.get('quality', 'best')

    if not url:
        return jsonify({'error': '❌ الرابط مطلوب'}), 400

    file_id = uuid.uuid4().hex[:8]
    base = os.path.join(DOWNLOAD_DIR, file_id)

    try:
        ydl_opts = {
            'outtmpl': f"{base}.%(ext)s",
            'quiet': True,
            'noplaylist': True,
        }

        if mode == 'audio':
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                }],
            })
        else:
            if quality == '480p':
                ydl_opts['format'] = 'best[height<=480]'
            elif quality == '720p':
                ydl_opts['format'] = 'best[height<=720]'
            elif quality == '1080p':
                ydl_opts['format'] = 'best[height<=1080]'
            else:
                ydl_opts['format'] = 'best[ext=mp4]/best'

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title', 'video')

        filename = None
        for f in os.listdir(DOWNLOAD_DIR):
            if f.startswith(file_id):
                filename = f
                break

        if not filename:
            return jsonify({'error': '❌ فشل'}), 500

        return jsonify({
            'success': True,
            'download_url': f"/get/{filename}",
            'title': title
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get/<filename>')
def get_file(filename):
    path = os.path.join(DOWNLOAD_DIR, filename)
    if not os.path.exists(path):
        return 'الملف غير موجود', 404

    return send_file(
        path,
        as_attachment=True,
        download_name=filename,
        mimetype='video/mp4' if filename.endswith('.mp4') else 'audio/mpeg'
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
