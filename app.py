from flask import Flask, render_template, request, send_file, jsonify, session
import os
import yt_dlp
import uuid
import time
import threading
import logging
from datetime import datetime

# إعداد التسجيل
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'easydown_secret_key_2026')

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

ALLOWED_DOMAINS = [
    "youtube.com", "youtu.be",
    "tiktok.com", "vm.tiktok.com", "vt.tiktok.com",
    "instagram.com", "www.instagram.com", "instagr.am",
    "facebook.com", "fb.watch", "www.facebook.com",
    "twitter.com", "x.com", "www.twitter.com",
    "snapchat.com", "www.snapchat.com"
]

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
        'error': '❌ حدث خطأ في التحميل',
        'connection_error': '❌ خطأ في الاتصال بالخادم',
        'enter_link': '⚠️ يرجى إدخال رابط الفيديو',
        'help_title': 'طريقة الاستخدام',
        'help_1': '1️⃣ الصق رابط الفيديو في الحقل أعلاه',
        'help_2': '2️⃣ اختر صيغة التحميل (فيديو أو صوت)',
        'help_3': '3️⃣ اختر الجودة المناسبة',
        'help_4': '4️⃣ اضغط على زر "تحميل"',
        'help_5': '5️⃣ انتظر حتى تجهيز الملف',
        'iphone_help_1': '📱 للآيفون: التحميل بدأ!',
        'iphone_help_2': '1️⃣ افتح تطبيق "الملفات" (Files)',
        'iphone_help_3': '2️⃣ اذهب إلى مجلد "تنزيلات" (Downloads)',
        'iphone_help_4': '3️⃣ اضغط على الفيديو ثم زر المشاركة',
        'iphone_help_5': '4️⃣ اختر "حفظ الفيديو" (Save Video)',
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
        'error': '❌ Download error',
        'connection_error': '❌ Connection error',
        'enter_link': '⚠️ Please enter video link',
        'help_title': 'How to use',
        'help_1': '1️⃣ Paste video link above',
        'help_2': '2️⃣ Choose format (Video/Audio)',
        'help_3': '3️⃣ Select quality',
        'help_4': '4️⃣ Click "Download" button',
        'help_5': '5️⃣ Wait for processing',
        'iphone_help_1': '📱 For iPhone: Download started!',
        'iphone_help_2': '1️⃣ Open "Files" app',
        'iphone_help_3': '2️⃣ Go to "Downloads" folder',
        'iphone_help_4': '3️⃣ Tap video then share button',
        'iphone_help_5': '4️⃣ Choose "Save Video"',
        'supported_sites': 'Supported sites',
        'footer': 'All rights reserved'
    }
}

def get_text(key, lang='ar'):
    return LANGUAGES.get(lang, LANGUAGES['ar']).get(key, key)

def cleanup():
    while True:
        try:
            now = time.time()
            for f in os.listdir(DOWNLOAD_DIR):
                path = os.path.join(DOWNLOAD_DIR, f)
                if os.path.isfile(path):
                    file_age = now - os.stat(path).st_mtime
                    if file_age > 3600:
                        try:
                            os.remove(path)
                            logger.info(f"تم حذف الملف القديم: {f}")
                        except Exception as e:
                            logger.error(f"خطأ في حذف الملف {f}: {e}")
        except Exception as e:
            logger.error(f"خطأ في عملية التنظيف: {e}")
        time.sleep(1800)

threading.Thread(target=cleanup, daemon=True).start()

@app.route('/')
def index():
    lang = request.args.get('lang', session.get('lang', 'ar'))
    if lang in LANGUAGES:
        session['lang'] = lang
    return render_template('index.html', lang=lang, texts=LANGUAGES[lang], languages=LANGUAGES)

@app.route('/set_language/<lang>')
def set_language(lang):
    if lang in LANGUAGES:
        session['lang'] = lang
    return {'success': True, 'lang': lang}

@app.route('/api/info', methods=['POST'])
def video_info():
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        if not url:
            return jsonify({'error': '⚠️ الرابط مطلوب'}), 400
        ydl_opts = {'quiet': True, 'no_warnings': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
        return jsonify({
            'success': True,
            'title': info.get('title', 'Video'),
            'duration': info.get('duration', 0)
        })
    except Exception as e:
        logger.error(f"Error in video_info: {e}")
        return jsonify({'error': str(e)}), 400

@app.route('/api/download', methods=['POST'])
def download():
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        mode = data.get('mode', 'video')
        quality = data.get('quality', 'best')

        if not url:
            return jsonify({'error': '❌ الرابط مطلوب'}), 400

        file_id = uuid.uuid4().hex[:8]
        base = os.path.join(DOWNLOAD_DIR, file_id)

        ydl_opts = {
            'outtmpl': f"{base}.%(ext)s",
            'quiet': True,
            'noplaylist': True,
            'cookiefile': 'cookies.txt',
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
                ydl_opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'

        logger.info(f"بدء تحميل: {url} - {mode} - {quality}")
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title', 'video')

        filename = None
        for f in os.listdir(DOWNLOAD_DIR):
            if f.startswith(file_id):
                filename = f
                break

        if not filename:
            return jsonify({'error': '❌ فشل في إنشاء الملف'}), 500

        download_url = f"/video/{filename}"
        page_url = f"/watch/{filename}"

        logger.info(f"تم التحميل بنجاح: {filename}")
        
        return jsonify({
            'success': True,
            'direct_download': True,
            'download_url': download_url,
            'page_url': page_url,
            'title': title,
            'filename': filename
        })

    except Exception as e:
        logger.error(f"Error in download: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/watch/<filename>')
def watch_video(filename):
    try:
        path = os.path.join(DOWNLOAD_DIR, filename)
        if not os.path.exists(path):
            return 'الملف غير موجود', 404

        return f'''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>EasyDown - فيديو</title>
            <style>
                body {{
                    background: #1a1a2e;
                    color: white;
                    font-family: sans-serif;
                    text-align: center;
                    padding: 20px;
                    margin: 0;
                }}
                .back-btn {{
                    display: inline-block;
                    margin: 20px auto;
                    padding: 15px 30px;
                    background: #00d2ff;
                    color: white;
                    text-decoration: none;
                    border-radius: 50px;
                    font-weight: bold;
                    font-size: 1.2rem;
                    border: none;
                    cursor: pointer;
                }}
                video {{
                    width: 100%;
                    max-width: 600px;
                    border-radius: 15px;
                    background: black;
                    margin: 20px 0;
                }}
                .save-btn {{
                    display: inline-block;
                    margin: 20px auto;
                    padding: 18px 40px;
                    background: #28a745;
                    color: white;
                    text-decoration: none;
                    border-radius: 50px;
                    font-weight: bold;
                    font-size: 1.3rem;
                    width: 80%;
                    max-width: 300px;
                    border: none;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <button onclick="history.back()" class="back-btn">🔙 رجوع للتطبيق</button>
                
                <video controls autoplay playsinline>
                    <source src="/video/{filename}" type="video/mp4">
                </video>
                
                <a href="/video/{filename}" download class="save-btn">💾 حفظ الفيديو</a>
            </div>
        </body>
        </html>
        '''
    except Exception as e:
        logger.error(f"Error in watch_video: {e}")
        return str(e), 500

@app.route('/video/<filename>')
def video_file(filename):
    """مسار مباشر للفيديو (ما يفتح صفحة جديدة)"""
    path = os.path.join(DOWNLOAD_DIR, filename)
    return send_file(path, mimetype='video/mp4')

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'الصفحة غير موجودة'}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'خطأ في الخادم'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
