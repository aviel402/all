from flask import Flask, render_template_string, request, jsonify, session, url_for
import json
import uuid
import random

app = Flask(__name__)
app.secret_key = 'shadow_maze_offline_key_v2'

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
# 🧠 המוח העצמאי (Offline Brain) 🧠
# ==========================================
class OfflineBrain:
    def __init__(self, state):
        self.state = state
        self.loc_id = state['loc']
        self.room = GAME_DATA["rooms"][self.loc_id]
        
    def think(self, user_text):
        txt = user_text.lower()
        inv = self.state['inv']
        
        # המרה של רשימת ה-ID לרשימת שמות בעברית לצורך התשובה
        inv_names = [GAME_DATA["items"][i]["name"] for i in inv]
        
        # 1. שאלות על המיקום
        if any(w in txt for w in ["איפה", "מקום", "מיקום", "תאר"]):
            return f"המדריך: אתה כרגע ב{self.room['name']}. הבט סביבך."

        # 2. חפצים
        if "מפתח" in txt:
            if "bone_key" in inv:
                return "המדריך: המפתח אצלך ביד."
            elif "bone_key" in self.room.get("items", []):
                return "המדריך: אני רואה מפתח בחדר. נסה 'קח מפתח'."
            else:
                return "המדריך: צריך מפתח לדלת הזאת, אבל הוא לא כאן."

        # 3. כללי
        if "מה" in txt and "תיק" in txt:
             if not inv_names: return "המדריך: התיק שלך ריק."
             return f"המדריך: יש לך בתיק {', '.join(inv_names)}."

        fallbacks = [
            f"המדריך: המממ... ({txt}) מעניין.",
            "המדריך: נסה להתרכז בחיפושים. הפקודה 'הסתכל' תעזור לך.",
            "המדריך: בדקת כבר את כל החדרים?",
            "המדריך: חפש חפצים שניתן לאסוף."
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
                "log": [{"text": "התעוררת במקום לא מוכר...", "type": "game"}],
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
        commands = {
            "go": self._go, "לך": self._go, 
            "take": self._take, "קח": self._take, "הרם": self._take,
            "look": self._look, "הסתכל": self._look,
            "inv": self._inv, "תיק": self._inv, "מלאי": self._inv,
            "use": self._use, "השתמש": self._use
        }

        if action in commands:
            arg = cmd_parts[1] if len(cmd_parts) > 1 else None
            commands[action](arg)
        else:
            brain = OfflineBrain(self.state)
            response = brain.think(user_input)
            self.add_msg(response, "ai")
        
        return self.state

    # --- פונקציות שתוקנו להצגת עברית ---
    
    def _look(self, arg):
        r = self.get_room()
        # מציג את תיאור החדר
        info = f"<b>{r['name']}</b><br>{r['desc']}"
        
        # תיקון תצוגת חפצים: המרה מ-ID לשם בעברית
        if r["items"]: 
            hebrew_names = []
            for item_id in r["items"]:
                # שולף את השם מתוך המאגר הגדול
                name = GAME_DATA["items"][item_id]["name"]
                hebrew_names.append(name)
            
            # מחבר אותם עם פסיקים
            info += f"<br><span style='color:#ffeaa7'>יש פה: {', '.join(hebrew_names)}</span>"
            
        if "enemies" in r: info += "<br><span style='color:red'>⚠️ זהירות: יש כאן אויב!</span>"
        self.add_msg(info, "game")

    def _inv(self, arg):
        if not self.state['inv']:
            self.add_msg("התיק שלך ריק לגמרי.", "game info")
        else:
            # גם כאן - המרה לעברית
            hebrew_names = [GAME_DATA["items"][i]["name"] for i in self.state['inv']]
            self.add_msg(f"בתיק שלך יש: {', '.join(hebrew_names)}", "game info")

    def _go(self, d):
        r = self.get_room()
        direction_map = {"קדימה": "north", "אחורה": "south", "יציאה": "out", "החוצה": "out", "דרום": "south", "צפון": "north"}
        d = direction_map.get(d, d)
        
        if self.state["loc"] == "cell" and d == "out":
             if GAME_DATA["rooms"]["cell"]["interactables"]["door"]["locked"]:
                 self.add_msg("הדלת נעולה. היא דורשת מפתח.", "game warning")
                 return

        if d in r["exits"]:
            self.state["loc"] = r["exits"][d]
            target_name = GAME_DATA["rooms"][self.state["loc"]]["name"]
            self.add_msg(f"הלכת אל {target_name}.", "game")
            self._look(None)
        else:
            self.add_msg("אי אפשר ללכת לשם.", "game warning")

    def _take(self, item):
        # מילון תרגום משמות בעברית שהמשתמש מקליד ל-ID
        input_mapping = {
            "מפתח": "bone_key", "המפתח": "bone_key",
            "כף": "rusted_spoon", "הכף": "rusted_spoon", "כפית": "rusted_spoon",
            "חרב": "old_sword", "החרב": "old_sword"
        }
        
        target_id = input_mapping.get(item, item)
        r = self.get_room()
        
        if target_id in r["items"]:
            self.state["inv"].append(target_id)
            r["items"].remove(target_id)
            # מציג למשתמש את השם בעברית ולא את ה-ID
            item_hebrew_name = GAME_DATA["items"][target_id]["name"]
            self.add_msg(f"לקחת את ה{item_hebrew_name}.", "game success")
        else:
            self.add_msg("אין פה חפץ כזה.", "game warning")

    def _use(self, arg):
        if ("key" in str(arg) or "מפתח" in str(arg)) and "bone_key" in self.state["inv"]:
             if self.state["loc"] == "cell":
                 GAME_DATA["rooms"]["cell"]["interactables"]["door"]["locked"] = False
                 self.add_msg("סובבת את מפתח העצם... הדלת נפתחה בחריקה.", "game success")
             else:
                 self.add_msg("המפתח לא מתאים לשום דבר כאן.", "game")
        else:
            self.add_msg("פעולה זו לא עשתה כלום.", "game")


# ==========================================
# שרת
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
    state = session.get("game_state", None)
    engine = GameEngine(state)
    
    if user_txt:
        engine.add_msg(user_txt, "user")
        engine.process_input(user_txt)
    
    session["game_state"] = engine.state
    
    # שליפת שם החדר בעברית בצורה בטוחה
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

# ממשק המשתמש (נותר זהה)
CHAT_HTML = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>הבריחה מהכלא</title>
    <style>
        body { background: #222; color: #fff; font-family: sans-serif; display: flex; height: 100vh; margin:0;}
        .sidebar { width: 220px; background: #333; padding: 20px; display:flex; flex-direction:column; gap:8px;}
        .sidebar div { background: #444; padding: 10px; cursor: pointer; border-radius: 4px; transition:0.2s; font-size:0.95rem;}
        .sidebar div:hover { background: #666; color: #81ecec; }
        
        .chat { flex-grow: 1; display: flex; flex-direction: column; background: #18181b; max-width: 900px; margin: 0 auto;}
        
        .msgs { flex-grow: 1; padding: 20px; overflow-y: auto; display: flex; flex-direction: column; gap: 12px; }
        
        .input-box { padding: 15px; background: #2d2d30; display: flex; }
        input { flex-grow: 1; padding: 12px; background: #3e3e42; color: white; border: none; font-size: 1.1rem; border-radius: 4px;}
        input:focus { outline: 1px solid #00cec9; }
        button { padding: 0 20px; margin-right:10px; background: #00cec9; border: none; cursor: pointer; font-weight:bold; border-radius: 4px;}
        
        .bubble { padding: 12px 18px; border-radius: 12px; max-width: 80%; line-height: 1.5; font-size: 1rem; }
        .bubble.user { align-self: flex-start; background: #00cec9; color: #111; border-bottom-right-radius: 0; }
        .bubble.game { align-self: flex-end; background: #2d2d33; border: 1px solid #3f3f46; border-bottom-left-radius: 0; color: #e4e4e7;}
        .bubble.ai { align-self: flex-end; background: linear-gradient(135deg, #6c5ce7, #a29bfe); color: white; border-bottom-left-radius: 0;} 
        
        .bubble.game.success { border-right: 4px solid #4ade80; }
        .bubble.game.warning { border-right: 4px solid #facc15; }
        
        #room-title { font-weight:bold; font-size:1.2rem; color: #00cec9; }
        
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-thumb { background: #555; border-radius: 4px; }
    </style>
</head>
<body>
    <div class="sidebar">
        <h3 style="color:#ddd; margin-bottom:15px;">פקודות מהירות</h3>
        <div onclick="cmd('הסתכל')">👁️ הבט בחדר</div>
        <div onclick="cmd('מלאי')">🎒 מה יש לי בתיק?</div>
        <div onclick="cmd('קח מפתח')">🔑 קח מפתח</div>
        <div onclick="cmd('השתמש במפתח')">🔓 פתח דלת</div>
        <div onclick="cmd('קח כף')">🥄 קח כף</div>
        <div onclick="cmd('לך החוצה')">🚪 צא למסדרון</div>
        <div onclick="cmd('לך צפונה')">⬆️ לך צפונה</div>
        <div onclick="reset()" style="margin-top:auto; background:#7f1d1d; color:#fca5a5;">🗑️ התחל מחדש</div>
    </div>
    
    <div class="chat">
        <div style="padding:15px; border-bottom:1px solid #333; display:flex; justify-content:space-between; align-items:center;">
            <span id="room-title">טוען...</span>
            <span style="font-size:0.8rem; color:#666;">Offline Mode</span>
        </div>
        
        <div class="msgs" id="log"></div>
        
        <div class="input-box">
            <input type="text" id="inp" placeholder="מה תרצה לעשות?" autofocus onkeydown="if(event.key==='Enter') send()">
            <button onclick="send()">שלח</button>
        </div>
    </div>

    <script>
        const API = "{{ api_url }}";
        
        async function send() {
            let inp = document.getElementById('inp');
            let val = inp.value;
            inp.value = '';
            
            if(val) appendMsg(val, 'user');

            let res = await fetch(API, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({command: val})
            });
            let data = await res.json();
            
            // ריקון הלוג והדפסה מחדש
            document.getElementById('log').innerHTML = '';
            data.log.forEach(m => appendMsg(m.text, m.type));
            
            document.getElementById('room-title').innerText = data.loc_name;
            scrollToBottom();
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
            scrollToBottom();
        }
        
        function scrollToBottom() {
            let el = document.getElementById('log');
            el.scrollTop = el.scrollHeight;
        }
        
        async function reset() { 
            await fetch("{{ reset_url }}", {method:'POST'}); 
            location.reload(); 
        }
        
        send();
    </script>
</body>
</html>
