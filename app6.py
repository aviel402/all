import random
import uuid
import json
from flask import Flask, render_template_string, request, jsonify, session, url_for

# ==========================================
# 🌎 מאגר הנתונים (אינסופי)
# ==========================================
BIOMES = [
    {"name": "יער אפל", "icon": "🌲", "danger": 1},
    {"name": "ביצות", "icon": "🐸", "danger": 2},
    {"name": "מבצר נטוש", "icon": "🏰", "danger": 3},
    {"name": "הר געש", "icon": "🌋", "danger": 4},
    {"name": "בית קברות", "icon": "🪦", "danger": 2},
    {"name": "כפר שקט", "icon": "🏡", "danger": 0},
    {"name": "מערת הקריסטל", "icon": "💎", "danger": 3},
]

NPCS = [
    {"name": "סוחר דרכים", "lines": ["זהב פותח דלתות.", "רוצה שיקוי?"]},
    {"name": "מכשפה עתיקה", "lines": ["העתיד שלך נראה... קצר.", "תן לי עין של דרקון ואתן לך כוח."]},
    {"name": "אביר עייף", "lines": ["המלך מת מזמן.", "אל תרד לקומה התחתונה."]},
    {"name": "קבצן", "lines": ["נדבה לאדון?", "ראיתי דברים איומים בחושך."]}
]

ENEMIES = [
    {"name": "גובלין", "hp": 20, "atk": 5, "xp": 10},
    {"name": "זאב רעב", "hp": 30, "atk": 8, "xp": 15},
    {"name": "שלד", "hp": 40, "atk": 10, "xp": 20},
    {"name": "דרקון זומבי (בוס)", "hp": 150, "atk": 25, "xp": 200},
]

# ==========================================
# ⚙️ מנוע המשחק
# ==========================================

app = Flask(__name__)
app.secret_key = 'ultra_rpg_fix_final_v5'

class WorldGen:
    def create_room(self, x, y):
        # אזור התחלה בטוח
        if x == 0 and y == 0:
            return {"name": "בסיס הבית", "icon": "🛡️", "enemy": None, "npc": None, "items": []}

        biome = random.choice(BIOMES)
        
        # 40% סיכוי לאויב
        enemy = None
        if random.random() < 0.4 and biome['danger'] > 0:
            base_en = random.choice(ENEMIES)
            enemy = base_en.copy()
            enemy["hp"] += biome['danger'] * 5 # אויבים חזקים יותר באזורים מסוכנים
            
        # 30% סיכוי ל-NPC
        npc = None
        if not enemy and random.random() < 0.3:
            npc = random.choice(NPCS)

        # 50% סיכוי לחפצים
        items = []
        if random.random() < 0.5:
            items.append(random.choice(["שיקוי", "מטבע", "יהלום", "חרב", "מגן"]))

        return {
            "name": f"{biome['name']} ({x},{y})",
            "icon": biome['icon'],
            "enemy": enemy,
            "npc": npc,
            "items": items
        }

