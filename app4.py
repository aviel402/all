from flask import Flask, render_template_string, request
import random

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>משחק 4 – אתגר אסטרטגי</title>
    <style>
        body { background: #0f172a; color: #e5e7eb; font-family: Arial, sans-serif; text-align:center; padding:40px;}
        .box { background: #1e293b; padding:30px; border-radius:20px; max-width:600px; margin:auto; box-shadow: 0 5px 15px rgba(0,0,0,0.5);}
        h1 { color: #38bdf8; }
        p { font-size: 18px; }
        button { margin:10px; padding:12px 30px; font-size:16px; border-radius:10px; border:none; cursor:pointer; transition: 0.2s; }
        button:hover { transform: scale(1.05); background: #06b6d4; color: #fff; }
        .status { margin: 15px 0; font-weight: bold; color: #a5f3fc; }
        .score { color: #facc15; font-size: 20px; }
    </style>
</head>
<body>
    <div class="box">
        <h1>משחק 4 – אתגר אסטרטגי</h1>
        <p class="status">רמה: {{ difficulty }} | משאבים: {{ resources }} | ניקוד: <span class="score">{{ score }}</span></p>
        <p>{{ message }}</p>

        {% if game_over %}
            <form method="post">
                <button type="submit" name="restart" value="1">שחק שוב</button>
            </form>
        {% else %}
            <form method="post">
                <button type="submit" name="action" value="1">פעולה 1 – בטוחה</button>
                <button type="submit" name="action" value="2">פעולה 2 – מסוכנת</button>
                <input type="hidden" name="difficulty" value="{{ difficulty }}">
                <input type="hidden" name="resources" value="{{ resources }}">
                <input type="hidden" name="score" value="{{ score }}">
            </form>
        {% endif %}
    </div>
</body>
</html>
"""

DIFFICULTY_SETTINGS = {
    "קל": 12,
    "בינוני": 8,
    "קשה": 5
}

@app.route("/", methods=["GET", "POST"])
def index():
    # ברירת מחדל
    difficulty = request.form.get("difficulty", "קל")
    resources = int(request.form.get("resources", DIFFICULTY_SETTINGS[difficulty]))
    score = int(request.form.get("score", 0))
    message = "בחר פעולה להמשיך במשחק."
    game_over = False

    # אתחול מחדש
    if "restart" in request.form:
        resources = DIFFICULTY_SETTINGS[difficulty]
        score = 0
        message = "המשחק התחיל מחדש!"

    elif "action" in request.form:
        action = int(request.form["action"])
        # אירוע אקראי: 20% סיכוי לאסון קטן
        event = random.randint(1, 100)
        if action == 1:
            resources -= 1
            score += 1
            message = "פעולה 1 הצליחה! +1 ניקוד"
        elif action == 2:
            resources -= 2
            score += 2
            message = "פעולה 2 מסוכנת – הצליחה! +2 ניקוד"

        # אירוע אקראי שמוריד משאב
        if event <= 20:
            resources -= 1
            message += " | אירוע לא צפוי פגע במשאבים!"

    # בדיקה אם המשחק נגמר
    if resources <= 0:
        game_over = True
        message = f"המשאבים נגמרו! סיימת עם ניקוד: {score}"

    return render_template_string(
        HTML,
        difficulty=difficulty,
        resources=resources,
        score=score,
        message=message,
        game_over=game_over
    )
