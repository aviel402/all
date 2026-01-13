from flask import Flask, render_template_string, request, redirect, url_for

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>משחק 4 – אתגר אסטרטגי</title>
    <style>
        body { background: #0f172a; color: #e5e7eb; font-family: Arial, sans-serif; text-align:center; padding:40px;}
        .box { background: #1e293b; padding:30px; border-radius:15px; max-width:500px; margin:auto; }
        button { margin:10px; padding:10px 25px; font-size:16px; border-radius:8px; border:none; cursor:pointer; }
    </style>
</head>
<body>
    <div class="box">
        <h1>משחק 4 – אתגר אסטרטגי</h1>
        <p>רמה: {{ difficulty }} | משאבים: {{ resources }}</p>
        <p>{{ message }}</p>

        {% if game_over %}
            <form method="post">
                <button type="submit" name="restart" value="1">שחק שוב</button>
            </form>
        {% else %}
            <form method="post">
                <button type="submit" name="action" value="1">פעולה 1</button>
                <button type="submit" name="action" value="2">פעולה 2</button>
                <input type="hidden" name="difficulty" value="{{ difficulty }}">
                <input type="hidden" name="resources" value="{{ resources }}">
            </form>
        {% endif %}
    </div>
</body>
</html>
"""

# הגדרות לפי רמות קושי
DIFFICULTY_SETTINGS = {
    "קל": 10,
    "בינוני": 7,
    "קשה": 5
}

@app.route("/", methods=["GET", "POST"])
def index():
    # ברירת מחדל
    difficulty = request.form.get("difficulty", "קל")
    resources = int(request.form.get("resources", DIFFICULTY_SETTINGS[difficulty]))
    game_over = False
    message = "בחר פעולה להמשיך במשחק."

    # בדיקה אם מתחילים מחדש
    if "restart" in request.form:
        resources = DIFFICULTY_SETTINGS[difficulty]
        message = "המשחק התחיל מחדש!"
    elif "action" in request.form:
        action = int(request.form["action"])
        # השפעה של כל פעולה על המשאבים
        if action == 1:
            resources -= 1  # פעולה בטוחה
            message = "פעולה 1 הצליחה, אך משאב קטן נצרך."
        elif action == 2:
            resources -= 2  # פעולה מסוכנת יותר
            message = "פעולה 2 מסוכנת יותר! שים לב למשאבים."

    # בדיקה אם המשחק נגמר
    if resources <= 0:
        game_over = True
        message = "המשאבים נגמרו! המשחק הסתיים."

    return render_template_string(
        HTML,
        difficulty=difficulty,
        resources=resources,
        message=message,
        game_over=game_over
    )
