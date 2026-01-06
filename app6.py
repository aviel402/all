from flask import Flask, render_template_string, request, jsonify, session, url_for
import json
import uuid
import random

app = Flask(__name__)
app.secret_key = 'map_hud_pro_v2'

# --- 🌍 נתונים ---
# אייקונים למפה
BIOME_ICONS = {
    "רפואי": "🏥", 
    "נשקייה": "🔫", 
    "מגורים": "🛌", 
    "טכני": "🔧", 
    "סתמי": "🔲",
    "התחלה": "🏠",
    "מסדרון": "⬛"
}

class WorldGenerator:
    def generate(self, x, y):
        # יצירת סוג חדר אקראי
        b_type = random.choice(["רפואי", "נשקייה", "מגורים", "טכני", "סתמי", "מסדרון", "מסדרון"])
        
        name = f"אזור {b_type}"
        desc_list = [
            "הקירות רועדים קלות.", "ריח של חשמל שרוף באוויר.", 
            "טיפות מים נופלות מהתקרה.", "הכל שקט. שקט מדי.",
            "אורות אדומים מהבהבים כאן."
        ]
        
        # חפצים אקראיים
        items = []
        if random.random() > 0.6:
            items.append(random.choice(["תחבושת", "סוללה", "מברג", "פנס", "מטבע"]))

        return {
            "name": name,
            "desc": random.choice(desc_list),
            "type": b_type,
            "items": items
        }

class GameEngine:
    def __init__(self, state=None):
        if not state:
            self.state = {
                "x": 0, "y": 0,
                "inv": [],
                "map": {}, 
                "log": [{"text": "המערכת אותחלה. נוע במרחב כדי למפות אותו.", "type": "system"}],
                "visited": ["0,0"]
            }
            # נקודת התחלה
            self.state["map"]["0,0"] = {"name":"בסיס", "desc":"היציאה לעולם.", "type":"התחלה", "items":[]}
        else:
            self.state = state
        self.gen = WorldGenerator()

    def get_key(self, x, y): return f"{x},{y}"

    def move(self, dx, dy):
        self.state["x"] += dx
        self.state["y"] += dy
        k = self.get_key(self.state["x"], self.state["y"])
        
        # יצירת חדר אם לא קיים
        is_new = False
        if k not in self.state["map"]:
            self.state["map"][k] = self.gen.generate(self.state["x"], self.state["y"])
            is_new = True
            
        if k not in self.state["visited"]:
            self.state["visited"].append(k)

        room = self.state["map"][k]
        msg = f"הגעת ל: {room['name']}"
        if is_new: msg += " (גילוי חדש!)"
        
        self.log(msg, "success" if is_new else "game")
        if room["items"]:
            self.log(f"מצאת: {', '.join(room['items'])}", "info")

    def take_item(self):
        k = self.get_key(self.state["x"], self.state["y"])
        room = self.state["map"][k]
        if room["items"]:
            item = room["items"].pop(0)
            self.state["inv"].append(item)
            self.log(f"לקחת את ה{item}.", "success")
        else:
            self.log("אין כאן כלום לקחת.", "warning")

    def log(self, txt, t):
        self.state["log"].append({"text": txt, "type": t})

    # --- רנדור המפה לתוך ה-HTML (רדיוס של 5 משבצות) ---
    def render_hud_map(self):
        cx, cy = self.state["x"], self.state["y"]
        r = 2
        html = "<div class='map-grid'>"
        
        for dy in range(r, -r - 1, -1):
            html += "<div class='map-row'>"
            for dx in range(-r, r + 1):
                tx, ty = cx + dx, cy + dy
                k = self.get_key(tx, ty)
                
                cell_content = "❓" # לא ידוע
                cell_class = "fog"
                
                if dx == 0 and dy == 0:
                    cell_content = "😎" # שחקן
                    cell_class = "player"
                elif k in self.state["visited"]:
                    # חדר מוכר
                    room = self.state["map"][k]
                    cell_content = BIOME_ICONS.get(room["type"], "⬜")
                    cell_class = "known"
                
                html += f"<span class='cell {cell_class}'>{cell_content}</span>"
            html += "</div>"
        html += "</div>"
        return html

# --- Routes ---
@app.route("/")
def index():
    if "uid" not in session: session["uid"] = str(uuid.uuid4())
    api_url = url_for('cmd')
    reset_url = url_for('reset')
    return render_template_string(HTML, api_url=api_url, reset_url=reset_url)

