from flask import Flask, render_template_string, request, jsonify, session
import json
import uuid

app = Flask(__name__)
app.secret_key = 'ultra_secret_pro_key'

# ==========================================
# 1. דאטה: העולם, החפצים והחוקים (Data Layer)
# ==========================================
GAME_DATA = {
    "start_room": "cell",
    "rooms": {
        "cell": {
            "name": "תא כלא מעופש",
            "desc": "קירות האבן סוגרים עליך. יש דלת ברזל נעולה מדרום. על הרצפה יש קש.",
            "exits": {"south": "corridor"},
            "items": ["rusted_spoon"],
            "interactables": {
                "door": {"desc": "דלת ברזל כבדה. היא נעולה.", "locked": True, "key": "guard_key"}
            }
        },
        "corridor": {
            "name": "מסדרון האבן",
            "desc": "מסדרון ארוך וחשוך. אתה רואה לפיד כבוי על הקיר.",
            "exits": {"north": "cell", "east": "armory"},
            "items": ["torch"],
            "enemies": ["guard"]
        },
        "armory": {
            "name": "נשקייה",
            "desc": "חדר מלא בנשקים ישנים. רובם שבורים, אך אחד נראה שמיש.",
            "exits": {"west": "corridor"},
            "items": ["sword", "shield"]
        }
    },
    "items": {
        "rusted_spoon": {"name": "כף חלודה", "desc": "לא יעיל כנשק, אבל אולי אפשר לחפור איתו?"},
        "guard_key": {"name": "מפתח השומר", "desc": "מפתח כבד מברזל."},
        "sword": {"name": "חרב קצרה", "desc": "חדה מספיק כדי לחתוך.", "damage": 10},
        "torch": {"name": "לפיד", "desc": "עשוי להאיר מקומות חשוכים."},
        "shield": {"name": "מגן עץ", "desc": "טוב להגנה בסיסית."}
    },
    "enemies": {
        "guard": {
            "name": "שומר רדום",
            "desc": "הוא יושב על שרפרף, מנמנם. חגורה עם מפתח תלויה עליו.",
            "hp": 20,
            "damage": 5,
            "loot": "guard_key",
            "status": "alive"
        }
    }
}

# ==========================================
# 2. מנוע המשחק (Logic Engine)
# ==========================================

