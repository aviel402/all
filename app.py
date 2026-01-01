from flask import Flask, render_template_string
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.serving import run_simple

# ייבוא כל המשחקים (הנחתי שהקבצים קיימים ובכולם יש משתנה בשם app)
from app1 import app as game1
from app2 import app as game2
from app3 import app as game3
from app4 import app as game4
from app5 import app as game5

# יצירת אפליקציית "לובי" ראשית
main_app = Flask(__name__)

# הגדרת עיצוב התפריט
MENU_HTML = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Arcade Station</title>
    <style>
        body { background-color: #0f0f13; color: #fff; font-family: 'Segoe UI', sans-serif; text-align: center; margin: 0; padding: 20px; }
        h1 { font-size: 3rem; margin-bottom: 10px; background: -webkit-linear-gradient(#eee, #333); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        p { color: #868; margin-bottom: 40px; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; max-width: 1000px; margin: 0 auto; }
        .card { 
            background: #1f1f23; border: 1px solid #333; padding: 20px; border-radius: 12px; 
            text-decoration: none; color: white; transition: 0.2s; display: flex; flex-direction: column; justify-content: center;
        }
        .card:hover { transform: translateY(-5px); border-color: #00d4ff; background: #25252b; }
        .card h2 { margin: 0; font-size: 1.5rem; }
        .card span { font-size: 30px; display: block; margin-bottom: 10px; }
        .tag { font-size: 0.8rem; color: #aaa; margin-top: 5px; }
    </style>
</head>
<body>
    <h1>🕹️ ARCADE STATION</h1>
    <p>בחר משחק</p>
    
    <div class="grid">
        <a href="/game1/" class="card"><span>🏝️</span><h2>הישרדות</h2><div class="tag">ניהול משאבים</div></a>
        <a href="/game2/" class="card"><span>⚔️</span><h2>RPG Legend</h2><div class="tag">הרפתקאות</div></a>
        <a href="/game3/" class="card"><span>🚀</span><h2>Genesis</h2><div class="tag">חלל וקבלת החלטות</div></a>
        <a href="/game4/" class="card"><span>🏙️</span><h2>Underworld</h2><div class="tag">כנופיות ועיר</div></a>
        <a href="/game5/" class="card"><span>🛡️</span><h2>Iron Legion</h2><div class="tag">אסטרטגיה וצבא</div></a>


    </div>
</body>
</html>
"""

@main_app.route('/')
def index():
    return render_template_string(MENU_HTML)

# שילוב כל האפליקציות באמצעות DispatcherMiddleware
# חשוב: שים לב לסלאש (/) בסוף הנתיב של כל אפליקציה בתפריט למעלה
app = DispatcherMiddleware(main_app, {
    '/game1': game1,
    '/game2': game2,
    '/game3': game3,
    '/game4': game4,
    '/game5': game5

})

if __name__ == "__main__":
    run_simple('0.0.0.0', 5000, app, use_reloader=True, use_debugger=True)
