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
            "success": True,
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

        # ✅ استخدام success بدلاً من status
        return jsonify({
            "success": True,
            "download_url": f"/get/{filename}",
            "title": title
        })

    except Exception as e:
        return jsonify({"error": f"❌ {str(e)}"}), 500

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
    app.run(host="0.0.0.0", port=5000, debug=True)
