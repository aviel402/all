import requests
import re
from flask import Flask, render_template_string, request, Response
from urllib.parse import urljoin

app = Flask(__name__)

def analyze_assets(html, base_url):
    """מחלץ תמונות וקבצים חיצוניים (JS/CSS)"""
    # חילוץ תמונות - חיפוש פשוט עם Regex
    img_urls = re.findall(r'<img [^>]*src=["\']([^"\']+)["\']', html, re.IGNORECASE)
    images = list(set([urljoin(base_url, img) for img in img_urls if img]))
    
    # חילוץ קבצים חיצוניים (Scripts & Stylesheets)
    scripts = re.findall(r'<script [^>]*src=["\']([^"\']+)["\']', html, re.IGNORECASE)
    styles = re.findall(r'<link [^>]*href=["\']([^"\']+)["\']', html, re.IGNORECASE)
    
    # איחוד רשימות וניקוי כפילויות
    all_externals = scripts + styles
    external_files = list(set([urljoin(base_url, f) for f in all_externals if f]))
    
    return images, external_files

HTML_PAGE = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>Web-Scanner Pro | Extract</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: #0f172a; color: #e2e8f0; font-family: system-ui, -apple-system, sans-serif; }
        .glass-card { background: rgba(30, 41, 59, 0.7); border-radius: 15px; border: 1px solid #334155; padding: 20px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); }
        .asset-list { max-height: 300px; overflow-y: auto; background: #1e293b; border-radius: 10px; padding: 15px; }
        
        /* גלילה מעוצבת */
        .asset-list::-webkit-scrollbar { width: 8px; }
        .asset-list::-webkit-scrollbar-track { background: #0f172a; }
        .asset-list::-webkit-scrollbar-thumb { background: #475569; border-radius: 4px; }

        .btn-action { background: linear-gradient(135deg, #00f2fe, #4facfe); border: none; color: white; margin-top: 5px; font-weight: bold; }
        .btn-action:hover { filter: brightness(1.1); color: white; }
        
        .file-link { color: #38bdf8; text-decoration: none; font-size: 0.9rem; display: block; margin-bottom: 8px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .file-link:hover { text-decoration: underline; color: #7dd3fc; }
        
        .raw-code-box { display: none; }
    </style>
</head>
<body class="container py-5">
    <h1 class="text-center mb-4 display-4 fw-bold" style="background: -webkit-linear-gradient(#00f2fe, #4facfe); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Web-Scanner Pro <small style="-webkit-text-fill-color: #64748b; font-size: 0.5em;">App 2</small></h1>
    
    <div class="glass-card mb-4">
        <form action="/app2" method="GET" class="row g-2">
            <div class="col-md-10">
                <input type="text" name="url" class="form-control bg-dark text-light border-secondary" placeholder="הכנס כתובת אתר (לדוגמה: ynet.co.il)..." value="{{ url }}" required>
            </div>
            <div class="col-md-2">
                <button type="submit" class="btn btn-action w-100 h-100">סרוק אתר 🔍</button>
            </div>
        </form>
    </div>

    {% if error %}
        <div class="alert alert-danger glass-card text-center border-danger text-danger bg-opacity-10">{{ error }}</div>
    {% endif %}

    {% if has_results %}
    <div class="row g-4">
        <div class="col-md-4">
            <div class="glass-card h-100 d-flex flex-column">
                <h4 class="mb-3 text-info">קוד מקור (HTML)</h4>
                <p class="text-secondary small">הקוד נסרק בהצלחה. ניתן להעתיק לקליפבורד או להוריד כקובץ מקומי.</p>
                <div class="mt-auto">
                    <button onclick="copyToClipboard()" class="btn btn-outline-info w-100 mb-2">העתק קוד לקליפבורד 📋</button>
                    <a href="/app2/download?url={{ url }}" class="btn btn-action w-100">הורד קובץ index.html 📥</a>
                </div>
            </div>
        </div>

        <div class="col-md-4">
            <div class="glass-card h-100">
                <h4 class="mb-3 text-warning">תמונות ({{ images|length }})</h4>
                <div class="asset-list">
                    {% if images %}
                        {% for img in images %}
                            <a href="{{ img }}" target="_blank" class="file-link" title="{{ img }}">🖼️ {{ img.split('/')[-1] or 'image' }}</a>
                        {% endfor %}
                    {% else %}
                        <div class="text-muted text-center mt-4">לא נמצאו תמונות</div>
                    {% endif %}
                </div>
            </div>
        </div>

        <div class="col-md-4">
            <div class="glass-card h-100">
                <h4 class="mb-3 text-success">קבצים חיצוניים ({{ externals|length }})</h4>
                <div class="asset-list">
                    {% if externals %}
                        {% for file in externals %}
                            <a href="{{ file }}" target="_blank" class="file-link" title="{{ file }}">🔗 {{ file.split('/')[-1] or 'file' }}</a>
                        {% endfor %}
                    {% else %}
                        <div class="text-muted text-center mt-4">לא נמצאו קבצים חיצוניים</div>
                    {% endif %}
                </div>
            </div>
        </div>
    </div>
    {% endif %}

    <textarea id="raw_code" class="raw-code-box">{{ html_content }}</textarea>

    <script>
        function copyToClipboard() {
            const code = document.getElementById('raw_code').value;
            if (!code) return;
            navigator.clipboard.writeText(code).then(() => {
                const btn = document.querySelector('.btn-outline-info');
                const originalText = btn.innerText;
                btn.innerText = 'הועתק בהצלחה! ✅';
                setTimeout(() => btn.innerText = originalText, 2000);
            });
        }
    </script>
</body>
</html>
"""

# שינוי נתיב ראשי ל-/app2
@app.route('/', methods=['GET'])
def index():
    target_url = request.args.get('url', '').strip()
    data = {
        "url": target_url, 
        "has_results": False,
        "images": [],
        "externals": [],
        "html_content": ""
    }
    
    if target_url:
        if not target_url.startswith(('http://', 'https://')):
            target_url = 'https://' + target_url
            data["url"] = target_url # עדכון ה-URL שמוצג למשתמש
            
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            res = requests.get(target_url, headers=headers, timeout=10)
            res.raise_for_status()
            
            # טיפול בקידוד עברית
            res.encoding = res.apparent_encoding
            
            images, externals = analyze_assets(res.text, target_url)
            
            data.update({
                "html_content": res.text,
                "images": images,
                "externals": externals,
                "has_results": True
            })
        except Exception as e:
            data["error"] = f"שגיאה בעת הסריקה: {str(e)}"
            
    return render_template_string(HTML_PAGE, **data)

# שינוי נתיב ההורדה ל-/app2/download
@app.route('/download')
def download():
    """מאפשר הורדה של הקוד כקובץ HTML"""
    target_url = request.args.get('url')
    if not target_url:
        return "No URL provided", 400
        
    try:
        if not target_url.startswith(('http://', 'https://')):
             target_url = 'https://' + target_url

        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        res = requests.get(target_url, headers=headers, timeout=10)
        res.encoding = res.apparent_encoding # חשוב לעברית בקובץ המורד
        
        return Response(
            res.text,
            mimetype="text/html",
            headers={"Content-disposition": "attachment; filename=index.html"}
        )
    except Exception as e:
        return f"Error downloading: {str(e)}", 500

if __name__ == '__main__':
    # מפעיל על פורט 5000 כברירת מחדל
    app.run(debug=True, port=5000)
