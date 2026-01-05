from flask import Flask, render_template_string, request, jsonify, session, url_for
import json
import uuid
import random

app = Flask(__name__)
app.secret_key = 'shadow_maze_offline_key'

# --- 🗺️ נתוני עולם (WORLD DATA) ---
GAME_DATA = {
    "start_room": "cell",
    "rooms": {
        "cell": {
            "name": "תא כלא עזוב",
            "desc": "אתה כלוא בתא אבן לח. טיפות מים נופלות מהתקרה.",
            "exits": {"out": "corridor"}, 
            "items": ["rusted_spoon"],
            "interactables": {
                "door": {"desc": "דלת ברזל חזקה. היא נעולה.", "locked": True, "key_needed": "bone_key"}
            }
        },
        "corridor": {
            "name": "המסדרון הארוך",
            "desc": "המסדרון חשוך ומלא קורי עכביש. יש כאן ריח של ריקבון.",
            "exits": {"cell": "cell", "north": "armory"},
            "items": [],
            "enemies": ["skeleton"]
        },
        "armory": {
            "name": "חדר הנשק",
            "desc": "חדר ששימש את השומרים. הרוב נבזז מזמן.",
            "exits": {"south": "corridor"},
            "items": ["old_sword", "bone_key"]
        }
    },
    "items": {
        "rusted_spoon": {"name": "כף חלודה", "desc": "אפשר לחפור איתה, או לאכול מרק דמיוני."},
        "old_sword": {"name": "חרב ישנה", "desc": "עדיין חדה מספיק כדי לחתוך."},
        "bone_key": {"name": "מפתח עצם", "desc": "מפתח מגולף מעצם לבנה. נראה חשוב."}
    }
}

# ==========================================
# 🧠 המוח העצמאי שלנו (Logic Brain) 🧠
# ==========================================
class OfflineBrain:
    def __init__(self, state):
        self.state = state
        self.loc_id = state['loc']
        self.room = GAME_DATA["rooms"][self.loc_id]
        
    def think(self, user_text):
        txt = user_text.lower()
        inv = self.state['inv']
        
        # --- תגובות מבוססות הקשר (Context) ---
        
        # 1. שאלות על המיקום
        if any(w in txt for w in ["איפה", "מקום", "מיקום", "תאר"]):
            return f"המדריך: אתה כרגע ב{self.room['name']}. הבט סביבך בזהירות."

        # 2. רמזים על חפצים ספציפיים (אם המשתמש מזכיר אותם)
        if "מפתח" in txt:
            if "bone_key" in inv:
                return "המדריך: יש לך את המפתח ביד. עכשיו רק נשאר למצוא מה הוא פותח..."
            elif "bone_key" in self.room.get("items", []):
                return "המדריך: אני רואה מפתח בחדר הזה. אולי כדאי לקחת אותו?"
            else:
                return "המדריך: המקום הזה דורש מפתח, אבל אני לא רואה אותו בחדר הזה."

        if "חרב" in txt or "נשק" in txt:
             if "old_sword" in inv:
                 return "המדריך: אתה חמוש ומוכן לקרב."
             elif "old_sword" in self.room.get("items", []):
                 return "המדריך: החרב מונחת לפניך. היא יכולה להגן עליך."
             else:
                 return "המדריך: אתה חשוף. כדאי שתמצא משהו להגן על עצמך."

        # 3. בקשות עזרה כלליות / יציאה
        if "צא" in txt or "לברוח" in txt or "יציאה" in txt:
            if self.loc_id == "cell" and GAME_DATA["rooms"]["cell"]["interactables"]["door"]["locked"]:
                return "המדריך: הדלת חוסמת את הדרך. בלי מפתח, אתה תישאר פה לנצח."
            else:
                return "המדריך: נסה לנוע בין החדרים בעזרת הפקודה 'לך'. חפש את האור בקצה המנהרה."
                
        # 4. זהות השחקן
        if "מי אני" in txt or "שמי" in txt:
            return "המדריך: אתה אסיר מספר 42. או לפחות זה מה שהיה כתוב על הדלת כשהתעוררת. העבר שלך הוא חידה."

        # 5. ברירת מחדל (Fallback) עם גיוון
        fallbacks = [
            f"המדריך: המממ... ({txt}) זו מחשבה מעניינת.",
            "המדריך: הקירות כאן עבים, אני בקושי שומע אותך. נסה להתרכז בחיפושים.",
            "המדריך: הרוח מייללת במסדרונות... עדיף שתעשה משהו מועיל.",
            "המדריך: אני מציע שתבדוק שוב את התיק שלך או את הרצפה."
        ]
        return random.choice(fallbacks)


