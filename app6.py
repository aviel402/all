from flask import Flask, render_template_string, request, jsonify, session, url_for
import json
import uuid
import random

app = Flask(__name__)
app.secret_key = 'map_explorer_ultra_v1'

# ==========================================
# 🌌 בורא העולמות (Expanded World Generator)
# ==========================================
class WorldGenerator:
    def __init__(self):
        # הרחבה ענקית לאפשרויות החדרים
        self.biomes = [
            {"type": "רפואי", "names": ["מרפאה", "חדר ניתוח", "מעבדה ביולוגית", "חדר הקפאה", "מחסן תרופות"], "items": ["מזרק אדרנלין", "תחבושת", "סכין מנתחים"]},
            {"type": "תעשייתי", "names": ["כור גרעיני", "חדר טורבינות", "צינור שירות", "מפעל ייצור", "מסדרון תחזוקה"], "items": ["מברג", "מפתח שוודי", "פיוז שרוף"]},
            {"type": "מגורים", "names": ["חדר שינה נטוש", "מטבחון", "חדר שירותים", "אולם כינוס", "חדר מעצר"], "items": ["כף", "מזרן קרוע", "תמונה ישנה"]},
            {"type": "טכנולוגי", "names": ["חדר שרתים", "מרכז בקרה", "חדר תקשורת", "עמדת טעינה"], "items": ["שבב זיכרון", "טאבלט שבור", "כבל נתונים"]}
        ]
        
        self.adjectives = ["מוצף במים שחורים", "מלא בעשן סמיך", "שקט בצורה מחרידה", "קפוא לחלוטין", "עם אורות מהבהבים", "שרוף ומפוייח", "מלא בצמחייה מוזרה"]
        self.loot_common = ["מטבע עתיק", "בטריה", "בורג", "שאריות מזון"]

    def generate_room(self, x, y):
        # בחירה אקראית של סוג אזור (Biome)
        biome = random.choice(self.biomes)
        base_name = random.choice(biome["names"])
        adj = random.choice(self.adjectives)
        
        name = f"{base_name}"
        desc = f"אתה נמצא ב{base_name}. המקום {adj}. הריח כאן מזכיר {biome['type']} ישן."
        
        # יצירת חפצים (סיכוי למשהו ספציפי לאזור, או זבל כללי)
        items = []
        if random.random() < 0.6:
            loot_source = biome["items"] if random.random() > 0.3 else self.loot_common
            items.append(random.choice(loot_source))

        return {
            "name": name,
            "desc": desc,
            "items": items,
            "coords": [x, y],
            "type": biome["type"]
        }

