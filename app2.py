import requests
import re
import io
import zipfile
import os
from flask import Flask, render_template_string, request, Response, send_file
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup  # נדרש: pip install beautifulsoup4

app = Flask(__name__)

# --- פונקציות עזר ---

def get_page_content(url):
    """מבצע בקשה עם זיוף דפדפן כדי שהאתר לא יחסום"""
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        # זיהוי קידוד אוטומטי (קריטי לעברית)
        response.encoding = response.apparent_encoding
        return response
    except Exception:
        return None

def generate_robust_zip(url):
    """
    1. מנתח את ה-HTML בעזרת BeautifulSoup
    2. עובר על כל תמונה, סקריפט ו-CSS
    3. מוריד אותם לזיכרון
    4. משנה את ה-src ב-HTML לנתיב מקומי (assets/...)
    5. אורז הכל ל-ZIP תקין
    """
    main_res = get_page_content(url)
    if not main_res: return None

    base_url = url
    soup = BeautifulSoup(main_res.text, 'html.parser')
    
    # ניצור קובץ ZIP בזיכרון
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        
        # מונה לקבצים כדי למנוע התנגשויות שמות
        file_counter = 0
        
        # הגדרת אילו תגיות לחפש ואילו תכונות לשנות
        # Tag Name | Attribute Name | Extension Default | Zip Folder
        targets = [
            ('img', 'src', '.jpg', 'assets'),
            ('script', 'src', '.js', 'assets'),
            ('link', 'href', '.css', 'assets')
        ]

        processed_urls = {}  # כדי לא להוריד את אותו קובץ פעמיים

        for tag_name, attr_name, default_ext, folder in targets:
            # מציאת כל התגיות מסוג זה שיש להן את התכונה (למשל img עם src)
            for tag in soup.find_all(tag_name, **{attr_name: True}):
                original_url = tag[attr_name]
                
                # התעלמות מקישורי DATA (base64) או קישורים ריקים
                if not original_url or original_url.startswith('data:') or original_url.startswith('#'):
                    continue

                abs_url = urljoin(base_url, original_url)

                # בדיקה אם כבר הורדנו את הקובץ הזה בסריקה הנוכחית
                if abs_url in processed_urls:
                    # רק נעדכן את ה-HTML לנתיב הקיים
                    tag[attr_name] = processed_urls[abs_url]
                    continue

                try:
                    # הורדת הנכס (Asset)
                    res = get_page_content(abs_url)
                    if res and res.status_code == 200:
                        file_counter += 1
                        
                        # ניסיון לחלץ סיומת מקורית, אם אין משתמשים בברירת מחדל
                        parsed_path = urlparse(abs_url).path
                        filename = os.path.basename(parsed_path)
                        name, ext = os.path.splitext(filename)
                        if not ext or len(ext) > 5: # סינון סיומות מוזרות
                            ext = default_ext
                        
                        # יצירת שם קובץ נקי
                        local_filename = f"{folder}/file_{file_counter}{ext}"
                        
                        # שמירה לתוך ה-ZIP
                        zip_file.writestr(local_filename, res.content)
                        
                        # --- החלק החשוב: שינוי ה-HTML ---
                        # אנחנו משנים את התכונה של התגית (DOM) לכתובת המקומית
                        tag[attr_name] = local_filename
                        
                        # הסרת integrity ו-crossorigin שמפריעים לטעינה מקומית
                        if tag.get('integrity'): del tag['integrity']
                        if tag.get('crossorigin'): del tag['crossorigin']

                        # שמירה במילון כדי לא להוריד כפילויות
                        processed_urls[abs_url] = local_filename

                except Exception as e:
                    print(f"Failed to process {abs_url}: {e}")
                    # במקרה של כישלון, משאירים את הלינק המקורי כמו שהוא
                    pass

        # בסוף: שומרים את ה-HTML המעודכן (עם הקישורים המקומיים) לתוך ה-ZIP
        # משתמשים ב-prettify כדי שהקוד יהיה קריא
        zip_file.writestr('index.html', soup.prettify("utf-8"))

    zip_buffer.seek(0)
    return zip_buffer

