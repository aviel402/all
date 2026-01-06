from flask import Flask, render_template_string, request, jsonify, session, url_for
import json
import uuid
import random

app = Flask(__name__)
app.secret_key = 'infinity_engine_x1'

# ==========================================
# 🌌 מנוע הבריאה (The Creator Engine) 🌌
# ==========================================
# זהו "המוח" שיודע לחבר מילים כדי ליצור עולם הגיוני אך אינסופי
class WorldGenerator:
    def __init__(self):
        self.prefixes = ["אפל", "רטוב", "נטוש", "קפוא", "לוהט", "מתכתי", "מוזר", "שקט", "מהדהד"]
        self.types = ["מסדרון", "אולם", "חדר", "צינוק", "מעבר", "גשר", "פיר", "מעבדה"]
        self.decor = ["עם נורות מהבהבות", "מלא בקורי עכביש", "שריח של דם עומד באוויר", "עם שלוליות מים", "שהקירות שלו זזים"]
        self.items = ["סוללה", "כבל", "מברג", "מסכה", "מזרק", "תחבושת", "שבב"]
    
    def generate_room(self, coords):
        # יצירת שם החדר משילוב אקראי
        name = f"{random.choice(self.types)} {random.choice(self.prefixes)}"
        desc = f"זהו {name}. המקום נראה {random.choice(self.prefixes)} ו{random.choice(self.decor)}."
        
        # יצירת חפצים (סיכוי של 40% שיהיה חפץ)
        room_items = []
        if random.random() < 0.4:
            room_items.append(random.choice(self.items))

        # הגדרת יציאות פוטנציאליות (לוגיקת מפה)
        # שומרים רק את הנתונים, המנוע יחבר אותם כשהשחקן יזוז
        return {
            "name": name,
            "desc": desc,
            "items": room_items,
            "coords": coords,
            "exits": ["north", "south", "east", "west"] # פוטנציאלית הכל פתוח
        }

# ==========================================
# 🎮 ניהול מצב (State Management)
# ==========================================
class GameEngine:
    def __init__(self, state=None):
        if not state:
            # התחלה מאפס
            self.state = {
                "x": 0, "y": 0, # מיקום בקואורדינטות (כמו GPS)
                "inv": [],
                "generated_rooms": {}, # הזיכרון של המחשב על חדרים שכבר יצרנו
                "log": [{"text": "SYSTEM ONLINE. Generating world...", "type": "system"}],
            }
            # יצירת חדר ההתחלה ידנית
            self.create_room_at(0, 0, start=True)
        else:
            self.state = state
            
        self.generator = WorldGenerator()

    def get_coords_str(self, x, y):
        return f"{x},{y}"

    def create_room_at(self, x, y, start=False):
        key = self.get_coords_str(x, y)
        if start:
             room = {
                 "name": "נקודת ההנחתה",
                 "desc": "התרמיל שלך נחת כאן. מכאן יוצאים ללא נודע.",
                 "items": ["פנס"],
                 "exits": ["north", "south", "east", "west"]
             }
        else:
            room = self.generator.generate_room([x, y])
        
        self.state["generated_rooms"][key] = room
        return room

    def add_msg(self, text, type="game"):
        self.state["log"].append({"text": text, "type": type})

    def get_current_room(self):
        key = self.get_coords_str(self.state["x"], self.state["y"])
        return self.state["generated_rooms"][key]

    def process_command(self, cmd):
        parts = cmd.strip().lower().split()
        if not parts: return

        action = parts[0]
        # מילון תנועה חכם לקואורדינטות
        move_map = {
            "צפון": (0, 1), "north": (0, 1), "למעלה": (0, 1),
            "דרום": (0, -1), "south": (0, -1), "למטה": (0, -1),
            "מזרח": (1, 0), "east": (1, 0), "ימינה": (1, 0),
            "מערב": (-1, 0), "west": (-1, 0), "שמאלה": (-1, 0)
        }

        if action in ["לך", "go", "נוע", "זוז"]:
            direction = parts[1] if len(parts) > 1 else ""
            if direction in move_map:
                dx, dy = move_map[direction]
                new_x = self.state["x"] + dx
                new_y = self.state["y"] + dy
                target_key = self.get_coords_str(new_x, new_y)

                # --- רגע הבריאה ---
                # אם החדר לא קיים בזיכרון, הבינה יוצרת אותו עכשיו!
                if target_key not in self.state["generated_rooms"]:
                    self.create_room_at(new_x, new_y)
                    self.add_msg(f"🧬 סריקה גיאולוגית הושלמה. אזור חדש נוצר.", "system")

                # הזזה
                self.state["x"] = new_x
                self.state["y"] = new_y
                
                # הצגה
                new_room = self.state["generated_rooms"][target_key]
                self.add_msg(f"הגעת אל: <b>{new_room['name']}</b>", "game")
                self.add_msg(new_room["desc"], "game")
                if new_room["items"]:
                    self.add_msg(f"על הרצפה: {', '.join(new_room['items'])}", "success")

            else:
                self.add_msg("לאן ללכת? (נסה: צפון, דרום, מזרח, מערב)", "warning")

        elif action in ["קח", "take", "אסוף"]:
            item = parts[1] if len(parts) > 1 else ""
            room = self.get_current_room()
            if item in room["items"]:
                self.state["inv"].append(item)
                room["items"].remove(item)
                self.add_msg(f"אספת: {item}", "success")
            else:
                self.add_msg("אין פה חפץ כזה.", "warning")
        
        elif action in ["הסתכל", "look", "סרוק"]:
            room = self.get_current_room()
            self.add_msg(f"מקום: {room['name']}<br>{room['desc']}", "game")
            if room["items"]: self.add_msg(f"חפצים: {room['items']}", "success")
            
        elif action in ["תיק", "inv"]:
            self.add_msg(f"ציוד: {self.state['inv']}", "info")
            
        else:
            self.add_msg("פקודה לא מוכרת. נסה לנוע (צפון/דרום...) או לאסוף.", "warning")


