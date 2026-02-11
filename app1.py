import requests
import re
import random
from flask import Flask, render_template_string, request
from urllib.parse import urljoin

app = Flask(__name__)

# --- רשימת ערכות נושא (THEMES) ---
# הרשימה המקורית + התוספות שלך מאוחדות לרשימה אחת גדולה
THEMES = [
    # המקוריות
    {"name": "Cyberpunk", "bg": "#0f0524", "primary": "#ff00ff", "secondary": "#00ffff", "text": "#ffffff", "code_theme": "prism-tomorrow"},
    {"name": "Deep Ocean", "bg": "#011627", "primary": "#2081C3", "secondary": "#63D2FF", "text": "#d6e8ee", "code_theme": "prism-okaidia"},
    {"name": "Forest Dark", "bg": "#1a1f16", "primary": "#5e8c31", "secondary": "#a2d240", "text": "#e8f0e2", "code_theme": "prism-twilight"},
    {"name": "Midnight Gold", "bg": "#121212", "primary": "#D4AF37", "secondary": "#FFD700", "text": "#f4f4f4", "code_theme": "prism-funky"},
    {"name": "Mars Rover", "bg": "#2b0f0e", "primary": "#e27d60", "secondary": "#e8a87c", "text": "#ffffff", "code_theme": "prism-coy"},
    {"name": "Soft Purple", "bg": "#2d1b33", "primary": "#c39bd3", "secondary": "#f06292", "text": "#f5f5f5", "code_theme": "prism-dark"},
    {"name": "Matrix", "bg": "#000000", "primary": "#00ff41", "secondary": "#008f11", "text": "#00ff41", "code_theme": "prism-tomorrow"},
    {"name": "Nordic Ice", "bg": "#2e3440", "primary": "#88c0d0", "secondary": "#81a1c1", "text": "#eceff4", "code_theme": "prism-nord"},
    
    # התוספות החדשות (Additional Themes)
    {"name": "Vaporwave Sunset", "bg": "#241744", "primary": "#ff71ce", "secondary": "#01cdfe", "text": "#fff2f1", "code_theme": "prism-tomorrow"},
    {"name": "Dracula Night", "bg": "#282a36", "primary": "#bd93f9", "secondary": "#ff79c6", "text": "#f8f8f2", "code_theme": "prism-tomorrow"},
    {"name": "Emerald City", "bg": "#021c1e", "primary": "#00676b", "secondary": "#2fb98a", "text": "#d8f3dc", "code_theme": "prism-okaidia"},
    {"name": "Monokai Classic", "bg": "#2d2a2e", "primary": "#ffd866", "secondary": "#ff6188", "text": "#fcfcfa", "code_theme": "prism-okaidia"},
    {"name": "Arctic Frost", "bg": "#f0f4f8", "primary": "#1b6ca8", "secondary": "#4ba3c3", "text": "#243b53", "code_theme": "prism-coy"},
    {"name": "Coffee House", "bg": "#3c2f2f", "primary": "#be9b7b", "secondary": "#854442", "text": "#fff4e6", "code_theme": "prism-twilight"},
    {"name": "Red Alert", "bg": "#0a0000", "primary": "#ff4d4d", "secondary": "#b30000", "text": "#ffe6e6", "code_theme": "prism-funky"},
    {"name": "Royal Velvet", "bg": "#1a1c2c", "primary": "#f4d03f", "secondary": "#d4af37", "text": "#e0e0e0", "code_theme": "prism-tomorrow"}
]

# --- פונקציות עזר ---

def fix_url(url):
    """מוודא שיש פרוטוקול תקין לכתובת"""
    if not url: return ""
    if not url.startswith(('http://', 'https://')):
        return 'https://' + url
    return url