class GameEngine:
    def __init__(self, state=None):
        if state:
            self.state = state
        else:
            self.state = {
                "loc": GAME_DATA["start_room"],
                "inv": [],
                "hp": 30,
                "flags": {}, # לשמירת דברים כמו "דלת נפתחה"
                "log": []
            }

    def get_room(self):
        return GAME_DATA["rooms"][self.state["loc"]]

    def add_log(self, text, type="neutral"):
        self.state["log"].append({"text": text, "type": type})

    def process(self, raw_input):
        parts = raw_input.strip().lower().split()
        if not parts: return self.state

        cmd = parts[0]
        arg = parts[1] if len(parts) > 1 else None

        # מילון פקודות לשיפור קריאות הקוד
        commands = {
            "go": self._cmd_move, "walk": self._cmd_move, "לך": self._cmd_move,
            "take": self._cmd_take, "get": self._cmd_take, "קח": self._cmd_take,
            "look": self._cmd_look, "examine": self._cmd_look, "הסתכל": self._cmd_look,
            "inv": self._cmd_inv, "i": self._cmd_inv, "תיק": self._cmd_inv,
            "use": self._cmd_use, "attack": self._cmd_attack, "השתמש": self._cmd_use, "תקוף": self._cmd_attack
        }

        if cmd in commands:
            commands[cmd](arg)
        else:
            self.add_log("פקודה לא מזוהה.", "error")
        
        return self.state

    # --- פונקציות עזר לפקודות ---

    def _cmd_move(self, direction):
        room = self.get_room()
        
        # תרגום כיוונים
        trans = {"north": "north", "צפון": "north", "south": "south", "דרום": "south", 
                 "east": "east", "מזרח": "east", "west": "west", "מערב": "west"}
        direction = trans.get(direction, direction)

        if direction in room["exits"]:
            target_id = room["exits"][direction]
            target_room = GAME_DATA["rooms"][target_id]
            
            # בדיקה האם יש נעילה (לוגיקה של דלתות)
            origin_interactables = room.get("interactables", {})
            # אם מנסים ללכת דרומה והדלת בדרום נעולה (לצורך הפשטות נניח שהדלת הראשית היא החסם)
            # לוגיקה חכמה תהיה לבדוק איזה Link חסום, כאן נבדוק אם יש דלת בחדר שהיא locked
            door = origin_interactables.get("door") 
            if door and door.get("locked") and direction == "south": # הארדקוד להדגמה
                 self.add_log("הדרך חסומה. הדלת נעולה.", "warning")
                 return

            # בדיקה אם יש אויב חי בחדר שחוסם מעבר
            if "enemies" in room:
                for enemy_id in room["enemies"]:
                    enemy = GAME_DATA["enemies"][enemy_id]
                    # בודקים במצב הגלובלי אם האויב מת
                    enemy_dead = self.state["flags"].get(f"{enemy_id}_dead", False)
                    if not enemy_dead:
                         self.add_log(f"ה{enemy['name']} חוסם את דרכך!", "danger")
                         return

            self.state["loc"] = target_id
            self.add_log(f"הלכת ל{target_room['name']}.", "success")
            self._cmd_look(None)
        else:
            self.add_log("אי אפשר ללכת לשם.", "warning")

    def _cmd_take(self, item_name):
        room = self.get_room()
        
        # תרגום חופשי
        translation = {"spoon": "rusted_spoon", "כף": "rusted_spoon", "key": "guard_key", "מפתח": "guard_key", 
                       "sword": "sword", "חרב": "sword", "shield": "shield", "מגן": "shield"}
        item_id = translation.get(item_name, item_name)

        if item_id in room.get("items", []):
            self.state["inv"].append(item_id)
            room["items"].remove(item_id) # זה מסיר רק בזיכרון של הבקשה הזו - צריך טיפול במערכת Persistent אמיתית
            # *הערה*: בקוד מלא, צריך לשמור את השינויים בעולם ב-state.flags או state.world_changes
            self.state["flags"][f"took_{item_id}_{self.state['loc']}"] = True # סימון שנלקח
            
            item_data = GAME_DATA["items"][item_id]
            self.add_log(f"לקחת: {item_data['name']}.", "success")
        else:
            self.add_log("אין כאן את זה.", "warning")

    def _cmd_look(self, target):
        room = self.get_room()
        
        if not target:
            # תיאור חדר כללי
            self.add_log(f"--- {room['name']} ---", "info")
            self.add_log(room["desc"])
            
            # הצגת חפצים שלא נלקחו (נבדוק גם ב-flags אם לקחנו כבר)
            items_here = [item for item in room.get("items", []) if not self.state["flags"].get(f"took_{item}_{self.state['loc']}")]
            if items_here:
                names = [GAME_DATA["items"][i]["name"] for i in items_here]
                self.add_log(f"חפצים: {', '.join(names)}", "highlight")

            # הצגת אויבים
            if "enemies" in room:
                for en_id in room["enemies"]:
                    if not self.state["flags"].get(f"{en_id}_dead"):
                        en = GAME_DATA["enemies"][en_id]
                        self.add_log(f"אויב: {en['name']} ({en['desc']})", "danger")
            
            # יציאות
            self.add_log(f"יציאות: {', '.join(room['exits'].keys())}")
        
        else:
            # כאן תוסיף בדיקת חפצים ספציפית
            self.add_log(f"אתה מסתכל על {target} אבל לא רואה משהו מיוחד.")

    def _cmd_inv(self, arg):
        if not self.state["inv"]:
            self.add_log("התיק שלך ריק.")
            return
        
        item_names = [GAME_DATA["items"][i]["name"] for i in self.state["inv"]]
        self.add_log(f"מלאי: {', '.join(item_names)}", "highlight")

    def _cmd_use(self, arg):
        # טיפול מורכב ב"Use key" וכדומה
        room = self.get_room()
        
        # לוגיקה לפתיחת דלתות
        if arg in ["key", "מפתח"] and "guard_key" in self.state["inv"]:
            if "door" in room.get("interactables", {}) and room["interactables"]["door"]["locked"]:
                room["interactables"]["door"]["locked"] = False
                self.add_log("הכנסת את המפתח... קליק! הדלת נפתחה.", "success")
                self.state["flags"]["door_unlocked"] = True
            else:
                self.add_log("אין כאן דלת נעולה שאפשר לפתוח.")
        else:
            self.add_log(f"אי אפשר להשתמש בזה כאן.")

    def _cmd_attack(self, target):
        room = self.get_room()
        # מציאת אויב בחדר
        target_enemy_id = None
        if "enemies" in room:
            # לקיחת האויב הראשון לצורך הדגמה
             target_enemy_id = room["enemies"][0]

        if target_enemy_id:
            enemy = GAME_DATA["enemies"][target_enemy_id]
            if self.state["flags"].get(f"{target_enemy_id}_dead"):
                self.add_log("הוא כבר מת.")
                return

            player_dmg = 2
            if "sword" in self.state["inv"]: player_dmg = 10
            elif "spoon" in self.state["inv"]: player_dmg = 3

            # הורדת חיים לאויב (דורש ניהול State לאויבים, נעשה הדמיה)
            current_hp = enemy["hp"] - self.state["flags"].get(f"{target_enemy_id}_dmg", 0)
            current_hp -= player_dmg
            self.state["flags"][f"{target_enemy_id}_dmg"] = self.state["flags"].get(f"{target_enemy_id}_dmg", 0) + player_dmg

            self.add_log(f"תקפת את {enemy['name']} וגרמת {player_dmg} נזק!", "success")

            if current_hp <= 0:
                self.state["flags"][f"{target_enemy_id}_dead"] = True
                self.add_log(f"ניצחת! {enemy['name']} נפל ארצה. נפל ממנו: {GAME_DATA['items'][enemy['loot']]['name']}", "success")
                room["items"].append(enemy['loot']) # הפלה לרצפה
            else:
                # האויב תוקף חזרה
                self.state["hp"] -= enemy["damage"]
                self.add_log(f"{enemy['name']} תוקף אותך! נפגעת ב-{enemy['damage']}. חיים: {self.state['hp']}", "danger")
        else:
            self.add_log("אין את מי לתקוף כאן.")


