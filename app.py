from flask import Flask, render_template, request, send_file, jsonify
from flask_cors import CORS
import os
import yt_dlp
import uuid
import time
import threading
from datetime import datetime
import logging

# تكوين السجلات
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder='.', static_folder='static')
CORS(app)

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

ALLOWED_DOMAINS = [
    "youtube.com", "youtu.be",
    "tiktok.com", "vm.tiktok.com", "vt.tiktok.com",
    "instagram.com", "www.instagram.com",
    "facebook.com", "fb.watch", "www.facebook.com",
    "twitter.com", "x.com", "www.twitter.com",
    "snapchat.com", "www.snapchat.com"
]

# تنظيف الملفات القديمة (كل ساعة)
def cleanup():
    """حذف الملفات التي مضى عليها أكثر من ساعة"""
    while True:
        try:
            now = time.time()
            for f in os.listdir(DOWNLOAD_DIR):
                path = os.path.join(DOWNLOAD_DIR, f)
                if os.path.isfile(path):
                    file_age = now - os.stat(path).st_mtime
                    if file_age > 3600:  # ساعة واحدة
                        try:
                            os.remove(path)
                            logger.info(f"تم حذف الملف القديم: {f}")
                        except Exception as e:
                            logger.error(f"خطأ في حذف الملف {f}: {e}")
        except Exception as e:
            logger.error(f"خطأ في عملية التنظيف: {e}")
        
        time.sleep(1800)  # كل 30 دقيقة

# بدء خيط التنظيف
cleanup_thread = threading.Thread(target=cleanup, daemon=True)
cleanup_thread.start()

def is_valid_url(url):
    """التحقق من صحة الرابط"""
    if not url or not isinstance(url, str):
        return False
    return any(domain in url for domain in ALLOWED_DOMAINS)

@app.route("/")
def index():
    """الصفحة الرئيسية"""
    try:
        return render_template("index.html")
    except Exception as e:
        logger.error(f"خطأ في تحميل الصفحة الرئيسية: {e}")
        return "خطأ في تحميل الصفحة", 500

@app.route("/api/info", methods=["POST"])
def video_info():
    """الحصول على معلومات الفيديو"""
    try:
        data = request.get_json()
        url = data.get("url", "").strip()
        
        if not url:
            return jsonify({"error": "⚠️ يرجى إدخال رابط صحيح"}), 400
        
        if not is_valid_url(url):
            return jsonify({"error": "❌ هذا الرابط غير مدعوم"}), 400
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'socket_timeout': 30
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
        duration = info.get('duration', 0)
        minutes = duration // 60
        seconds = duration % 60
        
        return jsonify({
            "status": "success",
            "title": info.get('title', 'فيديو'),
            "duration": f"{minutes}:{seconds:02d}",
            "duration_seconds": duration,
            "thumbnail": info.get('thumbnail', '')
        })
    
    except Exception as e:
        logger.error(f"خطأ في الحصول على معلومات الفيديو: {e}")
        return jsonify({"error": f"❌ لا يمكن الحصول على معلومات الفيديو: {str(e)}"}), 400

@app.route("/api/download", methods=["POST"])
def download():
    """تحميل الفيديو أو الصوت"""
    try:
        data = request.get_json()
        url = data.get("url", "").strip()
        mode = data.get("mode", "video")
        
        # التحقق من صحة البيانات
        if not url:
            return jsonify({"error": "⚠️ يرجى إدخال رابط صحيح"}), 400
        
        if not is_valid_url(url):
            return jsonify({"error": "❌ هذا الرابط غير مدعوم"}), 400
        
        if mode not in ["video", "audio"]:
            return jsonify({"error": "❌ نمط غير صحيح"}), 400
        
        # إنشاء معرّف فريد للملف
        file_id = uuid.uuid4().hex[:12]
        base_path = os.path.join(DOWNLOAD_DIR, file_id)
        
        try:
            # إعدادات التحميل الأساسية
            ydl_opts = {
                'outtmpl': f"{base_path}.%(ext)s",
                'quiet': False,
                'no_warnings': True,
                'noplaylist': True,
                'socket_timeout': 30,
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            }
            
            # إعدادات خاصة بالصوت
            if mode == "audio":
                ydl_opts.update({
                    'format': 'bestaudio/best',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                })
            else:
                # إعدادات خاصة بالفيديو
                ydl_opts.update({
                    'format': 'best[ext=mp4]/best',
                    'merge_output_format': 'mp4',
                })
            
            # تحميل الفيديو
            logger.info(f"بدء تحميل الفيديو: {url}")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                title = info.get('title', 'video')
            
            # البحث عن الملف المُنشأ
            filename = None
            expected_ext = "mp3" if mode == "audio" else "mp4"
            
            for f in os.listdir(DOWNLOAD_DIR):
                if f.startswith(file_id):
                    filename = f
                    break
            
            if not filename:
                logger.error(f"لم يتم العثور على الملف المُنشأ: {file_id}")
                return jsonify({"error": "❌ فشل في إنشاء الملف"}), 500
            
            # ✅ إنشاء رابط التحميل الكامل (المعدل)
            # استخدام request.host_url بدلاً من f"http://{request.host}" لضمان البروتوكول الصحيح
            base_url = request.host_url.rstrip('/')
            download_url = f"{base_url}/api/get/{filename}"
            
            logger.info(f"تم تحميل الملف بنجاح: {filename}")
            
            return jsonify({
                "status": "success",
                "download_url": download_url,
                "title": title,
                "filename": filename
            })
        
        except Exception as e:
            logger.error(f"خطأ في التحميل: {e}")
            return jsonify({"error": f"❌ فشل في تحميل الفيديو: {str(e)}"}), 500
    
    except Exception as e:
        logger.error(f"خطأ عام في معالجة الطلب: {e}")
        return jsonify({"error": "❌ حدث خطأ في معالجة الطلب"}), 500

@app.route("/api/get/<filename>")
def get_file(filename):
    """تحميل الملف"""
    try:
        # التحقق من أمان اسم الملف (منع Path Traversal)
        if ".." in filename or "/" in filename or "\\" in filename:
            return "اسم ملف غير صحيح", 403
        
        path = os.path.join(DOWNLOAD_DIR, filename)
        
        # التحقق من وجود الملف
        if not os.path.exists(path):
            logger.warning(f"محاولة الوصول إلى ملف غير موجود: {filename}")
            return jsonify({"error": "الملف غير موجود"}), 404
        
        # تحديد نوع الملف
        if filename.endswith(".mp3"):
            mimetype = "audio/mpeg"
        elif filename.endswith(".mp4"):
            mimetype = "video/mp4"
        else:
            mimetype = "application/octet-stream"
        
        logger.info(f"تحميل الملف: {filename}")
        
        return send_file(
            path,
            as_attachment=True,
            download_name=filename,
            mimetype=mimetype
        )
    
    except Exception as e:
        logger.error(f"خطأ في تحميل الملف: {e}")
        return jsonify({"error": "خطأ في تحميل الملف"}), 500

@app.errorhandler(404)
def not_found(error):
    """معالج الأخطاء 404"""
    return jsonify({"error": "المسار غير موجود"}), 404

@app.errorhandler(500)
def server_error(error):
    """معالج الأخطاء 500"""
    logger.error(f"خطأ في السيرفر: {error}")
    return jsonify({"error": "خطأ في السيرفر"}), 500

if __name__ == "__main__":
    # تشغيل السيرفر
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True,
        threaded=True
    )
