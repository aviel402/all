import requests
import re
import io
import zipfile
import os
from flask import Flask, render_template_string, request, Response, send_file
from urllib.parse import urljoin, urlparse

app = Flask(__name__)

# --- פונקציות עזר ---

def get_page_content(url):
    """פונקציה עוטפת לבקשות רשת עם הגדרות קידוד וכותרות"""
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.encoding = response.apparent_encoding
        return response
    except Exception as e:
        return None

def generate_zip(url):
    """
    1. מוריד את ה-HTML
    2. מוצא את כל הנכסים (תמונות, סקריפטים)
    3. מוריד אותם לזיכרון
    4. מעדכן את ה-HTML שיצביע לנכסים המקומיים
    5. מחזיר קובץ ZIP בייט-סטרים
    """
    main_response = get_page_content(url)
    if not main_response:
        return None

    html_content = main_response.text
    base_url = url
    
    # זיהוי כל הנכסים בעזרת Regex
    # קבוצה 1: התגית כולה, קבוצה 2: ה-URL
    assets_patterns = [
        (r'(<img [^>]*src=["\'])([^"\']+)(["\'])', 'images'),
        (r'(<script [^>]*src=["\'])([^"\']+)(["\'])', 'js'),
        (r'(<link [^>]*href=["\'])([^"\']+)(["\'])', 'css')
    ]

    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        file_counter = 0
        
        # מעבר על כל סוגי הקבצים (img, script, link)
        for pattern, folder_name in assets_patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            
            for prefix, src, suffix in matches:
                abs_url = urljoin(base_url, src)
                
                try:
                    # הורדת הנכס
                    asset_res = get_page_content(abs_url)
                    if asset_res and asset_res.status_code == 200:
                        # יצירת שם קובץ ייחודי מקומי
                        ext = os.path.splitext(urlparse(src).path)[1]
                        if not ext: ext = ".txt" # ברירת מחדל אם אין סיומת
                        if folder_name == 'images' and ext == '.txt': ext = '.jpg'
                        
                        file_counter += 1
                        local_filename = f"{folder_name}/file_{file_counter}{ext}"
                        
                        # כתיבה ל-ZIP
                        zip_file.writestr(local_filename, asset_res.content)
                        
                        # החלפה בקוד ה-HTML המקורי כך שיצביע לקובץ המקומי
                        # אנו מחליפים רק את ה-src הספציפי הזה
                        # (החלפה פשוטה עשויה להיות מסוכנת, אבל זה הפתרון הפשוט ללא דפדפן מלא)
                        html_content = html_content.replace(src, local_filename)
                except Exception as e:
                    print(f"Skipped {abs_url}: {e}")
                    continue

        # כתיבת קובץ ה-HTML המתוקן לראשי
        zip_file.writestr('index.html', html_content)
    
    zip_buffer.seek(0)
    return zip_buffer

