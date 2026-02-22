from flask import Flask, render_template, send_file, jsonify, request
import os
import yt_dlp
import uuid
import time
import threading

app = Flask(__name__)

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

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
        }

        # إذا كان في ملف كوكيز، استخدمه
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

        # ✅ الرابط يشير لصفحة الفيديو مع زر الرجوع
        download_url = f"/video/{filename}"

        return jsonify({
            'success': True,
            'download_url': download_url,
            'title': title,
            'filename': filename
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ✅ صفحة مشاهدة الفيديو مع زر الرجوع
@app.route('/video/<filename>')
def video_page(filename):
    path = os.path.join(DOWNLOAD_DIR, filename)
    
    if not os.path.exists(path):
        return 'الملف غير موجود', 404

    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>EasyDown - فيديو</title>
        <style>
            body {{
                background: #1a1a2e;
                color: white;
                font-family: sans-serif;
                text-align: center;
                padding: 20px;
                margin: 0;
            }}
            .back-btn {{
                display: inline-block;
                margin: 20px auto;
                padding: 15px 30px;
                background: #00d2ff;
                color: white;
                text-decoration: none;
                border-radius: 50px;
                font-weight: bold;
                font-size: 1.2rem;
                border: none;
                cursor: pointer;
            }}
            video {{
                width: 100%;
                max-width: 600px;
                border-radius: 15px;
                background: black;
                margin: 20px 0;
            }}
        </style>
    </head>
    <body>
        <button onclick="window.location.href='/'" class="back-btn">🔙 رجوع للتطبيق</button>
        <video controls>
            <source src="/get-video/{filename}" type="video/mp4">
        </video>
    </body>
    </html>
    '''

@app.route('/get-video/<filename>')
def get_video_file(filename):
    path = os.path.join(DOWNLOAD_DIR, filename)
    return send_file(path, mimetype='video/mp4')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
