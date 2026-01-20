import random
import uuid
from flask import Flask, render_template_string, request, jsonify, session, url_for

app = Flask(__name__)
# מפתח יציב
app.secret_key = 'battle_royale_stable_final_v55'

# ==========================================
# 🧬 דמויות
# ==========================================
HOSTS = {
    # דרגה 1
    "blob": {"name": "עיסה", "icon": "🦠", "hp": 25, "atk": 4},
    "fly":  {"name": "זבוב", "icon": "🪰", "hp": 15, "atk": 2},
    "rat":  {"name": "עכברוש", "icon": "🐀", "hp": 35, "atk": 6},
    
    # דרגה 2
    "soldier": {"name": "חייל", "icon": "👮", "hp": 90, "atk": 15},
    "wolf":    {"name": "זאב", "icon": "🐺", "hp": 70, "atk": 12},
    "alien":   {"name": "חייזר", "icon": "👽", "hp": 100, "atk": 18},
    
    # דרגה 3 (חזקים)
    "robot":   {"name": "רובוט", "icon": "🤖", "hp": 150, "atk": 22},
    "beast":   {"name": "מפלצת", "icon": "👺", "hp": 180, "atk": 25},
    "tank":    {"name": "טנק", "icon": "🚜", "hp": 250, "atk": 10},
    
    # בוסים
    "dragon":  {"name": "דרקון", "icon": "🐲", "hp": 350, "atk": 45}
}

BOT_NAMES = ["קילר", "נינג'ה", "ספקטר", "פנטום", "וייפר", "בלאק", "המשמיד", "צל", "נמסיס", "טיטאן"]