class Engine:
    def __init__(self, state=None):
        if not state:
            self.state = {
                "x": 0, "y": 0,
                "hp": 100, "max_hp": 100,
                "stamina": 100, "xp": 0, "level": 1, "gold": 0,
                "inv": [],
                "map": {},
                "visited": ["0,0"],
                "log": [{"text": "המערכת אותחלה. צא לדרך...", "type": "sys"}]
            }
            self.gen = WorldGen()
            self.state["map"]["0,0"] = self.gen.create_room(0,0)
        else:
            self.state = state
            self.gen = WorldGen()

    def get_pos(self): return f"{self.state['x']},{self.state['y']}"
    
    def log(self, t, type="game"): self.state["log"].append({"text": t, "type": type})

    def move(self, dx, dy):
        if self.state["stamina"] <= 0:
            self.log("אתה עייף מדי! (נוח - R)", "warning")
            return
        
        self.state["x"] += dx
        self.state["y"] += dy
        self.state["stamina"] -= 2
        
        k = self.get_pos()
        if k not in self.state["map"]:
            self.state["map"][k] = self.gen.create_room(self.state['x'], self.state['y'])
        
        if k not in self.state["visited"]: self.state["visited"].append(k)
        
        r = self.state["map"][k]
        self.log(f"זזת ל-{r['name']}", "game")
        if r["enemy"]: self.log(f"⚠️ אויב! {r['enemy']['name']}", "danger")

    def attack(self):
        r = self.state["map"][self.get_pos()]
        if not r["enemy"]:
            self.log("אין במי לתקוף.", "info")
            return
        
        e = r["enemy"]
        dmg = random.randint(10, 20) + self.state["level"]
        e["hp"] -= dmg
        self.log(f"תקפת בעוצמה! {dmg} נזק.", "success")
        
        if e["hp"] <= 0:
            self.log(f"🏆 ניצחת! קיבלת {e['xp']} XP.", "gold")
            self.state["xp"] += e["xp"]
            self.state["gold"] += random.randint(10, 50)
            self.check_level_up()
            r["enemy"] = None
        else:
            p_dmg = e["atk"]
            self.state["hp"] -= p_dmg
            self.log(f"נפגעת! -{p_dmg} חיים.", "danger")

    def talk(self):
        r = self.state["map"][self.get_pos()]
        if r["npc"]:
            self.log(f"🗣️ {r['npc']['name']}: {random.choice(r['npc']['lines'])}", "info")
        else:
            self.log("אין פה אף אחד.", "info")

    def take(self):
        r = self.state["map"][self.get_pos()]
        if r["items"]:
            for i in r["items"]: self.state["inv"].append(i)
            self.log(f"לקחת: {', '.join(r['items'])}", "success")
            r["items"] = []
        else:
            self.log("אין כאן כלום.", "info")
            
    def rest(self):
        self.state["hp"] = min(self.state["hp"] + 20, self.state["max_hp"])
        self.state["stamina"] = 100
        self.log("💤 נחת וחידשת כוחות.", "sys")
        
    def check_level_up(self):
        if self.state["xp"] > self.state["level"] * 50:
            self.state["level"] += 1
            self.state["max_hp"] += 20
            self.state["hp"] = self.state["max_hp"]
            self.log(f"⬆️ עלית לרמה {self.state['level']}!", "gold")

    def render_map(self):
        cx, cy = self.state["x"], self.state["y"]
        r = 2 
        html = "<div class='grid'>"
        for dy in range(r, -r - 1, -1):
            html += "<div class='row'>"
            for dx in range(-r, r + 1):
                k = f"{cx+dx},{cy+dy}"
                
                content = "🌫️"
                bg_class = "fog"
                
                if dx == 0 and dy == 0:
                    content = "👤"
                    bg_class = "player-cell"
                elif k in self.state["visited"]:
                    room = self.state["map"][k]
                    content = room["icon"]
                    if room["enemy"]: content = "👿"
                    bg_class = "room-cell"
                
                html += f"<div class='cell {bg_class}'>{content}</div>"
            html += "</div>"
        html += "</div>"
        return html


# ==========================================
# SERVER ROUTES
# ==========================================

@app.route("/")
def index():
    if "uid" not in session: session["uid"] = str(uuid.uuid4())
    # 📌 חישוב הכתובת האמיתית לשימוש ב-Javascript
    api_url = url_for('game_action') 
    return render_template_string(HTML, api_url=api_url)

