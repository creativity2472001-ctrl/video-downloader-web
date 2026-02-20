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
    return render_template('index.html')

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

        # رابط مباشر للفيديو - فقط mp4
        download_url = f"/files/{filename}"

        logger.info(f"تم التحميل بنجاح: {filename}")
        
        return jsonify({
            'success': True,
            'download_url': download_url,
            'title': title,
            'filename': filename
        })

    except Exception as e:
        logger.error(f"Error in download: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/files/<filename>')
def files(filename):
    """مسار مباشر للفيديو - يفتح في المتصفح مباشرة"""
    path = os.path.join(DOWNLOAD_DIR, filename)
    
    if not os.path.exists(path):
        return 'الملف غير موجود', 404
    
    # إرسال الملف كمحتوى فيديو مباشر
    return send_file(
        path,
        mimetype='video/mp4',
        as_attachment=False  # هذا يجعله يفتح في المتصفح مباشرة
    )

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'الصفحة غير موجودة'}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'خطأ في الخادم'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