# ==========================================
# ⚙️ מנוע (מתוקן)
# ==========================================
class Engine:
    def __init__(self, state=None):
        if not state or "wins" not in state:
            self.state = {
                "wins": 0,
                "game_over": False,
                "msg": ""
            }
            self.start_match()
        else:
            self.state = state

    def log(self, t, type="game"): 
        self.state["log"].append({"text": t, "type": type})
        if len(self.state["log"]) > 40: self.state["log"].pop(0)

    def pos_key(self, x, y): return f"{x},{y}"

    def start_match(self):
        # אתחול סיבוב חדש
        self.state.update({
            "x": 0, "y": 0,
            "host": "soldier",
            "hp": 90, "max_hp": 90,
            "map_size": 15, # מפה ענקית (-15 עד 15)
            "rivals": [],
            "corpses": {},
            "visited": ["0,0"],
            "game_over": False,
            "win_status": False,
            "log": [{"text": f"הקרב מתחיל! מטרות: 75", "type": "gold"}]
        })
        
        # יצירת 75 בוטים בפיזור חכם
        used_spots = set(["0,0"]) # המקום שלי תפוס
        
        for _ in range(75):
            h_type = random.choice(list(HOSTS.keys()))
            if h_type == "dragon": h_type = "rat" # מאזנים, שלא כולם יהיו דרקונים
            
            # חיפוש מקום פנוי (מנסה 10 פעמים)
            bx, by = 0, 0
            for attempt in range(10):
                bx = random.randint(-15, 15)
                by = random.randint(-15, 15)
                if f"{bx},{by}" not in used_spots:
                    break
            used_spots.add(f"{bx},{by}")
            
            bot = {
                "id": str(uuid.uuid4()),
                "name": random.choice(BOT_NAMES) + f"-{random.randint(10,99)}",
                "host": h_type,
                "hp": HOSTS[h_type]["hp"],
                "max": HOSTS[h_type]["hp"],
                "atk": HOSTS[h_type]["atk"],
                "x": bx, "y": by
            }
            self.state["rivals"].append(bot)

    def process_turn(self):
        if self.state["game_over"]: return

        px, py = self.state["x"], self.state["y"]
        next_gen_bots = []
        
        # לוגיקה לכל בוט
        for bot in self.state["rivals"]:
            # תזוזה
            if abs(bot["x"]-px) <= 4 and abs(bot["y"]-py) <= 4: # ציד קרוב
                dx = 1 if bot["x"] < px else (-1 if bot["x"] > px else 0)
                dy = 1 if bot["y"] < py else (-1 if bot["y"] > py else 0)
            else: # רנדומלי
                dx = random.choice([-1,0,1])
                dy = random.choice([-1,0,1])
                
            bot["x"] = max(-15, min(15, bot["x"] + dx))
            bot["y"] = max(-15, min(15, bot["y"] + dy))
            
            # בוט תוקף שחקן באותו חדר
            if bot["x"] == px and bot["y"] == py:
                dmg = bot["atk"] + random.randint(-2, 2)
                self.state["hp"] -= max(1, dmg)
                self.log(f"🩸 {bot['name']} תקף! (-{dmg})", "danger")
            
            next_gen_bots.append(bot)

        self.state["rivals"] = next_gen_bots
        
        # בדיקות סוף משחק
        if self.state["hp"] <= 0:
            self.state["hp"] = 0
            self.state["game_over"] = True
            self.state["win_status"] = False
            self.log("❌ מתת! נפסלת.", "critical")

        if len(self.state["rivals"]) == 0 and not self.state["game_over"]:
            self.state["game_over"] = True
            self.state["win_status"] = True
            self.state["wins"] += 1
            self.log("🏆 ניצחון!", "gold")

    def move(self, dx, dy):
        if self.state["game_over"]: return
        
        nx = max(-15, min(15, self.state["x"] + dx))
        ny = max(-15, min(15, self.state["y"] + dy))
        self.state["x"] = nx
        self.state["y"] = ny
        
        pos = self.pos_key(nx, ny)
        if pos not in self.state["visited"]: self.state["visited"].append(pos)
        self.process_turn()

    def attack(self, bot_index):
        if self.state["game_over"]: return
        
        # מחפש בוטים איתי בחדר
        room_bots = [b for b in self.state["rivals"] if b["x"] == self.state["x"] and b["y"] == self.state["y"]]
        if bot_index >= len(room_bots): return
        
        target = room_bots[bot_index]
        my_stats = HOSTS[self.state["host"]]
        dmg = my_stats["atk"] + random.randint(0, 5)
        
        target["hp"] -= dmg
        self.log(f"תקפת את {target['name']} (-{dmg})", "success")
        
        if target["hp"] <= 0:
            self.log(f"💀 חיסול! גופת {target['host']} נפלה.", "gold")
            # הופך לגופה
            self.state["corpses"][f"{target['x']},{target['y']}"] = {
                "type": target["host"],
                "max": target["max"]
            }
            # מחיקה מהמשחק (על ידי זיהוי ה-ID)
            self.state["rivals"] = [b for b in self.state["rivals"] if b["id"] != target["id"]]
        
        self.process_turn()

    def swap_body(self):
        if self.state["game_over"]: return
        pos = f"{self.state['x']},{self.state['y']}"
        if pos not in self.state["corpses"]: return
        
        corpse = self.state["corpses"][pos]
        self.state["host"] = corpse["type"]
        self.state["max_hp"] = corpse["max"]
        self.state["hp"] = corpse["max"] # FULL HEAL
        
        del self.state["corpses"][pos]
        self.log(f"🧬 נכנסת לגוף {HOSTS[self.state['host']]['name']}!", "gold")
        self.process_turn()

    def get_ui(self):
        # מפה רדיוס 4 (9x9)
        grid = []
        radius = 4 
        px, py = self.state["x"], self.state["y"]
        
        for dy in range(radius, -radius - 1, -1):
            row = []
            for dx in range(-radius, radius + 1):
                tx, ty = px + dx, py + dy
                k = f"{tx},{ty}"
                cell = {"icon": "", "cls": "fog"}
                
                # גבולות עולם (15)
                if tx < -15 or tx > 15 or ty < -15 or ty > 15:
                    cell["cls"] = "wall"
                elif dx == 0 and dy == 0:
                    cell["icon"] = "😎"
                    cell["cls"] = "me"
                elif k in self.state["visited"] or (abs(dx)<=2 and abs(dy)<=2):
                    has_bot = any(b for b in self.state["rivals"] if b["x"]==tx and b["y"]==ty)
                    has_dead = k in self.state["corpses"]
                    
                    if has_bot:
                        cell["icon"] = "🔴"
                        cell["cls"] = "danger"
                    elif has_dead:
                        cell["icon"] = "☠️"
                        cell["cls"] = "loot"
                    else:
                        cell["icon"] = "⬜"
                        cell["cls"] = "floor"
                row.append(cell)
            grid.append(row)

        # נתונים
        room_bots = []
        for i, b in enumerate(self.state["rivals"]):
            if b["x"] == px and b["y"] == py:
                b_info = b.copy()
                # תרגום שמות לאייקונים לתצוגה
                meta = HOSTS[b["host"]]
                b_info["icon"] = meta["icon"]
                b_info["type_name"] = meta["name"]
                room_bots.append(b_info)
        
        corpse = None
        pk = f"{px},{py}"
        if pk in self.state["corpses"]:
            ct = self.state["corpses"][pk]["type"]
            corpse = {"name": HOSTS[ct]["name"], "icon": HOSTS[ct]["icon"]}

        return {
            "player": {
                "name": HOSTS[self.state["host"]]["name"],
                "icon": HOSTS[self.state["host"]]["icon"],
                "hp": self.state["hp"], "max": self.state["max_hp"],
            },
            "game_state": {
                "over": self.state["game_over"],
                "win": self.state["win_status"],
                "wins_count": self.state["wins"]
            },
            "map": grid,
            "log": self.state["log"],
            "bots": room_bots,
            "corpse": corpse,
            "total_bots": len(self.state["rivals"])
        }

