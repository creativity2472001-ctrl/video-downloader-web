from flask import Flask, render_template, send_file, jsonify, request
import os
import yt_dlp
import uuid
import time
import threading
import logging

# إعداد التسجيل
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

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
        # إعدادات yt-dlp الأساسية
        ydl_opts = {
            'outtmpl': f"{base}.%(ext)s",
            'quiet': True,
            'noplaylist': True,
            'verbose': True,
            'socket_timeout': 60,
            'retries': 10,
            'fragment_retries': 10,
            'extractor_retries': 5,
            'impersonate': 'chrome',  # مهم جداً لجميع المواقع
        }

        # ملف الكوكيز إذا موجود
        if os.path.exists('cookies.txt'):
            ydl_opts['cookiefile'] = 'cookies.txt'
            logger.info("✅ تم العثور على ملف الكوكيز")
        else:
            logger.warning("⚠️ ملف الكوكيز غير موجود")

        # إعدادات خاصة لكل موقع
        if 'youtube.com' in url or 'youtu.be' in url:
            logger.info("🎬 إعدادات يوتيوب")
            ydl_opts['extractor_args'] = {'youtube': ['player-client=web']}
            
        elif 'instagram.com' in url:
            logger.info("📷 إعدادات انستغرام")
            ydl_opts['extractor_args'] = {'instagram': ['no-check-certificate']}
            ydl_opts['http_headers'] = {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
            }
            
        elif 'tiktok.com' in url:
            logger.info("🎵 إعدادات تيك توك")
            ydl_opts['extractor_args'] = {'tiktok': ['no-check-certificate']}
            
        elif 'facebook.com' in url or 'fb.watch' in url:
            logger.info("📘 إعدادات فيسبوك")
            ydl_opts['extractor_args'] = {'facebook': ['no-check-certificate']}

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
    """مسار مباشر للفيديو"""
    path = os.path.join(DOWNLOAD_DIR, filename)
    
    if not os.path.exists(path):
        return 'الملف غير موجود', 404
    
    return send_file(
        path,
        mimetype='video/mp4',
        as_attachment=False
    )

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