# ==========================================
# 3. ממשק משתמש ושרת (Frontend & Routes)
# ==========================================

@app.route("/")
def index():
    if "uid" not in session:
        session["uid"] = str(uuid.uuid4())
    return render_template_string(HTML_TEMPLATE)

@app.route("/api/command", methods=["POST"])
def api_command():
    # 1. מנסים לקבל נתונים בזהירות
    data = request.get_json(silent=True)
    if not data:
        data = {}
        
    cmd = data.get("command")
    
    # שליפת המצב מהסשן
    state = session.get("game_state", None)
    
    # 2. אתחול מנוע
    try:
        engine = GameEngine(state)
    except Exception as e:
        # אם יש שגיאה ביצירת המנוע, מתחילים חדש
        print(f"Error loading state: {e}")
        engine = GameEngine(None)
    
    # 3. ביצוע פקודה
    if not state and not cmd:
        # פעם ראשונה שפותחים את הדף
        engine._cmd_look(None)
    elif cmd:
        engine.process(cmd)
    
    # שמירת מצב ועדכון לקוח
    session["game_state"] = engine.state
    
    # 4. לוודא שלא חסר שום שדה בתשובה
    loc_name = "לא ידוע"
    if engine.state["loc"] in GAME_DATA["rooms"]:
        loc_name = GAME_DATA["rooms"][engine.state["loc"]]["name"]

    return jsonify({
        "log": engine.state["log"][-10:], # שולח 10 שורות אחרונות
        "full_log": engine.state["log"],
        "hp": engine.state.get("hp", 0),
        "loc_name": loc_name
    })
@app.route("/api/reset", methods=["POST"])
def api_reset():
    session.clear()
    return jsonify({"status": "ok"})

