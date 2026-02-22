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
        ydl_opts = {
            'outtmpl': f"{base}.%(ext)s",
            'quiet': True,
            'noplaylist': True,
        }

        if os.path.exists('cookies.txt'):
            ydl_opts['cookiefile'] = 'cookies.txt'

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
            return jsonify({'error': '❌ فشل في إنشاء الملف'}), 500

        # ✅ هنا السر: نوجه المستخدم لصفحة فيها زر رجوع
        download_url = f"/video/{filename}"

        return jsonify({
            'success': True,
            'download_url': download_url,
            'title': title,
            'filename': filename
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ✅ صفحة مشاهدة الفيديو مع زر رجوع (هذه الجديدة)
@app.route('/video/<filename>')
def video_page(filename):
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
            }}
        </style>
    </head>
    <body>
        <button onclick="window.location.href='/'" class="back-btn">🔙 رجوع للتطبيق</button>
        <video controls autoplay>
            <source src="/get-video/{filename}" type="video/mp4">
        </video>
        <a href="/get-video/{filename}" download class="save-btn">💾 حفظ الفيديو</a>
    </body>
    </html>
    '''

# ✅ مسار الفيديو الخام (للتشغيل والتحميل)
@app.route('/get-video/<filename>')
def get_video(filename):
    path = os.path.join(DOWNLOAD_DIR, filename)
    return send_file(path, mimetype='video/mp4')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
