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

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title', 'video')

        filename = None
        for f in os.listdir(DOWNLOAD_DIR):
            if f.startswith(file_id):
                filename = f
                break

        download_url = f"/video/{filename}"

        return jsonify({
            'success': True,
            'download_url': download_url,
            'title': title
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/video/<filename>')
def video_page(filename):
    path = os.path.join(DOWNLOAD_DIR, filename)
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
        <video controls>
            <source src="/{DOWNLOAD_DIR}/{filename}" type="video/mp4">
        </video>
    </body>
    </html>
    '''

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
