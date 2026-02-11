import requests
import re
from flask import Flask, render_template_string, request, Response
from urllib.parse import urljoin

app = Flask(__name__)

def analyze_assets(html, base_url):
    """מחלץ תמונות וקבצים חיצוניים (JS/CSS)"""
    # חילוץ תמונות
    img_urls = re.findall(r'<img [^>]*src="([^"]+)"', html)
    images = list(set([urljoin(base_url, img) for img in img_urls]))
    
    # חילוץ קבצים חיצוניים (Scripts & Stylesheets)
    scripts = re.findall(r'<script [^>]*src="([^"]+)"', html)
    styles = re.findall(r'<link [^>]*href="([^"]+)"', html)
    
    external_files = list(set([urljoin(base_url, f) for f in scripts + styles]))
    
    return images, external_files

HTML_PAGE = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>Web-Scanner Pro | Extract</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: #0f172a; color: #e2e8f0; font-family: system-ui; }
        .glass-card { background: rgba(30, 41, 59, 0.7); border-radius: 15px; border: 1px solid #334155; padding: 20px; }
        .asset-list { max-height: 300px; overflow-y: auto; background: #1e293b; border-radius: 10px; padding: 15px; }
        .btn-action { background: linear-gradient(135deg, #00f2fe, #4facfe); border: none; color: white; margin: 5px; }
        .file-link { color: #38bdf8; text-decoration: none; font-size: 0.9rem; display: block; margin-bottom: 5px; }
        .file-link:hover { text-decoration: underline; }
    </style>
</head>
<body class="container py-5">
    <h1 class="text-center mb-4">Web-Scanner Pro</h1>
    
    <div class="glass-card mb-4">
        <form method="GET" class="row g-2">
            <div class="col-md-10">
                <input type="url" name="url" class="form-control" placeholder="הכנס כתובת אתר..." value="{{ url }}" required>
            </div>
            <div class="col-md-2">
                <button type="submit" class="btn btn-action w-100">סרוק</button>
            </div>
        </form>
    </div>

    {% if error %}
        <div class="alert alert-danger">{{ error }}</div>
    {% endif %}

    {% if has_results %}
    <div class="row g-4">
        <div class="col-md-4">
            <div class="glass-card h-100">
                <h3>קוד מקור (HTML)</h3>
                <p>הקוד נסרק בהצלחה. ניתן להעתיק או להוריד כקובץ.</p>
                <button onclick="copyToClipboard()" class="btn btn-outline-info w-100 mb-2">העתק קוד לקליפבורד</button>
                <a href="php/download?url={{ url }}" class="btn btn-action w-100">הורד קובץ index.html</a>
            </div>
        </div>

        <div class="col-md-4">
            <div class="glass-card h-100">
                <h3>תמונות ({{ images|length }})</h3>
                <div class="asset-list">
                    {% for img in images %}
                        <a href="{{ img }}" target="_blank" class="file-link">📄 {{ img.split('/')[-1] or 'image' }}</a>
                    {% endfor %}
                </div>
            </div>
        </div>

        <div class="col-md-4">
            <div class="glass-card h-100">
                <h3>קבצים חיצוניים ({{ externals|length }})</h3>
                <div class="asset-list">
                    {% for file in externals %}
                        <a href="{{ file }}" target="_blank" class="file-link">⚙️ {{ file.split('/')[-1] }}</a>
                    {% endfor %}
                </div>
            </div>
        </div>
    </div>
    {% endif %}

    <textarea id="raw_code" style="display:none;">{{ html_content }}</textarea>

    <script>
        function copyToClipboard() {
            const code = document.getElementById('raw_code').value;
            navigator.clipboard.writeText(code).then(() => alert('הקוד הועתק!'));
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    target_url = request.args.get('url', '').strip()
    data = {"url": target_url, "has_results": False}
    
    if target_url:
        try:
            if not target_url.startswith('http'): target_url = 'https://' + target_url
            headers = {'User-Agent': 'Mozilla/5.0'}
            res = requests.get(target_url, headers=headers, timeout=10)
            res.raise_for_status()
            
            images, externals = analyze_assets(res.text, target_url)
            data.update({
                "html_content": res.text,
                "images": images,
                "externals": externals,
                "has_results": True,
                "url": target_url
            })
        except Exception as e:
            data["error"] = f"שגיאה: {str(e)}"
            
    return render_template_string(HTML_PAGE, **data)

@app.route('/download')
def download():
    """מאפשר הורדה של הקוד כקובץ HTML"""
    target_url = request.args.get('url')
    s = requests.session()
    res = s.get(target_url, headers={'User-Agent': 'Mozilla/5.0'})
    return Response(
        res.text,
        mimetype="text/html",
        headers={"Content-disposition": "attachment; filename=index.html"}
    )

if __name__ == '__main__':
    app.run(debug=True)
