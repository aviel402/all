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

try: from app6 import app as game6
except ImportError: game6 = create_dummy_app("משחק 6 - ההרפתקה (לא נמצא הקובץ)")
    
try: from app7 import app as game7
except ImportError: game7 = create_dummy_app("משחק 7")

try: from app8 import app as game8
except ImportError: game8 = create_dummy_app("משחק 8")


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
            --primary: #6c7ce7;
            --accent: #00cec9;
            --bg-dark: #0a0a0c;
            --card-bg: #1e1e24;
            --glow-primary: rgba(108, 124, 231, 0.4);
            --glow-accent: rgba(0, 206, 201, 0.4);
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
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
            overflow-x: hidden;
        }

        /* Animated background particles */
        body::before {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: 
                radial-gradient(circle at 20% 50%, var(--glow-primary) 0%, transparent 50%),
                radial-gradient(circle at 80% 80%, var(--glow-accent) 0%, transparent 50%);
            opacity: 0.1;
            animation: float 15s ease-in-out infinite;
            pointer-events: none;
            z-index: 0;
        }

        @keyframes float {
            0%, 100% { transform: translate(0, 0); }
            33% { transform: translate(30px, -30px); }
            66% { transform: translate(-20px, 20px); }
        }

        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.05); }
        }

        h1 {
            position: relative;
            z-index: 1;
            font-size: clamp(2rem, 6vw, 3.5rem);
            margin: 0 0 10px 0;
            background: linear-gradient(90deg, #a29bfe, #74b9ff, #00cec9);
            background-size: 200% auto;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-weight: 900;
            text-transform: uppercase;
            letter-spacing: 3px;
            animation: fadeInUp 0.8s ease-out, gradientShift 3s ease-in-out infinite;
        }

        @keyframes gradientShift {
            0%, 100% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
        }

        p.subtitle {
            position: relative;
            z-index: 1;
            color: #b2bec3;
            font-size: clamp(1rem, 3vw, 1.2rem);
            margin-bottom: 60px;
            font-weight: 300;
            animation: fadeInUp 0.8s ease-out 0.2s both;
        }

        .grid {
            position: relative;
            z-index: 1;
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
            animation: fadeInUp 0.6s ease-out both;
            backdrop-filter: blur(10px);
        }

        .card:nth-child(1) { animation-delay: 0.1s; }
        .card:nth-child(2) { animation-delay: 0.2s; }
        .card:nth-child(3) { animation-delay: 0.3s; }
        .card:nth-child(4) { animation-delay: 0.4s; }
        .card:nth-child(5) { animation-delay: 0.5s; }
        .card:nth-child(6) { animation-delay: 0.6s; }
        .card:nth-child(7) { animation-delay: 0.7s; }
        .card:nth-child(8) { animation-delay: 0.8s; }

        .card::after {
            content: '';
            position: absolute;
            top: 50%;
            left: 50%;
            width: 0;
            height: 0;
            border-radius: 50%;
            background: radial-gradient(circle, var(--glow-accent) 0%, transparent 70%);
            transform: translate(-50%, -50%);
            transition: width 0.6s, height 0.6s;
            opacity: 0;
            pointer-events: none;
        }

        .card:hover::after {
            width: 300px;
            height: 300px;
            opacity: 0.3;
        }

        .card:hover {
            transform: translateY(-15px) scale(1.03);
            background: linear-gradient(135deg, #252530 0%, #2a2a35 100%);
            border-color: var(--accent);
            box-shadow: 
                0 20px 40px rgba(0, 206, 201, 0.2),
                0 0 30px rgba(0, 206, 201, 0.1);
        }

        .card::before {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0; height: 4px;
            background: linear-gradient(90deg, var(--primary), var(--accent));
            opacity: 0;
            transition: 0.35s;
        }

        .card:hover::before { 
            opacity: 1;
            box-shadow: 0 0 20px var(--glow-accent);
        }

        .emoji-icon {
            font-size: 60px;
            margin-bottom: 15px;
            filter: drop-shadow(0 0 15px rgba(255,255,255,0.3));
            transition: all 0.4s cubic-bezier(0.68, -0.55, 0.265, 1.55);
        }

        .card:hover .emoji-icon {
            transform: scale(1.2) rotate(10deg);
            filter: drop-shadow(0 0 25px rgba(0, 206, 201, 0.6));
            animation: pulse 1s ease-in-out infinite;
        }

        .card h2 {
            margin: 10px 0;
            font-size: clamp(1.3rem, 4vw, 1.8rem);
            font-weight: 700;
            transition: color 0.3s;
        }

        .card:hover h2 {
            color: var(--accent);
        }

        .tag {
            font-size: 0.85rem;
            color: #81ecec;
            background: rgba(129, 236, 236, 0.15);
            padding: 6px 14px;
            border-radius: 20px;
            margin-top: 10px;
            border: 1px solid rgba(129, 236, 236, 0.2);
            transition: all 0.3s;
        }

        .card:hover .tag {
            background: rgba(129, 236, 236, 0.25);
            border-color: rgba(129, 236, 236, 0.4);
            transform: scale(1.05);
        }

        footer {
            position: relative;
            z-index: 1;
            margin-top: 80px;
            color: #636e72;
            font-size: 0.85rem;
            animation: fadeInUp 1s ease-out 1s both;
        }

        /* Responsive Design */
        @media (max-width: 768px) {
            body {
                padding: 20px 15px;
            }

            .grid {
                grid-template-columns: 1fr;
                gap: 20px;
            }

            h1 {
                letter-spacing: 2px;
            }

            p.subtitle {
                margin-bottom: 40px;
            }

            .card {
                padding: 25px 15px;
            }
        }

        @media (max-width: 480px) {
            .emoji-icon {
                font-size: 50px;
            }

            .card {
                border-radius: 15px;
            }

            footer {
                margin-top: 60px;
            }
        }

        /* Accessibility */
        .card:focus {
            outline: 2px solid var(--accent);
            outline-offset: 4px;
        }

        @media (prefers-reduced-motion: reduce) {
            *,
            *::before,
            *::after {
                animation-duration: 0.01ms !important;
                animation-iteration-count: 1 !important;
                transition-duration: 0.01ms !important;
            }
        }

        /* Loading state */
        .loading {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: var(--bg-dark);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 9999;
            opacity: 1;
            transition: opacity 0.5s;
        }

        .loading.hidden {
            opacity: 0;
            pointer-events: none;
        }

        .spinner {
            width: 50px;
            height: 50px;
            border: 4px solid rgba(255,255,255,0.1);
            border-top-color: var(--accent);
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="loading" id="loading">
        <div class="spinner"></div>
    </div>

    <h1>Arcade Station</h1>
    <p class="subtitle">בחר את ההרפתקה הבאה שלך</p>
    
    <div class="grid">
        <a href="/game1/" class="card" tabindex="0" role="button" aria-label="משחק הישרדות">
            <span class="emoji-icon">🏝️</span>
            <h2>הישרדות</h2>
            <div class="tag">ניהול משאבים</div>
        </a>
        <a href="/game2/" class="card" tabindex="0" role="button" aria-label="משחק RPG Legend">
            <span class="emoji-icon">⚔️</span>
            <h2>RPG Legend</h2>
            <div class="tag">אקשן טקסטואלי</div>
        </a>
        <a href="/game3/" class="card" tabindex="0" role="button" aria-label="משחק Genesis">
            <span class="emoji-icon">🚀</span>
            <h2>Genesis</h2>
            <div class="tag">מסע בחלל</div>
        </a>
        <a href="/game4/" class="card" tabindex="0" role="button" aria-label="משחק קוד אדום">
            <span class="emoji-icon">💻</span>
            <h2>קוד אדום</h2>
            <div class="tag">פרוץ, גנוב, היעלם</div>
        </a>

        <a href="/game5/" class="card" tabindex="0" role="button" aria-label="משחק IRON LEGION">
            <span class="emoji-icon">🔫</span>
            <h2>IRON LEGION</h2>
            <div class="tag">מלחמות</div>
        </a>

        <a href="/game6/" class="card" tabindex="0" role="button" aria-label="משחק מבוך הצללים">
            <span class="emoji-icon">🗝️</span>
            <h2>מבוך הצללים</h2>
            <div class="tag">הרפתקה אפלה</div>
        </a>

        <a href="/game7/" class="card" tabindex="0" role="button" aria-label="משחק PROXIMA COMMAND">
            <span class="emoji-icon">🔥</span>
            <h2>PROXIMA COMMAND</h2>
            <div class="tag">לחץ, קבלת החלטות וניהול משאבים</div>
        </a>
        
        <a href="/game8/" class="card" tabindex="0" role="button" aria-label="משחק הטפיל">
            <span class="emoji-icon">🦠</span>
            <h2>הטפיל</h2>
            <div class="tag">תודעה טפילית</div>
        </a>
    </div>

    <footer>
        &copy; aviel aluf x0583289789@gmail.com
    </footer>

    <script>
        // Hide loading screen when page is fully loaded
        window.addEventListener('load', function() {
            setTimeout(function() {
                document.getElementById('loading').classList.add('hidden');
            }, 300);
        });

        // Keyboard navigation support
        document.querySelectorAll('.card').forEach(card => {
            card.addEventListener('keypress', function(e) {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    window.location.href = this.href;
                }
            });
        });
    </script>
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
    '/game6': game6,
    '/game7': game7,
    '/game8': game8

})

if __name__ == "__main__":
    print("🎮 Arcade Station Running at http://localhost:5000")
    print("✨ Press CTRL+C to stop the server")
    run_simple('0.0.0.0', 5000, app, use_reloader=True, use_debugger=True)