# ממשק ה-Web המעוצב (CSS+JS)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>מבוך הצללים</title>
    <style>
        :root {
            --bg-color: #0d1117;
            --text-color: #c9d1d9;
            --highlight: #58a6ff;
            --danger: #f85149;
            --success: #3fb950;
            --input-bg: #161b22;
        }
        body {
            background-color: var(--bg-color);
            color: var(--text-color);
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            display: flex;
            justify-content: center;
            height: 100vh;
            overflow: hidden;
        }
        .container {
            width: 100%;
            max-width: 900px;
            display: flex;
            flex-direction: column;
            padding: 20px;
            box-sizing: border-box;
        }
        header {
            border-bottom: 1px solid #30363d;
            padding-bottom: 10px;
            margin-bottom: 10px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        h1 { margin: 0; font-size: 1.5rem; color: var(--highlight); }
        .stats { font-size: 0.9rem; }
        
        #game-log {
            flex-grow: 1;
            overflow-y: auto;
            background: #111;
            padding: 15px;
            border-radius: 8px;
            border: 1px solid #30363d;
            font-family: 'Consolas', monospace;
            line-height: 1.6;
        }
        
        .entry { margin-bottom: 10px; animation: fadeIn 0.3s ease; }
        .entry.error { color: #8b949e; }
        .entry.danger { color: var(--danger); font-weight: bold; }
        .entry.success { color: var(--success); }
        .entry.highlight { color: #e3b341; }
        .entry.info { color: #58a6ff; font-weight: bold; margin-top: 15px; border-top: 1px solid #333; padding-top:10px;}

        #input-area {
            margin-top: 15px;
            display: flex;
            gap: 10px;
        }
        input {
            flex-grow: 1;
            background: var(--input-bg);
            border: 1px solid #30363d;
            color: white;
            padding: 15px;
            border-radius: 5px;
            font-size: 1.1rem;
            outline: none;
        }
        input:focus { border-color: var(--highlight); }
        button {
            padding: 0 25px;
            background: #238636;
            color: white;
            border: none;
            border-radius: 5px;
            font-weight: bold;
            cursor: pointer;
            transition: 0.2s;
        }
        button:hover { background: #2ea043; }
        
        /* גלילה מותאמת */
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-thumb { background: #30363d; border-radius: 4px; }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(5px); }
            to { opacity: 1; transform: translateY(0); }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>מבוך הצללים</h1>
            <div class="stats">
                <span id="loc-display">מיקום: טוען...</span> | 
                <span id="hp-display" style="color:var(--danger)">HP: --</span>
                <button onclick="resetGame()" style="background:#da3633; padding:5px 10px; margin-right:10px; font-size:0.8rem">איפוס</button>
            </div>
        </header>

        <div id="game-log">
            <!-- לוג המשחק ייכנס לפה -->
        </div>

        <form id="input-area" onsubmit="sendCommand(event)">
            <input type="text" id="cmd-input" placeholder="מה תרצה לעשות? (לדוגמה: לך מזרח, קח חרב, תקוף...)" autofocus autocomplete="off">
            <button type="submit">שלח</button>
        </form>
    </div>

    <script>
        const logContainer = document.getElementById('game-log');
        const inputField = document.getElementById('cmd-input');
        
        // טעינה ראשונית
        document.addEventListener("DOMContentLoaded", () => sendCommand(null, ''));

        async function sendCommand(event, manualCmd = null) {
            if(event) event.preventDefault();
            
            const cmd = manualCmd !== null ? manualCmd : inputField.value;
            if(!cmd && manualCmd === null) return;

            // ניקוי שדה
            inputField.value = '';

            // הצגה מקומית של פקודת המשתמש
            if (cmd) {
                appendLog({text: "> " + cmd}, 'neutral');
            }

            try {
                const response = await fetch('/api/command', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ command: cmd })
                });
                
                const data = await response.json();
                
                // עדכון לוג מלא או תוספות
                // אנחנו נציג את הבלוק האחרון של הלוגים
                data.log.forEach(entry => appendLog(entry));

                // עדכון סטטיסטיקות UI
                document.getElementById('hp-display').innerText = "HP: " + data.hp;
                document.getElementById('loc-display').innerText = "מיקום: " + data.loc_name;

            } catch (err) {
                console.error(err);
                appendLog({text: "שגיאת תקשורת עם השרת."}, 'error');
            }
        }

        function appendLog(entry, typeOverride=null) {
            const div = document.createElement('div');
            div.className = 'entry ' + (typeOverride || entry.type || '');
            div.innerText = entry.text;
            logContainer.appendChild(div);
            logContainer.scrollTop = logContainer.scrollHeight;
        }

        async function resetGame() {
            await fetch('/api/reset', { method: 'POST' });
            location.reload();
        }
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(debug=True, port=5000)