def extract_data(html, base_url):
    """חילוץ תמונות וכותרות מה-HTML"""
    # חילוץ תמונות (Regex)
    img_urls = re.findall(r'<img [^>]*src=["\']([^"\']+)["\']', html, re.IGNORECASE)
    # המרת נתיבים יחסיים לנתיבים מלאים (Absolute URLs)
    full_img_urls = list(set([urljoin(base_url, u) for u in img_urls if u and not u.startswith('data:')]))
    
    # חילוץ כותרת
    title_match = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
    title = title_match.group(1).strip() if title_match else "ללא כותרת"

    # חילוץ תיאור (Meta Description)
    desc_match = re.search(r'<meta name=["\']description["\'] content=["\'](.*?)["\']', html, re.IGNORECASE)
    description = desc_match.group(1).strip() if desc_match else "ללא תיאור"

    return {
        "images": full_img_urls[:16], # הגבלת כמות תמונות לתצוגה כדי למנוע האטה
        "total_images": len(full_img_urls),
        "title": title,
        "description": description
    }

# --- HTML TEMPLATE ---
# משתמש ב-Jinja2 Variables כדי להזריק את צבעי ה-Theme לתוך ה-CSS
HTML_PAGE = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Web-Scanner Pro | {{ theme.name }}</title>
    
    <!-- Bootstrap CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    
    <!-- Prism CSS (Dynamic Theme) -->
    <link href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/themes/{{ theme.code_theme }}.min.css" rel="stylesheet" />
    
    <style>
        :root { 
            --bg: {{ theme.bg }}; 
            --primary: {{ theme.primary }}; 
            --secondary: {{ theme.secondary }}; 
            --text: {{ theme.text }}; 
        }
        
        body { 
            background: var(--bg); 
            color: var(--text); 
            font-family: 'Segoe UI', system-ui, sans-serif; 
            transition: background 0.5s ease; 
            min-height: 100vh; 
        }
        
        /* אפקט זכוכית */
        .glass-card { 
            background: rgba(255, 255, 255, 0.03); 
            backdrop-filter: blur(16px); 
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid rgba(255, 255, 255, 0.08); 
            border-radius: 16px; 
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
        }
        
        .btn-gradient { 
            background: linear-gradient(135deg, var(--primary), var(--secondary)); 
            border: none; 
            color: #000; 
            font-weight: bold;
            transition: 0.3s;
        }
        .btn-gradient:hover { filter: brightness(1.1); transform: translateY(-2px); color: #000; }
        
        .search-box { 
            background: rgba(0,0,0,0.3); 
            border: 1px solid var(--primary); 
            color: var(--text); 
            border-radius: 10px; 
            padding: 12px;
        }
        .search-box::placeholder { color: rgba(255,255,255,0.5); }
        .search-box:focus { background: rgba(0,0,0,0.5); color: var(--text); border-color: var(--secondary); box-shadow: 0 0 10px var(--secondary); outline: none; }

        /* כרטיסיות מידע */
        .info-card { 
            border-right: 3px solid var(--primary); 
            padding: 15px; 
            background: rgba(0,0,0,0.15); 
            border-radius: 8px; 
            height: 100%;
        }
        
        /* גלריית תמונות */
        .img-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(80px, 1fr)); gap: 10px; }
        .img-preview { 
            width: 100%; height: 80px; object-fit: cover; 
            border-radius: 8px; border: 1px solid var(--secondary); 
            transition: transform 0.2s; cursor: pointer; background: #000;
        }
        .img-preview:hover { transform: scale(1.15); z-index: 10; box-shadow: 0 0 10px rgba(0,0,0,0.5); }

        /* אזור הקוד */
        .code-window { position: relative; }
        pre { max-height: 500px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.1); margin: 0; }
        
        /* --- מצב קוד בלבד (מסך מלא) --- */
        body.code-only-mode { overflow: hidden; }
        body.code-only-mode .main-ui { display: none !important; }
        body.code-only-mode .code-section { 
            position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; 
            z-index: 9999; background: var(--bg); padding: 0; margin: 0; 
        }
        body.code-only-mode .code-container { width: 100%; height: 100%; max-width: none; padding: 0; }
        body.code-only-mode pre { 
            height: 100vh !important; 
            max-height: none !important; 
            border-radius: 0; 
            border: none;
        }
        
        /* סמלים וכפתורים */
        .theme-badge { 
            position: fixed; bottom: 20px; left: 20px; 
            background: var(--primary); color: #000; 
            padding: 6px 16px; border-radius: 30px; 
            font-weight: bold; font-size: 13px; 
            box-shadow: 0 0 20px var(--primary);
            z-index: 100;
        }
        
        .floating-exit { display: none; position: fixed; top: 20px; left: 20px; z-index: 10000; }
        body.code-only-mode .floating-exit { display: block; }
        
        /* גלילה */
        ::-webkit-scrollbar { width: 10px; height: 10px; }
        ::-webkit-scrollbar-track { background: rgba(0,0,0,0.2); }
        ::-webkit-scrollbar-thumb { background: var(--primary); border-radius: 5px; }
    </style>
