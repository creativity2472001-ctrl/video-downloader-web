from flask import Flask, render_template, request, send_file, jsonify, url_for, make_response
import os
import yt_dlp
import uuid
import time
import threading

app = Flask(__name__)

# مجلد التحميلات
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# النطاقات المدعومة لجميع المنصات
ALLOWED_DOMAINS = [
    "youtube.com", "youtu.be", "youtube-nocookie.com",
    "tiktok.com", "vm.tiktok.com",
    "instagram.com", "www.instagram.com", "instagr.am",
    "facebook.com", "fb.watch", "fb.com",
    "twitter.com", "x.com", "t.co",
    "pinterest.com", "pin.it",
    "likee.video", "likee.com",
    "t.me",
    "reddit.com", "v.redd.it",
    "snapchat.com", "www.snapchat.com",
    "vimeo.com",
    "dailymotion.com", "www.dailymotion.com",
    "twitcasting.tv"
]

# تنظيف الملفات القديمة (أقدم من 6 ساعات)
def cleanup_old_files():
    while True:
        now = time.time()
        for f in os.listdir(DOWNLOAD_DIR):
            f_path = os.path.join(DOWNLOAD_DIR, f)
            if os.path.isfile(f_path):
                if os.stat(f_path).st_mtime < now - 6*3600:
                    try:
                        os.remove(f_path)
                    except:
                        pass
        time.sleep(1800)

threading.Thread(target=cleanup_old_files, daemon=True).start()

def get_ydl_opts(mode, file_id):
    base_path = os.path.join(DOWNLOAD_DIR, f"{file_id}.%(ext)s")
    opts = {
        'outtmpl': base_path,
        'restrictfilenames': True,
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
    }

    if mode == "audio":
        opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192'
            }]
        })
    else:
        opts.update({
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'merge_output_format': 'mp4',
            'postprocessor_args': [
                '-vcodec', 'libx264',
                '-pix_fmt', 'yuv420p',
                '-acodec', 'aac'
            ],
        })
    return opts

@app.route("/")
def index():
    return render_template("index.html")

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
        ydl_opts = get_ydl_opts(mode, file_id)
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

        ext = "mp3" if mode == "audio" else "mp4"
        filename = f"{file_id}.{ext}"
        download_url = url_for('get_file', filename=filename, _external=True)

        return jsonify({
            "status": "success",
            "download_url": download_url,
            "title": info.get('title', 'MixMediaApp File')
        })

    except Exception as e:
        return jsonify({"error": f"❌ فشل السيرفر: {str(e)}"}), 500


@app.route("/files/<filename>")
def get_file(filename):
    file_path = os.path.join(DOWNLOAD_DIR, filename)

    if not os.path.exists(file_path):
        return "❌ الملف غير موجود", 404

    mimetype = "audio/mpeg" if filename.endswith(".mp3") else "video/mp4"

    response = make_response(send_file(
        file_path,
        mimetype=mimetype
    ))

    # iOS: inline لتمكين Share → Save
    response.headers["Content-Disposition"] = f"inline; filename={filename}"
    response.headers["X-Content-Type-Options"] = "nosniff"

    return response


@app.route("/sw.js")
def sw():
    return app.send_static_file("sw.js")


if name == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
