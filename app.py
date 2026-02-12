from flask import Flask, render_template, request, send_file, jsonify, after_this_request
import os
import yt_dlp
import threading
import uuid

app = Flask(__name__)

DOWNLOAD_DIR = "downloads"
MAX_FILESIZE = 500 * 1024 * 1024  # 500MB
ALLOWED_DOMAINS = ["instagram.com", "tiktok.com", "youtube.com", "pinterest.com", "likee.video"]
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

VIDEO_OPTIONS = {
    'format': 'best[ext=mp4]/best',
    'outtmpl': f'{DOWNLOAD_DIR}/%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
}

AUDIO_OPTIONS = {
    'format': 'bestaudio/best',
    'outtmpl': f'{DOWNLOAD_DIR}/%(title)s.%(ext)s',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
    'restrictfilenames': True,
    'noplaylist': True,
}

def is_valid_url(url):
    try:
        u = url.lower()
        return any(domain in u for domain in ALLOWED_DOMAINS)
    except:
        return False

def download_media(url, mode="video"):
    options = VIDEO_OPTIONS if mode=="video" else AUDIO_OPTIONS
    with yt_dlp.YoutubeDL(options) as ydl:
        info = ydl.extract_info(url, download=False)
        filesize = info.get("filesize") or info.get("filesize_approx") or 0
        if filesize > MAX_FILESIZE:
            raise ValueError("حجم الفيديو أكبر من الحد المسموح به (500MB).")
        ydl.download([url])
        filename = ydl.prepare_filename(info)
        if mode == "audio":
            filename = filename.rsplit(".", 1)[0] + ".mp3"
        return filename

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/get_qualities", methods=["POST"])
def get_qualities():
    url = request.form.get("videoUrl")
    mode = request.form.get("mode")
    if not is_valid_url(url):
        return jsonify({"qualities": [], "error": "الرابط غير مدعوم"})
    try:
        options = VIDEO_OPTIONS if mode == "video" else AUDIO_OPTIONS
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get("formats", [])
            qualities = []
            for f in formats:
                if mode=="video" and f.get("ext")=="mp4":
                    q = f.get("format_note") or f.get("height")
                    if q and str(q) not in qualities:
                        qualities.append(str(q))
                elif mode=="audio":
                    abr = f.get("abr")
                    if abr and str(abr)+"kbps" not in qualities:
                        qualities.append(str(abr)+"kbps")
            if not qualities:
                qualities = ["Unavailable"]
            return jsonify({"qualities": qualities})
    except Exception as e:
        return jsonify({"qualities": [], "error": str(e)})

@app.route("/download", methods=["POST"])
def download():
    url = request.form.get("videoUrl")
    mode = request.form.get("mode")
    if not url or not mode:
        return "❌ الرجاء إدخال رابط صالح واختيار نوع التحميل"
    if not is_valid_url(url):
        return "❌ الرابط غير مدعوم"

    result = {}
    def worker():
        try:
            file_path = download_media(url, mode)
            result["file_path"] = file_path
        except Exception as e:
            result["error"] = str(e)

    thread = threading.Thread(target=worker)
    thread.start()
    thread.join()  # للبساطة الآن، لاحقًا يمكن إزالة join لدعم تحميلات متعددة

    if "error" in result:
        return f"❌ فشل التحميل: {result['error']}"

    file_path = result.get("file_path")

    @after_this_request
    def cleanup(response):
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            print("Cleanup error:", e)
        return response

    return send_file(file_path, as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
