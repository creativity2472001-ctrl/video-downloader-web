from flask import Flask, render_template, request, send_file, jsonify, url_for
import os
import yt_dlp
import uuid
import time
import threading

app = Flask(__name__)

# إعداد المجلدات
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# المواقع المدعومة
ALLOWED_DOMAINS = ["youtube.com", "youtu.be", "instagram.com", "tiktok.com", "pinterest.com", "likee.video", "facebook.com"]

def cleanup_old_files():
    """وظيفة لحذف الملفات القديمة (أقدم من ساعة) تلقائياً لتوفير المساحة"""
    while True:
        now = time.time()
        for f in os.listdir(DOWNLOAD_DIR):
            f_path = os.path.join(DOWNLOAD_DIR, f)
            if os.stat(f_path).st_mtime < now - 3600:
                try:
                    os.remove(f_path)
                except:
                    pass
        time.sleep(1800) # تنظيف كل 30 دقيقة

# تشغيل التنظيف في الخلفية
threading.Thread(target=cleanup_old_files, daemon=True).start()

def get_ydl_opts(mode, file_id):
    """إعدادات خرافية للسرعة والتوافق"""
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
        # معالجة الفيديو بسرعة Ultrafast لضمان عدم تأخر التحميل على الموبايل
        opts.update({
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'merge_output_format': 'mp4',
            'postprocessor_args': [
                '-vcodec', 'libx264',
                '-preset', 'ultrafast',  # السرعة الخرافية هنا
                '-crf', '28',            # توازن مثالي بين الحجم والجودة
                '-acodec', 'aac',
                '-pix_fmt', 'yuv420p'
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
        return jsonify({"error": "الرابط غير مدعوم أو غير صحيح"}), 400

    file_id = uuid.uuid4().hex[:8]
    
    try:
        ydl_opts = get_ydl_opts(mode, file_id)
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            # تصحيح الامتداد النهائي بعد المعالجة
            if mode == "audio":
                final_name = filename.rsplit(".", 1)[0] + ".mp3"
            else:
                final_name = filename.rsplit(".", 1)[0] + ".mp4"
            
            if not os.path.exists(final_name):
                # في بعض الحالات yt_dlp لا يغير الاسم في المخرجات البرمجية
                # هذا السطر للبحث عن الملف الفعلي بـ ID الفريد
                for f in os.listdir(DOWNLOAD_DIR):
                    if f.startswith(file_id):
                        final_name = os.path.join(DOWNLOAD_DIR, f)
                        break

            basename = os.path.basename(final_name)
            download_url = url_for('get_file', filename=basename, _external=True)
            
            return jsonify({
                "status": "success",
                "download_url": download_url,
                "title": info.get('title', 'EasyDown_File')
            })

    except Exception as e:
        print(f"DEBUG ERROR: {str(e)}")
        return jsonify({"error": "فشل التجهيز. تأكد من أن الفيديو عام وغير محظور"}), 500

@app.route("/files/<filename>")
def get_file(filename):
    """إرسال الملف مع إجبار الموبايل على التحميل المباشر"""
    return send_file(os.path.join(DOWNLOAD_DIR, filename), as_attachment=True)

@app.route("/sw.js")
def sw():
    return app.send_static_file("sw.js")

if __name__ == "__main__":
    # تشغيل السيرفر
    app.run(host="0.0.0.0", port=5000, debug=False)
