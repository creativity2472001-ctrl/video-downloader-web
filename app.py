from flask import Flask, render_template

# إنشاء التطبيق
app = Flask(__name__)

# الصفحة الرئيسية
@app.route("/")
def index():
    return render_template("index.html")  # سيرجع صفحة index.html

# تشغيل السيرفر
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
