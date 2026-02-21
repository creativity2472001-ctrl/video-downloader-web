from flask import Flask, render_template, send_file, jsonify, request
import os
import yt_dlp
import uuid
import time
import threading

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
        # إعدادات yt-dlp المتقدمة لجميع المواقع
        ydl_opts = {
            'outtmpl': f"{base}.%(ext)s",
            'quiet': True,
            'noplaylist': True,
            'cookiefile': 'cookies.txt',  # ملف الكوكيز
            'extractor_args': {'youtube': ['bgutil']},  # لليوتيوب
            'impersonate': 'chrome',  # انتحال متصفح لفيسبوك
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
            # تحسين اختيار الجودة
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
            return jsonify({'error': '❌ فشل في إنشاء الملف'}), 500

        # رابط مباشر للفيديو
        download_url = f"/v/{filename}"

        return jsonify({
            'success': True,
            'download_url': download_url,
            'title': title,
            'filename': filename
        })

    except Exception as e:
        # تسجيل الخطأ للمساعدة في التصحيح
        print(f"Download error: {e}")
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
    app.run(host='0.0.0.0', port=5000, debug=True)
