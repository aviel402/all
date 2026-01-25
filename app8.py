import random
import uuid
from flask import Flask, render_template_string, request, jsonify, session, url_for

app = Flask(__name__)
# שינוי מפתח מוחק סשנים ישנים ומונע באגים
app.secret_key = 'deathmatch_stable_v15_fixed'

# ==========================================
# 🧬 מאגר נתונים
# ==========================================
HOSTS = {
    "blob": {"name": "רפש", "icon": "🦠", "hp": 25, "atk": 4},
    "rat":  {"name": "עכברוש", "icon": "🐀", "hp": 35, "atk": 6},
    "dog":  {"name": "כלב קרב", "icon": "🐕", "hp": 50, "atk": 10},
    "soldier": {"name": "חייל", "icon": "👮", "hp": 90, "atk": 15},
    "robot": {"name": "רובוט", "icon": "🤖", "hp": 120, "atk": 18},
    "demon": {"name": "שד", "icon": "👹", "hp": 160, "atk": 25},
    "dragon": {"name": "דרקון", "icon": "🐲", "hp": 300, "atk": 40}
}

BOT_NAMES = ["גולגולת", "וייפר", "פנטום", "המשמיד", "צל", "בלאק", "כאוס", "הצייד"]

# ==========================================
# ⚙️ מנוע לוגי יציב
# ==========================================
class Engine:
    def __init__(self, state=None):
        # מנגנון שחזור או התחלה מחדש
        if not state or "wins" not in state:
            self.state = {
                "wins": 0,
                "game_over": False,
                "msg": "המתן לאתחול...",
            }
            self.start_match()
        else:
            self.state = state

    def pos_key(self, x, y): return f"{x},{y}"
    
    def log(self, txt, t="game"):
        self.state["log"].append({"text": txt, "type": t})
        if len(self.state["log"]) > 25: self.state["log"].pop(0)

    # אתחול סיבוב חדש (משאיר ניקוד)
    def start_match(self):
        self.state.update({
            "x": 0, "y": 0, # מיקום התחלה
            "hp": 30, "max_hp": 30, "host": "blob", # דמות התחלתית
            "map_radius": 7, # מפה 15 על 15
            "rivals": [],
            "corpses": {}, # מילון גופות במיקום "x,y"
            "log": [{"text": "הקרב מתחיל. חסל את כולם.", "type": "gold"}],
            "visited": ["0,0"],
            "game_over": False
        })
        
        # יצירת בוטים (כמות עולה לפי ניצחונות)
        num_bots = 5 + self.state["wins"]
        used_pos = set(["0,0"])
        
        for _ in range(num_bots):
            # בחירת דמות לבוט
            h_type = random.choice(list(HOSTS.keys()))
            if h_type == "dragon": h_type = "rat" # לאזן, שלא יתחילו עם דרקון
            
            # מיקום רנדומלי
            bx, by = 0, 0
            while f"{bx},{by}" in used_pos:
                bx = random.randint(-7, 7)
                by = random.randint(-7, 7)
            used_pos.add(f"{bx},{by}")
            
            bot = {
                "id": str(uuid.uuid4()),
                "name": random.choice(BOT_NAMES),
                "host": h_type,
                "hp": HOSTS[h_type]["hp"],
                "max": HOSTS[h_type]["hp"],
                "atk": HOSTS[h_type]["atk"],
                "x": bx, "y": by
            }
            self.state["rivals"].append(bot)

    # === לוגיקת AI ותורות ===
    def process_turn(self):
        if self.state["game_over"]: return

        px, py = self.state["x"], self.state["y"]
        surviving_bots = []
        
        for bot in self.state["rivals"]:
            # הבוט זז
            dist_x = px - bot["x"]
            dist_y = py - bot["y"]
            
            # אם השחקן קרוב (טווח 3) הבוט מתקרב (AI בסיסי)
            dx, dy = 0, 0
            if abs(dist_x) <= 3 and abs(dist_y) <= 3:
                dx = 1 if dist_x > 0 else (-1 if dist_x < 0 else 0)
                dy = 1 if dist_y > 0 else (-1 if dist_y < 0 else 0)
            else:
                # סתם זז
                dx = random.choice([-1, 0, 1])
                dy = random.choice([-1, 0, 1])
            
            # גבולות מפה לבוט
            bot["x"] = max(-7, min(7, bot["x"] + dx))
            bot["y"] = max(-7, min(7, bot["y"] + dy))
            
            # התקפה אם באותה משבצת
            if bot["x"] == px and bot["y"] == py:
                dmg = bot["atk"] + random.randint(-1, 2)
                self.state["hp"] -= dmg
                self.log(f"🩸 {bot['name']} תקף אותך! (-{dmg})", "danger")
            
            # שמירה
            surviving_bots.append(bot)

        self.state["rivals"] = surviving_bots
        
        # בדיקת מוות שחקן
        if self.state["hp"] <= 0:
            self.state["hp"] = 0
            self.state["game_over"] = True
            self.state["win_status"] = False
            self.log("❌ מתת! לחץ על ריסט כדי להתחיל מחדש.", "danger")

        # בדיקת ניצחון
        if len(self.state["rivals"]) == 0:
            self.state["game_over"] = True
            self.state["win_status"] = True
            self.state["wins"] += 1
            self.log("🏆 ניצחון! חיסלת את כולם.", "gold")

    # === פעולות שחקן ===
    def move(self, dx, dy):
        if self.state["game_over"]: return
        
        nx = self.state["x"] + dx
        ny = self.state["y"] + dy
        
        # גבולות מפה לשחקן (15x15)
        if nx < -7 or nx > 7 or ny < -7 or ny > 7:
            self.log("הגעת לקצה הזירה.", "sys")
            return
            
        self.state["x"] = nx
        self.state["y"] = ny
        
        pos = self.pos_key(nx, ny)
        if pos not in self.state["visited"]: self.state["visited"].append(pos)
        
        self.process_turn() # תור העולם

    def attack(self, bot_index):
        if self.state["game_over"]: return
        
        px, py = self.state["x"], self.state["y"]
        # מסננים רק את הבוטים שבחדר שלי
        room_bots = [b for b in self.state["rivals"] if b["x"] == px and b["y"] == py]
        
        if bot_index >= len(room_bots): return # הגנה
        
        target = room_bots[bot_index]
        my_stats = HOSTS[self.state["host"]]
        
        # חישוב נזק
        dmg = my_stats["atk"] + random.randint(0, 5)
        target["hp"] -= dmg
        self.log(f"פגעת ב-{target['name']} (-{dmg})", "success")
        
        # מוות של בוט
        if target["hp"] <= 0:
            self.log(f"💀 חיסלת את {target['name']}!", "gold")
            # יצירת גופה
            self.state["corpses"][f"{px},{py}"] = {
                "type": target["host"],
                "max_hp": target["max"]
            }
            # הסרה מרשימת החיים (נעשית על ידי חיפוש ב-ID)
            self.state["rivals"] = [b for b in self.state["rivals"] if b["id"] != target["id"]]
        
        self.process_turn()

    def swap_body(self):
        if self.state["game_over"]: return
        
        pos = f"{self.state['x']},{self.state['y']}"
        if pos not in self.state["corpses"]: return
        
        corpse = self.state["corpses"][pos]
        new_type = corpse["type"]
        
        # ביצוע החלפה
        self.state["host"] = new_type
        self.state["max_hp"] = HOSTS[new_type]["hp"] # עדכון מקסימום לגוף החדש
        self.state["hp"] = self.state["max_hp"]      # ריפוי מלא!
        
        del self.state["corpses"][pos]
        self.log(f"🧬 נכנסת לגוף חדש: {HOSTS[new_type]['name']}!", "success")
        
        self.process_turn()

    # === נתונים לממשק ===
    def get_ui(self):
        # 1. מפה (4x4 רדיוס, כלומר 9x9 גריד)
        grid = []
        radius = 4 
        px, py = self.state["x"], self.state["y"]
        
        for dy in range(radius, -radius - 1, -1):
            row = []
            for dx in range(-radius, radius + 1):
                tx, ty = px + dx, py + dy
                k = f"{tx},{ty}"
                cell = {"icon": "", "cls": "fog"}
                
                # גבולות
                if tx < -7 or tx > 7 or ty < -7 or ty > 7:
                    cell["cls"] = "wall"
                elif dx == 0 and dy == 0:
                    cell["icon"] = "🤠"
                    cell["cls"] = "me"
                elif k in self.state["visited"] or (abs(dx)<=1 and abs(dy)<=1):
                    # בדיקת תוכן
                    has_bot = any(b for b in self.state["rivals"] if b["x"]==tx and b["y"]==ty)
                    has_body = k in self.state["corpses"]
                    
                    if has_bot:
                        cell["icon"] = "😈"
                        cell["cls"] = "enemy"
                    elif has_body:
                        cell["icon"] = "💀"
                        cell["cls"] = "body"
                    else:
                        cell["icon"] = "⬜"
                        cell["cls"] = "floor"
                row.append(cell)
            grid.append(row)

        # 2. מידע חדר
        room_bots = [b for b in self.state["rivals"] if b["x"] == px and b["y"] == py]
        clean_bots = []
        for b in room_bots:
            dat = b.copy()
            dat["meta"] = HOSTS[b["host"]]
            clean_bots.append(dat)
            
        corpse = None
        pos_k = f"{px},{py}"
        if pos_k in self.state["corpses"]:
            c_data = self.state["corpses"][pos_k]
            corpse = {
                "name": HOSTS[c_data["type"]]["name"],
                "icon": HOSTS[c_data["type"]]["icon"],
                "max": c_data["max_hp"]
            }

        return {
            "player": {
                "name": HOSTS[self.state["host"]]["name"],
                "icon": HOSTS[self.state["host"]]["icon"],
                "hp": self.state["hp"], "max": self.state["max_hp"],
            },
            "game_state": {
                "over": self.state["game_over"],
                "win": self.state.get("win_status", False),
                "wins_count": self.state["wins"]
            },
            "map": grid,
            "log": self.state["log"],
            "bots": clean_bots,
            "corpse": corpse
        }

