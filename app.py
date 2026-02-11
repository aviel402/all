from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.serving import run_simple
from flask import Flask, render_template_string

# --- 1. דף "בפיתוח" מעוצב (למקרה שאחת האפליקציות חסרה) ---
def development_page(text):
    return '''
      <style>
        body {
          margin: 0;
          font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
          background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
          color: #fff;
          height: 100vh;
          display: flex;
          align-items: center;
          justify-content: center;
        }
        .hero { text-align: center; padding: 40px 20px; }
        h1 { font-size: clamp(2rem, 5vw, 3.5rem); margin: 0; font-weight: 700; }
        .subtitle { margin-top: 16px; font-size: 1.2rem; opacity: 0.85; }
      </style>
      <div class="hero">
        <h1>''' + text + '''</h1>
        <div class="subtitle">🚧 האתר עדיין בפיתוח או שהקובץ חסר 🚧</div>
      </div>
    '''

def create_dummy_app(text):
    dummy = Flask(__name__)
    @dummy.route('/')
    def index():
        return development_page(text)
    return dummy

# --- 2. ייבוא בטוח של האפליקציות ---
# מנסה לייבא את app1 ו-app2. אם הקבצים לא קיימים, יוצר אפליקציה דמי.
try:
    from app1 import app as app1
except ImportError:
    print("Warning: app1.py not found.")
    app1 = create_dummy_app("App 1")

try:
    from app2 import app as app2
except ImportError:
    print("Warning: app2.py not found.")
    app2 = create_dummy_app("App 2")

# --- 3. הגדרת התפריט הראשי ---
MENU_HTML = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>Arcade Station</title>
    <!-- תיקון: הוספת הקישור המלא לפונט Heebo -->
    <link href="https://fonts.googleapis.com/css2?family=Heebo:wght@400;700;900&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary: #6c7ce7;
            --accent: #00cec9;
            --bg-dark: #0a0a0c;
            --card-bg: #1e1e24;
        }

        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            background-color: var(--bg-dark);
            color: #dfe6e9;
            font-family: 'Heebo', sans-serif;
            text-align: center;
            padding: 40px 20px;
            min-height: 100vh;
        }

        h1 {
            font-size: clamp(2rem, 6vw, 3.5rem);
            margin-bottom: 10px;
            background: linear-gradient(90deg, #a29bfe, #74b9ff, #00cec9);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 900;
            text-transform: uppercase;
        }

        .subtitle {
            color: #b2bec3;
            font-size: 1.2rem;
            margin-bottom: 60px;
        }

        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 30px;
            max-width: 800px;
            margin: 0 auto;
        }

        .card {
            background: var(--card-bg);
            border-radius: 20px;
            padding: 40px 20px;
            text-decoration: none;
            color: white;
            transition: all 0.4s;
            border: 1px solid rgba(255,255,255,0.05);
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        }

        .card:hover {
            transform: translateY(-8px) scale(1.02);
            border-color: var(--accent);
            box-shadow: 0 15px 30px rgba(0, 206, 201, 0.2);
            background: #25252d;
        }

        .emoji-icon {
            font-size: 60px;
            margin-bottom: 20px;
        }
        
        h2 { font-weight: 700; }
        
        p.desc {
            font-size: 0.9rem;
            color: #b2bec3;
            margin-top: 10px;
        }

        footer {
            margin-top: 80px;
            color: #636e72;
            font-size: 0.85rem;
        }
    </style>
</head>
<body>
    <h1>Arcade Station</h1>
    <p class="subtitle">בחר את הכלי איתו תרצה לעבוד</p>

    <div class="grid">
        <!-- קישור לאפליקציה 1 -->
        <a href="/app1/" class="card">
            <div class="emoji-icon">🕹️</div>
            <h2>Web Scanner V1</h2>
            <p class="desc">סריקה ויזואלית ושינוי ערכות נושא</p>
        </a>

        <!-- קישור לאפליקציה 2 -->
        <a href="/app2/" class="card">
            <div class="emoji-icon">⚡</div>
            <h2>Web Ripper V3</h2>
            <p class="desc">הורדת אתרים מלאה כולל ZIP מתוקן</p>
        </a>
    </div>

    <footer>&copy; Web Scanner Pro Suite</footer>
</body>
</html>
"""

# --- 4. הגדרת האפליקציה הראשית ---
app = Flask(__name__)

@app.route('/')
def index():
    return render_template_string(MENU_HTML)

# --- 5. חיבור האפליקציות באמצעות Dispatcher ---
# בקשות ל-/app1 ילכו ל-app1, בקשות ל-/app2 ילכו ל-app2, והשאר ל-main_app
application = DispatcherMiddleware(app, {
    '/app1/': app1,
    '/app2/': app2
})

# --- 6. הרצה ---
if __name__ == "__main__":
    print("🎮 Arcade Station running at http://localhost:5000")
    print("👉 App 1 available at http://localhost:5000/app1")
    print("👉 App 2 available at http://localhost:5000/app2")
    
    # שימוש ב-run_simple של Werkzeug להרצת מספר אפליקציות במקביל
    run_simple('0.0.0.0', 5000, application, use_reloader=True, use_debugger=True)