# --- ממשק משתמש ---
HTML_UI = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>Web-Scanner Pro v2</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { 
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: #fff; 
            font-family: 'Segoe UI', system-ui; 
            min-height: 100vh; 
            display: flex; 
            align-items: center; 
            justify-content: center;
        }
        .container-box { 
            background: rgba(255,255,255,0.1); 
            padding: 40px; 
            border-radius: 20px; 
            box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
            backdrop-filter: blur(8px);
            border: 1px solid rgba(255, 255, 255, 0.18);
            width: 100%;
            max-width: 600px;
            text-align: center;
        }
        
        .title { 
            font-size: 2.5rem; 
            font-weight: bold; 
            margin-bottom: 20px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
        }

        .search-box {
            background: rgba(255,255,255,0.9);
            border: none;
            padding: 15px;
            border-radius: 50px;
            margin-bottom: 30px;
            text-align: left; /* ל-URL באנגלית */
            direction: ltr;
        }

        .btn-custom {
            display: block;
            width: 100%;
            padding: 15px;
            margin: 10px 0;
            border: none;
            border-radius: 12px;
            font-size: 1.1rem;
            font-weight: 600;
            text-decoration: none;
            color: white;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .btn-custom:hover { transform: translateY(-2px); color: white; }

        .btn-1 { background: linear-gradient(90deg, #FDBB2D 0%, #22C1C3 100%); } /* Copy */
        .btn-2 { background: linear-gradient(90deg, #93A5CF 0%, #E4EfE9 100%); color: #333 !important;} /* HTML Only */
        .btn-3 { background: linear-gradient(90deg, #fc466b 0%, #3f5efb 100%); } /* Full ZIP */

        textarea { display: none; }
    </style>
</head>
<body>

    <div class="container-box">
        <div class="title">Scrape Master 3000</div>
        
        <form action="/app2" method="GET">
            <div class="input-group">
                <input type="text" name="url" class="form-control search-box" placeholder="https://example.com" value="{{ url }}" required>
                <button class="btn btn-primary" style="border-radius: 50px; margin-left: -50px; z-index: 10;" type="submit">GO</button>
            </div>
        </form>

        {% if error %}
            <div class="alert alert-danger mt-3">{{ error }}</div>
        {% endif %}

        {% if has_results %}
            <p class="mt-3 opacity-75">האתר נסרק בהצלחה! בחר פעולה:</p>
            
            <button onclick="copyCode()" class="btn-custom btn-1">
                📋 העתק קוד מקור (Copy Code)
            </button>

            <a href="/app2/dl_html?url={{ url }}" class="btn-custom btn-2">
                📄 הורד HTML בלבד (Download HTML)
            </a>

            <a href="/app2/dl_zip?url={{ url }}" class="btn-custom btn-3">
                📦 הורד הכל כ-ZIP (תמונות מקושרות)
            </a>

            <textarea id="hidden-code">{{ html_content }}</textarea>
        {% endif %}
    </div>

    <script>
        function copyCode() {
            const code = document.getElementById('hidden-code').value;
            navigator.clipboard.writeText(code).then(() => {
                alert('הקוד הועתק בהצלחה!');
            });
        }
    </script>
</body>
</html>
"""

# --- ROUTES ---

@app.route('/app2')
def index():
    url = request.args.get('url', '').strip()
    data = {"url": url, "has_results": False}

    if url:
        url = url if url.startswith('http') else 'https://' + url
        data["url"] = url
        res = get_page_content(url)
        if res and res.status_code == 200:
            data["html_content"] = res.text
            data["has_results"] = True
        else:
            data["error"] = "שגיאה בחיבור לאתר. בדוק את הכתובת."

    return render_template_string(HTML_UI, **data)

@app.route('/app2/dl_html')
def download_html():
    url = request.args.get('url')
    res = get_page_content(url)
    if res:
        return Response(res.text, mimetype="text/html", 
                        headers={"Content-Disposition": "attachment; filename=page.html"})
    return "Error", 500

@app.route('/app2/dl_zip')
def download_zip():
    url = request.args.get('url')
    if not url: return "No URL", 400

    zip_buffer = generate_robust_zip(url)
    if zip_buffer:
        return send_file(zip_buffer, mimetype="application/zip", as_attachment=True, download_name="site_backup.zip")
    else:
        return "שגיאה ביצירת ה-ZIP (אולי האתר חוסם גישה)", 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
