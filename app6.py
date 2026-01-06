from flask import Flask, render_template_string, request, jsonify, session, url_for
import json
import uuid
import random

app = Flask(__name__)
app.secret_key = 'dungeon_battle_v3'

# --- ⚔️ הגדרות עולם ואויבים ---
BIOMES = {
    "מסדרון": "⬛", "רפואי": "🏥", "נשקייה": "🛡️", 
    "מגורים": "🛌", "כור": "☢️", "מוצף": "💧"
}

ENEMIES = [
    {"name": "רובוט שמירה", "icon": "🤖", "hp": 20, "desc": "רובוט ישן עם לייזר חלוד."},
    {"name": "זומבי חלל", "icon": "🧟", "hp": 15, "desc": "חליפת חלל קרועה, משהו זז בפנים."},
    {"name": "רחפן קרב", "icon": "🛸", "hp": 10, "desc": "מזמזם באוויר ומחפש מטרות."},
    {"name": "גוש בוץ חי", "icon": "🦠", "hp": 25, "desc": "עיסה ירוקה ומבעבעת על הרצפה."}
]

ITEMS = ["סוללה", "ערכת עזרה ראשונה", "שבב", "מפתח", "רימון הלם", "מטבעות"]

# --- 🎲 מנוע יצירת חדרים ---
class WorldGenerator:
    def generate(self, x, y):
        # בחירת סוג חדר
        b_type = random.choice(list(BIOMES.keys()))
        
        # בחירת אויב (30% סיכוי)
        enemy = None
        if random.random() < 0.35 and (x != 0 or y != 0): # בלי אויבים בהתחלה
            base_enemy = random.choice(ENEMIES)
            enemy = base_enemy.copy() # מעתיקים כדי לא לשנות את המקור
        
        # בחירת חפצים
        loot = []
        if random.random() < 0.5:
            loot.append(random.choice(ITEMS))

        return {
            "name": f"אזור {b_type}",
            "type": b_type,
            "enemy": enemy, # אם אין, זה יהיה None
            "items": loot,
            "cleared": False # האם ניצחנו בחדר הזה
        }

