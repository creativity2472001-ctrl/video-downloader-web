from flask import Flask, render_template, request, send_file, jsonify
import os
import yt_dlp
import uuid
import time
import threading
from datetime import datetime

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

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/info", methods=["POST"])
def video_info():
    data = request.get_json()
    url = data.get("url")
    try:
        ydl_opts = {'quiet': True, 'no_warnings': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
        duration = info.get('duration', 0)
        minutes = duration // 60
        seconds = duration % 60
        return jsonify({
            "title": info.get('title', 'Video'),
            "duration": f"{minutes}:{seconds:02d}"
        })
    except:
        return jsonify({"error": "❌ لا يمكن الحصول على معلومات الفيديو"}), 400

@app.route("/download", methods=["POST"])
def download():
    data = request.get_json()
    url = data.get("url")
    mode = data.get("mode", "video")

    if not url:
        return jsonify({"error": "❌ الرابط مطلوب"}), 400

    if not any(domain in url for domain in ALLOWED_DOMAINS):
        return jsonify({"error": "❌ هذا الرابط غير مدعوم"}), 400

    file_id = uuid.uuid4().hex[:8]
    try:
        base = os.path.join(DOWNLOAD_DIR, file_id)
        opts = {
            'outtmpl': f"{base}.%(ext)s",
            'quiet': True,
            'noplaylist': True,
        }

        if mode == "audio":
            opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                }],
            })
        else:
            opts.update({
                'format': 'best[ext=mp4]/best',
            })

        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title', 'video')

        filename = None
        for f in os.listdir(DOWNLOAD_DIR):
            if f.startswith(file_id):
                filename = f
                break

        if not filename:
            return jsonify({"error": "❌ فشل العثور على الملف"}), 500

        # رابط مباشر للمشاهدة والتحميل
        video_url = f"/watch/{filename}"
        download_url = f"/get/{filename}"

        return jsonify({
            "status": "success",
            "video_url": video_url,
            "download_url": download_url,
            "title": title
        })

    except Exception as e:
        return jsonify({"error": f"❌ {str(e)}"}), 500

# 🎬 مسار لعرض الفيديو مباشرة في الصفحة
@app.route("/watch/<filename>")
def watch_video(filename):
    path = os.path.join(DOWNLOAD_DIR, filename)
    if not os.path.exists(path):
        return "الملف غير موجود", 404
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>مشاهدة الفيديو</title>
        <style>
            body {{
                background: linear-gradient(135deg, #1a1a2e, #16213e);
                color: white;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                padding: 20px;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                min-height: 100vh;
                box-sizing: border-box;
            }}
            .video-container {{
                max-width: 800px;
                width: 100%;
                background: rgba(255, 255, 255, 0.05);
                backdrop-filter: blur(10px);
                border-radius: 25px;
                padding: 20px;
                box-shadow: 0 20px 50px rgba(0,0,0,0.5);
                border: 1px solid rgba(255,255,255,0.1);
            }}
            video {{
                width: 100%;
                border-radius: 15px;
                background: black;
            }}
            .title {{
                text-align: center;
                margin: 20px 0;
                font-size: 1.2rem;
                color: #00d2ff;
                word-break: break-word;
            }}
            .save-btn {{
                display: inline-block;
                width: 100%;
                padding: 18px;
                border-radius: 15px;
                background: linear-gradient(45deg, #28a745, #34ce57);
                color: white;
                text-decoration: none;
                text-align: center;
                font-weight: bold;
                font-size: 1.2rem;
                border: none;
                cursor: pointer;
                transition: transform 0.3s;
                margin-top: 15px;
            }}
            .save-btn:hover {{
                transform: translateY(-2px);
            }}
            .instructions {{
                text-align: center;
                margin-top: 20px;
                color: #888;
                font-size: 0.9rem;
            }}
        </style>
    </head>
    <body>
        <div class="video-container">
            <div class="title">🎬 {filename}</div>
            <video controls playsinline webkit-playsinline preload="auto">
                <source src="/get/{filename}" type="video/mp4">
                متصفحك لا يدعم تشغيل الفيديو.
            </video>
            <a href="/get/{filename}" class="save-btn" download>
                <i class="fas fa-download"></i> ⬇️ حفظ الفيديو
            </a>
            <div class="instructions">
                💡 للآيفون: اضغط مطولاً على الفيديو ثم اختر "Save Video"
            </div>
        </div>
    </body>
    </html>
    '''

@app.route("/get/<filename>")
def get_file(filename):
    path = os.path.join(DOWNLOAD_DIR, filename)
    if not os.path.exists(path):
        return "الملف غير موجود", 404

    return send_file(
        path,
        as_attachment=True,
        download_name=filename,
        mimetype="video/mp4" if filename.endswith(".mp4") else "audio/mpeg"
    )

if __name__ == "__main__":
    print("="*50)
    print("🚀 EasyDown - تطبيق تحميل الفيديوهات")
    print("="*50)
    print("📱 متوفر على:")
    print("   - محلياً: http://127.0.0.1:5000")
    print("   - على الشبكة: http://192.168.0.104:5000")
    print("="*50)
    app.run(host="0.0.0.0", port=5000, debug=True)
