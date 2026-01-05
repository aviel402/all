from flask import Flask, render_template_string, request, jsonify, session, url_for
import json
import uuid
import random

app = Flask(__name__)
# מפתח סודי חדש שמנקה בכוח סשנים ישנים כדי למנוע התנגשויות (פותר את ה-500)
app.secret_key = 'cyber_dungeon_pro_edition_v1'

# --- 🌑 מאגר נתונים (WORLD DATA) ---
GAME_DATA = {
    "start_room": "cell",
    "rooms": {
        "cell": {
            "name": "תא בידוד 402",
            "desc": "קירות בטון חשופים. טחב על התקרה. הריח כאן מתכתי וכבד.",
            "exits": {"out": "corridor"},
            "items": ["spoon"],
            "interactables": {
                "door": {"locked": True, "key_id": "key_card"}
            }
        },
        "corridor": {
            "name": "מסדרון ראשי",
            "desc": "אורות הפלורוסנט מהבהבים. המסדרון מתפצל. הרצפה דביקה.",
            "exits": {"cell": "cell", "north": "control_room"},
            "items": [],
        },
        "control_room": {
            "name": "חדר בקרה",
            "desc": "מסכים מנופצים, כבלים קרועים. גופה של שומר יושבת על הכסא.",
            "exits": {"south": "corridor"},
            "items": ["baton", "key_card"]
        }
    },
    "items": {
        "spoon": {"name": "כף חלודה", "desc": "שייר של ארוחה אחרונה."},
        "baton": {"name": "אלה טקטית", "desc": "נשק לטווח קצר."},
        "key_card": {"name": "כרטיס גישה אדום", "desc": "פותח דלתות ביטחון."}
    }
}

