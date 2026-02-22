from flask import Flask, render_template, send_file, jsonify, request
import os
import yt_dlp
import uuid
import time
import threading

app = Flask(__name__)

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# ===============================
# تنظيف الملفات القديمة كل 30 دقيقة
# ===============================
def cleanup_old_files():
    while True:
        now = time.time()
        for filename in os.listdir(DOWNLOAD_DIR):
            path = os.path.join(DOWNLOAD_DIR, filename)
            if os.path.isfile(path):
                if now - os.path.getmtime(path) > 1800:  # 30 دقيقة
                    os.remove(path)
        time.sleep(1800)

threading.Thread(target=cleanup_old_files, daemon=True).start()

# ===============================
# الصفحة الرئيسية
# ===============================
@app.route('/')
def index():
    return render_template('index.html')

# ===============================
# تحميل الفيديو
# ===============================
@app.route('/download', methods=['POST'])
def download():
    data = request.get_json()
    url = data.get('url')

    file_id = uuid.uuid4().hex[:8]
    base = os.path.join(DOWNLOAD_DIR, file_id)

    try:
        ydl_opts = {
            'outtmpl': f"{base}.%(ext)s",
            'format': 'best[ext=mp4]/best',
            'quiet': True,
            'noplaylist': True
        }

        if os.path.exists('cookies.txt'):
            ydl_opts['cookiefile'] = 'cookies.txt'

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title', 'video')

        filename = None
        for f in os.listdir(DOWNLOAD_DIR):
            if f.startswith(file_id):
                filename = f
                break

        if not filename:
            return jsonify({'error': 'File not found'}), 500

        return jsonify({
            'success': True,
            'download_url': f"/v/{filename}",
            'filename': filename,
            'title': title
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===============================
# تقديم الفيديو
# ===============================
@app.route('/v/<filename>')
def get_video(filename):
    path = os.path.join(DOWNLOAD_DIR, filename)
    return send_file(
        path,
        mimetype='video/mp4',
        as_attachment=False,
        download_name=filename
    )

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
