from flask import Flask, render_template, request, send_file, after_this_request
import os
import yt_dlp
import uuid

app = Flask(__name__)

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

ALLOWED_DOMAINS = ["youtube.com", "youtu.be", "instagram.com", "tiktok.com", "pinterest.com", "likee.video"]

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

def sanitize_filename(name):
    """إزالة الرموز الغريبة وإضافة UUID لتجنب التعارض"""
    safe_name = "".join(c for c in name if c.isalnum() or c in "-_ ")
    return f"{safe_name}_{uuid.uuid4().hex}"

def download_media(url, mode="video"):
    options = VIDEO_OPTIONS if mode=="video" else AUDIO_OPTIONS
    with yt_dlp.YoutubeDL(options) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        if mode == "audio":
            filename = filename.rsplit(".", 1)[0] + ".mp3"
        return filename

def is_valid_url(url):
    try:
        from urllib.parse import urlparse
        hostname = urlparse(url).hostname
        return any(domain in hostname for domain in ALLOWED_DOMAINS)
    except:
        return False

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/download", methods=["POST"])
def download():
    url = request.form.get("videoUrl")
    mode = request.form.get("mode", "video")

    if not url or not is_valid_url(url):
        return "❌ الرابط غير مدعوم", 400

    try:
        file_path = download_media(url, mode)

        @after_this_request
        def remove_file(response):
            try:
                os.remove(file_path)
            except Exception as e:
                print("Failed to delete file:", e)
            return response

        return send_file(file_path, as_attachment=True)
    except yt_dlp.utils.DownloadError:
        return "❌ الرابط غير صالح أو الفيديو غير متاح", 400
    except Exception as e:
        return f"❌ حدث خطأ أثناء التحميل: {str(e)}", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
