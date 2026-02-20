import os
import logging
from flask import Flask, request, jsonify, Response
import requests
from yt_dlp import YoutubeDL

# --- الإعدادات الأساسية ---
app = Flask(__name__)

# إعداد تسجيل الأخطاء (Logging)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- المسار الأول: للحصول على رابط الفيديو المباشر (معدل) ---
@app.route('/api/download', methods=['POST'])
def get_video_info():
    data = request.get_json()
    url = data.get('url')
    quality = data.get('quality', 'best')

    if not url:
        return jsonify({'success': False, 'error': 'URL is required'}), 400

    try:
        logger.info(f"Fetching info for URL: {url} with quality: {quality}")

        # إعدادات yt-dlp لاستخراج الرابط فقط
        ydl_opts = {
            'format': f'bestvideo[height<={quality[:-1]}][ext=mp4]+bestaudio[ext=m4a]/best[height<={quality[:-1]}][ext=mp4]/best',
            'quiet': True,
            'no_warnings': True,
            'logger': logger,
        }

        with YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            
            # الحصول على الرابط المباشر للفيديو
            direct_url = info_dict.get('url')
            title = info_dict.get('title', 'video')
            filename = f"{title}.mp4"

        if not direct_url:
            return jsonify({'success': False, 'error': 'Could not extract direct video URL.'}), 500

        logger.info(f"Successfully extracted direct URL for: {title}")
        
        # إرجاع الرابط المباشر إلى الواجهة الأمامية
        return jsonify({
            'success': True,
            'download_url': direct_url, # هذا هو الرابط المباشر للفيديو
            'filename': filename
        })

    except Exception as e:
        logger.error(f"Error in get_video_info: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# --- المسار الثاني: لإجبار تنزيل الفيديو (هذا هو الحل الحاسم) ---
@app.route('/api/force-download', methods=['GET'])
def force_download():
    video_url = request.args.get('url')
    filename = request.args.get('filename', 'video.mp4')

    if not video_url:
        return jsonify({"success": False, "error": "Video URL parameter is missing"}), 400

    try:
        logger.info(f"Streaming video to client from: {video_url}")

        # جلب الفيديو كـ stream لتجنب استهلاك الذاكرة
        response = requests.get(video_url, stream=True, timeout=30)
        response.raise_for_status() # التأكد من نجاح الطلب

        # إعداد الترويسات الصحيحة لإجبار التنزيل
        headers = {
            'Content-Disposition': f'attachment; filename="{filename}"',
            'Content-Type': response.headers.get('content-type', 'video/mp4'),
        }
        if 'content-length' in response.headers:
            headers['Content-Length'] = response.headers['content-length']

        # إرجاع استجابة تقوم ببث محتوى الفيديو مباشرة إلى المستخدم
        return Response(response.iter_content(chunk_size=8192), headers=headers)

    except requests.exceptions.RequestException as e:
        logger.error(f"Error streaming video: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to stream video data. The URL might be invalid or protected.",
            "reason": str(e)
        }), 500


# --- معالجة الأخطاء ---
@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'الصفحة غير موجودة'}), 404

@app.errorhandler(500)
def server_error(e):
    # إرجاع الخطأ كـ JSON ليكون متوافقًا
    return jsonify({'error': 'خطأ داخلي في الخادم'}), 500


if __name__ == '__main__':
    # Railway يوفر PORT عبر متغير البيئة
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