# ==========================================
# לוגיקה חכמה (Engine)
# ==========================================
class GameEngine:
    def __init__(self, state=None):
        if state:
            self.state = state
        else:
            self.state = {
                "loc": "cell",
                "inv": [],
                "hp": 30,
                "log": [{"text": "התעוררת... (המערכת רצה במצב עצמאי)", "type": "game"}],
                "flags": {}
            }

    def add_msg(self, text, type="game"):
        self.state["log"].append({"text": text, "type": type})

    def get_room(self):
        return GAME_DATA["rooms"][self.state["loc"]]

    def process_input(self, user_input):
        cmd_parts = user_input.strip().lower().split()
        if not cmd_parts: return self.state

        action = cmd_parts[0]
        # מילון פקודות טכניות
        commands = {
            "go": self._go, "לך": self._go, 
            "take": self._take, "קח": self._take,
            "look": self._look, "הסתכל": self._look,
            "inv": self._inv, "תיק": self._inv, "מלאי": self._inv,
            "use": self._use, "השתמש": self._use
        }

        # אם זו פקודה טכנית שמנוע המשחק מכיר - בצע אותה
        if action in commands:
            arg = cmd_parts[1] if len(cmd_parts) > 1 else None
            commands[action](arg)
        else:
            # 💡 אם לא, הפעל את המוח העצמאי שבנינו
            brain = OfflineBrain(self.state)
            response = brain.think(user_input)
            self.add_msg(response, "ai")
        
        return self.state

    # --- פעולות טכניות ---
    def _go(self, d):
        r = self.get_room()
        direction_map = {"קדימה": "north", "אחורה": "south", "יציאה": "out", "החוצה": "out", "דרום": "south", "צפון": "north"}
        d = direction_map.get(d, d)
        
        # בדיקת דלתות
        if self.state["loc"] == "cell" and d == "out":
             if GAME_DATA["rooms"]["cell"]["interactables"]["door"]["locked"]:
                 self.add_msg("הדלת נעולה. אתה צריך מפתח.", "game warning")
                 return

        if d in r["exits"]:
            self.state["loc"] = r["exits"][d]
            self.add_msg(f"הלכת ל-{d}.", "game")
            self._look(None)
        else:
            self.add_msg("אי אפשר ללכת לשם.", "game warning")

    def _take(self, item):
        mapping = {"מפתח": "bone_key", "כף": "rusted_spoon", "חרב": "old_sword"}
        target = mapping.get(item, item)
        r = self.get_room()
        if target in r["items"]:
            self.state["inv"].append(target)
            r["items"].remove(target)
            self.add_msg(f"לקחת: {target}", "game success")
        else:
            self.add_msg("אין פה את זה.", "game warning")

    def _use(self, arg):
        if ("key" in str(arg) or "מפתח" in str(arg)) and "bone_key" in self.state["inv"]:
             if self.state["loc"] == "cell":
                 GAME_DATA["rooms"]["cell"]["interactables"]["door"]["locked"] = False
                 self.add_msg("הכנסת את המפתח... קליק! נפתח.", "game success")
             else:
                 self.add_msg("אין מה לפתוח פה.", "game")
        else:
            self.add_msg("זה לא עובד.", "game")

    def _look(self, arg):
        r = self.get_room()
        info = f"אתה ב{r['name']}. {r['desc']}"
        if r["items"]: info += f"<br>יש פה: {r['items']}"
        if "enemies" in r: info += "<br><span style='color:red'>⚠️ זהירות: אויב!</span>"
        self.add_msg(info, "game")

    def _inv(self, arg):
        self.add_msg(f"תיק: {self.state['inv']}", "game info")


# ==========================================
# שרת וניתובים
# ==========================================

@app.route("/")
def index():
    if "uid" not in session: session["uid"] = str(uuid.uuid4())
    api_url = url_for('api_command')
    reset_url = url_for('api_reset')
    return render_template_string(CHAT_HTML, api_url=api_url, reset_url=reset_url)