# ==========================================
# SERVER
# ==========================================
@app.route("/")
def index():
    if "uid" not in session: session["uid"] = str(uuid.uuid4())
    api = url_for("update")
    return render_template_string(HTML, api=api)

@app.route("/update", methods=["POST"])
def update():
    try: eng = Engine(session.get("war_royale_stable"))
    except: eng = Engine(None)
    
    d = request.json or {}
    act = d.get("a")
    val = d.get("v")
    
    if act=="start": eng = Engine(None)
    elif act=="next": eng.start_match()
    elif act=="move": eng.move(*val)
    elif act=="atk": eng.attack(val)
    # תיקון התקפה: תוקף תמיד את הראשון ברשימה של החדר (0)
    elif act=="attack_first": eng.attack(0) 
    elif act=="swap": eng.swap_body()
    
    session["war_royale_stable"] = eng.state
    return jsonify(eng.get_ui())

# ==========================================
# HTML UI
# ==========================================
HTML = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>TOTAL WAR 75</title>
<style>
    * { box-sizing: border-box; }
    body { background: #111; color: #ddd; font-family: 'Segoe UI', sans-serif; margin:0; height:100vh; display:flex; flex-direction:column; overflow:hidden;}
    
    .top { height:60px; background:#222; display:flex; justify-content:space-between; align-items:center; padding:0 20px; border-bottom:2px solid #555;}
    .stat-badge { background:#333; padding:5px 10px; border-radius:5px; border:1px solid #666; font-weight:bold;}
    
    .content { flex:1; display:flex; overflow:hidden;}
    
    /* RADAR */
    .left-col { width:220px; background:#050505; border-left:1px solid #333; display:flex; flex-direction:column; align-items:center; padding:10px; justify-content:center;}
    .grid { display:grid; gap:1px; background:#222; border:1px solid #444; width:200px; height:200px;}
    .cell { display:flex; align-items:center; justify-content:center; background:#000; font-size:12px;}
    .me { background:#0f0; border:1px solid white; z-index:2;}
    .danger { background:red; animation: blink 0.5s infinite;}
    .loot { background:gold; color:black;}
    .fog { opacity:0.1; } .wall { background:#400; color:red;} .empty{background:#181818}
    @keyframes blink { 50%{opacity:0.5}}

    /* MAIN STAGE */
    .center-stage { flex:1; display:flex; flex-direction:column; background: radial-gradient(circle, #222, #000); padding:20px; align-items:center;}
    .cards-area { flex:1; display:flex; gap:10px; flex-wrap:wrap; justify-content:center; align-content:center; overflow-y:auto; width:100%;}
    
    .card { 
        width:110px; height:140px; background:#2a2a2a; border:1px solid #555; border-radius:8px; 
        display:flex; flex-direction:column; align-items:center; justify-content:space-between; padding:5px;
        box-shadow:0 4px 10px rgba(0,0,0,0.5);
    }
    .c-btn { width:100%; padding:5px; border:none; cursor:pointer; border-radius:4px; font-weight:bold; }
    
    .corpse-alert { 
        margin-top:10px; padding:10px; background:#332a00; border:1px solid gold; 
        color:gold; width:80%; text-align:center; border-radius:8px; display:none;
        animation: pop 0.3s;
    }
    @keyframes pop { from{transform:scale(0);} to{transform:scale(1);} }

    /* LOGS */
    .log-box { height:120px; background:#080808; border-top:1px solid #444; padding:10px; font-size:12px; font-family:monospace; overflow-y:auto;}
    .msg { margin-bottom:2px;} .critical{color:red} .gold{color:gold} .success{color:#0f0}

    /* FOOTER / CONTROLS */
    .controls { height:140px; background:#1b1b1b; display:grid; grid-template-columns: 1fr 200px 1fr; align-items:center; padding:0 20px;}
    .d-pad { display:grid; grid-template-columns:repeat(3,1fr); gap:5px; width:140px; direction:ltr;}
    .btn { height:40px; background:#333; border:1px solid #555; color:white; border-radius:5px; font-size:20px; cursor:pointer;}
    .btn:active { background:#555;}
    
    .overlay { position:fixed; inset:0; background:rgba(0,0,0,0.95); display:none; flex-direction:column; justify-content:center; align-items:center; z-index:99; color:white;}
    .big-btn { padding:15px 40px; font-size:24px; border:none; cursor:pointer; font-weight:bold; margin-top:20px;}
</style>
</head>
<body>

<div id="o-win" class="overlay">
    <h1 style="font-size:60px; color:gold">🏆 המנצח! 🏆</h1>
    <p>חיסלת את כל הבוטים.</p>
    <button class="big-btn" style="background:gold" onclick="api('next')">שלב הבא (+1 נק')</button>
</div>

<div id="o-lose" class="overlay">
    <h1 style="font-size:60px; color:red">☠️ הובסת ☠️</h1>
    <p>נפסלת מהתחרות.</p>
    <button class="big-btn" style="background:red; color:white" onclick="api('start')">נסה שוב</button>
</div>

<div class="top">
    <div style="display:flex; gap:10px; align-items:center">
        <span style="font-size:30px" id="me-icon">🤠</span>
        <div>
            <div id="me-name" style="font-weight:bold">...</div>
            <div style="font-size:12px; color:#f66">HP: <span id="me-hp">0</span></div>
        </div>
    </div>
    <div class="stat-badge">בוטים נותרו: <span id="cnt" style="color:red; font-size:18px">...</span></div>
    <div class="stat-badge" style="color:gold">גביעים: <span id="wins">0</span></div>
</div>

<div class="content">
    <div class="left-col">
        <small style="color:#0f0; margin-bottom:5px">RADAR (Zoom: 4x)</small>
        <div class="grid" id="map"></div>
    </div>
    
    <div class="center-stage">
        <div class="cards-area" id="stage"></div>
        
        <div id="swap-box" class="corpse-alert">
            <div>נמצאה גופה: <span id="c-name" style="font-weight:bold"></span></div>
            <button class="c-btn" style="background:gold; margin-top:5px; color:black" onclick="api('swap')">♻️ קח גוף (רפא ל-100%)</button>
        </div>
    </div>
</div>

<div class="log-box" id="logs"></div>

<div class="controls">
    <div>
        <button onclick="api('start')" style="background:#400; color:#f88; border:none; padding:10px;">RESET</button>
    </div>
    
    <div class="d-pad">
        <button class="btn" style="grid-column:2" onclick="api('move',[0,1])">⬆</button>
        <button class="btn" style="grid-column:1; grid-row:2" onclick="api('move',[-1,0])">⬅</button>
        <button class="btn" style="grid-column:2; grid-row:2" onclick="api('move',[0,-1])">⬇</button>
        <button class="btn" style="grid-column:3; grid-row:2" onclick="api('move',[1,0])">➡</button>
    </div>
    
    <div></div>
</div>

<script>
    const API = "{{ api }}";
    window.onload = ()=> api('');

    async function api(a, v=null) {
        try {
            let r = await fetch(API, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({a:a, v:v})});
            let d = await r.json();
            
            // SCREENS
            document.getElementById("o-lose").style.display = d.game_state.over && !d.game_state.win ? 'flex' : 'none';
            document.getElementById("o-win").style.display = d.game_state.win ? 'flex' : 'none';

            // INFO
            let p = d.player;
            document.getElementById("me-icon").innerText = p.icon;
            document.getElementById("me-name").innerText = p.name;
            document.getElementById("me-hp").innerText = p.hp + "/" + p.max;
            document.getElementById("cnt").innerText = d.total_bots;
            document.getElementById("wins").innerText = d.game_state.wins_count;

            // MAP
            let mh="";
            d.map.forEach(row => {
                row.forEach(c => mh+=`<div class='cell ${c.cls}'>${c.icon}</div>`);
            });
            let grid = document.getElementById("map");
            grid.innerHTML = mh;
            // 9x9 grid forced style (4 radius * 2 + 1)
            grid.style.gridTemplateColumns = `repeat(9, 1fr)`;
            grid.style.gridTemplateRows = `repeat(9, 1fr)`;

            // STAGE (Enemies)
            let sh = "";
            if (d.bots.length === 0) sh = "<div style='color:#555'>השטח נקי... תמשיך לזוז.</div>";
            else {
                d.bots.forEach(b => {
                    sh += `<div class="card">
                        <div style="font-size:30px;">${b.icon}</div>
                        <div style="font-weight:bold; font-size:12px;">${b.name}</div>
                        <div style="color:#aaa; font-size:10px;">${b.type_name}</div>
                        <div style="color:#f55; font-size:12px;">${b.hp} HP</div>
                        <button class="c-btn" style="background:#a22; color:white" onclick="api('attack_first')">⚔️ תקיפה</button>
                    </div>`;
                });
            }
            document.getElementById("stage").innerHTML = sh;

            // CORPSE UI
            let sbox = document.getElementById("swap-box");
            if (d.corpse) {
                sbox.style.display = "block";
                document.getElementById("c-name").innerText = d.corpse.icon + " " + d.corpse.name;
            } else {
                sbox.style.display = "none";
            }

            // LOG
            let lh = "";
            d.log.slice().reverse().forEach(l => {
                lh += `<div class="msg ${l.type}">> ${l.text}</div>`;
            });
            document.getElementById("logs").innerHTML = lh;

        } catch(e) { console.error(e); }
    }
    
    // Keyboard
    window.onkeydown = e => {
        if(e.key=="ArrowUp" || e.key=="w") api('move',[0,1]);
        if(e.key=="ArrowDown" || e.key=="s") api('move',[0,-1]);
        if(e.key=="ArrowLeft" || e.key=="a") api('move',[-1,0]);
        if(e.key=="ArrowRight" || e.key=="d") api('move',[1,0]);
    }
</script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(port=5006, debug=True)
