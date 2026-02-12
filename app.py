from flask import Flask, render_template, request, send_file, jsonify, url_for, Response
import os
import yt_dlp
import uuid
import time
import threading

app = Flask(__name__)

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

ALLOWED_DOMAINS = ["youtube.com", "youtu.be", "instagram.com", "tiktok.com", "pinterest.com", "likee.video", "facebook.com", "fb.watch", "x.com", "twitter.com"]

def cleanup_old_files():
    while True:
        now = time.time()
        for f in os.listdir(DOWNLOAD_DIR):
            f_path = os.path.join(DOWNLOAD_DIR, f)
            if os.stat(f_path).st_mtime < now - 3600:
                try: os.remove(f_path)
                except: pass
        time.sleep(1800)

threading.Thread(target=cleanup_old_files, daemon=True).start()

def get_ydl_opts(mode, file_id):
    base_path = os.path.join(DOWNLOAD_DIR, f"{file_id}_%(title)s.%(ext)s")
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
            'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}]
        })
    else:
        opts.update({
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'merge_output_format': 'mp4',
            'postprocessor_args': ['-vcodec', 'libx264', '-preset', 'ultrafast', '-acodec', 'aac', '-pix_fmt', 'yuv420p'],
        })
    return opts

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/download", methods=["POST"])
def download():
    data = request.get_json()
    url, mode = data.get("url"), data.get("mode", "video")
    if not url or not any(domain in url.lower() for domain in ALLOWED_DOMAINS):
        return jsonify({"error": "الرابط غير مدعوم"}), 400
    file_id = uuid.uuid4().hex[:8]
    try:
        ydl_opts = get_ydl_opts(mode, file_id)
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            ext = ".mp3" if mode == "audio" else ".mp4"
            final_name = filename.rsplit(".", 1)[0] + ext
            if not os.path.exists(final_name):
                for f in os.listdir(DOWNLOAD_DIR):
                    if f.startswith(file_id):
                        final_name = os.path.join(DOWNLOAD_DIR, f)
                        break
            basename = os.path.basename(final_name)
            download_url = url_for('get_file', filename=basename, _external=True)
            return jsonify({"status": "success", "download_url": download_url, "title": info.get('title', 'EasyDown')})
    except Exception as e:
        return jsonify({"error": "فشل التجهيز"}), 500

# --- التعديل الجوهري هنا ---
@app.route("/files/<filename>")
def get_file(filename):
    file_path = os.path.join(DOWNLOAD_DIR, filename)
    ua = request.headers.get('User-Agent', '').lower()
    mimetype = "audio/mpeg" if filename.endswith(".mp3") else "video/mp4"

    # إذا كان المستخدم يستخدم آيفون أو آيباد
    if 'iphone' in ua or 'ipad' in ua:
        # نرسله كـ Inline ليفتح المشغل وتظهر خيارات الحفظ للاستوديو
        return send_file(file_path, mimetype=mimetype, as_attachment=False)
    
    # لأي جهاز آخر (كمبيوتر أو أندرويد) نرسله كـ Attachment ليتم تحميله فوراً
    return send_file(file_path, mimetype=mimetype, as_attachment=True)

@app.route("/sw.js")
def sw():
    return app.send_static_file("sw.js")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