# --- 🕹️ מנוע משחק ---
class GameEngine:
    def __init__(self, state=None):
        if not state:
            self.state = {
                "x": 0, "y": 0,
                "hp": 100,
                "max_hp": 100,
                "xp": 0,
                "inv": [],
                "map": {},
                "visited": ["0,0"],
                "log": [{"text": "המערכת אותחלה. השתמש בכפתורים כדי לשרוד.", "type": "system"}]
            }
            # חדר התחלה בטוח
            self.state["map"]["0,0"] = {
                "name": "בסיס האם", "type": "רפואי", 
                "enemy": None, "items": ["אקדח בסיסי"], "cleared": True
            }
        else:
            self.state = state
        self.gen = WorldGenerator()

    def get_key(self, x, y): return f"{x},{y}"

    def move(self, dx, dy):
        self.state["x"] += dx
        self.state["y"] += dy
        k = self.get_key(self.state["x"], self.state["y"])
        
        is_new = False
        if k not in self.state["map"]:
            self.state["map"][k] = self.gen.generate(self.state["x"], self.state["y"])
            is_new = True
            
        if k not in self.state["visited"]:
            self.state["visited"].append(k)

        room = self.state["map"][k]
        
        # דיווח על כניסה
        if is_new: self.log(f"⚡ גילוי חדש: {room['name']}", "system")
        else: self.log(f"הגעת ל-{room['name']}", "game")

        # דיווח על אויבים
        if room["enemy"]:
            e = room["enemy"]
            self.log(f"⚠️ סכנה! {e['name']} ({e['icon']}) חוסם את הדרך!", "warning")
            self.log(e['desc'], "info")
        elif room["items"]:
            self.log(f"יש כאן: {', '.join(room['items'])}", "success")

    def attack(self):
        k = self.get_key(self.state["x"], self.state["y"])
        room = self.state["map"][k]
        
        if not room["enemy"]:
            self.log("אין כאן במי להילחם. אתה יורה באוויר.", "game")
            return
            
        # קרב!
        enemy = room["enemy"]
        dmg = random.randint(5, 15)
        enemy["hp"] -= dmg
        self.log(f"💥 פגעת ב-{enemy['name']} והורדת {dmg} נזק!", "success")
        
        if enemy["hp"] <= 0:
            # ניצחון
            self.log(f"💀 ה-{enemy['name']} הושמד!", "system")
            room["enemy"] = None
            room["cleared"] = True
            self.state["xp"] += 10
            # אולי האויב הפיל משהו
            if random.random() > 0.5:
                loot = "גביש אנרגיה"
                room["items"].append(loot)
                self.log(f"האויב הפיל: {loot}", "info")
        else:
            # האויב מחזיר מלחמה
            player_dmg = random.randint(2, 8)
            self.state["hp"] -= player_dmg
            self.log(f"🩸 ה-{enemy['name']} תקף אותך! איבדת {player_dmg} חיים.", "warning")
            if self.state["hp"] <= 0:
                self.log("☠️ נהרגת בקרב... המערכת תבצע ריסט בקרוב.", "warning")
                self.state["hp"] = 0

    def take(self):
        k = self.get_key(self.state["x"], self.state["y"])
        room = self.state["map"][k]
        if room["items"]:
            item = room["items"].pop(0)
            
            # אם זה חפץ רפואי - מרפא מיד
            if "עזרה" in item:
                self.state["hp"] = min(self.state["hp"] + 20, 100)
                self.log("❤️ השתמשת בערכת עזרה ראשונה.", "success")
            else:
                self.state["inv"].append(item)
                self.log(f"אספת: {item}", "success")
        else:
            self.log("החדר ריק מחפצים שימושיים.", "game")

    def log(self, txt, t):
        self.state["log"].append({"text": txt, "type": t})

    # --- רינדור מפה עם אויבים ---
    def render_map(self):
        cx, cy = self.state["x"], self.state["y"]
        r = 2 # רדיוס תצוגה
        html = "<div class='map-grid'>"
        
        for dy in range(r, -r - 1, -1):
            html += "<div class='map-row'>"
            for dx in range(-r, r + 1):
                tx, ty = cx + dx, cy + dy
                k = self.get_key(tx, ty)
                
                content = "🌫️" # ערפל
                cls = "fog"
                
                if dx == 0 and dy == 0:
                    content = "🧑‍🚀" # שחקן
                    cls = "player"
                elif k in self.state["visited"]:
                    room = self.state["map"][k]
                    # אם יש אויב חי - מציגים גולגולת
                    if room["enemy"]:
                        content = "💀"
                        cls = "danger"
                    else:
                        content = BIOMES.get(room["type"], "⬜")
                        cls = "safe"
                
                html += f"<span class='cell {cls}'>{content}</span>"
            html += "</div>"
        html += "</div>"
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
    txt = d.get("cmd", "")
    eng = GameEngine(session.get("game"))

    if eng.state["hp"] <= 0 and txt != "reset":
         return jsonify({
             "log": [{"text": "אתה מת. לחץ על אתחול כדי להתחיל מחדש.", "type": "warning"}], 
             "hud": "☠️", "stats": "DEAD"
         })

    if txt == "צפון": eng.move(0, 1)
    elif txt == "דרום": eng.move(0, -1)
    elif txt == "מזרח": eng.move(1, 0)
    elif txt == "מערב": eng.move(-1, 0)
    elif txt == "תקוף": eng.attack()
    elif txt == "קח": eng.take()
    elif txt == "תיק": eng.log(f"תיק: {eng.state['inv']}", "info")
    elif txt == "הסתכל": eng.move(0,0) # רק לרענן תצוגה
    elif txt == "reset": 
        session.clear()
        return jsonify({"reload": True})

    session["game"] = eng.state
    
    k = eng.get_key(eng.state['x'], eng.state['y'])
    r_name = eng.state['map'][k]['name']
    
    return jsonify({
        "log": eng.state["log"],
        "hud": eng.render_map(),
        "room_name": r_name,
        "hp": eng.state["hp"],
        "xp": eng.state["xp"]
    })

