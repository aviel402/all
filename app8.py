import random
import uuid
import math
from flask import Flask, render_template_string, request, jsonify, session, url_for

app = Flask(__name__)
app.secret_key = 'war_royale_75_bots_v99'

# ==========================================
# 🧬 מאגר גופים עצום (20+ סוגים)
# ==========================================
HOSTS = {
    # -- עלובים (דרגה 1) --
    "blob":    {"name": "עיסה", "icon": "🦠", "hp": 20, "atk": 3},
    "fly":     {"name": "זבוב", "icon": "🪰", "hp": 10, "atk": 1},
    "chicken": {"name": "תרנגולת", "icon": "🐔", "hp": 15, "atk": 5},
    "rat":     {"name": "עכברוש", "icon": "🐀", "hp": 30, "atk": 6},
    "spider":  {"name": "עכביש", "icon": "🕷️", "hp": 25, "atk": 8},

    # -- לוחמים (דרגה 2) --
    "soldier": {"name": "חייל", "icon": "👮", "hp": 80, "atk": 15},
    "wolf":    {"name": "זאב", "icon": "🐺", "hp": 60, "atk": 12},
    "ninja":   {"name": "נינג'ה", "icon": "🥷", "hp": 50, "atk": 25},
    "zombie":  {"name": "זומבי", "icon": "🧟", "hp": 70, "atk": 10},
    "alien":   {"name": "חייזר", "icon": "👽", "hp": 90, "atk": 18},
    "boxer":   {"name": "מתאגרף", "icon": "🥊", "hp": 100, "atk": 14},

    # -- כבדים (דרגה 3) --
    "gorilla": {"name": "גורילה", "icon": "🦍", "hp": 140, "atk": 20},
    "robot":   {"name": "רובוט", "icon": "🤖", "hp": 150, "atk": 22},
    "wizard":  {"name": "מכשף", "icon": "🧙‍♂️", "hp": 80, "atk": 40},
    "tank":    {"name": "טנק", "icon": "🚜", "hp": 250, "atk": 10},
    "demon":   {"name": "שד", "icon": "👺", "hp": 160, "atk": 28},

    # -- בוסים אגדיים (דרגה 4) --
    "dragon":  {"name": "דרקון", "icon": "🐲", "hp": 350, "atk": 50},
    "rex":     {"name": "דינוזאור", "icon": "🦖", "hp": 300, "atk": 45},
    "ufo":     {"name": "חללית", "icon": "🛸", "hp": 200, "atk": 60}
}

# שמות רנדומליים לבוטים
BOT_PREFIX = ["סוכן", "לוחם", "פרויקט", "רוצח", "צל", "אומגה"]