@app.route("/action", methods=["POST"])
def game_action():
    data = request.json or {}
    act = data.get("a")
    val = data.get("v")

    # ניסיון טעינת מצב, אם נכשל מתחילים חדש (מונע קריסות 500)
    try:
        eng = Engine(session.get("game"))
    except:
        eng = Engine(None)

    if eng.state["hp"] <= 0 and act != "reset":
        return jsonify({"dead": True})

    if act == "move": eng.move(*val)
    elif act == "attack": eng.attack()
    elif act == "talk": eng.talk()
    elif act == "take": eng.take()
    elif act == "rest": eng.rest()
    elif act == "reset": 
        session.clear()
        return jsonify({"reload": True})
    
    session["game"] = eng.state
    
    room = eng.state["map"][eng.get_pos()]
    return jsonify({
        "log": eng.state["log"],
        "hud": eng.render_map(),
        "loc": room["name"],
        "hp": eng.state["hp"],
        "st": eng.state["stamina"],
        "lvl": eng.state["level"],
        "inv": eng.state["inv"]
    })


# ==========================================
# FRONTEND HTML
# ==========================================
HTML = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Ultimate RPG</title>
<link href="https://fonts.googleapis.com/css2?family=Assistant:wght@400;700&display=swap" rel="stylesheet">
<style>
    /* CSS Grid Layout */
    body { background: #111; color: white; margin: 0; font-family: 'Assistant', sans-serif; height: 100vh; display: grid; grid-template-rows: 60px 1fr 240px; overflow: hidden; }

    /* TOP BAR */
    .top-bar { background: #222; border-bottom: 2px solid #333; display: flex; align-items: center; justify-content: space-between; padding: 0 20px; }
    .stat-badge { background: #333; padding: 5px 10px; border-radius: 5px; font-weight: bold; margin-left: 10px; border: 1px solid #444; font-size:14px;}
    .map-radar { display: flex; flex-direction: column; align-items: center; }

    /* MIDDLE (Log area) */
    .log-area { background: #151515; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 8px; box-shadow: inset 0 0 20px #000; }
    .msg { padding: 10px; border-radius: 5px; background: rgba(255,255,255,0.05); font-size: 15px; border-right: 3px solid #555;}
    .sys { color: #81d4fa; text-align: center; border: none; background: none;}
    .danger { background: rgba(255,0,0,0.15); border-right-color: #f44336; }
    .success { background: rgba(0,255,0,0.1); border-right-color: #00e676; }
    .gold { color: gold; text-align: center; font-size: 18px; border:none; text-shadow: 0 0 10px gold; }
    
    /* MAP CSS */
    .grid { display: flex; flex-direction: column; gap: 4px; }
    .row { display: flex; gap: 4px; }
    .cell { width: 40px; height: 40px; background: #222; display: flex; align-items: center; justify-content: center; font-size: 20px; border-radius: 6px; box-shadow: 0 2px 2px rgba(0,0,0,0.5);}
    .player-cell { background: #003300; border: 2px solid #0f0; }
    .room-cell { background: #333; border: 1px solid #555; }
    .fog { opacity: 0.1; }

    /* BOTTOM CONTROLS */
    .control-panel { background: #1c1c1c; padding: 10px; border-top: 2px solid #444; display: flex; gap: 10px; }
    
    .d-pad-container { 
        display: grid; grid-template-columns: repeat(3, 1fr); gap: 5px; width: 150px; 
        /* מכריח את החיצים להיות בסידור נכון ללא קשר לעברית */
        direction: ltr; 
    }
    
    .actions-container { flex: 1; display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }

    .btn { background: #333; border: 1px solid #555; color: white; border-radius: 8px; font-size: 18px; cursor: pointer; transition: 0.1s; }
    .btn:active { background: #555; transform: scale(0.96); }
    
    /* Arrow specific positions in grid */
    .btn-up { grid-column: 2; grid-row: 1; }
    .btn-left { grid-column: 1; grid-row: 2; }
    .btn-right { grid-column: 3; grid-row: 2; }
    .btn-down { grid-column: 2; grid-row: 2; }
    
    .atk { background: #7f1d1d; } 
    .rest { background: #0d47a1; }

    /* INV Panel */
    .inv-panel { position:absolute; bottom:250px; left:10px; background:rgba(0,0,0,0.8); padding:10px; border-radius:5px; border:1px solid #555; max-width:150px;}
    .title-loc { font-size: 1.5rem; font-weight:bold; color:white; }

</style>
</head>
<body>

    <!-- שורת סטטוס -->
    <div class="top-bar">
        <div style="display:flex;">
            <div class="stat-badge">❤️ <span id="hp">100</span></div>
            <div class="stat-badge">⚡ <span id="st">100</span></div>
            <div class="stat-badge">⭐ <span id="lvl">1</span></div>
        </div>
        <div class="title-loc" id="loc">טוען...</div>
        
        <div class="map-radar" id="map-target"></div>
    </div>

    <!-- לוג ראשי -->
    <div class="log-area" id="log-target">
        <div class="msg sys">המערכת מנסה להתחבר...</div>
    </div>
    
    <div class="inv-panel">
        <small style="color:#aaa">תיק ציוד:</small>
        <div id="inv-target" style="font-size:12px;">ריק</div>
    </div>

    <!-- בקרה -->
    <div class="control-panel">
        
        <div class="actions-container">
            <button class="btn atk" onclick="send('attack')">⚔️ תקיפה</button>
            <button class="btn" onclick="send('talk')">💬 דבר</button>
            <button class="btn" onclick="send('take')">✋ אסוף</button>
            <button class="btn rest" onclick="send('rest')">💤 לנוח</button>
            <button class="btn" onclick="send('reset')" style="background:#444; font-size:12px">🔄</button>
        </div>
        
        <div class="d-pad-container">
            <button class="btn btn-up" onclick="send('move',[0,1])">⬆️</button>
            <button class="btn btn-left" onclick="send('move',[-1,0])">⬅️</button>
            <button class="btn btn-down" onclick="send('move',[0,-1])">⬇️</button>
            <button class="btn btn-right" onclick="send('move',[1,0])">➡️</button>
        </div>

    </div>

<script>
    const API = "{{ api_url }}"; // מוזרק מפייתון בצורה דינמית

    document.addEventListener("DOMContentLoaded", () => send("look"));

    async function send(action, val=null) {
        let logBox = document.getElementById("log-target");
        
        try {
            let res = await fetch(API, {
                method:'POST', 
                headers:{'Content-Type':'application/json'},
                body:JSON.stringify({a: action, v: val})
            });
            
            // הגנה ממסך שחור במקרה של שגיאת שרת
            if (res.status != 200) {
                logBox.innerHTML += `<div class="msg danger">שגיאת שרת (${res.status}). נסה לאפס משחק.</div>`;
                return;
            }

            let d = await res.json();
            
            if (d.dead) { 
                alert("Game Over! מתת. מתחילים מחדש."); 
                send('reset'); 
                return; 
            }
            if (d.reload) location.reload();

            // עדכונים למסך
            document.getElementById("hp").innerText = d.hp;
            document.getElementById("st").innerText = d.st;
            document.getElementById("lvl").innerText = d.lvl;
            document.getElementById("loc").innerText = d.loc;
            document.getElementById("map-target").innerHTML = d.hud;
            document.getElementById("inv-target").innerText = d.inv.length ? d.inv.join(", ") : "ריק";

            // רינדור הודעות ללוג
            logBox.innerHTML = "";
            d.log.forEach(item => {
                logBox.innerHTML += `<div class="msg ${item.type}">${item.text}</div>`;
            });
            logBox.scrollTop = logBox.scrollHeight;
            
        } catch(e) { 
            console.error(e);
            logBox.innerHTML += `<div class="msg danger">שגיאת רשת.</div>`;
        }
    }
    
    // שליטה במקלדת
    window.addEventListener('keydown', (e) => {
        const k = e.key;
        if(k === "ArrowUp") send('move',[0,1]);
        if(k === "ArrowDown") send('move',[0,-1]);
        if(k === "ArrowLeft") send('move',[-1,0]);
        if(k === "ArrowRight") send('move',[1,0]);
        if(k === " ") send('attack');
        if(k === "e" || k === "Enter") send('take');
    });
</script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(port=5006, debug=True)