</head>
<body class="container py-4">
    
    <!-- כפתור יציאה ממסך מלא (מוסתר בהתחלה) -->
    <button class="btn btn-danger floating-exit shadow" onclick="toggleCodeOnly()">❌ יציאה ממסך מלא</button>

    <!-- Header Section -->
    <div class="main-ui text-center mb-5">
        <h1 class="display-4 fw-bold" style="color: var(--primary); text-shadow: 0 0 20px rgba(0,0,0,0.5);">Web Scanner <span style="color: var(--secondary)">Pro</span></h1>
        <p class="opacity-75 lead">מערכת חקר וסריקת קוד מקור</p>
        
        <!-- Theme Randomizer Button -->
        <form method="GET" action="/" class="d-inline-block mt-2">
            <!-- אם יש כבר URL נשמור אותו כשנחליף ערכת נושא -->
            <input type="hidden" name="url" value="{{ url if url else '' }}">
            <input type="hidden" name="new_theme" value="true">
            <button type="submit" class="btn btn-sm btn-outline-light rounded-pill px-4">🎲 החלף עיצוב</button>
        </form>
    </div>

    <!-- Search Section -->
    <div class="main-ui row justify-content-center">
        <div class="col-lg-8">
            <div class="glass-card p-4 mb-4">
                <form method="POST" action="/" class="row g-2 align-items-center">
                    <div class="col-md-9">
                        <input type="text" name="url" class="form-control search-box text-start" 
                               dir="ltr" placeholder="https://example.com" value="{{ url }}" required>
                        <!-- משמרים את העיצוב הנוכחי כשמחפשים -->
                        <input type="hidden" name="theme_idx" value="{{ theme_index }}">
                    </div>
                    <div class="col-md-3">
                        <button type="submit" class="btn btn-gradient w-100 py-2">סרוק אתר 🚀</button>
                    </div>
                </form>
            </div>
        </div>
    </div>

    {% if error %}
    <div class="main-ui alert alert-danger text-center glass-card border-danger text-danger">
        <h4 class="mb-1">⚠️ שגיאה</h4>
        <p class="m-0">{{ error }}</p>
    </div>
    {% endif %}

    {% if html_content %}
    <div class="main-ui row justify-content-center mb-4">
        <div class="col-lg-10">
            <div class="glass-card p-4">
                <div class="row g-4">
                    <!-- Metadata Info -->
                    <div class="col-md-6">
                        <div class="info-card">
                            <h5 style="color: var(--secondary)">📄 מידע כללי</h5>
                            <div class="mb-2"><strong>Title:</strong> {{ metadata.title }}</div>
                            <div class="mb-2 small opacity-75"><strong>Desc:</strong> {{ metadata.description[:120] }}...</div>
                            <div class="badge bg-secondary">אורך הדף: {{ "{:,}".format(html_content|length) }} תווים</div>
                        </div>
                    </div>
                    
                    <!-- Images Gallery -->
                    <div class="col-md-6">
                        <div class="info-card">
                            <h5 style="color: var(--secondary)">🖼️ גלריית תמונות ({{ metadata.total_images }})</h5>
                            {% if metadata.images %}
                                <div class="img-grid mt-2">
                                    {% for img in metadata.images %}
                                        <a href="{{ img }}" target="_blank">
                                            <img src="{{ img }}" class="img-preview" alt="img" onerror="this.style.display='none'">
                                        </a>
                                    {% endfor %}
                                </div>
                                {% if metadata.total_images > 16 %}
                                    <small class="d-block mt-2 text-muted">מציג 16 תמונות ראשונות...</small>
                                {% endif %}
                            {% else %}
                                <p class="text-muted mt-2">לא נמצאו תמונות נגישות בסריקה.</p>
                            {% endif %}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Code Section -->
    <div class="code-section row justify-content-center">
        <div class="col-lg-12 code-container">
            <div class="main-ui d-flex justify-content-between align-items-center mb-2 px-2">
                <h5 class="m-0 text-light"><span class="badge bg-dark border border-secondary">Source Code</span></h5>
                <div class="btn-group">
                    <button class="btn btn-sm btn-outline-info" onclick="copyCode(this)">📋 העתק הכל</button>
                    <button class="btn btn-sm btn-warning fw-bold" onclick="toggleCodeOnly()">🖥️ מסך מלא</button>
                </div>
            </div>
            
            <div class="code-window">
                <pre><code id="main-code" class="language-html">{{ html_content | e }}</code></pre>
            </div>
        </div>
    </div>
    {% endif %}

    <div class="theme-badge">🎨 Theme: {{ theme.name }}</div>

    <!-- PrismJS Scripts -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/prism.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-markup.min.js"></script>
    
    <script>
        function toggleCodeOnly() {
            document.body.classList.toggle('code-only-mode');
        }

        function copyCode(btn) {
            const code = document.getElementById('main-code').textContent;
            navigator.clipboard.writeText(code).then(() => {
                const originalText = btn.innerHTML;
                btn.innerHTML = '✅ הועתק!';
                btn.classList.remove('btn-outline-info');
                btn.classList.add('btn-success');
                setTimeout(() => {
                    btn.innerHTML = originalText;
                    btn.classList.add('btn-outline-info');
                    btn.classList.remove('btn-success');
                }, 2000);
            }).catch(err => {
                console.error('Failed to copy: ', err);
                alert("שגיאה בהעתקה, אנא נסה ידנית.");
            });
        }
    </script>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    html_content = None
    error = None
    metadata = {}
    target_url = ""

    # ניהול לוגיקת עיצוב (Themes Logic)
    # ננסה לקחת אינדקס מהטופס או מה-Query string
    req_theme_idx = request.values.get('theme_idx') 
    is_new_random = request.args.get('new_theme')

    # בחירת עיצוב
    if req_theme_idx and req_theme_idx.isdigit() and not is_new_random:
        idx = int(req_theme_idx) % len(THEMES)
        current_theme_index = idx
    else:
        # רנדומלי (ברירת מחדל או אם לחצו על הכפתור)
        current_theme_index = random.randint(0, len(THEMES) - 1)
    
    selected_theme = THEMES[current_theme_index]

    # אם זו בקשת POST (לחיצה על סריקה) או GET עם פרמטר url
    if request.method == 'POST':
        target_url = request.form.get('url', '').strip()
    elif request.method == 'GET':
        target_url = request.args.get('url', '').strip()

    if target_url:
        fixed_url = fix_url(target_url)
        try:
            # הגדרות Request כדי למנוע חסימות נפוצות
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.9,he;q=0.8'
            }
            
            response = requests.get(fixed_url, headers=headers, timeout=10)
            response.raise_for_status() # בדיקה אם חזר סטטוס שגיאה (404/500)
            
            # זיהוי קידוד (קריטי לאתרים בעברית)
            if response.encoding is None or response.encoding == 'ISO-8859-1':
                response.encoding = response.apparent_encoding
                
            html_content = response.text
            metadata = extract_data(html_content, fixed_url)
            
            # מעדכנים את ה-target_url המוצג שיהיה זה שסרקנו בפועל
            target_url = fixed_url

        except requests.exceptions.MissingSchema:
            error = "כתובת URL לא תקינה (Missing Schema)."
        except requests.exceptions.ConnectionError:
            error = "שגיאת חיבור. השרת לא הגיב או שהדומיין לא קיים."
        except requests.exceptions.Timeout:
            error = "הבקשה ארכה יותר מדי זמן (Timeout)."
        except Exception as e:
            error = f"שגיאה כללית: {str(e)}"

    return render_template_string(HTML_PAGE, 
                                 html_content=html_content, 
                                 error=error, 
                                 url=target_url, 
                                 theme=selected_theme,
                                 theme_index=current_theme_index,
                                 metadata=metadata)

if __name__ == '__main__':
    # מומלץ: debug=True לפיתוח, מכובה ב-Production
    app.run(debug=True, port=5000)