# ==========================================
# ⚙️ מנוע הזירה (מתוקן)
# ==========================================
class Engine:
    def __init__(self, state=None):
        if not state or "rivals" not in state:
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

    def pos(self): return f"{self.state['x']},{self.state['y']}"

    def start_match(self):
        # איפוס נתונים
        self.state["x"] = 0
        self.state["y"] = 0
        self.state["host"] = "soldier" # מתחילים כחייל
        self.state["hp"] = 80
        self.state["max_hp"] = 80
        
        self.state["map_bound"] = 15 # גודל מפה (30x30)
        self.state["rivals"] = []
        self.state["corpses"] = {} 
        self.state["visited"] = ["0,0"]
        self.state["game_over"] = False
        self.state["won_match"] = False
        
        # הודעת פתיחה
        bot_count = 75 # המספר שביקשת
        self.state["log"] = [{"text": f"הקרב מתחיל! {bot_count} בוטים נכנסו לזירה.", "type": "gold"}]

        # יצירת צבא בוטים
        types = list(HOSTS.keys())
        for i in range(bot_count):
            h_type = random.choice(types)
            
            # איזון: סיכוי נמוך לבוסים
            if HOSTS[h_type]["hp"] > 200 and random.random() > 0.05:
                h_type = "rat" # רובם חלשים

            bot = {
                "id": str(uuid.uuid4()),
                "name": f"{random.choice(BOT_PREFIX)}-{random.randint(10,99)}",
                "host": h_type,
                "hp": HOSTS[h_type]["hp"],
                "max": HOSTS[h_type]["hp"],
                "x": random.randint(-15, 15),
                "y": random.randint(-15, 15)
            }
            # מניעת חפיפה עם השחקן בהתחלה
            if bot["x"]==0 and bot["y"]==0: bot["x"]=5 
            
            self.state["rivals"].append(bot)

    # === AI System (בוטים נלחמים בכולם) ===
    def process_turn(self):
        if self.state["game_over"]: return

        px, py = self.state["x"], self.state["y"]
        next_rivals = []
        
        # מילון עזר למיקומים כדי לזהות קרבות בוט-נגד-בוט
        # מפתח: "x,y", ערך: רשימת בוטים במיקום הזה
        loc_map = {} 

        # 1. תזוזה של הבוטים
        for bot in self.state["rivals"]:
            # בוט מתקרב לשחקן אם הוא קרוב (Hunt)
            if abs(bot["x"]-px) <= 3 and abs(bot["y"]-py) <= 3:
                dx = 1 if bot["x"] < px else (-1 if bot["x"] > px else 0)
                dy = 1 if bot["y"] < py else (-1 if bot["y"] > py else 0)
            else:
                # תנועה רנדומלית
                dx = random.choice([-1,0,1])
                dy = random.choice([-1,0,1])
            
            bot["x"] = max(-15, min(15, bot["x"] + dx))
            bot["y"] = max(-15, min(15, bot["y"] + dy))
            
            k = f"{bot['x']},{bot['y']}"
            if k not in loc_map: loc_map[k] = []
            loc_map[k].append(bot)

        # 2. עיבוד קרבות
        # אם יש במיקום של השחקן בוטים -> הם תוקפים את השחקן
        # אם יש כמה בוטים באותו מיקום -> הם נלחמים ביניהם
        
        my_pos = self.pos()
        
        for k, bots_in_room in loc_map.items():
            
            # --- קרב: שחקן נגד בוטים ---
            if k == my_pos:
                for bot in bots_in_room:
                    # בוט תוקף שחקן
                    dmg = HOSTS[bot["host"]]["atk"] + random.randint(-2,2)
                    self.state["hp"] -= max(1, dmg)
                    self.log(f"🩸 {bot['name']} תקף אותך! (-{dmg})", "danger")
            
            # --- קרב: בוט נגד בוט (Battle Royale) ---
            if len(bots_in_room) > 1:
                # בוט אחד שורד, השאר חוטפים
                attacker = bots_in_room[0]
                target = bots_in_room[1]
                
                dmg = HOSTS[attacker["host"]]["atk"]
                target["hp"] -= dmg
                
                if target["hp"] <= 0:
                    # יצירת גופה מהבוט המת
                    self.state["corpses"][k] = {"type": target["host"], "max": target["max"]}
                    # בוט מת לא נכנס לרשימה הסופית
                    continue 

            # הבוטים ששרדו ממשיכים לסיבוב הבא
            for b in bots_in_room:
                if b["hp"] > 0:
                    next_rivals.append(b)

        self.state["rivals"] = next_rivals

        # 3. בדיקות סוף משחק
        if self.state["hp"] <= 0:
            self.state["hp"] = 0
            self.state["game_over"] = True
            self.state["won_match"] = False
            self.log("❌ מתת! אתה נפסל מהטורניר.", "critical")

        if len(self.state["rivals"]) == 0 and not self.state["game_over"]:
            self.state["game_over"] = True
            self.state["won_match"] = True
            self.state["wins"] += 1
            self.log("🏆 ניצחון מוחלט! חיסלת את כולם.", "gold")

    # === שליטת שחקן ===
    def move(self, dx, dy):
        if self.state["game_over"]: return
        
        nx = max(-15, min(15, self.state["x"] + dx))
        ny = max(-15, min(15, self.state["y"] + dy))
        self.state["x"] = nx
        self.state["y"] = ny
        
        if self.pos() not in self.state["visited"]: self.state["visited"].append(self.pos())
        self.process_turn()

    def attack(self, idx):
        if self.state["game_over"]: return
        
        # מחפש בוטים במיקום שלי
        room_bots = [b for b in self.state["rivals"] if f"{b['x']},{b['y']}" == self.pos()]
        if idx >= len(room_bots): return
        
        bot = room_bots[idx]
        dmg = HOSTS[self.state["host"]]["atk"] + random.randint(0, 5)
        bot["hp"] -= dmg
        self.log(f"תקפת את {bot['name']} (-{dmg})", "success")
        
        if bot["hp"] <= 0:
            self.log(f"💀 הרגת את {bot['name']}!", "gold")
            self.state["corpses"][self.pos()] = {"type": bot["host"], "max": HOSTS[bot["host"]]["hp"]}
            # מחיקה (נעשית בפועל ב-process_turn או כאן ידנית, ה-turn ינקה אותו כי ה-HP <=0)
        
        self.process_turn()

    def swap(self):
        if self.state["game_over"]: return
        pos = self.pos()
        
        if pos in self.state["corpses"]:
            c_data = self.state["corpses"][pos]
            
            # שדרוג!
            self.state["host"] = c_data["type"]
            self.state["max_hp"] = HOSTS[c_data["type"]]["hp"]
            self.state["hp"] = self.state["max_hp"] # ריפוי
            
            self.log(f"🧬 לקחת את הגוף של {HOSTS[c_data['type']]['name']}", "gold")
            del self.state["corpses"][pos]
            self.process_turn()

    def get_ui(self):
        # מפה רדיוס 4 (9x9)
        grid = []
        cx, cy = self.state["x"], self.state["y"]
        radius = 4
        
        for dy in range(radius, -radius-1, -1):
            row = []
            for dx in range(-radius, radius+1):
                tx, ty = cx+dx, cy+dy
                k = f"{tx},{ty}"
                
                sym = "⬛"
                cls = "fog"
                
                # גבולות עולם (15)
                if tx < -15 or tx > 15 or ty < -15 or ty > 15:
                    sym = "🧱"
                    cls = "wall"
                
                elif dx==0 and dy==0:
                    sym = "😎"
                    cls = "me"
                elif k in self.state["visited"] or (abs(dx)<=1 and abs(dy)<=1):
                    # בדיקת תוכן
                    has_bot = any(b for b in self.state["rivals"] if b["x"]==tx and b["y"]==ty)
                    has_dead = k in self.state["corpses"]
                    
                    if has_bot: 
                        sym = "🔴"
                        cls = "danger"
                    elif has_dead:
                        sym = "⚰️"
                        cls = "loot"
                    else:
                        sym = "⬜"
                        cls = "empty"
                        
                row.append({"s":sym, "c":cls})
            grid.append(row)

        # נתוני זירה
        room_bots = []
        for i, b in enumerate(self.state["rivals"]):
            if b["x"] == cx and b["y"] == cy:
                b_info = b.copy()
                b_info["idx"] = i # אינדקס אמיתי לא בטוח כאן, עדיף להעביר רק לתצוגה
                # במערכת האמיתית פה נעשה מיפוי פשוט לתצוגה
                room_bots.append({
                    "name": b["name"], 
                    "type": HOSTS[b["host"]]["name"],
                    "icon": HOSTS[b["host"]]["icon"],
                    "hp": b["hp"], 
                    "max": b["max"]
                })
        
        corpse = None
        if self.pos() in self.state["corpses"]:
            ct = self.state["corpses"][self.pos()]["type"]
            corpse = {"name": HOSTS[ct]["name"], "icon": HOSTS[ct]["icon"]}

        return {
            "map": grid,
            "log": self.state["log"],
            "bots": room_bots,
            "corpse": corpse,
            "me": {
                "name": HOSTS[self.state["host"]]["name"],
                "icon": HOSTS[self.state["host"]]["icon"],
                "hp": self.state["hp"], "max": self.state["max_hp"]
            },
            "total_bots": len(self.state["rivals"]),
            "win": self.state.get("won_match", False),
            "dead": self.state.get("game_over", False) and not self.state.get("won_match", False),
            "wins_count": self.state["wins"]
        }

