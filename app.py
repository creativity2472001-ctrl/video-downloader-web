from flask import Flask, render_template, send_file, jsonify, request
import os
import yt_dlp
import uuid
import time
import threading
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

ALLOWED_DOMAINS = [
    "youtube.com", "youtu.be",
    "tiktok.com", "vm.tiktok.com",
    "instagram.com", "www.instagram.com",
    "facebook.com", "fb.watch",
    "twitter.com", "x.com"
]

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
    return render_template('index.html')

@app.route('/download', methods=['POST'])
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
        # إعدادات بسيطة وواضحة
        ydl_opts = {
            'outtmpl': f"{base}.%(ext)s",
            'quiet': True,
            'noplaylist': True,
            'verbose': True,  # هذا راح يظهر تفاصيل أكثر في الـ logs
        }

        # إضافة ملف الكوكيز إذا كان موجوداً
        if os.path.exists('cookies.txt'):
            ydl_opts['cookiefile'] = 'cookies.txt'
            logger.info("✅ تم العثور على ملف الكوكيز")

        # إعدادات الصوت أو الفيديو
        if mode == 'audio':
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
            }]
        else:
            if quality == '480p':
                ydl_opts['format'] = 'best[height<=480]'
            elif quality == '720p':
                ydl_opts['format'] = 'best[height<=720]'
            elif quality == '1080p':
                ydl_opts['format'] = 'best[height<=1080]'
            else:
                ydl_opts['format'] = 'best[ext=mp4]/best'

        logger.info(f"بدء تحميل: {url}")

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

        download_url = f"/v/{filename}"

        logger.info(f"✅ تم التحميل بنجاح: {filename}")

        return jsonify({
            'success': True,
            'download_url': download_url,
            'title': title,
            'filename': filename
        })

    except Exception as e:
        logger.error(f"❌ خطأ في التحميل: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/v/<filename>')
def get_video(filename):
    path = os.path.join(DOWNLOAD_DIR, filename)
    if not os.path.exists(path):
        return 'الملف غير موجود', 404
    return send_file(path, mimetype='video/mp4')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
