from flask import Flask, render_template, request, send_file, jsonify, url_for
import os
import yt_dlp
import uuid

app = Flask(__name__)

# إعداد المجلدات اللازمة
DOWNLOAD_DIR = "downloads"
STATIC_DIR = "static"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# المواقع المدعومة
ALLOWED_DOMAINS = ["youtube.com", "youtu.be", "instagram.com", "tiktok.com", "pinterest.com", "likee.video", "facebook.com"]

def get_ydl_opts(mode, file_id):
    """إعداد خيارات التحميل مع حل مشكلة الترميز"""
    base_path = os.path.join(DOWNLOAD_DIR, f"{file_id}_%(title)s.%(ext)s")
    
    opts = {
        'outtmpl': base_path,
        'restrictfilenames': True,
        'noplaylist': True,
        'quiet': True,
    }

    if mode == "audio":
        opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}]
        })
    else:
        # التعديل الذهبي: إجبار الترميز على H.264 ليعمل على كل أجهزة الكمبيوتر والموبايل
        opts.update({
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'merge_output_format': 'mp4',
            'postprocessor_args': [
                '-vcodec', 'libx264',   # الترميز العالمي المتوافق
                '-acodec', 'aac',       # ترميز صوت متوافق
                '-pix_fmt', 'yuv420p'   # يضمن تشغيله على مشغلات ويندوز القديمة
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

    if not url or not any(domain in url.lower() for domain in ALLOWED_DOMAINS):
        return jsonify({"error": "رابط غير مدعوم"}), 400

    file_id = uuid.uuid4().hex[:8]
    try:
        ydl_opts = get_ydl_opts(mode, file_id)
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            # التأكد من الامتداد بعد المعالجة
            if mode == "audio":
                filename = filename.rsplit(".", 1)[0] + ".mp3"
            else:
                filename = filename.rsplit(".", 1)[0] + ".mp4"
            
            basename = os.path.basename(filename)
            # التأكد من وجود الملف فعلياً قبل إرسال الرابط
            if os.path.exists(os.path.join(DOWNLOAD_DIR, basename)):
                download_url = url_for('get_file', filename=basename, _external=True)
                return jsonify({
                    "status": "success",
                    "download_url": download_url,
                    "title": info.get('title', 'EasyDown_File')
                })
            else:
                return jsonify({"error": "حدث خطأ في معالجة الملف"}), 500

    except Exception as e:
        print(f"Error: {str(e)}") # للتشخيص
        return jsonify({"error": "فشل التحميل، تأكد من أن الرابط عام وليس خاص"}), 500

@app.route("/files/<filename>")
def get_file(filename):
    """تقديم الملف للتحميل من مجلد downloads"""
    return send_file(os.path.join(DOWNLOAD_DIR, filename), as_attachment=True)

# مسار خاص للـ Service Worker لضمان ظهور زر "تثبيت التطبيق"
@app.route("/sw.js")
def sw():
    return app.send_static_file("sw.js")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
