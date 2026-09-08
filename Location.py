import subprocess
import sys
import os
import datetime
import json

# تثبيت المكتبات المطلوبة تلقائياً لو مش موجودة
try:
    from flask import Flask, request, jsonify
    from flask_cors import CORS
    import requests
except ImportError:
    print("جاري تثبيت المكتبات المطلوبة...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "flask", "flask-cors", "requests"])
    from flask import Flask, request, jsonify
    from flask_cors import CORS
    import requests

app = Flask(__name__)
CORS(app)  # السماح بطلبات من أي نطاق (مثل GitHub Pages)

LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

def get_location(ip):
    """الحصول على الموقع التقريبي من IP باستخدام خدمة ip-api.com"""
    try:
        response = requests.get(f'http://ip-api.com/json/{ip}', timeout=5)
        data = response.json()
        if data['status'] == 'success':
            return f"{data['city']}, {data['regionName']}, {data['country']}"
        else:
            return "Unknown"
    except Exception:
        return "Unknown"

@app.route('/')
def home():
    return "<h1>الخادم يعمل بنجاح</h1>"

@app.route('/log', methods=['POST', 'OPTIONS'])
def log_data():
    """استقبال البيانات من صفحة HTML و تسجيلها في ملف"""
    if request.method == 'OPTIONS':
        return '', 200

    try:
        if request.is_json:
            data = request.get_json()
            ip = data.get('ip', request.remote_addr)
            user_agent = data.get('userAgent', request.headers.get('User-Agent'))
            timestamp = data.get('timestamp', datetime.datetime.now().isoformat())
        else:
            ip = request.remote_addr
            user_agent = request.headers.get('User-Agent')
            timestamp = datetime.datetime.now().isoformat()

        location = get_location(ip)

        record = {
            "timestamp": timestamp,
            "ip": ip,
            "location": location,
            "user_agent": user_agent
        }

        log_file = os.path.join(LOG_DIR, "captured_data.json")
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')

        print(f"[✓] تم تسجيل بيانات: {ip} - {location}")
        return jsonify({"status": "success"}), 200

    except Exception as e:
        print(f"[✗] خطأ: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/view')
def view_data():
    """عرض البيانات المسجلة في صفحة ويب بسيطة"""
    log_file = os.path.join(LOG_DIR, "captured_data.json")
    records = []

    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
    except FileNotFoundError:
        pass

    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>البيانات المسجلة</title>
        <style>
            body { font-family: Arial; background: #f4f4f4; padding: 20px; }
            table { width: 100%; border-collapse: collapse; background: white; }
            th { background: #007bff; color: white; padding: 10px; }
            td, th { border: 1px solid #ddd; padding: 8px; text-align: left; }
            tr:nth-child(even) { background: #f2f2f2; }
        </style>
    </head>
    <body>
        <h2>البيانات المسجلة</h2>
        <table>
            <tr><th>التوقيت</th><th>IP</th><th>الموقع</th><th>المتصفح</th></tr>
    """
    for r in records:
        html += f"<tr><td>{r.get('timestamp','')}</td><td>{r.get('ip','')}</td><td>{r.get('location','')}</td><td>{r.get('user_agent','')}</td></tr>"
    html += """
        </table>
        <p><a href="/">الصفحة الرئيسية</a></p>
    </body>
    </html>
    """
    return html

if __name__ == '__main__':
    print("🚀 الخادم يعمل على المنفذ 8080...")
    app.run(host='0.0.0.0', port=8080, debug=False)
