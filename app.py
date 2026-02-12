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

# النطاقات المدعومة
ALLOWED_DOMAINS = [
    "youtube.com", "youtu.be", "instagram.com", "tiktok.com",
    "pinterest.com", "likee.video", "facebook.com", "fb.watch",
    "x.com", "twitter.com"
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
    # استخدام اسم ملف بسيط لتجنب مشاكل اللغة العربية في الروابط
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
        # السر الأول: ترميز H.264 ليعمل الفيديو في استوديو الآيفون والأندرويد فوراً
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
    url, mode = data.get("url"), data.get("mode", "video")

    if not url:
        return jsonify({"error": "❌ الرابط مطلوب"}), 400

    file_id = uuid.uuid4().hex[:8]
    try:
        ydl_opts = get_ydl_opts(mode, file_id)
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            
            # تحديد الامتداد النهائي
            ext = "mp3" if mode == "audio" else "mp4"
            filename = f"{file_id}.{ext}"
            
            # إنشاء رابط تحميل خارجي كامل
            download_url = url_for('get_file', filename=filename, _external=True)

            return jsonify({
                "status": "success",
                "download_url": download_url,
                "title": info.get('title', 'EasyDown File')
            })
    except Exception as e:
        return jsonify({"error": f"❌ فشل السيرفر: {str(e)}"}), 500

@app.route("/files/<filename>")
def get_file(filename):
    file_path = os.path.join(DOWNLOAD_DIR, filename)
    if not os.path.exists(file_path):
        return "❌ الملف غير موجود", 404

    # السر الثاني: إجبار المتصفح على "التنزيل" (Attachment) بدلاً من "المشاهدة"
    mimetype = "audio/mpeg" if filename.endswith(".mp3") else "video/mp4"
    
    response = make_response(send_file(
        file_path,
        mimetype=mimetype,
        as_attachment=True,
        download_name=filename
    ))
    
    # هيدرات إضافية لضمان عمل التحميل في Safari و Chrome Mobile
    response.headers["Content-Disposition"] = f"attachment; filename={filename}"
    response.headers["X-Content-Type-Options"] = "nosniff"
    
    return response

@app.route("/sw.js")
def sw():
    return app.send_static_file("sw.js")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
