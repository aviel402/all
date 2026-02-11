import requests
import re
import io
import zipfile
import os
import mimetypes
from flask import Flask, render_template_string, request, Response, send_file
from urllib.parse import urljoin, urlparse, unquote
from bs4 import BeautifulSoup  # pip install beautifulsoup4

app = Flask(__name__)

# --- קונפיגורציה לזיוף דפדפן ---
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Referer': 'https://www.google.com/',
    'Accept-Language': 'en-US,en;q=0.5'
}

def clean_filename(url):
    """יוצר שם קובץ נקי מכתובת URL"""
    path = urlparse(url).path
    filename = os.path.basename(unquote(path))
    if not filename: return "file"
    # הסרת תווים בעייתיים
    return re.sub(r'[^a-zA-Z0-9._-]', '', filename)

def generate_fixed_zip(url):
    """
    מייצר ZIP שבו כל הקישורים תוקנו כך שיעבדו אופליין בצורה מושלמת.
    מטפל בבעיות Lazy Load שיש באתרים כמו CrazyGames.
    """
    try:
        session = requests.Session()
        session.headers.update(HEADERS)
        response = session.get(url, timeout=15)
        response.encoding = response.apparent_encoding
        
        if response.status_code != 200: return None

        soup = BeautifulSoup(response.text, 'html.parser')
        base_url = url
        
        # זיכרון ליצירת ה-ZIP
        zip_buffer = io.BytesIO()
        
        # מעקב כדי לא להוריד אותו קובץ פעמיים
        downloaded_files = {} 
        file_counter = 0

        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            
            # 1. חיפוש נכסים: תמונות, סקריפטים, עיצובים
            # אנחנו מחפשים גם src וגם data-src (לטעינה עצלה)
            tags_to_process = [
                ('img', ['src', 'data-src'], 'assets_img'),
                ('script', ['src'], 'assets_js'),
                ('link', ['href'], 'assets_css')
            ]

            for tag_name, attrs, folder in tags_to_process:
                for tag in soup.find_all(tag_name):
                    
                    # ניקוי תגיות בעייתיות לאופליין
                    if tag.has_attr('srcset'): del tag['srcset'] 
                    if tag.has_attr('crossorigin'): del tag['crossorigin']
                    if tag.has_attr('integrity'): del tag['integrity']

                    # בדיקה אם קיים אחד מהמאפיינים (src/href/data-src)
                    target_attr = None
                    original_val = None
                    
                    for attr in attrs:
                        if tag.has_attr(attr) and tag[attr]:
                            target_attr = attr
                            original_val = tag[attr]
                            break
                    
                    if not target_attr: continue
                    if original_val.startswith('data:') or original_val.startswith('#'): continue

                    # המרה לכתובת מלאה
                    abs_url = urljoin(base_url, original_val)
                    
                    # בדיקה אם כבר הורדנו
                    if abs_url in downloaded_files:
                        tag[target_attr] = downloaded_files[abs_url] # עדכון ה-HTML לקובץ המקומי
                        continue

                    try:
                        # הורדת הקובץ
                        file_res = session.get(abs_url, timeout=5)
                        if file_res.status_code == 200:
                            file_counter += 1
                            
                            # קביעת שם קובץ וסיומת
                            ext = os.path.splitext(clean_filename(abs_url))[1]
                            if not ext: # אם אין סיומת, ננסה לנחש לפי ה-Content-Type
                                content_type = file_res.headers.get('Content-Type', '')
                                ext = mimetypes.guess_extension(content_type.split(';')[0]) or '.bin'

                            local_filename = f"{folder}/res_{file_counter}{ext}"
                            
                            # כתיבה ל-ZIP
                            zf.writestr(local_filename, file_res.content)
                            
                            # עדכון ה-HTML שיצביע לקובץ המקומי
                            tag[target_attr] = local_filename
                            
                            # טיפול מיוחד ל-Lazy Load:
                            # אם הורדנו מ-data-src, נעביר את זה ל-src כדי שהדפדפן יציג את זה מיד
                            if target_attr == 'data-src':
                                tag['src'] = local_filename
                                del tag['data-src']

                            downloaded_files[abs_url] = local_filename
                            print(f"Downloaded: {abs_url}")

                    except Exception as e:
                        print(f"Failed asset: {abs_url} - {e}")
                        pass

            # הוספת CSS בסיסי כדי שהאתר ייראה טוב בתוך iframe אם צריך
            extra_css = soup.new_tag("style")
            extra_css.string = "body { margin: 0; padding: 0; overflow-x: hidden; } img { max-width: 100%; }"
            if soup.head: soup.head.append(extra_css)

            # שמירת ה-HTML המעובד
            zf.writestr('index.html', soup.prettify())
        
        zip_buffer.seek(0)
        return zip_buffer

    except Exception as e:
        print(f"Error generating ZIP: {e}")
        return None


