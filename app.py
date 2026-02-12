from flask import Flask, render_template, request, send_file, jsonify, url_for
import os
import yt_dlp
import uuid
import threading
import time

app = Flask(__name__)

# إعداد مجلد التحميلات
DOWNLOAD_DIR = "downloads"
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

# قائمة النطاقات المدعومة
ALLOWED_DOMAINS = [
    "youtube.com", "youtu.be", "instagram.com", "tiktok.com",
    "pinterest.com", "likee.video", "facebook.com"
]

# مدة الاحتفاظ بالملفات (بالساعات)
FILE_EXPIRY_HOURS = 6


def get_ydl_opts(mode, file_id):
    """إعداد خيارات التحميل بناءً على فيديو أو صوت"""
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
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        })
    else:
        # تحميل أفضل جودة فيديو MP4 متاحة
        opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'

    return opts


def is_valid_url(url):
    return any(domain in url.lower() for domain in ALLOWED_DOMAINS)


def clean_old_files():
    """حذف الملفات الأقدم من FILE_EXPIRY_HOURS"""
    now = time.time()
    for filename in os.listdir(DOWNLOAD_DIR):
        file_path = os.path.join(DOWNLOAD_DIR, filename)
        if os.path.isfile(file_path):
            file_age = (now - os.path.getmtime(file_path)) / 3600
            if file_age > FILE_EXPIRY_HOURS:
                try:
                    os.remove(file_path)
                    print(f"🗑️ تم حذف الملف القديم: {filename}")
                except Exception as e:
                    print(f"⚠️ خطأ أثناء حذف {filename}: {e}")


def process_download(url, mode, file_id, results):
    """تشغيل التحميل في الخلفية"""
    try:
        ydl_opts = get_ydl_opts(mode, file_id)
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

            if mode == "audio":
                filename = filename.rsplit(".", 1)[0] + ".mp3"

            basename = os.path.basename(filename)
            download_url = url_for('get_file', filename=basename, _external=True)

            results["status"] = "success"
            results["download_url"] = download_url
            results["title"] = info.get('title', 'EasyDown_File')

    except Exception as e:
        results["status"] = "error"
        results["message"] = str(e)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/download", methods=["POST"])
def download():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    url = data.get("url")
    mode = data.get("mode", "video")

    if not url or not is_valid_url(url):
        return jsonify({"error": "رابط غير مدعوم أو غير صحيح"}), 400

    file_id = uuid.uuid4().hex[:8]
    results = {}

    # تشغيل التحميل في الخلفية
    thread = threading.Thread(target=process_download, args=(url, mode, file_id, results))
    thread.start()
    thread.join()  # يمكن لاحقًا جعله غير متزامن بالكامل

    clean_old_files()  # تنظيف الملفات القديمة

    if results.get("status") == "success":
        return jsonify(results)
    else:
        return jsonify({"error": results.get("message", "فشل السيرفر في معالجة الرابط")}), 500


@app.route("/files/<filename>")
def get_file(filename):
    file_path = os.path.join(DOWNLOAD_DIR, filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    return "الملف غير موجود أو تم حذفه", 404


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