# --- UI HTML ---
HTML = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DUNGEON COMBAT</title>
    <style>
        body { background:#111; color:#eee; font-family: 'Segoe UI', sans-serif; margin:0; height:100vh; display:flex; flex-direction:column; overflow:hidden;}
        
        /* אזור עליון - סטטוס ומפה */
        .header { background:#222; padding:10px; display:flex; align-items:center; justify-content:space-between; border-bottom:2px solid #444;}
        .stats { font-weight:bold; font-size:14px; display:flex; gap:15px;}
        .hp-bar { color: #ff5555; }
        .xp-bar { color: #55aaff; }

        .map-container { display:flex; flex-direction:column; align-items:center; background:#000; padding:5px; border-radius:5px; border:1px solid #333; margin:0 auto;}
        .map-row { display:flex; }
        .cell { width:35px; height:35px; display:flex; align-items:center; justify-content:center; font-size:20px;}
        .player { border:2px solid #0f0; background:#002200; border-radius:5px;}
        .danger { background:#330000; animation:pulse 1s infinite;}
        .safe { background:#1a1a1a; }
        .fog { background:#111; opacity:0.2; }

        @keyframes pulse { 0% { opacity:1; } 50% { opacity:0.6; } 100% { opacity:1; } }

        /* אזור אמצעי - לוג */
        .log-area { flex-grow:1; overflow-y:auto; padding:15px; background: #0a0a0a;}
        .msg { padding:6px; margin-bottom:5px; border-radius:4px;}
        .system { color:#aaa; font-size:12px; text-align:center; margin:10px 0;}
        .game { color:#fff; }
        .warning { color:#ff6b6b; background:rgba(255,0,0,0.1); border-right:3px solid #f00;}
        .success { color:#51cf66; }
        .info { color:#74c0fc; font-style:italic;}

        /* אזור תחתון - כפתורים */
        .controls { 
            background:#1b1b1b; padding:15px; border-top:2px solid #444; 
            display:grid; grid-template-columns: repeat(3, 1fr); gap:8px;
            height: 220px;
        }
        
        .btn { 
            background: #333; color: white; border:1px solid #555; border-radius:8px;
            font-size:24px; cursor:pointer; display:flex; flex-direction:column;
            align-items:center; justify-content:center; active:scale(0.95);
        }
        .btn:active { background: #555; transform: translateY(2px); }
        .btn span { font-size:12px; margin-top:5px; color:#aaa; }
        
        .atk-btn { background: #5a1a1a; border-color:#a33; }
        .mov-btn { background: #1a1a5a; border-color:#33a; }
        .sys-btn { background: #222; border-color:#444; font-size:18px;}

    </style>
</head>
<body>

    <div class="header">
        <div class="stats">
            <span class="hp-bar">❤️ <span id="hp">100</span></span>
            <span class="xp-bar">⭐ <span id="xp">0</span></span>
        </div>
        <div class="map-container" id="map-target"></div>
        <div style="font-size:12px; color:#888; width:60px; text-align:left;">מפה<br>רדאר</div>
    </div>

    <div class="log-area" id="log-target"></div>

    <div class="controls">
        <button class="btn sys-btn" onclick="send('הסתכל')">👁️<span>סרוק</span></button>
        <button class="btn mov-btn" onclick="send('צפון')">⬆️<span>צפון</span></button>
        <button class="btn sys-btn" onclick="send('תיק')">🎒<span>תיק</span></button>

        <button class="btn mov-btn" onclick="send('מזרח')">➡️<span>מזרח</span></button>
        <button class="btn atk-btn" onclick="send('תקוף')">⚔️<span>תקוף!</span></button>
        <button class="btn mov-btn" onclick="send('מערב')">⬅️<span>מערב</span></button>

        <button class="btn sys-btn" onclick="send('קח')">✋<span>קח</span></button>
        <button class="btn mov-btn" onclick="send('דרום')">⬇️<span>דרום</span></button>
        <button class="btn sys-btn" onclick="send('reset')" style="color:#f55;">🛑<span>אתחול</span></button>
    </div>

<script>
    const API = "{{ api_url }}";

    document.addEventListener("DOMContentLoaded", ()=> send("הסתכל"));

    async function send(cmd) {
        try {
            let r = await fetch(API, {
                method:'POST', headers:{'Content-Type':'application/json'},
                body: JSON.stringify({cmd: cmd})
            });
            let d = await r.json();
            
            if(d.reload) location.reload();

            // Render HUD
            document.getElementById("hp").innerText = d.hp;
            document.getElementById("xp").innerText = d.xp;
            if(d.hud) document.getElementById("map-target").innerHTML = d.hud;

            // Render Log
            let l = document.getElementById("log-target");
            l.innerHTML = "";
            d.log.forEach(item => {
                l.innerHTML += `<div class='msg ${item.type}'>${item.text}</div>`;
            });
            l.scrollTop = l.scrollHeight;

        } catch(e) { console.error(e); }
    }
</script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(port=5006, debug=True)