# --- 🧠 מנוע לוגי (Logic Core) ---
class GameEngine:
    def __init__(self, state=None):
        # אתחול חסין-תקלות
        if not state or "loc" not in state:
            self.state = {
                "loc": "cell",
                "inv": [],
                "log": [{"text": "המערכת אותחלה. החיבור למוח נוצר...", "type": "system"}],
                "flags": {}
            }
        else:
            self.state = state
        
        # וידוא שהמיקום תקין למניעת קריסות
        if self.state["loc"] not in GAME_DATA["rooms"]:
            self.state["loc"] = "cell"

    def add_msg(self, text, type="game"):
        self.state["log"].append({"text": text, "type": type})

    def get_room_data(self):
        return GAME_DATA["rooms"][self.state["loc"]]

    # מערכת תגובות חכמה (ללא API חיצוני)
    def ai_response(self, text):
        t = text.lower()
        inv_ids = self.state["inv"]
        current_room = self.get_room_data()
        
        # תרגום שמות חפצים בתיק לעברית לתצוגה
        inv_names = [GAME_DATA["items"][x]["name"] for x in inv_ids] if inv_ids else []

        if any(w in t for w in ["מיקום", "איפה", "סביב", "מקום"]):
            return f"Neural Link: אתה מאותר ב-<b>{current_room['name']}</b>. הזהירות נדרשת."

        if "מפתח" in t or "כרטיס" in t:
            if "key_card" in inv_ids:
                return "Neural Link: כרטיס הגישה בידיים שלך."
            elif "key_card" in current_room.get("items", []):
                return "Neural Link: יש כאן כרטיס גישה. קח אותו."
            return "Neural Link: נדרש אישור כניסה (כרטיס) כדי לעבור בדלתות מסוימות."

        if "מה" in t and "תיק" in t:
            if not inv_names: return "Neural Link: התיק שלך ריק."
            return f"Neural Link: ציוד נוכחי: {', '.join(inv_names)}."

        responses = [
            "Neural Link: הפקודה לא ברורה. נסה להתמקד בחפצים.",
            "Neural Link: הרעש הסטטי בראש מפריע. נסה שוב.",
            "Neural Link: סרוק את הסביבה ('הסתכל').",
            f"Neural Link: המערכת מזהה שניסית להגיד '{text}', אך ללא הצלחה."
        ]
        return random.choice(responses)

    def process_command(self, cmd_text):
        parts = cmd_text.strip().lower().split()
        if not parts: return self.state
        
        cmd = parts[0]
        arg = parts[1] if len(parts) > 1 else ""

        # פקודות מערכת
        actions = {
            "go": self._go, "לך": self._go, "move": self._go,
            "take": self._take, "קח": self._take, "get": self._take,
            "look": self._look, "הסתכל": self._look, "סרוק": self._look,
            "inv": self._inv, "תיק": self._inv, "ציוד": self._inv,
            "use": self._use, "השתמש": self._use,
            "help": self._help, "עזרה": self._help
        }

        if cmd in actions:
            actions[cmd](arg)
        else:
            # הפעלת AI מקומי
            response = self.ai_response(cmd_text)
            self.add_msg(response, "ai")
        
        return self.state

    # -- מימושים --
    def _help(self, arg):
        self.add_msg("פקודות: הסתכל, קח [חפץ], תיק, לך [כיוון], השתמש ב...", "info")

    def _look(self, arg):
        r = self.get_room_data()
        html = f"<div class='scan-line'></div>סריקת אזור: <b>{r['name']}</b><br>{r['desc']}"
        
        # תצוגת חפצים
        if r.get("items"):
            names = [GAME_DATA["items"][i]["name"] for i in r["items"]]
            html += f"<br><br><span style='color:#00ff9d'>⚠️ זוהו אובייקטים: {', '.join(names)}</span>"
            
        self.add_msg(html, "game")

    def _inv(self, arg):
        inv = self.state["inv"]
        if not inv: 
            self.add_msg("סטטוס ציוד: ריק", "info")
            return
        names = [GAME_DATA["items"][i]["name"] for i in inv]
        self.add_msg(f"ציוד טקטי: {', '.join(names)}", "info")

    def _go(self, direction):
        # תרגום כיוונים
        d_map = {"קדימה": "north", "אחורה": "south", "יציאה": "out", "החוצה": "out", 
                 "צפון": "north", "דרום": "south"}
        direction = d_map.get(direction, direction)
        
        r = self.get_room_data()
        
        # בדיקת נעילות (לדוגמה בתא ההתחלה)
        if self.state["loc"] == "cell" and direction == "out":
            if r["interactables"]["door"]["locked"]:
                self.add_msg("שגיאה: דלת נעולה. נדרש מפתח גישה.", "warning")
                return

        if direction in r.get("exits", {}):
            self.state["loc"] = r["exits"][direction]
            new_r = GAME_DATA["rooms"][self.state["loc"]]
            self.add_msg(f"מעבר ל{new_r['name']} בוצע.", "game")
            self._look(None)
        else:
            self.add_msg("נתיב חסום או לא קיים.", "warning")

    def _take(self, item_name):
        # מיפוי פשוט לעברית
        name_map = {"כף": "spoon", "אלה": "baton", "כרטיס": "key_card", "מפתח": "key_card"}
        target_id = name_map.get(item_name, item_name)
        
        r = self.get_room_data()
        if target_id in r.get("items", []):
            self.state["inv"].append(target_id)
            r["items"].remove(target_id)
            item_n = GAME_DATA["items"][target_id]["name"]
            self.add_msg(f"{item_n} נוסף למלאי.", "success")
        else:
            self.add_msg("פריט לא נמצא בסריקה.", "warning")

    def _use(self, arg):
        if "כרטיס" in arg or "מפתח" in arg:
            if "key_card" in self.state["inv"]:
                 if self.state["loc"] == "cell":
                     GAME_DATA["rooms"]["cell"]["interactables"]["door"]["locked"] = False
                     self.add_msg("גישה מאושרת. הדלת נפתחה.", "success")
                 else:
                     self.add_msg("אין כאן מערכת נעילה מתאימה.", "info")
            else:
                 self.add_msg("אין ברשותך כרטיס גישה.", "warning")
        else:
             self.add_msg("פקודה לא ישימה.", "info")


# --- 🌐 Routes ---

@app.route("/")
def index():
    if "uid" not in session: session["uid"] = str(uuid.uuid4())
    return render_template_string(HTML_INTERFACE)

@app.route("/api/command", methods=["POST"])
def handle_command():
    try:
        # 1. קבלת הפקודה
        data = request.get_json(silent=True) or {}
        user_cmd = data.get("command", "")
        
        # 2. טעינת מצב
        current_state = session.get("game_state", None)
        engine = GameEngine(current_state)
        
        # 3. עיבוד
        if user_cmd:
            engine.add_msg(user_cmd, "user")
            engine.process_command(user_cmd)
        
        # 4. שמירה
        session["game_state"] = engine.state
        
        # 5. מניעת קריסה בשליפת שם
        loc_id = engine.state["loc"]
        loc_name = GAME_DATA["rooms"].get(loc_id, {}).get("name", "Unknown Sector")
        
        return jsonify({
            "log": engine.state["log"],
            "loc_name": loc_name
        })

    except Exception as e:
        # מלכודת 500: אם יש קריסה, מחזירים הודעת מערכת יפה במקום שגיאת שרת
        return jsonify({
            "log": [{"text": "שגיאת מערכת קריטית. מנסה לשחזר יציבות...", "type": "warning"}],
            "loc_name": "System Failure"
        })