# ==========================================
# 🗺️ מנוע מפה ולוגיקה
# ==========================================
class GameEngine:
    def __init__(self, state=None):
        if not state:
            self.state = {
                "x": 0, "y": 0,
                "inv": [],
                "generated_rooms": {}, # זיכרון המפה: "0,0": {...}
                "visited": ["0,0"], # רשימה פשוטה למפה הויזואלית
                "log": [{"text": "מערכת מיפוי הופעלה. המפה בצד מתעדכנת...", "type": "system"}],
            }
            # חדר ראשון
            self.create_room_at(0, 0, start=True)
        else:
            self.state = state
            
        self.generator = WorldGenerator()

    def get_key(self, x, y): return f"{x},{y}"

    def create_room_at(self, x, y, start=False):
        key = self.get_key(x, y)
        if start:
            room = {"name": "נקודת התחלה", "desc": "פתח המנהרה. מכאן אפשר לצאת לכל כיוון.", "items": ["פנס כיס"], "type": "start"}
        else:
            room = self.generator.generate_room(x, y)
        
        self.state["generated_rooms"][key] = room
        if key not in self.state["visited"]:
            self.state["visited"].append(key)
        return room

    def get_current_room(self):
        return self.state["generated_rooms"][self.get_key(self.state["x"], self.state["y"])]

    # --- יצירת מפה ויזואלית (ASCII ART HTML) ---
    def render_map(self):
        # מציג רדיוס של 3x3 מסביב לשחקן
        radius = 3
        cx, cy = self.state["x"], self.state["y"]
        html_map = ""
        
        # סריקה מלמעלה למטה (Y יורד)
        for dy in range(radius, -radius -1, -1):
            row_html = "<div class='map-row'>"
            for dx in range(-radius, radius + 1):
                tx, ty = cx + dx, cy + dy
                t_key = self.get_key(tx, ty)
                
                # תאים במפה
                cell_class = "map-cell empty"
                content = "·" # אזור לא ידוע
                
                if tx == cx and ty == cy:
                    content = "@" # השחקן
                    cell_class = "map-cell player"
                elif t_key in self.state["generated_rooms"]:
                    content = "■" # חדר ידוע
                    # צביעה לפי סוג ביום
                    rtype = self.state["generated_rooms"][t_key].get("type", "std")
                    cell_class = f"map-cell room-{rtype}"
                
                row_html += f"<span class='{cell_class}'>{content}</span>"
            row_html += "</div>"
        
        return html_map

    def process_command(self, cmd):
        if not cmd: return
        parts = cmd.strip().lower().split()
        action = parts[0]
        
        # --- תנועה משודרגת ---
        dirs = {
            "צפון": (0, 1), "קדימה": (0, 1), "n": (0, 1),
            "דרום": (0, -1), "אחורה": (0, -1), "s": (0, -1),
            "מזרח": (1, 0), "ימינה": (1, 0), "e": (1, 0), "מז": (1, 0),
            "מערב": (-1, 0), "שמאלה": (-1, 0), "w": (-1, 0), "מע": (-1, 0)
        }

        # תמיכה ב-"לך למערב" או רק "מערב"
        d_vec = None
        if action in ["לך", "go", "נוע"] and len(parts) > 1:
            d_vec = dirs.get(parts[1])
        elif action in dirs:
            d_vec = dirs[action]

        if d_vec:
            dx, dy = d_vec
            nx, ny = self.state["x"] + dx, self.state["y"] + dy
            
            # בדיקה אם צריך לייצר חדר
            n_key = self.get_key(nx, ny)
            is_new = n_key not in self.state["generated_rooms"]
            
            if is_new:
                new_room = self.create_room_at(nx, ny)
                self.add_msg(f"✨ גילוי חדש: {new_room['name']}", "system")
            
            # ביצוע תנועה
            self.state["x"] = nx
            self.state["y"] = ny
            if n_key not in self.state["visited"]: self.state["visited"].append(n_key)
            
            # תיאור החדר החדש
            r = self.get_current_room()
            self.add_msg(f"הגעת ל<b>{r['name']}</b>.", "game")
            self.add_msg(r['desc'], "game")
            if r['items']: self.add_msg(f"חפצים: {', '.join(r['items'])}", "success")

        # --- איסוף חפצים ---
        elif action in ["קח", "take", "אסוף"]:
            item = parts[1] if len(parts) > 1 else ""
            room = self.get_current_room()
            if item in room["items"]:
                self.state["inv"].append(item)
                room["items"].remove(item)
                self.add_msg(f"לקחת: {item}", "success")
            else:
                self.add_msg("לא מוצא את זה פה.", "warning")

        elif action in ["הסתכל", "look"]:
            r = self.get_current_room()
            self.add_msg(f"{r['name']}<br>{r['desc']}", "game")
            if r['items']: self.add_msg(f"רואה כאן: {r['items']}", "success")
            
        elif action in ["תיק", "inv"]:
            self.add_msg(f"תיק: {self.state['inv']}", "info")
            
        else:
            self.add_msg("פקודה לא מזוהה. נסה: צפון, דרום, מזרח, מערב.", "warning")

    def add_msg(self, text, type):
        self.state["log"].append({"text": text, "type": type})


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
    coords = f"X: {engine.state['x']}, Y: {engine.state['y']}"
    
    # מחזירים גם את ה-HTML של המפה שנוצרה מחדש
    return jsonify({
        "log": engine.state["log"], 
        "loc_name": curr['name'],
        "coords": coords,
        "map_html": engine.render_map() 
    })

