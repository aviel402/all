from flask import Flask, render_template_string, request, jsonify, session, url_for
import json
import uuid
import random

app = Flask(__name__)
app.secret_key = 'emoji_map_final_fix'

# --- 🌍 הגדרת סוגי חדרים וצבעים ---
# כל סוג חדר יקבל צבע/אייקון אחר במפה
BIOMES = {
    "רפואי": {"icon": "🏥", "items": ["תחבושת", "מזרק", "תרופה"]},
    "נשקייה": {"icon": "⚔️", "items": ["אקדח", "סכין", "קסדה"]},
    "מגורים": {"icon": "🛏️", "items": ["שמיכה", "שעון", "ספר"]},
    "טכני": {"icon": "🔋", "items": ["סוללה", "כבל", "מברג"]},
    "סתמי": {"icon": "⬛", "items": ["אבן", "אבק"]},
    "התחלה": {"icon": "🏳️", "items": ["פנס"]}
}

class WorldGenerator:
    def generate(self, x, y):
        # בחירה רנדומלית של סוג חדר
        biome_type = random.choice(["רפואי", "נשקייה", "מגורים", "טכני", "סתמי", "סתמי"])
        biome_data = BIOMES[biome_type]
        
        name = f"חדר {biome_type}"
        desc = f"זהו אזור מסוג {biome_type}. {random.choice(['האורות מהבהבים', 'יש ריח מוזר', 'שקט כאן', 'הכל מבולגן'])}."
        
        # חפצים
        room_items = []
        if random.random() > 0.4:
            room_items.append(random.choice(biome_data["items"]))
            
        return {
            "name": name,
            "desc": desc,
            "type": biome_type, # חשוב לצביעת המפה
            "items": room_items
        }

class GameEngine:
    def __init__(self, state=None):
        if not state:
            self.state = {
                "x": 0, "y": 0,
                "inv": [],
                "map_data": {}, # "0,0": {"type": "start"}
                "log": [{"text": "מערכת המיפוי הופעלה. המפה בצד שמאל.", "type": "system"}],
                "visited": ["0,0"]
            }
            # חדר ראשון
            self.state["map_data"]["0,0"] = {
                "name": "נקודת התחלה", 
                "desc": "פתח המנהרה.", 
                "type": "התחלה", 
                "items": ["מפה"]
            }
        else:
            self.state = state
        self.gen = WorldGenerator()

    def get_pos_key(self, x, y):
        return f"{x},{y}"

    def move(self, dx, dy):
        # חישוב מיקום חדש
        self.state["x"] += dx
        self.state["y"] += dy
        nx, ny = self.state["x"], self.state["y"]
        key = self.get_pos_key(nx, ny)

        # האם החדר קיים? אם לא - צור אותו
        if key not in self.state["map_data"]:
            new_room = self.gen.generate(nx, ny)
            self.state["map_data"][key] = new_room
            self.add_log(f"✨ גילית חדר חדש: {new_room['name']}", "system")
        
        # סימון כ"ביקרתי"
        if key not in self.state["visited"]:
            self.state["visited"].append(key)
            
        r = self.state["map_data"][key]
        self.add_log(f"הגעת ל<b>{r['name']}</b>.", "game")
        if r["items"]:
            self.add_log(f"ראית על הרצפה: {', '.join(r['items'])}", "success")

    def take(self, item_sub):
        curr_key = self.get_pos_key(self.state["x"], self.state["y"])
        room = self.state["map_data"][curr_key]
        
        found = None
        for i in room["items"]:
            if item_sub in i: found = i
            
        if found:
            self.state["inv"].append(found)
            room["items"].remove(found)
            self.add_log(f"לקחת: {found}", "success")
        else:
            self.add_log("אין פה את זה.", "warning")

    def add_log(self, txt, type):
        self.state["log"].append({"text": txt, "type": type})

    # --- יצירת המפה ---
    def render_map_html(self):
        cx, cy = self.state["x"], self.state["y"]
        radius = 2 # מציג 2 משבצות לכל כיוון (סה"כ 5X5)
        
        html = "<table style='border-collapse: collapse; margin: 0 auto;'>"
        
        # לולאה על ה-Y (מלמעלה למטה)
        for dy in range(radius, -radius - 1, -1):
            html += "<tr>"
            # לולאה על ה-X (משמאל לימין)
            for dx in range(-radius, radius + 1):
                tx, ty = cx + dx, cy + dy
                key = self.get_pos_key(tx, ty)
                
                # עיצוב התא
                bg = "#111" # צבע רקע של חושך
                symbol = "⬛" # ריבוע שחור לריק
                opacity = "0.3"
                border = "1px solid #222"
                
                # אם השחקן נמצא פה כרגע
                if dx == 0 and dy == 0:
                    symbol = "🧑‍🚀" # אתה
                    bg = "#333"
                    opacity = "1.0"
                    border = "2px solid #00cec9"
                
                # אם ביקרנו בחדר הזה בעבר (והוא לא המיקום הנוכחי)
                elif key in self.state["visited"]:
                    room = self.state["map_data"][key]
                    # ריבוע ירוק
                    symbol = "🟩" 
                    opacity = "0.8"
                    
                # בניית ה-HTML לתא בודד
                html += f"""
                <td style='
                    width: 40px; height: 40px; 
                    text-align: center; vertical-align: middle; 
                    background: {bg}; font-size: 20px; 
                    opacity: {opacity}; border: {border};'>
                    {symbol}
                </td>"""
            html += "</tr>"
        html += "</table>"
        
        # מקרא (Legend) מתחת למפה
        html += "<div style='font-size:12px; margin-top:10px; color:#aaa;'>🧑‍🚀=אתה | 🟩=חדר | ⬛=ריק</div>"
        return html


