from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.serving import run_simple
from flask import Flask, render_template_string, redirect, url_for
import random


# --- 1. Styled "Under Development" Page ---
def development_page(text):
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
        <h1>{text}</h1>
        <div class="subtitle">🚧 האתר עדיין בפיתוח 🚧</div>
      </div>
    '''


def create_dummy_app(text):
    dummy = Flask(__name__)

    @dummy.route('/')
    def index():
        return development_page(text)

    return dummy


# --- 2. Safe import apps ---
try:
    from app1 import app as app1
except ImportError:
    app1 = create_dummy_app("App 1")

try:
    from app2 import app as app2
except ImportError:
    app2 = create_dummy_app("App 2")


# --- 3. Main Launcher ---
main_app = Flask(__name__)


@main_app.route('/')
def index():
    return render_template_string(MENU_HTML)


# ✅ Proper random routing handled in backend
@main_app.route('/random/')
def random_redirect():
    return redirect('/app1/' if random.random() < 0.5 else '/app2/')


MENU_HTML = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>Arcade Station</title>
    <link href="https://fonts.googleapis.com/css2?family=Heebo:wght@300;700;900&display=swap" rel="stylesheet">
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
            border: 1px solid rgba(255,255,255,0.05);
        }

        .card:hover {
            transform: translateY(-8px) scale(1.02);
            border-color: var(--accent);
            box-shadow: 0 15px 30px rgba(0, 206, 201, 0.2);
        }

        .emoji-icon {
            font-size: 50px;
            margin-bottom: 15px;
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
    <p class="subtitle">בחר את ההרפתקה הבאה שלך</p>

    <div class="grid">
        <a href="/app1/" class="card">
            <div class="emoji-icon">🕹️</div>
            <h2>גרסה 1</h2>
        </a>

        

        <a href="/app2/" class="card">
            <div class="emoji-icon">⚡</div>
            <h2>גרסה 2</h2>
        </a>
    </div>

    <footer>&copy; Aviel Aluf</footer>
</body>
</html>
"""


# --- 4. Connect Apps ---
app = DispatcherMiddleware(main_app, {
    '/app1': app1,
    '/app2': app2
})


# --- 5. Run ---
if __name__ == "__main__":
    print("🎮 Arcade Station running at http://localhost:5000")
    run_simple('0.0.0.0', 5000, app, use_reloader=True, use_debugger=True)