# --- WEB SERVER ---

@app.route("/")
def index():
    if "uid" not in session: session["uid"] = str(uuid.uuid4())
    api_url = url_for('cmd')
    return render_template_string(HTML, api_url=api_url)

@app.route("/api/cmd", methods=["POST"])
def cmd():
    data = request.json or {}
    txt = data.get("cmd", "")
    state = session.get("game", None)
    
    engine = GameEngine(state)
    if txt:
        engine.add_msg(txt, "user")
        engine.process_command(txt)
        
    session["game"] = engine.state
    
    curr = engine.get_current_room()
    coords = f"POS: {engine.state['x']}, {engine.state['y']}"
    
    return jsonify({"log": engine.state["log"], "loc_name": f"{curr['name']} ({coords})"})

# --- Cyber Interface ---
HTML = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>GENESIS ENGINE</title>
<style>
    body { background: #000; color: #0f0; font-family: monospace; display:flex; flex-direction:column; height:100vh; margin:0; padding:10px; box-sizing:border-box;}
    #screen { flex-grow:1; border: 1px solid #333; padding:10px; overflow-y:auto; margin-bottom:10px; box-shadow: 0 0 20px rgba(0,255,0,0.1); }
    .msg { margin-bottom:8px; line-height:1.4;}
    .user { color: #fff; background: #222; padding:2px; display:inline-block;}
    .system { color: #555; text-align:center; margin:15px 0; font-size:0.8rem;}
    .success { color: #0ff; }
    .warning { color: orange; }
    
    #controls { display:flex; gap:10px;}
    input { background: #111; border:1px solid #0f0; color:#0f0; padding:15px; flex-grow:1; font-size:1.1rem;}
    button { background: #0f0; color: black; border:none; padding:0 25px; font-weight:bold; cursor:pointer;}
</style>
</head>
<body>
    <div style="border-bottom:1px solid #333; margin-bottom:10px; display:flex; justify-content:space-between">
        <span id="loc">INIT...</span>
        <span>PROCEDURAL GENERATION: ON</span>
    </div>
    
    <div id="screen"></div>
    
    <div id="controls">
        <input type="text" id="inp" placeholder="נוע לכיוון כלשהו כדי ליצור את העולם..." autofocus>
        <button onclick="send()">שלח</button>
    </div>

<script>
const API="{{ api_url }}";

document.addEventListener("DOMContentLoaded", ()=> send("הסתכל"));

document.getElementById("inp").addEventListener("keypress", (e)=>{
    if(e.key==="Enter") send();
});

async function send(txtOverride){
    let inp = document.getElementById("inp");
    let val = txtOverride || inp.value;
    if(!txtOverride) inp.value="";
    
    if(!val) return;
    
    let res = await fetch(API, {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify({cmd: val})
    });
    let d = await res.json();
    
    let scr = document.getElementById("screen");
    scr.innerHTML="";
    d.log.forEach(l => {
        let div = document.createElement("div");
        div.className = "msg "+l.type;
        div.innerHTML = l.text;
        scr.appendChild(div);
    });
    scr.scrollTop = scr.scrollHeight;
    
    document.getElementById("loc").innerText = d.loc_name;
}
</script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(port=5006, debug=True)