# ==========================================
# SERVER
# ==========================================
@app.route("/")
def index():
    if "uid" not in session: session["uid"] = str(uuid.uuid4())
    return render_template_string(HTML, api=url_for("update"))

@app.route("/api", methods=["POST"])
def update():
    try: eng = Engine(session.get("war_royale"))
    except: eng = Engine(None)
    
    d = request.json
    a = d.get("a")
    v = d.get("v")
    
    if a=="start": eng = Engine(None)
    elif a=="next": eng.init_match()
    elif a=="move": eng.move(*v)
    elif a=="atk": eng.attack(v) # כאן שולחים את המיקום היחסי בחדר (0, 1, 2)
    # תיקון קטן: המערכת תתקוף את הראשון בחדר תמיד כדי למנוע סנכרון אינדקסים מסובך
    elif a=="attack_first": eng.attack(0) 
    elif a=="swap": eng.swap_body()
    
    session["war_royale"] = eng.state
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
    <p>חיסלת את כל 75 הבוטים.</p>
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
    <div class="stat-badge">בוטים נותרו: <span id="cnt" style="color:red; font-size:18px">75</span></div>
    <div class="stat-badge" style="color:gold">גביעים: <span id="wins">0</span></div>
</div>

<div class="content">
    <div class="left-col">
        <small style="color:#0f0; margin-bottom:5px">RADAR (4x Range)</small>
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
            document.getElementById("o-lose").style.display = d.dead ? 'flex' : 'none';
            document.getElementById("o-win").style.display = d.win ? 'flex' : 'none';

            // INFO
            let p = d.player;
            document.getElementById("me-icon").innerText = p.icon;
            document.getElementById("me-name").innerText = p.name;
            document.getElementById("me-hp").innerText = p.hp + "/" + p.max;
            document.getElementById("cnt").innerText = d.total_bots;
            document.getElementById("wins").innerText = d.wins_count;

            // MAP
            let mh="";
            d.map.forEach(row => {
                row.forEach(c => mh+=`<div class='cell ${c.c}'>${c.s}</div>`);
            });
            let grid = document.getElementById("map");
            grid.innerHTML = mh;
            // 9x9 grid forced style
            grid.style.gridTemplateColumns = `repeat(${d.map[0].length}, 1fr)`;
            grid.style.gridTemplateRows = `repeat(${d.map.length}, 1fr)`;

            // STAGE (Enemies)
            let sh = "";
            if (d.bots.length === 0) sh = "<div style='color:#555'>השטח נקי... תמשיך לזוז.</div>";
            else {
                d.bots.forEach(b => {
                    sh += `<div class="card">
                        <div style="font-size:30px;">${b.icon}</div>
                        <div style="font-weight:bold; font-size:12px;">${b.name}</div>
                        <div style="color:#aaa; font-size:10px;">${b.type}</div>
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
