from flask import Flask, render_template, request, send_file, jsonify, url_for, make_response
import os
import yt_dlp
import uuid
import time
import threading
import json
from datetime import datetime

app = Flask(__name__)

# 1. إعدادات المجلدات
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# 2. النطاقات المدعومة
ALLOWED_DOMAINS = [
    "youtube.com", "youtu.be", "youtube-nocookie.com",
    "tiktok.com", "vm.tiktok.com",
    "instagram.com", "www.instagram.com", "instagr.am",
    "facebook.com", "fb.watch", "fb.com",
    "twitter.com", "x.com", "t.co",
    "pinterest.com", "pin.it",
    "likee.video", "likee.com",
    "t.me", "reddit.com", "v.redd.it",
    "snapchat.com", "www.snapchat.com",
    "vimeo.com", "dailymotion.com", "twitcasting.tv"
]

# 3. تنظيف الملفات القديمة
def cleanup_old_files():
    while True:
        now = time.time()
        for f in os.listdir(DOWNLOAD_DIR):
            f_path = os.path.join(DOWNLOAD_DIR, f)
            if os.path.isfile(f_path) and os.stat(f_path).st_mtime < now - 6*3600:
                try: os.remove(f_path)
                except: pass
        time.sleep(1800)

threading.Thread(target=cleanup_old_files, daemon=True).start()

# 4. إعدادات yt-dlp المحسنة للصوت والفيديو
def get_ydl_opts(mode, file_id):
    # نحدد الامتداد المؤقت لـ yt-dlp
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
                'preferredquality': '192',
            }],
            # هذا الخيار يضمن حذف ملف الفيديو الأصلي بعد استخراج الـ MP3
            'keepvideo': False, 
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

# 5. تتبع المستخدمين (نظام الإعلانات)
USERS_FILE = "users.json"

def load_users():
    if not os.path.exists(USERS_FILE): return {}
    try:
        with open(USERS_FILE, "r") as f: return json.load(f)
    except: return {}

def save_users(users):
    with open(USERS_FILE, "w") as f: json.dump(users, f)

def is_first_video_today(user_id):
    users = load_users()
    today = datetime.now().strftime("%Y-%m-%d")
    if user_id not in users or users[user_id]["date"] != today:
        users[user_id] = {"date": today, "count": 1}
        save_users(users)
        return True
    else:
        users[user_id]["count"] += 1
        save_users(users)
        return False

# 6. المسارات
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

    user_ip = request.remote_addr
    first_video = is_first_video_today(user_ip)

    # نظام الإعلانات: إذا لم يكن الفيديو الأول اطلب مشاهدة إعلان
    if not first_video:
        return jsonify({
            "status": "ad_required",
            "message": "🎬 يجب مشاهدة الإعلان قبل التنزيل"
        })

    file_id = uuid.uuid4().hex[:8]
    try:
        ydl_opts = get_ydl_opts(mode, file_id)
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

        # التأكد من الامتداد النهائي بعد المعالجة بـ FFmpeg
        final_ext = "mp3" if mode == "audio" else "mp4"
        filename = f"{file_id}.{final_ext}"
        file_path = os.path.join(DOWNLOAD_DIR, filename)

        # فحص إضافي للتأكد من نجاح التحويل بـ FFmpeg
        if not os.path.exists(file_path):
             return jsonify({"error": "❌ فشل استخراج الملف، تأكد من تثبيت FFmpeg"}), 500

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

    mimetype = "audio/mpeg" if filename.endswith(".mp3") else "video/mp4"
    
    response = make_response(send_file(
        file_path,
        mimetype=mimetype,
        as_attachment=True,
        download_name=filename
    ))

    response.headers["Content-Disposition"] = f"attachment; filename={filename}"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response

@app.route("/sw.js")
def sw():
    return app.send_static_file("sw.js")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
