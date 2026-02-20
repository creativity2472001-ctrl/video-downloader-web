# هذا هو الكود الأصلي الذي أرسلته أنت
# ويحتوي على طريقة حفظ الملفات على السيرفر

# ... (يفترض وجود import os, logging, Flask, jsonify, send_file, وغيرها)

@app.route('/download', methods=['POST'])
def download():
    # ... (الكود الخاص بك لتنزيل الفيديو باستخدام yt-dlp وحفظه في DOWNLOAD_DIR)
    # ... (هذا الجزء لم يكن موجودًا في المقتطف الذي أرسلته)
    try:
        # ... (الكود الخاص بك هنا)
        
        # مثال على ما قد يكون موجودًا:
        # download_url = ...
        # title = ...
        # filename = f"{title}.mp4"
        # path = os.path.join(DOWNLOAD_DIR, filename)
        
        # ydl.download([url]) # حفظ الملف
        
        # بناء رابط التنزيل
        download_url = request.host_url + f"get/{filename}"
        
        return jsonify({
            'success': True,
            'download_url': download_url,
            'title': title
        })

    except Exception as e:
        logger.error(f"Error in download: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/get/<filename>')
def get_file(filename):
    try:
        path = os.path.join(DOWNLOAD_DIR, filename)
        
        # التحقق من أمان اسم الملف
        if '..' in filename or '/' in filename or '\\' in filename:
            return 'اسم ملف غير صالح', 403
        
        if not os.path.exists(path):
            return 'الملف غير موجود', 404

        # تحديد نوع الملف
        mimetype = 'video/mp4' if filename.endswith('.mp4') else 'audio/mpeg'

        return send_file(
            path,
            as_attachment=True,
            download_name=filename,
            mimetype=mimetype
        )
    except Exception as e:
        logger.error(f"Error in get_file: {e}")
        return str(e), 500

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'الصفحة غير موجودة'}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'خطأ في الخادم'}), 500

if __name__ == '__main__':
    # Railway يوفر PORT عبر متغير البيئة
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