@app.route("/api/reset", methods=["POST"])
def reset_game():
    session.clear()
    return jsonify({"status": "ok"})


# --- 🎨 High-End Cyberpunk UI ---

HTML_INTERFACE = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
    <title>TERMINAL // PROT-06</title>
    <link href="https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Heebo:wght@400;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-dark: #050505;
            --panel-bg: #0a0a0c;
            --neon-blue: #00f3ff;
            --neon-pink: #bc13fe;
            --neon-green: #00ff9d;
            --text-main: #e0e0e0;
            --border: 1px solid rgba(0, 243, 255, 0.2);
        }

        body {
            background-color: var(--bg-dark);
            color: var(--text-main);
            font-family: 'Heebo', sans-serif;
            margin: 0;
            display: flex;
            justify-content: center;
            height: 100vh;
            overflow: hidden;
            background-image: linear-gradient(0deg, transparent 24%, rgba(0, 243, 255, .03) 25%, rgba(0, 243, 255, .03) 26%, transparent 27%, transparent 74%, rgba(0, 243, 255, .03) 75%, rgba(0, 243, 255, .03) 76%, transparent 77%, transparent), linear-gradient(90deg, transparent 24%, rgba(0, 243, 255, .03) 25%, rgba(0, 243, 255, .03) 26%, transparent 27%, transparent 74%, rgba(0, 243, 255, .03) 75%, rgba(0, 243, 255, .03) 76%, transparent 77%, transparent);
            background-size: 50px 50px;
        }

        /* Container Setup */
        .interface {
            display: flex;
            width: 100%;
            max-width: 1200px;
            height: 100vh;
        }

        /* Sidebar - Controls */
        .sidebar {
            width: 250px;
            background: var(--panel-bg);
            border-left: var(--border);
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 15px;
            box-shadow: -5px 0 20px rgba(0,0,0,0.5);
            z-index: 2;
        }
        
        .hud-header {
            font-family: 'Share Tech Mono', monospace;
            color: var(--neon-blue);
            font-size: 1.5rem;
            margin-bottom: 20px;
            text-align: center;
            text-shadow: 0 0 10px var(--neon-blue);
            letter-spacing: 2px;
            border-bottom: 1px solid #333;
            padding-bottom: 10px;
        }

        .cmd-btn {
            background: rgba(255,255,255,0.03);
            border: 1px solid #333;
            color: #888;
            padding: 12px;
            cursor: pointer;
            transition: 0.3s;
            text-align: right;
            border-radius: 4px;
            font-size: 0.9rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .cmd-btn:hover {
            border-color: var(--neon-blue);
            color: #fff;
            background: rgba(0, 243, 255, 0.1);
            transform: translateX(-5px);
        }

        /* Main Terminal Area */
        .terminal {
            flex-grow: 1;
            display: flex;
            flex-direction: column;
            padding: 20px;
            position: relative;
        }

        .location-bar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: var(--border);
            padding-bottom: 15px;
            margin-bottom: 15px;
            color: var(--neon-blue);
            font-family: 'Share Tech Mono', monospace;
        }

        .log-container {
            flex-grow: 1;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 10px;
            padding-right: 10px;
            font-size: 1.05rem;
        }

        /* Messages Styling */
        .msg {
            max-width: 80%;
            padding: 12px 16px;
            border-radius: 4px;
            line-height: 1.6;
            animation: fadeIn 0.3s ease;
            position: relative;
        }
        
        .msg.user {
            align-self: flex-start;
            background: rgba(0, 243, 255, 0.1);
            border-right: 2px solid var(--neon-blue);
            color: #fff;
        }
        
        .msg.game {
            align-self: flex-end;
            background: rgba(255, 255, 255, 0.05);
            border-left: 2px solid #555;
            color: #ccc;
        }
        
        .msg.ai {
            align-self: flex-end;
            border: 1px solid var(--neon-pink);
            background: rgba(188, 19, 254, 0.05);
            color: #e0d0ff;
            box-shadow: 0 0 10px rgba(188, 19, 254, 0.1);
        }
        
        .msg.success { border-left: 2px solid var(--neon-green); color: var(--neon-green); align-self: flex-end;}
        .msg.warning { border-left: 2px solid #ffcc00; color: #ffcc00; align-self: flex-end;}
        .msg.system { text-align: center; color: #555; align-self: center; font-size: 0.8rem; border: none; background: transparent;}

        /* Input Area */
        .input-deck {
            margin-top: 15px;
            display: flex;
            gap: 10px;
            border-top: var(--border);
            padding-top: 15px;
        }
        
        input[type="text"] {
            flex-grow: 1;
            background: rgba(0,0,0,0.3);
            border: 1px solid #333;
            color: #fff;
            padding: 15px;
            font-family: 'Heebo', sans-serif;
            font-size: 1rem;
            border-radius: 4px;
        }
        
        input:focus {
            outline: none;
            border-color: var(--neon-blue);
            box-shadow: 0 0 10px rgba(0, 243, 255, 0.1);
        }
        
        .send-btn {
            background: var(--neon-blue);
            color: #000;
            border: none;
            padding: 0 25px;
            font-weight: bold;
            cursor: pointer;
            border-radius: 4px;
            transition: 0.3s;
        }
        
        .send-btn:hover {
            background: #fff;
            box-shadow: 0 0 15px var(--neon-blue);
        }

        @keyframes fadeIn { from { opacity: 0; transform: translateY(5px); } to { opacity: 1; transform: translateY(0); } }

        /* Custom Scrollbar */
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: #000; }
        ::-webkit-scrollbar-thumb { background: #333; border-radius: 3px; }
        ::-webkit-scrollbar-thumb:hover { background: var(--neon-blue); }

        @media(max-width: 768px) {
            .sidebar { display: none; } /* מובייל נקי */
        }
    </style>
</head>
<body>
    <div class="interface">
        
        <div class="sidebar">
            <div class="hud-header">NET_LINK</div>
            <div class="cmd-btn" onclick="inject('סרוק אזור')"><span>👁️</span> סריקת שטח</div>
            <div class="cmd-btn" onclick="inject('סטטוס ציוד')"><span>🎒</span> בדיקת ציוד</div>
            <div class="cmd-btn" onclick="inject('קח כרטיס')"><span>💳</span> השג אישור</div>
            <div class="cmd-btn" onclick="inject('השתמש כרטיס')"><span>🔓</span> פתח גישה</div>
            <div class="cmd-btn" onclick="inject('נוע קדימה')"><span>⬆️</span> התקדם</div>
            <div style="flex-grow:1"></div>
            <div class="cmd-btn" onclick="hardReset()" style="border-color:#ff3333; color:#ff3333"><span>🛑</span> אתחול מערכת</div>
        </div>

        <div class="terminal">
            <div class="location-bar">
                <span id="loc-display">SECTOR: UNKNOWN</span>
                <span style="font-size:0.8rem; opacity:0.7">CONN: STABLE</span>
            </div>
            
            <div class="log-container" id="game-log">
                <!-- Log goes here -->
            </div>
            
            <div class="input-deck">
                <input type="text" id="cmd-input" placeholder="Enter Command..." autocomplete="off">
                <button class="send-btn" onclick="sendCmd()">EXE</button>
            </div>
        </div>

    </div>

    <script>
        // Init logic
        document.addEventListener('DOMContentLoaded', () => sendCmd(null));

        function inject(txt) {
            document.getElementById('cmd-input').value = txt;
            sendCmd();
        }

        async function sendCmd(txtOverride) {
            const inp = document.getElementById('cmd-input');
            const txt = txtOverride !== undefined ? txtOverride : inp.value;
            if (txtOverride !== null) inp.value = '';

            try {
                const res = await fetch('/api/command', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({command: txt})
                });
                
                if (res.status === 500) { throw new Error('Server Crash'); }
                
                const data = await res.json();
                renderLog(data.log);
                document.getElementById('loc-display').innerText = "SECTOR: " + data.loc_name.toUpperCase();

            } catch (e) {
                console.error("Link Failure", e);
                // נפילה שקטה - המשתמש לא רואה שגיאה מכוערת
            }
        }

        function renderLog(log) {
            const container = document.getElementById('game-log');
            container.innerHTML = '';
            
            log.forEach(item => {
                const div = document.createElement('div');
                div.className = `msg ${item.type}`;
                div.innerHTML = item.text;
                container.appendChild(div);
            });
            container.scrollTop = container.scrollHeight;
        }

        async function hardReset() {
            await fetch('/api/reset', {method:'POST'});
            location.reload();
        }

        // Enter key support
        document.getElementById('cmd-input').addEventListener("keyup", function(event) {
            if (event.key === "Enter") sendCmd();
        });

    </script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(port=5006, debug=False) 
    # debug=False כדי להסתיר שגיאות בטרמינל שנראות לא מקצועיות