@app.route("/api/cmd", methods=["POST"])
def cmd():
    data = request.json or {}
    txt = data.get("cmd", "").strip().lower()
    
    eng = GameEngine(session.get("game"))
    
    if txt:
        eng.log(f"> {txt}", "user")
        
        # זיהוי פקודות (כולל קיצורי עברית)
        if txt in ["צפון", "צ", "קדימה", "n", "up"]: eng.move(0, 1)
        elif txt in ["דרום", "ד", "אחורה", "s", "down"]: eng.move(0, -1)
        elif txt in ["מזרח", "מז", "ימינה", "e", "right"]: eng.move(1, 0)
        elif txt in ["מערב", "מע", "שמאלה", "w", "left"]: eng.move(-1, 0)
        elif "קח" in txt or "take" in txt: eng.take_item()
        elif "תיק" in txt or "inv" in txt: eng.log(str(eng.state["inv"]), "info")
        elif "ז" in txt: eng.log("לאן לזוז? (צ, ד, מז, מע)", "warning")
        else: eng.log("נסה: צ (צפון), ד (דרום), מז, מע או 'קח'.", "warning")

    session["game"] = eng.state
    
    k = eng.get_key(eng.state["x"], eng.state["y"])
    curr = eng.state["map"][k]
    
    return jsonify({
        "log": eng.state["log"],
        "hud": eng.render_hud_map(),
        "loc_text": f"{curr['name']} ({eng.state['x']}, {eng.state['y']})"
    })

@app.route("/api/reset", methods=["POST"])
def reset():
    session.clear()
    return jsonify({"ok": True})

# --- CLIENT HTML ---
HTML = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>EXPLORER HUD</title>
    <style>
        body { background-color: #050505; color: #0f0; font-family: 'Segoe UI', sans-serif; margin: 0; display: flex; flex-direction: column; height: 100vh; overflow: hidden;}
        
        /* אזור עליון - המפה */
        .hud-area {
            background: #111; 
            border-bottom: 2px solid #005500;
            padding: 10px;
            text-align: center;
            height: 180px; /* מקום למפה */
            display: flex; flex-direction: column; align-items: center; justify-content: center;
        }
        
        .map-grid { display: flex; flex-direction: column; align-items: center; gap: 2px; }
        .map-row { display: flex; gap: 2px; }
        .cell { 
            width: 30px; height: 30px; 
            display: flex; align-items: center; justify-content: center;
            font-size: 18px; border-radius: 4px;
        }
        .fog { background: #222; opacity: 0.2; }
        .known { background: #222; border: 1px solid #444; }
        .player { background: #004400; border: 1px solid #0f0; box-shadow: 0 0 10px #0f0;}
        
        /* אזור אמצעי - הלוג */
        .chat-area { 
            flex-grow: 1; 
            overflow-y: auto; 
            padding: 20px; 
            background: linear-gradient(#050505, #0a0a0a);
        }
        .msg { margin-bottom: 8px; line-height: 1.4; padding: 5px;}
        .msg.user { color: #888; border-right: 2px solid #888; font-size: 0.9em; }
        .msg.system { color: #00cec9; text-align: center; font-size: 0.8em; margin: 10px 0; border-top: 1px dashed #333;}
        .msg.success { color: #0f0; }
        .msg.game { color: #ddd; }
        .msg.warning { color: orange; }

        /* אזור תחתון - קלט */
        .input-area { 
            padding: 15px; 
            background: #111; border-top: 1px solid #333; 
            display: flex; gap: 10px;
        }
        input { 
            flex-grow: 1; padding: 15px; 
            background: #000; color: #0f0; border: 1px solid #0f0; 
            font-family: inherit; font-size: 1.1em;
        }
        button { background: #005500; color: #fff; border: none; padding: 0 20px; font-weight: bold; cursor: pointer;}

        .btn-reset { position: absolute; top: 10px; right: 10px; background: #500; color: white; padding: 5px; font-size: 10px; cursor: pointer; border: none;}
    </style>
</head>
<body>

    <button class="btn-reset" onclick="hardReset()">🔄 איפוס משחק</button>

    <div class="hud-area">
        <div id="loc-name" style="margin-bottom: 5px; font-weight: bold; color: white;">טוען לווין...</div>
        <div id="map-target"></div>
    </div>

    <div class="chat-area" id="log-target"></div>

    <div class="input-area">
        <input type="text" id="inp" placeholder="הקלד: צ, ד, מז, מע..." autofocus>
        <button onclick="send()">שלח</button>
    </div>

<script>
    const API = "{{ api_url }}";
    const RES = "{{ reset_url }}";
    
    // שליחה ראשונית לרינדור
    document.addEventListener("DOMContentLoaded", () => send(""));

    async function send(txtOverride) {
        let inp = document.getElementById("inp");
        let val = (txtOverride !== undefined) ? txtOverride : inp.value;
        if(val !== "") inp.value = "";
        
        let res = await fetch(API, {
            method:'POST',
            headers:{'Content-Type':'application/json'},
            body: JSON.stringify({cmd: val})
        });
        let d = await res.json();
        
        // Render HUD
        document.getElementById("loc-name").innerText = d.loc_text;
        document.getElementById("map-target").innerHTML = d.hud;
        
        // Render LOG
        let logDiv = document.getElementById("log-target");
        logDiv.innerHTML = "";
        d.log.forEach(l => {
            let div = document.createElement("div");
            div.className = "msg " + l.type;
            div.innerText = l.text;
            logDiv.appendChild(div);
        });
        logDiv.scrollTop = logDiv.scrollHeight;
    }

    async function hardReset(){
        await fetch(RES, {method:'POST'});
        location.reload();
    }

    document.getElementById("inp").addEventListener("keypress", (e) => {
        if(e.key === "Enter") send();
    });
</script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(port=5006, debug=True)
