from flask import Flask, render_template, request, send_file, jsonify
import os
import yt_dlp
import uuid
import time
import threading
import re
from datetime import datetime

app = Flask(__name__)

# إعدادات المجلدات
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# قائمة المواقع المدعومة
SUPPORTED_SITES = [
    {"name": "YouTube", "icon": "fab fa-youtube", "domains": ["youtube.com", "youtu.be"]},
    {"name": "TikTok", "icon": "fab fa-tiktok", "domains": ["tiktok.com", "vm.tiktok.com"]},
    {"name": "Instagram", "icon": "fab fa-instagram", "domains": ["instagram.com"]},
    {"name": "Facebook", "icon": "fab fa-facebook", "domains": ["facebook.com", "fb.watch"]},
    {"name": "Twitter/X", "icon": "fab fa-twitter", "domains": ["twitter.com", "x.com"]},
    {"name": "Snapchat", "icon": "fab fa-snapchat", "domains": ["snapchat.com"]},
    {"name": "Pinterest", "icon": "fab fa-pinterest", "domains": ["pinterest.com"]},
    {"name": "Reddit", "icon": "fab fa-reddit", "domains": ["reddit.com"]}
]

ALLOWED_DOMAINS = []
for site in SUPPORTED_SITES:
    ALLOWED_DOMAINS.extend(site["domains"])

# تنظيف الملفات القديمة (كل ساعة)
def cleanup_old_files():
    while True:
        try:
            now = time.time()
            for filename in os.listdir(DOWNLOAD_DIR):
                file_path = os.path.join(DOWNLOAD_DIR, filename)
                if os.path.isfile(file_path):
                    file_age = now - os.path.getmtime(file_path)
                    if file_age > 3600:  # ساعة واحدة
                        os.remove(file_path)
                        print(f"🗑️ تم حذف الملف القديم: {filename}")
        except Exception as e:
            print(f"خطأ في التنظيف: {e}")
        time.sleep(1800)  # كل 30 دقيقة

# بدء خيط التنظيف
threading.Thread(target=cleanup_old_files, daemon=True).start()

def is_valid_url(url):
    """التحقق من صحة الرابط"""
    if not url or not isinstance(url, str):
        return False
    url = url.lower()
    return any(domain in url for domain in ALLOWED_DOMAINS)

def clean_filename(filename):
    """تنظيف اسم الملف من الرموز غير المسموح بها"""
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    return filename.strip()[:100]  # تحديد طول اسم الملف

@app.route('/')
def index():
    """الصفحة الرئيسية"""
    return render_template('index.html', supported_sites=SUPPORTED_SITES)

@app.route('/api/info', methods=['POST'])
def get_video_info():
    """الحصول على معلومات الفيديو"""
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        
        if not url:
            return jsonify({'error': '⚠️ يرجى إدخال رابط'}), 400
        
        if not is_valid_url(url):
            return jsonify({'error': '❌ هذا الرابط غير مدعوم'}), 400
        
        # إعدادات yt-dlp
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
        
        # استخراج المعلومات
        title = info.get('title', 'فيديو')
        duration = info.get('duration', 0)
        minutes = duration // 60
        seconds = duration % 60
        duration_str = f"{minutes}:{seconds:02d}"
        
        # تحديد موقع المصدر
        source = 'موقع آخر'
        for site in SUPPORTED_SITES:
            if any(domain in url.lower() for domain in site['domains']):
                source = site['name']
                break
        
        return jsonify({
            'success': True,
            'title': title,
            'duration': duration_str,
            'source': source,
            'thumbnail': info.get('thumbnail', '')
        })
        
    except Exception as e:
        return jsonify({'error': f'❌ خطأ: {str(e)}'}), 400

@app.route('/api/download', methods=['POST'])
def download_video():
    """تحميل الفيديو أو الصوت"""
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        mode = data.get('mode', 'video')
        
        if not url:
            return jsonify({'error': '⚠️ يرجى إدخال رابط'}), 400
        
        if not is_valid_url(url):
            return jsonify({'error': '❌ هذا الرابط غير مدعوم'}), 400
        
        # إنشاء معرف فريد للملف
        file_id = uuid.uuid4().hex[:10]
        
        # إعدادات التحميل
        ydl_opts = {
            'outtmpl': os.path.join(DOWNLOAD_DIR, f'{file_id}.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
            'extract_flat': False,
        }
        
        # إعدادات خاصة حسب نوع التحميل
        if mode == 'audio':
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            })
        else:
            ydl_opts.update({
                'format': 'best[ext=mp4]/best',
            })
        
        # تحميل الفيديو
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = clean_filename(info.get('title', 'video'))
        
        # البحث عن الملف المحمل
        filename = None
        for f in os.listdir(DOWNLOAD_DIR):
            if f.startswith(file_id):
                filename = f
                break
        
        if not filename:
            return jsonify({'error': '❌ فشل في إنشاء الملف'}), 500
        
        # إنشاء رابط التحميل
        download_url = f"/api/get/{filename}"
        
        return jsonify({
            'success': True,
            'download_url': download_url,
            'title': title,
            'mode': mode
        })
        
    except Exception as e:
        return jsonify({'error': f'❌ فشل التحميل: {str(e)}'}), 500

@app.route('/api/get/<filename>')
def get_file(filename):
    """تحميل الملف"""
    try:
        # التحقق من أمان اسم الملف
        if '..' in filename or '/' in filename or '\\' in filename:
            return '❌ اسم ملف غير صالح', 403
        
        file_path = os.path.join(DOWNLOAD_DIR, filename)
        
        if not os.path.exists(file_path):
            return '❌ الملف غير موجود', 404
        
        # تحديد نوع الملف
        if filename.endswith('.mp3'):
            mimetype = 'audio/mpeg'
        elif filename.endswith('.mp4'):
            mimetype = 'video/mp4'
        else:
            mimetype = 'application/octet-stream'
        
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename,
            mimetype=mimetype
        )
        
    except Exception as e:
        return f'❌ خطأ: {str(e)}', 500

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': '❌ الصفحة غير موجودة'}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': '❌ خطأ في الخادم'}), 500

if __name__ == '__main__':
    print('=' * 50)
    print('🚀 EasyDown - تطبيق تحميل الفيديوهات')
    print('=' * 50)
    print('📱 متوفر على:')
    print(f'   - محلياً: http://127.0.0.1:5000')
    print('   - على الشبكة: http://[عنوان IP]:5000')
    print('=' * 50)
    
    app.run(host='0.0.0.0', port=5000, debug=True)
