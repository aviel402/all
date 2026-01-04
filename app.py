from flask import Flask, render_template_string
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.serving import run_simple

# נסה לייבא. אם חסר קובץ, נשתמש באפליקציית דמה (Dummy App) כדי שהקוד ירוץ
def create_dummy_app(text):
    dummy = Flask(__name__)
    @dummy.route('/')
    def index(): return f"<h1 style='color:white; text-align:center; margin-top:50px;'>{text}<br>עדיין בפיתוח</h1>"
    return dummy

try: from app1 import app as game1
except ImportError: game1 = create_dummy_app("משחק 1")

try: from app2 import app as game2
except ImportError: game2 = create_dummy_app("משחק 2")

try: from app3 import app as game3
except ImportError: game3 = create_dummy_app("משחק 3")

try: from app4 import app as game4
except ImportError: game4 = create_dummy_app("משחק 4")

try: from app5 import app as game5
except ImportError: game5 = create_dummy_app("משחק 5")

# app6 הוא המשחק ששלחתי לך כרגע (וודא ששמרת אותו כ-app6.py)
try: from app6 import app as game6
except ImportError: game6 = create_dummy_app("משחק 6 - ההרפתקה (לא נמצא הקובץ)")


# --- הלאוצ'ר הראשי ---
main_app = Flask(__name__)

MENU_HTML = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Arcade Hub</title>
    <link href="https://fonts.googleapis.com/css2?family=Heebo:wght@300;700;900&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary: #6c5ce7;
            --accent: #00cec9;
            --bg-dark: #121212;
            --card-bg: #1e1e24;
        }

        body {
            background-color: var(--bg-dark);
            background-image: radial-gradient(circle at 10% 20%, rgb(30, 30, 30) 0%, rgb(10, 10, 12) 90%);
            color: #dfe6e9;
            font-family: 'Heebo', sans-serif;
            text-align: center;
            margin: 0;
            padding: 40px 20px;
            min-height: 100vh;
        }

        h1 {
            font-size: 3.5rem;
            margin: 0;
            background: linear-gradient(90deg, #a29bfe, #74b9ff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 900;
            text-transform: uppercase;
            letter-spacing: 2px;
            text-shadow: 0 5px 15px rgba(0,0,0,0.5);
        }

        p.subtitle {
            color: #b2bec3;
            font-size: 1.2rem;
            margin-bottom: 60px;
            font-weight: 300;
        }

        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 30px;
            max-width: 1200px;
            margin: 0 auto;
            perspective: 1000px;
        }

        .card {
            background: var(--card-bg);
            border-radius: 20px;
            padding: 30px 20px;
            text-decoration: none;
            color: white;
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            display: flex;
            flex-direction: column;
            align-items: center;
            position: relative;
            border: 1px solid rgba(255,255,255,0.05);
            overflow: hidden;
            box-shadow: 0 10px 20px rgba(0,0,0,0.3);
        }

        .card:hover {
            transform: translateY(-10px) scale(1.02);
            background: #252530;
            border-color: var(--accent);
            box-shadow: 0 20px 40px rgba(0, 206, 201, 0.2);
        }

        .card::before {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0; height: 4px;
            background: linear-gradient(90deg, var(--primary), var(--accent));
            opacity: 0;
            transition: 0.3s;
        }

        .card:hover::before { opacity: 1; }

        .emoji-icon {
            font-size: 60px;
            margin-bottom: 15px;
            filter: drop-shadow(0 0 10px rgba(255,255,255,0.2));
            transition: 0.3s;
        }

        .card:hover .emoji-icon {
            transform: scale(1.1) rotate(5deg);
        }

        .card h2 {
            margin: 10px 0;
            font-size: 1.8rem;
            font-weight: 700;
        }

        .tag {
            font-size: 0.9rem;
            color: #81ecec;
            background: rgba(129, 236, 236, 0.1);
            padding: 5px 12px;
            border-radius: 15px;
            margin-top: 10px;
        }

        footer {
            margin-top: 80px;
            color: #636e72;
            font-size: 0.8rem;
        }
    </style>
</head>
<body>
    <h1>Arcade Station</h1>
    <p class="subtitle">בחר את ההרפתקה הבאה שלך</p>
    
    <div class="grid">
        <a href="/game1/" class="card">
            <span class="emoji-icon">🏝️</span>
            <h2>הישרדות</h2>
            <div class="tag">ניהול משאבים</div>
        </a>
        <a href="/game2/" class="card">
            <span class="emoji-icon">⚔️</span>
            <h2>RPG Legend</h2>
            <div class="tag">אקשן טקסטואלי</div>
        </a>
        <a href="/game3/" class="card">
            <span class="emoji-icon">🚀</span>
            <h2>Genesis</h2>
            <div class="tag">מסע בחלל</div>
        </a>
        <a href="/game4/" class="card">
            <span class="emoji-icon">🏙️</span>
            <h2>Underworld</h2>
            <div class="tag">פשע ומסתורין</div>
        </a>
        <a href="/game5/" class="card">
            <span class="emoji-icon">🛡️</span>
            <h2>Iron Legion</h2>
            <div class="tag">אסטרטגיה</div>
        </a>
        <a href="/game6/" class="card">
            <span class="emoji-icon">🗝️</span>
            <h2>מבוך הצללים</h2>
            <div class="tag">הרפתקה אפלה</div>
        </a>
    </div>

    <footer>
        &copy; 2026 Developed by Python Arcade System
    </footer>
</body>
</html>
"""

@main_app.route('/')
def index():
    return render_template_string(MENU_HTML)

# בניית הניתוב הראשי
app = DispatcherMiddleware(main_app, {
    '/game1': game1,
    '/game2': game2,
    '/game3': game3,
    '/game4': game4,
    '/game5': game5,
    '/game6': game6  # משחק מבוך הצללים שלנו
})

if __name__ == "__main__":
    print("Arcade Station Running at http://localhost:5000")
    run_simple('0.0.0.0', 5000, app, use_reloader=True, use_debugger=True)