# ==========================================
# שרת Flask
# ==========================================
@app.route("/")
def index():
    if "uid" not in session: session["uid"] = str(uuid.uuid4())
    api = url_for("api_handle")
    return render_template_string(HTML, api=api)

@app.route("/api", methods=["POST"])
def api_handle():
    # טעינה בטוחה
    try: 
        state = session.get("dm_final_15")
        if not state: raise Exception("No State")
        eng = Engine(state)
    except: 
        eng = Engine(None) # משחק חדש במקרה של תקלה

    d = request.json or {}
    act = d.get("a")
    val = d.get("v")

    if act == "new": eng = Engine(None) # ריסט יזום (כפתור או הפסד)
    elif act == "next": eng.start_match() # ניצחון - המשך
    elif act == "move": eng.move(*val)
    elif act == "atk": eng.attack(val)
    elif act == "swap": eng.swap_body()

    session["dm_final_15"] = eng.state
    return jsonify(eng.get_ui())

# ==========================================
# CLIENT (HTML/JS/CSS)
# ==========================================
HTML = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ARENA 15</title>
<style>
    /* CSS */
    * { box-sizing:border-box; user-select:none; }
    body { background: #111; color:#eee; font-family:'Segoe UI',sans-serif; margin:0; height:100vh; display:flex; flex-direction:column; overflow:hidden;}
    
    /* Top Bar */
    .top { height:60px; background:#222; border-bottom:2px solid #666; display:flex; justify-content:space-between; align-items:center; padding:0 15px;}
    .badge { background:#333; border:1px solid #555; padding:5px 10px; border-radius:5px; font-weight:bold;}
    
    /* Main Layout */
    .mid { flex:1; display:flex; overflow:hidden;}
    
    /* Radar (Left) */
    .map-box { width:220px; background:#050505; border-left:1px solid #444; padding:10px; display:flex; align-items:center; justify-content:center;}
    .grid { display:grid; gap:1px; background:#222; border:1px solid #555; width:200px; height:200px;}
    .cell { background:#000; display:flex; align-items:center; justify-content:center; font-size:12px;}
    .me { background: #00ff00; }
    .enemy { background: #ff0000; animation: flash 1s infinite; }
    .body { background: gold; }
    .fog { opacity: 0.1; } .wall { background: #330000; } .floor { background:#111;}
    @keyframes flash { 50% { opacity: 0.5; }}

    /* Scene (Right) */
    .scene { flex:1; display:flex; flex-direction:column; background: #151515;}
    .log-box { height: 100px; overflow-y:auto; font-size:13px; padding:10px; border-bottom:1px solid #333; background:#111; font-family:monospace;}
    .msg { margin-bottom:2px; } .gold{color:gold} .danger{color:#f55}
    
    .room-view { flex:1; padding:20px; overflow-y:auto; display:flex; flex-wrap:wrap; gap:15px; align-content:flex-start; justify-content:center;}
    .card { width:120px; height:150px; background:#222; border:1px solid #444; border-radius:8px; display:flex; flex-direction:column; align-items:center; justify-content:space-around; padding:5px;}
    .c-icon { font-size:40px;}
    .c-btn { width:100%; border:none; padding:8px; color:white; border-radius:4px; cursor:pointer; font-weight:bold;}
    
    /* Footer / Controls */
    .bot { height:160px; background:#222; border-top:2px solid #666; display:grid; grid-template-columns: 2fr 1fr; align-items:center; padding:0 20px;}
    
    .pad { width:140px; display:grid; grid-template-columns:repeat(3,1fr); gap:5px; margin:0 auto; direction:ltr;}
    .move-btn { height:40px; font-size:20px; background:#444; border:1px solid #666; color:white; border-radius:5px; cursor:pointer;}
    .move-btn:active { background:#666;}
    .u{grid-column:2} .l{grid-row:2} .d{grid-row:2} .r{grid-row:2}

    .corpse-box { border: 2px dashed gold; background:#220; }
    
    /* Modal */
    .modal { position:fixed; inset:0; background:rgba(0,0,0,0.95); z-index:99; display:none; flex-direction:column; align-items:center; justify-content:center;}
    .title { font-size:50px; margin-bottom:20px; color:white; text-shadow:0 0 20px red;}
    .m-btn { font-size:24px; padding:15px 40px; background:red; border:none; color:black; font-weight:bold; cursor:pointer;}
</style>
</head>
<body>

<div id="m-lose" class="modal">
    <div class="title" style="color:#f55">GAME OVER</div>
    <div style="margin-bottom:20px; color:#aaa">מתת בקרב.</div>
    <button class="m-btn" onclick="api('new')">משחק חדש</button>
</div>

<div id="m-win" class="modal">
    <div class="title" style="color:gold; text-shadow:0 0 20px gold">נ י צ ח ו ן !</div>
    <div style="margin-bottom:20px; color:#aaa">כל היריבים חוסלו.</div>
    <button class="m-btn" onclick="api('next')" style="background:gold">שלב הבא</button>
</div>

<div class="top">
    <div style="display:flex; align-items:center; gap:10px">
        <span style="font-size:30px;" id="p-ic">🦠</span>
        <div>
            <div style="font-weight:bold" id="p-nm">...</div>
            <div style="font-size:12px; color:#f55">HP: <span id="p-hp">0</span></div>
        </div>
    </div>
    <div class="badge" style="color:gold">גביעים: <span id="wins">0</span></div>
</div>

<div class="mid">
    <div class="scene">
        <div class="log-box" id="logs"></div>
        <div class="room-view" id="cards"></div>
    </div>
    <div class="map-box">
        <div class="grid" id="map"></div>
    </div>
</div>

<div class="bot">
    <div>
        <button class="move-btn" style="font-size:14px; background:#500;" onclick="api('new')">RESET</button>
    </div>
    <div class="pad">
        <button class="move-btn u" onclick="api('move',[0,1])">⬆</button>
        <button class="move-btn l" onclick="api('move',[-1,0])">⬅</button>
        <button class="move-btn d" onclick="api('move',[0,-1])">⬇</button>
        <button class="move-btn r" onclick="api('move',[1,0])">➡</button>
    </div>
</div>

<script>
    const API = "{{ api }}";
    
    window.onload = ()=> api('init');

    async function api(act, val=null){
        let r = await fetch(API, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({a:act, v:val})});
        let d = await r.json();
        
        // Modals
        if (d.game_state.over) {
            if(d.game_state.win) document.getElementById("m-win").style.display = "flex";
            else document.getElementById("m-lose").style.display = "flex";
        } else {
            document.getElementById("m-win").style.display = "none";
            document.getElementById("m-lose").style.display = "none";
        }

        // Stats
        document.getElementById("p-ic").innerText = d.player.icon;
        document.getElementById("p-nm").innerText = d.player.name;
        document.getElementById("p-hp").innerText = d.player.hp + "/" + d.player.max;
        document.getElementById("wins").innerText = d.game_state.wins_count;

        // Map
        let mh="";
        let gridSize = d.map.length; // usually 9
        d.map.forEach(row=>{
            row.forEach(c=> mh+=`<div class="cell ${c.cls}">${c.icon}</div>`);
        });
        let grid = document.getElementById("map");
        grid.innerHTML = mh;
        grid.style.gridTemplateColumns = `repeat(${gridSize}, 1fr)`;
        grid.style.gridTemplateRows = `repeat(${gridSize}, 1fr)`;

        // Scene Cards
        let ch = "";
        
        if (d.bots.length === 0 && !d.corpse) {
            ch = "<div style='color:#555; width:100%; text-align:center;'>השטח נקי מאויבים.</div>";
        } else {
            // אויבים
            d.bots.forEach((b,i) => {
                ch += `<div class="card">
                    <div class="c-icon">${b.meta.icon}</div>
                    <div style="font-weight:bold">${b.name}</div>
                    <div style="color:#aaa; font-size:12px">${b.meta.name}</div>
                    <div style="color:#f55">${b.hp} HP</div>
                    <button class="c-btn" style="background:#a22" onclick="api('atk',${i})">⚔️ חיסול</button>
                </div>`;
            });
            // גופה
            if (d.corpse) {
                let c = d.corpse;
                ch += `<div class="card corpse-box">
                    <div class="c-icon">${c.icon}</div>
                    <div style="font-weight:bold; color:gold">${c.name}</div>
                    <div style="font-size:12px;">${c.max} MaxHP</div>
                    <button class="c-btn" style="background:gold; color:black" onclick="api('swap')">♻️ החלף גוף</button>
                </div>`;
            }
        }
        document.getElementById("cards").innerHTML = ch;

        // Logs
        let lh="";
        d.log.slice().reverse().forEach(l=> lh+=`<div class="msg ${l.type}">${l.text}</div>`);
        document.getElementById("logs").innerHTML = lh;
    }
    
    // Keyboard
    window.onkeydown = e => {
        if(e.key=="ArrowUp") api('move',[0,1]);
        if(e.key=="ArrowDown") api('move',[0,-1]);
        if(e.key=="ArrowLeft") api('move',[-1,0]);
        if(e.key=="ArrowRight") api('move',[1,0]);
    }
</script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(port=5006, debug=True)
