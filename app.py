from flask import Flask, render_template, request, send_file
import os
import yt_dlp

app = Flask(__name__)
DOWNLOAD_DIR = "downloads"
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

def download_media(url, mode="video"):
    options = VIDEO_OPTIONS if mode=="video" else AUDIO_OPTIONS
    with yt_dlp.YoutubeDL(options) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        if mode=="audio":
            filename = filename.rsplit(".",1)[0] + ".mp3"
        return filename

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/download", methods=["POST"])
def download():
    url = request.form.get("videoUrl")
    mode = request.form.get("mode")  # "video" أو "audio"
    try:
        file_path = download_media(url, mode)
        return send_file(file_path, as_attachment=True)
    except Exception as e:
        return f"❌ فشل التحميل: {str(e)}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