# --- UI WITH MINIMAP ---
HTML = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>INFINITE MAPPER</title>
<link href="https://fonts.googleapis.com/css2?family=Rubik:wght@300;500;700&family=Source+Code+Pro:wght@400;700&display=swap" rel="stylesheet">
<style>
    :root { --bg: #0b0c10; --panel: #1f2833; --neon: #66fcf1; --text: #c5c6c7; }
    body { background: var(--bg); color: var(--text); font-family: 'Rubik', sans-serif; margin:0; height:100vh; display:flex; overflow:hidden;}
    
    /* Layout */
    .container { display:flex; width:100%; max-width:1200px; margin:0 auto; }
    .sidebar { width: 300px; background: #15151e; padding: 20px; border-left: 2px solid #222; display:flex; flex-direction:column; gap:20px;}
    .main { flex-grow:1; display:flex; flex-direction:column; padding:20px; position:relative;}

    /* Minimap Box */
    .map-box { 
        background: black; border: 2px solid var(--neon); 
        border-radius: 8px; padding: 10px; text-align:center;
        font-family: 'Source Code Pro', monospace; 
        min-height: 150px; display:flex; flex-direction:column; justify-content:center;
    }
    .map-row { display:block; line-height: 1; height: 25px;}
    .map-cell { 
        display:inline-block; width: 25px; height: 25px; text-align:center; vertical-align:middle; line-height:25px;
        color: #333; 
    }
    .map-cell.player { color: #fff; font-weight:bold; text-shadow: 0 0 5px white; animation: blink 1s infinite;}
    
    /* Color Codes for Biomes in Map */
    .map-cell.room-רפואי { color: #ff5555; }
    .map-cell.room-תעשייתי { color: #f1c40f; }
    .map-cell.room-טכנולוגי { color: #3498db; }
    .map-cell.room-מגורים { color: #2ecc71; }
    .map-cell.room-start { color: #fff; }

    /* Controls Sidebar */
    .controls { display:grid; grid-template-columns: 1fr 1fr; gap:10px; }
    .btn { background: #222; color:white; border:1px solid #444; padding:12px; cursor:pointer; text-align:center; transition:0.2s;}
    .btn:hover { border-color: var(--neon); color: var(--neon); background:#000;}

    /* Log */
    .log-window { flex-grow:1; overflow-y:auto; margin-bottom:15px; background: rgba(0,0,0,0.2); border: 1px solid #333; padding:15px; border-radius:4px;}
    .msg { margin-bottom:10px; }
    .msg.user { color: #888; border-right: 2px solid #888; padding-right:8px;}
    .msg.game { color: #ddd; }
    .msg.system { color: #555; font-size:0.8rem; text-align:center; margin-top:5px; border-top:1px dashed #333; padding-top:5px;}
    .msg.success { color: #4cd137; }

    input { background: #111; border:1px solid #333; padding:15px; color:white; width:100%; box-sizing:border-box; font-family:inherit;}
    input:focus { border-color: var(--neon); outline:none; }

    @keyframes blink { 50% { opacity: 0.5; } }

    /* Responsive */
    @media(max-width: 700px) {
        .container { flex-direction:column-reverse; }
        .sidebar { width: auto; height: auto; border-left:none; border-top:2px solid #333; padding:10px;}
        .map-row { height: 18px; } .map-cell { width: 18px; height: 18px; font-size:12px; line-height:18px;}
    }
</style>
</head>
<body>
    <div class="container">
        
        <div class="main">
            <div style="display:flex; justify-content:space-between; margin-bottom:10px;">
                <h2 style="margin:0; color:var(--neon)" id="room-name">...</h2>
                <span id="coords" style="color:#555">X:0 Y:0</span>
            </div>
            
            <div class="log-window" id="chat"></div>
            
            <div style="display:flex;">
                <input type="text" id="inp" placeholder="הקלד: מזרח, מערב, קח כף..." autofocus>
                <button onclick="send()" class="btn" style="width:80px">שלח</button>
            </div>
        </div>

        <div class="sidebar">
            <div style="color:white; margin-bottom:5px;">📡 SCANNER (MINIMAP)</div>
            <div class="map-box" id="map-display">
                <!-- Map Injected Here -->
            </div>
            
            <div style="margin-top:20px; color:#aaa; font-size:0.9rem">בקרה ידנית:</div>
            <div class="controls">
                <div class="btn" onclick="send('צפון')">⬆️ צפון</div>
                <div class="btn" onclick="send('דרום')">⬇️ דרום</div>
                <div class="btn" onclick="send('מזרח')">⬅️ מזרח</div>
                <div class="btn" onclick="send('מערב')">➡️ מערב</div>
                <div class="btn" onclick="send('הסתכל')">👁️ סרוק</div>
                <div class="btn" onclick="send('תיק')">🎒 תיק</div>
            </div>
        </div>
    </div>

<script>
const API="{{ api_url }}";

document.addEventListener("DOMContentLoaded", () => send("הסתכל"));

document.getElementById("inp").addEventListener("keypress", (e) => {
    if(e.key==="Enter") send();
});

async function send(txtOverride) {
    let inp = document.getElementById("inp");
    let val = txtOverride || inp.value;
    if(!txtOverride) inp.value = "";
    if(!val) return;
    
    let res = await fetch(API, {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify({cmd: val})
    });
    let d = await res.json();
    
    // Update Log
    let logWin = document.getElementById("chat");
    logWin.innerHTML = "";
    d.log.forEach(l => {
        let div = document.createElement("div");
        div.className = "msg "+l.type;
        div.innerHTML = l.text;
        logWin.appendChild(div);
    });
    logWin.scrollTop = logWin.scrollHeight;
    
    // Update HUD
    document.getElementById("room-name").innerText = d.loc_name;
    document.getElementById("coords").innerText = d.coords;
    
    // Update Map HTML
    document.getElementById("map-display").innerHTML = d.map_html;
}
</script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(port=5006, debug=True)