# --- SERVER ---
@app.route("/")
def index():
    if "uid" not in session: session["uid"] = str(uuid.uuid4())
    api_url = url_for('cmd')
    return render_template_string(HTML, api_url=api_url)

@app.route("/api/cmd", methods=["POST"])
def cmd():
    d = request.json or {}
    txt = d.get("cmd", "").strip()
    
    eng = GameEngine(session.get("game"))
    
    # עיבוד פקודה
    if txt:
        eng.add_log(txt, "user")
        if txt in ["צפון", "n", "קדימה"]: eng.move(0, 1)
        elif txt in ["דרום", "s", "אחורה"]: eng.move(0, -1)
        elif txt in ["מזרח", "e", "ימינה"]: eng.move(1, 0)
        elif txt in ["מערב", "w", "שמאלה"]: eng.move(-1, 0)
        elif txt.startswith("קח"): eng.take(txt.replace("קח", "").strip())
        elif "תיק" in txt: eng.add_log(str(eng.state["inv"]), "info")
        else: eng.add_log("פקודה לא מזוהה. השתמש בלחצנים.", "warning")

    session["game"] = eng.state
    
    # מידע ללקוח
    curr_key = eng.get_pos_key(eng.state["x"], eng.state["y"])
    curr_room = eng.state["map_data"][curr_key]
    
    return jsonify({
        "log": eng.state["log"],
        "loc_name": curr_room["name"],
        "map_html": eng.render_map_html()
    })

# --- CLIENT HTML ---
HTML = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>מפת אקספלורר</title>
    <style>
        body { background:#0a0a0a; color:white; font-family:sans-serif; margin:0; display:flex; height:100vh;}
        .container { display:flex; width:100%; max-width:1000px; margin:0 auto; box-shadow:0 0 20px #000;}
        
        .main { flex:1; display:flex; flex-direction:column; background:#1a1a1a; padding:10px;}
        .sidebar { width:260px; background:#111; border-left:2px solid #333; padding:15px; display:flex; flex-direction:column; align-items:center;}
        
        /* Map Box Style */
        .map-box { 
            background: #000; padding: 10px; border-radius: 8px; border: 1px solid #444; 
            margin-bottom: 20px; box-shadow: 0 0 10px #000;
        }

        .log { flex:1; overflow-y:auto; background:rgba(0,0,0,0.3); padding:10px; border-radius:5px; margin-bottom:10px;}
        .msg { padding:5px; border-bottom:1px solid #222;}
        .user { color:#aaa; font-style:italic;}
        .game { color:#fff; font-weight:bold;}
        .success { color:#4cd137;} .warning{color:#e1b12c;} .system{color:#00cec9;}
        
        /* D-PAD Controls */
        .controls { display:grid; grid-template-columns: repeat(3, 1fr); gap:5px; width:100%; max-width:200px;}
        .btn { background:#333; border:none; color:white; padding:15px; font-size:20px; cursor:pointer; border-radius:5px;}
        .btn:active { background:#555;}
        
    </style>
</head>
<body>
<div class="container">
    <div class="main">
        <h2 style="margin:0; color:#00cec9" id="r-name">טוען...</h2>
        <div class="log" id="log"></div>
    </div>
    
    <div class="sidebar">
        <!-- MAP AREA -->
        <div class="map-box" id="map-target">
            <!-- המפה תיכנס לפה -->
        </div>
        
        <!-- CONTROLS -->
        <div class="controls">
            <div></div>
            <button class="btn" onclick="go('צפון')">⬆️</button>
            <div></div>
            
            <button class="btn" onclick="go('מערב')">➡️</button>
            <button class="btn" onclick="go('קח')">✋</button>
            <button class="btn" onclick="go('מזרח')">⬅️</button>
            
            <div></div>
            <button class="btn" onclick="go('דרום')">⬇️</button>
            <div></div>
        </div>
        <div style="margin-top:10px; font-size:12px; color:#555">לחץ על הלחצנים כדי לנוע ולגלות את המפה</div>
    </div>
</div>

<script>
    const API="{{ api_url }}";
    
    // Auto start
    document.addEventListener("DOMContentLoaded", () => go(""));

    async function go(cmd) {
        let res = await fetch(API, {
            method:'POST',
            headers:{'Content-Type':'application/json'},
            body: JSON.stringify({cmd: cmd})
        });
        let data = await res.json();
        
        // Render Log
        let l = document.getElementById("log");
        l.innerHTML = "";
        data.log.forEach(item => {
            l.innerHTML += `<div class='msg ${item.type}'>${item.text}</div>`;
        });
        l.scrollTop = l.scrollHeight;
        
        // Render Name & Map
        document.getElementById("r-name").innerText = data.loc_name;
        document.getElementById("map-target").innerHTML = data.map_html;
    }
</script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(port=5006, debug=True)
