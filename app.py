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
            .restart-btn {{
                display: inline-block;
                margin: 20px auto;
                padding: 15px 30px;
                background: #28a745;
                color: white;
                text-decoration: none;
                border-radius: 50px;
                font-weight: bold;
                font-size: 1.2rem;
                border: none;
                cursor: pointer;
            }}
        </style>
    </head>
    <body>
        <video controls>
            <source src="/get-video/{filename}" type="video/mp4">
        </video>
        
        <button onclick="window.location.href='/'" class="restart-btn">
            🔄 الرجوع للصفحة الرئيسية
        </button>
        
        <div style="margin-top: 30px; color: #ccc; font-size: 0.9rem;">
            <p>🔹 لحفظ الفيديو: اضغط على الثلاث نقاط (⋮) في مشغل الفيديو</p>
            <p>🔹 اختر "Save Video"</p>
        </div>
    </body>
    </html>
    '''