@app.route("/api/command", methods=["POST"])
def api_command():
    data = request.get_json(silent=True) or {}
    user_txt = data.get("command", "")
    
    # שים לב: אנחנו מעבירים עותק (Copy) כדי שהמשחק לא "יתאפס" סתם
    # לוקחים את ה state מהsession
    state = session.get("game_state", None)
    
    engine = GameEngine(state)
    
    if user_txt:
        engine.add_msg(user_txt, "user")
        engine.process_input(user_txt)
    
    session["game_state"] = engine.state
    
    loc_name = "לא ידוע"
    if engine.state["loc"] in GAME_DATA["rooms"]:
        loc_name = GAME_DATA["rooms"][engine.state["loc"]]["name"]

    return jsonify({
        "log": engine.state["log"],
        "loc_name": loc_name
    })

@app.route("/api/reset", methods=["POST"])
def api_reset():
    session.clear()
    return jsonify({"status": "ok"})

# ממשק משתמש
CHAT_HTML = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>הרפתקה - מוח עצמאי</title>
    <style>
        body { background: #222; color: #fff; font-family: sans-serif; display: flex; height: 100vh; margin:0;}
        .sidebar { width: 220px; background: #333; padding: 20px; }
        .sidebar div { background: #444; padding: 10px; margin: 5px 0; cursor: pointer; border-radius: 4px; transition:0.2s}
        .sidebar div:hover { background: #666; color: #81ecec; }
        .chat { flex-grow: 1; display: flex; flex-direction: column; background: #111; max-width: 900px; margin: 0 auto;}
        .msgs { flex-grow: 1; padding: 20px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; }
        .input-box { padding: 15px; background: #222; display: flex; }
        input { flex-grow: 1; padding: 10px; background: #333; color: white; border: none; font-size: 1.1rem; }
        button { padding: 10px 20px; background: #00cec9; border: none; cursor: pointer; font-weight:bold;}
        
        .bubble { padding: 10px 15px; border-radius: 8px; max-width: 80%; line-height: 1.4; }
        .bubble.user { align-self: flex-start; background: #00cec9; color: black; border-bottom-right-radius: 0; }
        .bubble.game { align-self: flex-end; background: #333; border: 1px solid #444; border-bottom-left-radius: 0; }
        .bubble.ai { align-self: flex-end; background: linear-gradient(135deg, #a29bfe, #6c5ce7); color: white; border:1px solid #6c5ce7;} 
        .bubble.game.success { border-right: 4px solid lime; }
        .bubble.game.warning { border-right: 4px solid orange; }
    </style>
</head>
<body>
    <div class="sidebar">
        <h3>פקודות</h3>
        <div onclick="cmd('הסתכל')">👁️ הסתכל</div>
        <div onclick="cmd('מלאי')">🎒 מה בתיק</div>
        <div onclick="cmd('השתמש במפתח')">🔑 השתמש במפתח</div>
        <div onclick="cmd('לך החוצה')">🚪 צא למסדרון</div>
        <div onclick="cmd('לך לצפון')">⬆️ לך צפונה</div>
        <div onclick="reset()" style="color:salmon; margin-top:30px;">🔄 התחל מחדש</div>
    </div>
    <div class="chat">
        <div style="padding:15px; border-bottom:1px solid #333;" id="title">חדר...</div>
        <div class="msgs" id="log"></div>
        <div class="input-box">
            <input type="text" id="inp" placeholder="שאל את המדריך העצמאי..." onkeydown="if(event.key==='Enter') send()">
            <button onclick="send()">➤</button>
        </div>
    </div>

    <script>
        const API = "{{ api_url }}";
        
        async function send() {
            let val = document.getElementById('inp').value;
            document.getElementById('inp').value = '';
            if(val) appendMsg(val, 'user');

            let res = await fetch(API, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({command: val})
            });
            let data = await res.json();
            
            document.getElementById('log').innerHTML = '';
            data.log.forEach(m => appendMsg(m.text, m.type));
            document.getElementById('title').innerText = data.loc_name;
        }

        function cmd(txt) {
            document.getElementById('inp').value = txt;
            send();
        }

        function appendMsg(txt, type) {
            let el = document.getElementById('log');
            let d = document.createElement('div');
            d.className = 'bubble ' + type;
            d.innerHTML = txt;
            el.appendChild(d);
            el.scrollTop = el.scrollHeight;
        }
        
        async function reset() { await fetch("{{ reset_url }}", {method:'POST'}); location.reload(); }
        send();
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(port=5006, debug=True)
