from flask import Flask, render_template_string, request, jsonify, session, url_for
import json
import uuid

# משנים את ה-name כדי שלא יהיה 'app' סתמי, עוזר בדיבאג
app = Flask(__name__)
app.secret_key = 'ultra_secret_pro_key_game6'

# =========================
# DATA & LOGIC (SAME)
# נשאיר את לוגיקת המשחק והנתונים זהים למה ששלחתי קודם
# כדי לחסוך מקום, אני מדלג כאן על הגדרת ה-GAME_DATA וה-GameEngine המלאים
# *** העתק לכאן את מחלקת GameEngine והמילונים מהקוד הקודם ***
# לצורך ההדגמה אשים כאן גרסה מקוצרת שעובדת, אתה תדביק את המלאה
# =========================

GAME_DATA = {
    "start_room": "cell",
    "rooms": {
        "cell": {
            "name": "תא כלא חשוך (app6)",
            "desc": "אתה כאן. הדלת נעולה.",
            "exits": {},
            "items": [],
        }
    }
}

class GameEngine:
    def __init__(self, state=None):
        if state:
            self.state = state
        else:
            self.state = {"loc": "cell", "inv": [], "hp": 30, "flags": {}, "log": []}
            self.add_log("המשחק התחיל...")

    def add_log(self, text, type="neutral"):
        self.state["log"].append({"text": text, "type": type})

    def process(self, raw_input):
        # לוגיקה מקוצרת להדגמה - החלף בלוגיקה המלאה שלך
        self.add_log(f"אמרת: {raw_input}", "info")
        return self.state
    
    # ... כאן צריך להדביק את הפונקציות המלאות של המנוע ...

# =========================
# ROUTES (החלק החשוב לתיקון)
# =========================

@app.route("/")
def index():
    if "uid" not in session:
        session["uid"] = str(uuid.uuid4())
    
    # --- התיקון הקריטי: ---
    # אנחנו יוצרים את הכתובת המלאה ל-API בהתאם למיקום שה-Middleware נתן לנו
    api_url = url_for('api_command') # זה יחזיר "/game6/api/command" אוטומטית!
    reset_url = url_for('api_reset')
    
    # מעבירים את הכתובות ל-HTML
    return render_template_string(HTML_TEMPLATE, api_url=api_url, reset_url=reset_url)

@app.route("/api/command", methods=["POST"])
def api_command():
    data = request.get_json(silent=True) or {}
    cmd = data.get("command")
    state = session.get("game_state", None)
    
    engine = GameEngine(state) # שים לב: עליך להדביק את מחלקת ה-Engine המלאה למעלה
    
    if cmd:
        engine.process(cmd)
    
    session["game_state"] = engine.state
    
    loc_name = "..."
    if engine.state["loc"] in GAME_DATA["rooms"]:
        loc_name = GAME_DATA["rooms"][engine.state["loc"]]["name"]

    return jsonify({
        "log": engine.state["log"][-10:],
        "hp": engine.state["hp"],
        "loc_name": loc_name
    })

@app.route("/api/reset", methods=["POST"])
def api_reset():
    session.clear()
    return jsonify({"status": "ok"})

# HTML עם התיקון ב-JavaScript
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>משחק 6</title>
    <style>
        body { background-color: #111; color: #ddd; font-family: monospace; padding: 20px; text-align:center;}
        #log { border: 1px solid #444; height: 300px; overflow-y: scroll; padding: 10px; text-align: right; background: black; margin: 20px auto; max-width: 600px;}
        .entry { padding: 2px 0; }
        .entry.info { color: cyan; }
    </style>
</head>
<body>
    <h1>משחק 6 - הרפתקה</h1>
    <h3 id="loc-display">מיקום...</h3>
    
    <div id="log"></div>

    <input type="text" id="cmd" placeholder="פקודה..." onkeydown="if(event.key==='Enter') send()">
    <button onclick="send()">שלח</button>
    <br><br>
    <button onclick="doReset()">אפס משחק</button>
    <br>
    <a href="/" style="color: #666; font-size: 12px; margin-top:20px; display:block;">חזרה לתפריט הראשי</a>

    <script>
        // *** כאן הקסם: שימוש במשתנים שקיבלנו מהפייתון ***
        const API_URL = "{{ api_url }}"; 
        const RESET_URL = "{{ reset_url }}";

        async function send() {
            const inp = document.getElementById('cmd');
            const val = inp.value;
            inp.value = '';

            // משתמשים בכתובת הדינמית
            const res = await fetch(API_URL, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({command: val})
            });
            const data = await res.json();
            
            const logDiv = document.getElementById('log');
            logDiv.innerHTML = ''; 
            data.log.forEach(l => {
                const d = document.createElement('div');
                d.className = 'entry ' + l.type;
                d.innerText = l.text;
                logDiv.appendChild(d);
            });
            document.getElementById('loc-display').innerText = data.loc_name;
            logDiv.scrollTop = logDiv.scrollHeight;
        }

        async function doReset() {
            await fetch(RESET_URL, {method: 'POST'});
            location.reload();
        }

        // הפעלה ראשונית לרענון מסך
        send();
    </script>
</body>
</html>
"""

# כדי שירוץ עצמאית לבדיקה
if __name__ == "__main__":
    app.run(port=5006, debug=True)
