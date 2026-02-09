from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.serving import run_simple
from flask import Flask, render_template_string, send_from_directory
import os
import random

x = '/app1' if random.random() < 0.5 else '/app2'


# --- 1. דף "בפיתוח" מעוצב ---
def a(text):
    return f'''
      <style>
        body {{
          margin: 0;
          font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
          background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
          color: #fff;
          height: 100vh;
          display: flex;
          align-items: center;
          justify-content: center;
        }}
        .hero {{ text-align: center; padding: 40px 20px; }}
        h1 {{ font-size: clamp(2rem, 5vw, 3.5rem); margin: 0; font-weight: 700; }}
        .subtitle {{ margin-top: 16px; font-size: 1.2rem; opacity: 0.85; }}
      </style>
      <div class="hero">
        <div>
          <h1>{text}</h1>
          <div class="subtitle">🚧 האתר עדיין בפיתוח 🚧</div>
        </div>
      </div>
    '''

# פונקציית דמה ליצירת אפליקציות חסרות
def create_dummy_app(text):
    dummy = Flask(__name__)
    @dummy.route('/')
    def index():
        return a(text)
    return dummy

# --- 2. ייבוא בטוח של האפליקציות ---
# נסה לייבא - אם לא קיים, השתמש בדמה
try: from app1 import app as app1
except ImportError: app1 = create_dummy_app("app 1")

try: from app2 import app as app2
except ImportError: app2 = create_dummy_app("app 2")


# --- 3. הלאוצ'ר הראשי ---
main_app = Flask(__name__)

@main_app.route('/')
def index():
    return render_template_string(MENU_HTML)

MENU_HTML = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>Web-Scanner Pro</title>
    <link href="                                                       ;700;900&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary: #6c7ce7;
            --accent: #00cec9;
            --bg-dark: #0a0a0c;
            --card-bg: #1e1e24;
            --glow-primary: rgba(108, 124, 231, 0.4);
            --glow-accent: rgba(0, 206, 201, 0.4);
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            background-color: var(--bg-dark);
            background-image: radial-gradient(circle at 10% 20%, rgb(30, 30, 30) 0%, rgb(10, 10, 12) 90%);
            color: #dfe6e9;
            font-family: 'Heebo', sans-serif;
            text-align: center;
            padding: 40px 20px;
            min-height: 100vh;
        }

        h1 {
            font-size: clamp(2rem, 6vw, 3.5rem);
            margin: 0 0 10px 0;
            background: linear-gradient(90deg, #a29bfe, #74b9ff, #00cec9);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 900;
            text-transform: uppercase;
        }

        .subtitle { color: #b2bec3; font-size: 1.2rem; margin-bottom: 60px; font-weight: 300; }

        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 30px;
            max-width: 1200px;
            margin: 0 auto;
        }

        .card {
            background: var(--card-bg);
            border-radius: 20px;
            padding: 30px 20px;
            text-decoration: none;
            color: white;
            transition: all 0.4s;
            display: flex; flex-direction: column; align-items: center;
            border: 1px solid rgba(255,255,255,0.05);
            box-shadow: 0 10px 20px rgba(0,0,0,0.3);
            position: relative; overflow: hidden;
        }

        .card:hover {
            transform: translateY(-10px) scale(1.03);
            border-color: var(--accent);
            box-shadow: 0 20px 40px rgba(0, 206, 201, 0.2);
            background: linear-gradient(135deg, #252530 0%, #2a2a35 100%);
        }

        .emoji-icon { font-size: 60px; margin-bottom: 15px; filter: drop-shadow(0 0 15px rgba(255,255,255,0.3)); }
        
        .card h2 { margin: 10px 0; font-size: 1.5rem; font-weight: 700; }
        
        .tag {
            font-size: 0.85rem; color: #81ecec; background: rgba(129, 236, 236, 0.15);
            padding: 6px 14px; border-radius: 20px; margin-top: 10px;
            border: 1px solid rgba(129, 236, 236, 0.2);
        }

        footer { margin-top: 80px; color: #636e72; font-size: 0.85rem; }
    </style>
</head>
<body>
    <h1>Arcade Station</h1>
    <p class="subtitle">בחר את ההרפתקה הבאה שלך</p>

    <div class="grid">
        <a href="/app1/" class="card"><span class="emoji-icon">v1</span><h2>מגניב</h2><div class="tag">לאינטרנט רגיל</div></a>
        <a href=" """+x+"""/"class="card"><span class="emoji-icon">רנדומלי</span><h2><<< >>></h2><div class="tag"></div></a>
        <a href="/app2/" class="card"><span class="emoji-icon">v2</span><h2>פשוט</h2><div class="tag">לאינטרנט מסונן</div></a>
    </div>

    <footer>&copy; Aviel Aluf x0583289789@gmail.com</footer>
</body>
</html>
"""

# --- 4. חיבור האפליקציות ---
app = DispatcherMiddleware(main_app, {
    'app1':app1,
    'app2':app2
})

# --- 5. הרצה ---
if __name__ == "__main__":
    print("🎮 Arcade Station Running at http://localhost:5000")
    run_simple('0.0.0.0', 5000, app, use_reloader=True, use_debugger=True)