# --- עיצוב ותבנית HTML ---
HTML_UI = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>Web Ripper V3</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {
            background-color: #121212;
            color: white;
            height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: 'Segoe UI', sans-serif;
            overflow: hidden;
        }
        
        .container-center {
            text-align: center;
            background: #1e1e1e;
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 0 20px rgba(0,0,0,0.5);
            width: 100%;
            max-width: 500px;
            border: 1px solid #333;
        }

        .title-gradient {
            background: linear-gradient(90deg, #00C9FF 0%, #92FE9D 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 800;
            font-size: 2.5rem;
            margin-bottom: 20px;
        }

        .form-control {
            background: #2d2d2d;
            border: 1px solid #444;
            color: white;
            padding: 15px;
            text-align: center;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        .form-control:focus {
            background: #333;
            color: white;
            box-shadow: none;
            border-color: #00C9FF;
        }

        .action-btn {
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 18px;
            font-size: 1.2rem;
            font-weight: bold;
            color: white;
            border: none;
            border-radius: 12px;
            text-decoration: none;
            margin-bottom: 15px;
            transition: 0.3s;
            cursor: pointer;
            width: 100%;
        }

        .btn-copy { background: #6c5ce7; }
        .btn-html { background: #00cec9; color: #333; }
        .btn-zip { background: linear-gradient(45deg, #fd79a8, #e84393); }
        .btn-new { background: #636e72; font-size: 0.9rem; padding: 10px;}

        .action-btn:hover { transform: scale(1.03); opacity: 0.9; color: white; }

        .hidden-area { display: none; }
    </style>
</head>
<body>

    <div class="container-center">
        {% if not has_results %}
            <!-- מסך ראשי: חיפוש -->
            <div class="title-gradient">Web Scanner</div>
            <form action="/app2" method="POST">
                <input type="text" name="url" class="form-control" placeholder="https://..." required>
                <button type="submit" class="action-btn" style="background: linear-gradient(90deg, #00C9FF 0%, #92FE9D 100%); color: #000;">
                    סרוק כעת 🚀
                </button>
            </form>
            {% if error %}
                <div class="text-danger mt-2">{{ error }}</div>
            {% endif %}

        {% else %}
            <!-- מסך תוצאות: רק כפתורים -->
            <div class="title-gradient">הסריקה הושלמה! ✅</div>
            
            <button onclick="copyToClipboard()" class="action-btn btn-copy">
                העתק קוד 📋
            </button>
            
            <a href="/app2/download/html?target={{ encoded_url }}" class="action-btn btn-html">
                הורד HTML 📄
            </a>
            
            <a href="/app2/download/zip?target={{ encoded_url }}" class="action-btn btn-zip">
                הורד חבילה מלאה (ZIP) 📦
            </a>

            <div class="mt-4 border-top pt-3 border-secondary">
                <a href="/app2" class="action-btn btn-new">סרוק אתר אחר ↺</a>
            </div>

            <!-- הקוד עצמו מוסתר כאן לצורך העתקה -->
            <textarea id="hidden-code" class="hidden-area">{{ html_content }}</textarea>
        {% endif %}
    </div>

    <script>
        function copyToClipboard() {
            const code = document.getElementById('hidden-code').value;
            navigator.clipboard.writeText(code).then(() => {
                const btn = document.querySelector('.btn-copy');
                const orig = btn.innerText;
                btn.innerText = 'הועתק בהצלחה! 👌';
                setTimeout(() => btn.innerText = orig, 1500);
            });
        }
    </script>
</body>
</html>
"""

# --- מסלולים (Routes) ---

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form.get('url')
        try:
            session = requests.Session()
            session.headers.update(HEADERS)
            if not url.startswith('http'): url = 'https://' + url
            
            res = session.get(url, timeout=10)
            res.encoding = res.apparent_encoding
            
            # קידוד ה-URL כדי להעביר אותו בטוח לכפתורי ההורדה
            from urllib.parse import quote
            encoded_url = quote(url)

            return render_template_string(HTML_UI, 
                                          has_results=True, 
                                          html_content=res.text,
                                          encoded_url=encoded_url)
        except Exception as e:
            return render_template_string(HTML_UI, has_results=False, error="שגיאה בסריקת האתר. וודא שהכתובת תקינה.")
            
    return render_template_string(HTML_UI, has_results=False)

@app.route('/download/html')
def download_html():
    from urllib.parse import unquote
    url = unquote(request.args.get('target'))
    
    try:
        session = requests.Session()
        session.headers.update(HEADERS)
        res = session.get(url)
        res.encoding = res.apparent_encoding
        return Response(res.text, mimetype="text/html", headers={"Content-Disposition": "attachment; filename=scanned_page.html"})
    except:
        return "Error", 500

@app.route('/download/zip')
def download_zip_route():
    from urllib.parse import unquote
    url = unquote(request.args.get('target'))
    
    zip_buffer = generate_fixed_zip(url)
    
    if zip_buffer:
        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name='website_complete.zip'
        )
    else:
        return "שגיאה ביצירת הקובץ. ייתכן והאתר חוסם גישה.", 400

if __name__ == '__main__':
    app.run(debug=True, port=5000)