# --- HTML Template ---
HTML_PAGE = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>Web-Scanner Pro | App 2</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: #0f172a; color: #e2e8f0; font-family: 'Segoe UI', system-ui, sans-serif; min-height: 100vh; display: flex; flex-direction: column; align-items: center; justify-content: center; }
        .glass-card { 
            background: rgba(30, 41, 59, 0.7); 
            border-radius: 20px; 
            border: 1px solid #334155; 
            padding: 40px; 
            box-shadow: 0 10px 25px rgba(0,0,0,0.5); 
            backdrop-filter: blur(10px);
            width: 100%;
            max-width: 700px;
        }
        
        h1 { 
            background: -webkit-linear-gradient(#00f2fe, #4facfe); 
            -webkit-background-clip: text; 
            -webkit-text-fill-color: transparent; 
            font-weight: 800;
            margin-bottom: 30px;
        }

        .search-input {
            background: #1e293b;
            border: 1px solid #475569;
            color: white;
            padding: 15px;
            border-radius: 12px;
            font-size: 1.1rem;
        }
        .search-input:focus {
            background: #334155;
            color: white;
            box-shadow: 0 0 15px rgba(79, 172, 254, 0.3);
            border-color: #4facfe;
        }

        /* עיצוב כפתורים מיוחד */
        .action-btn {
            padding: 20px;
            border-radius: 15px;
            border: none;
            color: white;
            font-size: 1.2rem;
            font-weight: 600;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            text-decoration: none;
            margin-bottom: 15px;
            width: 100%;
        }

        .btn-copy { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
        .btn-download-html { background: linear-gradient(135deg, #2af598 0%, #009efd 100%); }
        .btn-download-zip { background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 99%, #fecfef 100%); color: #444; }

        .action-btn:hover { transform: translateY(-3px); box-shadow: 0 5px 15px rgba(0,0,0,0.3); color: inherit; }
        
        textarea { display: none; }
    </style>
</head>
<body>

    <div class="glass-card text-center">
        <h1>Web-Scanner Pro</h1>
        
        <form action="/app2" method="GET" class="mb-4">
            <div class="input-group">
                <input type="text" name="url" class="form-control search-input" placeholder="הדבק כאן כתובת אתר..." value="{{ url }}" required>
                <button class="btn btn-primary px-4 fw-bold" type="submit">סרוק 🚀</button>
            </div>
        </form>

        {% if error %}
            <div class="alert alert-danger">{{ error }}</div>
        {% endif %}

        {% if has_results %}
            <div class="d-grid gap-3 mt-5">
                <!-- כפתור 1: העתקה -->
                <button onclick="copyToClipboard()" class="action-btn btn-copy">
                   📋 העתק קוד מקור (Copy Source)
                </button>

                <!-- כפתור 2: הורדת HTML -->
                <a href="/app2/download_html?url={{ url }}" class="action-btn btn-download-html">
                   📄 הורד כקובץ HTML (Download File)
                </a>

                <!-- כפתור 3: הורדת ZIP מלא -->
                <a href="/app2/download_zip?url={{ url }}" class="action-btn btn-download-zip">
                   📦 הורד אתר מלא ב-ZIP (כולל תמונות)
                </a>
            </div>

            <!-- אזור מוסתר להעתקה -->
            <textarea id="raw_code">{{ html_content }}</textarea>
        {% endif %}
    </div>

    <script>
        function copyToClipboard() {
            const code = document.getElementById('raw_code').value;
            navigator.clipboard.writeText(code).then(() => {
                const btn = document.querySelector('.btn-copy');
                const originalText = btn.innerText;
                btn.innerText = '✅ הקוד הועתק בהצלחה!';
                setTimeout(() => btn.innerText = originalText, 2000);
            });
        }
    </script>
</body>
</html>
"""

# --- Routes ---

@app.route('/', methods=['GET'])
def index():
    target_url = request.args.get('url', '').strip()
    data = {"url": target_url, "has_results": False, "html_content": ""}
    
    if target_url:
        target_url = target_url if target_url.startswith(('http://', 'https://')) else 'https://' + target_url
        data["url"] = target_url
        
        res = get_page_content(target_url)
        if res and res.status_code == 200:
            data.update({
                "html_content": res.text,
                "has_results": True
            })
        else:
            data["error"] = "לא ניתן לגשת לאתר זה (שגיאת חיבור או כתובת שגויה)."
            
    return render_template_string(HTML_PAGE, **data)

@app.route('/download_html')
def download_html():
    target_url = request.args.get('url')
    if not target_url: return "Missing URL", 400
    
    res = get_page_content(target_url)
    if res:
        return Response(
            res.text,
            mimetype="text/html",
            headers={"Content-disposition": "attachment; filename=website_scan.html"}
        )
    return "Error downloading content", 500

@app.route('/download_zip')
def download_zip_route():
    target_url = request.args.get('url')
    if not target_url: return "Missing URL", 400
    
    try:
        zip_buffer = generate_zip(target_url)
        if zip_buffer:
            return send_file(
                zip_buffer,
                mimetype='application/zip',
                as_attachment=True,
                download_name='full_website_scan.zip'
            )
        else:
            return "Could not generate ZIP (Page might be inaccessible)", 500
    except Exception as e:
        return f"System Error: {str(e)}", 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
