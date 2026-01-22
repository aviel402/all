import random
import uuid
import math
import time
from flask import Flask, render_template_string, request, jsonify, session, url_for

app = Flask(__name__)
app.secret_key = 'parasite_enhanced_v30'

# ==========================================
# 🧬 מאגר גופים עצום (20+ סוגים)
# ==========================================
HOSTS = {
    # חלשים
    "blob":    {"name": "עיסה", "icon": "🦠", "hp": 25, "atk": 4, "tier": 1},
    "fly":     {"name": "זבוב", "icon": "🪰", "hp": 10, "atk": 1, "tier": 1},
    "rat":     {"name": "עכברוש", "icon": "🐀", "hp": 35, "atk": 6, "tier": 1},
    "spider":  {"name": "עכביש", "icon": "🕷️", "hp": 30, "atk": 8, "tier": 1},

    # לוחמים
    "soldier": {"name": "חייל", "icon": "👮", "hp": 100, "atk": 15, "tier": 2},
    "wolf":    {"name": "זאב", "icon": "🐺", "hp": 70, "atk": 12, "tier": 2},
    "ninja":   {"name": "נינג'ה", "icon": "🥷", "hp": 60, "atk": 25, "tier": 2},
    "alien":   {"name": "חייזר", "icon": "👽", "hp": 90, "atk": 18, "tier": 2},
    "boxer":   {"name": "מתאגרף", "icon": "🥊", "hp": 120, "atk": 14, "tier": 2},

    # כבדים
    "robot":   {"name": "רובוט", "icon": "🤖", "hp": 150, "atk": 22, "tier": 3},
    "tank":    {"name": "טנק", "icon": "🚜", "hp": 250, "atk": 10, "tier": 3},
    "demon":   {"name": "שד", "icon": "👺", "hp": 180, "atk": 28, "tier": 3},

    # בוסים
    "dragon":  {"name": "דרקון", "icon": "🐲", "hp": 400, "atk": 50, "tier": 4},
    "rex":     {"name": "דינוזאור", "icon": "🦖", "hp": 350, "atk": 45, "tier": 4}
}

BOT_PREFIX = ["סוכן", "לוחם", "צייד", "צל", "מחסל", "טורף", "שומר", "גלאי"]

# ==========================================
# ⚙️ מנוע משופר
# ==========================================
class Engine:
    def __init__(self, state=None):
        if not state or "wins" not in state:
            self.state = {
                "wins": 0,
                "total_kills": 0,
                "total_possessions": 0,
                "game_over": False
            }
            self.start_match()
        else:
            self.state = state

    def log(self, t, type="game"): 
        self.state["log"].append({"text": t, "type": type})
        if len(self.state["log"]) > 30: self.state["log"].pop(0)

    def pos_key(self, x, y): return f"{x},{y}"

    def start_match(self):
        # אתחול שחקן
        self.state["x"] = 0
        self.state["y"] = 0
        self.state["host"] = "soldier"
        self.state["hp"] = 100
        self.state["max_hp"] = 100
        
        # אתחול עולם
        self.state["map_bound"] = 15
        self.state["rivals"] = []
        self.state["corpses"] = {}
        self.state["visited"] = ["0,0"]
        
        self.state["game_over"] = False
        self.state["won_match"] = False
        
        # Stats למשחק הנוכחי
        self.state["match_kills"] = 0
        self.state["match_possessions"] = 0
        self.state["start_time"] = time.time()
        self.state["damage_dealt"] = 0
        self.state["damage_taken"] = 0
        
        bot_count = 75
        self.state["log"] = [{"text": f"הקרב מתחיל! {bot_count} אויבים במפה.", "type": "gold"}]

        types = list(HOSTS.keys())
        for i in range(bot_count):
            h_type = random.choice(types)
            if HOSTS[h_type]["hp"] > 200 and random.random() > 0.1: h_type = "rat"

            bx = random.randint(-15, 15)
            by = random.randint(-15, 15)
            if bx==0 and by==0: bx=5

            bot = {
                "id": str(uuid.uuid4()),
                "name": f"{random.choice(BOT_PREFIX)}-{random.randint(10,99)}",
                "host": h_type,
                "hp": HOSTS[h_type]["hp"],
                "max": HOSTS[h_type]["hp"],
                "atk": HOSTS[h_type]["atk"],
                "x": bx,
                "y": by
            }
            self.state["rivals"].append(bot)

    def process_turn(self):
        if self.state["game_over"]: return

        px, py = self.state["x"], self.state["y"]
        next_generation = []
        loc_map = {}

        # 1. תזוזת בוטים (חכמים יותר)
        for bot in self.state["rivals"]:
            dx = 0; dy = 0
            distance_to_player = abs(bot["x"]-px) + abs(bot["y"]-py)
            
            # בוטים חזקים רודפים ממרחק רחוק יותר
            chase_range = 4 if HOSTS[bot["host"]]["tier"] <= 2 else 6
            
            if distance_to_player <= chase_range:
                dx = 1 if bot["x"] < px else (-1 if bot["x"] > px else 0)
                dy = 1 if bot["y"] < py else (-1 if bot["y"] > py else 0)
            else:
                dx = random.choice([-1,0,1])
                dy = random.choice([-1,0,1])
            
            bot["x"] = max(-15, min(15, bot["x"] + dx))
            bot["y"] = max(-15, min(15, bot["y"] + dy))
            
            k = self.pos_key(bot["x"], bot["y"])
            if k not in loc_map: loc_map[k] = []
            loc_map[k].append(bot)

        # 2. קרבות בחדרים
        for pos, bots in loc_map.items():
            
            if pos == self.pos_key(px, py):
                for b in bots:
                    dmg = b["atk"] + random.randint(-2, 2)
                    self.state["hp"] -= max(1, dmg)
                    self.state["damage_taken"] += max(1, dmg)
                    self.log(f"⚔️ {b['name']} ({HOSTS[b['host']]['name']}) תקף אותך! -{dmg}❤️", "danger")
            
            if len(bots) > 1:
                atkr = bots[0]
                trgt = bots[1]
                trgt["hp"] -= atkr["atk"]
                
                if trgt["hp"] <= 0:
                    self.state["corpses"][pos] = {"type": trgt["host"], "max": trgt["max"]}
                    trgt["dead_flag"] = True

        # 3. סינון מתים
        for bot in self.state["rivals"]:
            if bot.get("dead_flag"): continue
            next_generation.append(bot)
        
        self.state["rivals"] = next_generation

        # 4. בדיקת סטטוס שחקן
        if self.state["hp"] <= 0:
            self.state["hp"] = 0
            self.state["game_over"] = True
            self.state["won_match"] = False
            self.log("💀 מתת בקרב. המשחק נגמר.", "critical")

        # 5. בדיקת ניצחון
        if len(self.state["rivals"]) == 0:
            self.state["game_over"] = True
            self.state["won_match"] = True
            self.state["wins"] += 1
            self.log("👑 האלוף! חיסלת את כל היריבים.", "gold")

    def move(self, dx, dy):
        if self.state["game_over"]: return
        
        nx = self.state["x"] + dx
        ny = self.state["y"] + dy
        if nx < -15 or nx > 15 or ny < -15 or ny > 15:
            self.log("הגעת לקיר הזירה.", "sys")
            return

        self.state["x"] = nx
        self.state["y"] = ny
        
        pk = self.pos_key(nx, ny)
        if pk not in self.state["visited"]: self.state["visited"].append(pk)
        
        self.process_turn()

    def attack(self, bot_id):
        if self.state["game_over"]: return
        
        px, py = self.state["x"], self.state["y"]
        target = next((b for b in self.state["rivals"] if b["id"] == bot_id), None)
        
        if not target:
            self.log("המטרה ברחה או מתה.", "sys")
            return
            
        if target["x"] != px or target["y"] != py:
            self.log("המטרה רחוקה מדי.", "sys")
            return

        my_atk = HOSTS[self.state["host"]]["atk"]
        dmg = my_atk + random.randint(0, 5)
        target["hp"] -= dmg
        self.state["damage_dealt"] += dmg
        self.log(f"פגעת ב-{target['name']} (-{dmg})", "success")
        
        if target["hp"] <= 0:
            self.state["match_kills"] += 1
            self.state["total_kills"] += 1
            self.log(f"💀 חיסלת את {target['name']}!", "gold")
            self.state["corpses"][self.pos_key(px, py)] = {
                "type": target["host"],
                "max": target["max"]
            }
            self.state["rivals"].remove(target)
        
        self.process_turn()

    def swap_body(self):
        if self.state["game_over"]: return
        
        pos = self.pos_key(self.state["x"], self.state["y"])
        if pos not in self.state["corpses"]: return
        
        corpse = self.state["corpses"][pos]
        
        self.state["host"] = corpse["type"]
        self.state["max_hp"] = corpse["max"]
        self.state["hp"] = corpse["max"]
        self.state["match_possessions"] += 1
        self.state["total_possessions"] += 1
        
        del self.state["corpses"][pos]
        self.log(f"🧬 השתלת תודעה ל-{HOSTS[corpse['type']]['name']}.", "success")
        
        self.process_turn()

    def get_ui(self):
        px, py = self.state["x"], self.state["y"]
        
        # מפה
        grid = []
        for dy in range(4, -5, -1):
            row = []
            for dx in range(-4, 5):
                tx, ty = px+dx, py+dy
                k = self.pos_key(tx, ty)
                
                cls = "fog"
                txt = ""
                
                if tx < -15 or tx > 15 or ty < -15 or ty > 15:
                    cls = "wall"
                    txt = "🧱"
                elif dx==0 and dy==0:
                    cls = "me"
                    txt = "🤠"
                elif k in self.state["visited"] or (abs(dx)<=2 and abs(dy)<=2):
                    bots_here = [b for b in self.state["rivals"] if b["x"]==tx and b["y"]==ty]
                    if bots_here:
                        cls = "danger"
                        txt = "👹"
                    elif k in self.state["corpses"]:
                        cls = "loot"
                        txt = "⚰️"
                    else:
                        cls = "empty"
                        txt = "·"
                        
                row.append({"c":cls, "t":txt})
            grid.append(row)

        # אויבים בחדר
        room_bots = []
        for b in self.state["rivals"]:
            if b["x"] == px and b["y"] == py:
                room_bots.append({
                    "id": b["id"],
                    "name": b["name"],
                    "host_name": HOSTS[b["host"]]["name"],
                    "icon": HOSTS[b["host"]]["icon"],
                    "hp": b["hp"], "max": b["max"],
                    "atk": b["atk"],
                    "tier": HOSTS[b["host"]]["tier"]
                })
        
        # גופה בחדר
        corpse = None
        if self.pos_key(px,py) in self.state["corpses"]:
            c = self.state["corpses"][self.pos_key(px,py)]
            corpse = {
                "name": HOSTS[c["type"]]["name"],
                "icon": HOSTS[c["type"]]["icon"],
                "max": c["max"],
                "atk": HOSTS[c["type"]]["atk"],
                "tier": HOSTS[c["type"]]["tier"]
            }

        # חישוב זמן משחק
        survival_time = int(time.time() - self.state.get("start_time", time.time()))

        return {
            "map": grid,
            "log": self.state["log"],
            "player": {
                "name": HOSTS[self.state["host"]]["name"],
                "icon": HOSTS[self.state["host"]]["icon"],
                "hp": self.state["hp"], "max": self.state["max_hp"],
                "atk": HOSTS[self.state["host"]]["atk"]
            },
            "room_bots": room_bots,
            "room_corpse": corpse,
            "game_state": {
                "over": self.state["game_over"],
                "win": self.state["won_match"],
                "rivals_left": len(self.state["rivals"]),
                "wins": self.state["wins"]
            },
            "stats": {
                "kills": self.state["match_kills"],
                "possessions": self.state["match_possessions"],
                "survival_time": survival_time,
                "damage_dealt": self.state["damage_dealt"],
                "damage_taken": self.state["damage_taken"],
                "total_kills": self.state["total_kills"],
                "total_possessions": self.state["total_possessions"]
            }
        }

# ==========================================
# APP SETUP
# ==========================================
@app.route("/")
def idx():
    if "uid" not in session: session["uid"] = str(uuid.uuid4())
    return render_template_string(HTML, api=url_for("handle_act"))

@app.route("/api", methods=["POST"])
def handle_act():
    try: eng = Engine(session.get("dm_enhanced"))
    except: eng = Engine(None)
    
    req = request.json
    a = req.get("a")
    v = req.get("v")
    
    if a=="start": eng = Engine(None)
    elif a=="next": eng.start_match()
    elif a=="move": eng.move(*v)
    elif a=="atk": eng.attack(v)
    elif a=="swap": eng.swap_body()
    
    session["dm_enhanced"] = eng.state
    return jsonify(eng.get_ui())

# ==========================================
# UI משופר
# ==========================================
HTML = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>🦠 Parasite Arena</title>
<link href="https://fonts.googleapis.com/css2?family=Heebo:wght@300;500;700&display=swap" rel="stylesheet">
<style>
    * { box-sizing:border-box; user-select:none; margin:0; padding:0;}
    body { 
        background: linear-gradient(135deg, #0a0a0a 0%, #1a0a1a 100%); 
        color:#eee; 
        height:100vh; 
        display:flex; 
        flex-direction:column; 
        font-family:'Heebo', sans-serif; 
        overflow:hidden;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }

    @keyframes pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.05); }
    }

    @keyframes glow {
        0%, 100% { box-shadow: 0 0 10px rgba(0,255,136,0.3); }
        50% { box-shadow: 0 0 20px rgba(0,255,136,0.6); }
    }
    
    /* HUD */
    .top { 
        height:70px; 
        background: linear-gradient(135deg, #111 0%, #1a1a2e 100%); 
        border-bottom:2px solid #00ff88; 
        display:flex; 
        justify-content:space-between; 
        align-items:center; 
        padding:0 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.5);
    }
    .player-info {
        display:flex;
        align-items:center;
        gap:15px;
        animation: fadeIn 0.5s ease-out;
    }
    .badge { 
        background: linear-gradient(135deg, #222 0%, #333 100%); 
        padding:8px 16px; 
        border-radius:20px; 
        font-weight:700;
        border: 1px solid #444;
    }
    
    /* Layout */
    .mid { flex:1; display:flex; overflow:hidden;}
    .side { 
        width:280px; 
        background: linear-gradient(180deg, #0e0e0e 0%, #1a0a1a 100%); 
        border-left:2px solid #333; 
        padding:15px; 
        display:flex; 
        flex-direction:column; 
        gap:15px;
        overflow-y: auto;
    }
    .stage { 
        flex:1; 
        padding:20px; 
        overflow-y:auto; 
        display:flex; 
        flex-wrap:wrap; 
        align-content:flex-start; 
        justify-content:center; 
        gap:15px; 
        background: radial-gradient(circle at center, #1a1a2e 0%, #0a0a0a 100%);
    }
    
    /* Stats Panel */
    .stats-panel {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #00ff8844;
        animation: fadeIn 0.6s ease-out;
    }
    .stat-row {
        display: flex;
        justify-content: space-between;
        padding: 6px 0;
        border-bottom: 1px solid #ffffff11;
        font-size: 13px;
    }
    .stat-row:last-child { border-bottom: none; }
    .stat-label { color: #aaa; }
    .stat-value { color: #00ff88; font-weight: 700; }
    
    /* Map Grid */
    .grid { 
        display:grid; 
        grid-template-columns:repeat(9, 1fr); 
        gap:2px; 
        background: linear-gradient(135deg, #222 0%, #333 100%); 
        border:2px solid #444; 
        border-radius: 8px;
        padding: 4px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.5);
    }
    .cell { 
        width:100%; 
        aspect-ratio:1; 
        background:#0a0a0a; 
        display:flex; 
        align-items:center; 
        justify-content:center; 
        font-size:14px;
        border-radius: 3px;
        transition: all 0.2s;
    }
    .me { 
        background: linear-gradient(135deg, #00ff88 0%, #00aa55 100%); 
        animation: glow 2s infinite;
        z-index:2;
    }
    .danger { 
        background: linear-gradient(135deg, #ff3366 0%, #aa0033 100%); 
        animation: pulse 1s infinite;
    }
    .loot { 
        background: linear-gradient(135deg, #ffaa00 0%, #aa6600 100%); 
        color:black;
    }
    .wall { background:#200; }
    .empty { background:#0a0a0a; opacity: 0.5; }
    
    /* Health Bars */
    .hp-bar-container {
        width: 100%;
        height: 8px;
        background: #222;
        border-radius: 4px;
        overflow: hidden;
        margin-top: 5px;
        border: 1px solid #444;
    }
    .hp-bar {
        height: 100%;
        background: linear-gradient(90deg, #ff3366 0%, #ff6688 100%);
        transition: width 0.3s, background 0.3s;
        border-radius: 4px;
    }
    .hp-bar.high { background: linear-gradient(90deg, #00ff88 0%, #00ddaa 100%); }
    .hp-bar.mid { background: linear-gradient(90deg, #ffaa00 0%, #ffcc33 100%); }
    
    /* Entities */
    .card { 
        width:140px; 
        height:180px; 
        background: linear-gradient(135deg, #1a1a1a 0%, #2a2a2a 100%); 
        border:2px solid #444; 
        border-radius:12px; 
        display:flex; 
        flex-direction:column; 
        align-items:center; 
        padding:12px; 
        text-align:center;
        transition: all 0.3s;
        animation: fadeIn 0.4s ease-out;
        position: relative;
        overflow: hidden;
    }
    .card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0; height: 3px;
        background: linear-gradient(90deg, #ff3366 0%, #ffaa00 100%);
        opacity: 0;
        transition: 0.3s;
    }
    .card:hover::before { opacity: 1; }
    .card:hover { 
        transform: translateY(-5px); 
        border-color: #00ff88;
        box-shadow: 0 10px 30px rgba(0,255,136,0.3);
    }
    .card.corpse-card {
        border-color: #ffaa00;
    }
    .card.corpse-card::before {
        background: linear-gradient(90deg, #ffaa00 0%, #ff6600 100%);
        opacity: 1;
    }
    .c-icon { font-size:45px; margin: 10px 0;}
    .tier-badge {
        position: absolute;
        top: 8px;
        left: 8px;
        background: #000;
        color: #ffaa00;
        padding: 3px 8px;
        border-radius: 10px;
        font-size: 10px;
        font-weight: 700;
        border: 1px solid#ffaa00;
    }
    .btn-kill { 
        width:100%; 
        margin-top:auto; 
        background: linear-gradient(135deg, #ff3366 0%, #cc0033 100%); 
        border:none; 
        color:white; 
        padding:10px; 
        border-radius:8px; 
        cursor:pointer;
        font-weight: 700;
        transition: all 0.3s;
        font-family: inherit;
    }
    .btn-kill:hover { 
        background: linear-gradient(135deg, #ff5577 0%, #ff0033 100%); 
        transform: scale(1.05);
    }
    .btn-swap { 
        width:100%; 
        margin-top:auto; 
        background: linear-gradient(135deg, #ffaa00 0%, #ff8800 100%); 
        border:none; 
        color:black; 
        font-weight:700; 
        padding:10px; 
        border-radius:8px; 
        cursor:pointer;
        transition: all 0.3s;
        font-family: inherit;
    }
    .btn-swap:hover {
        background: linear-gradient(135deg, #ffcc33 0%, #ffaa00 100%);
        transform: scale(1.05);
    }
    
    /* Logs & Controls */
    .log-panel { 
        height:110px; 
        background: linear-gradient(135deg, #000 0%, #0a0a0a 100%); 
        border-top:2px solid #333; 
        padding:12px; 
        overflow-y:auto; 
        font-size:13px; 
        font-family:monospace;
    }
    .msg { 
        padding: 4px 0; 
        animation: fadeIn 0.3s ease-out;
    }
    .l-g{color:#ffaa00; font-weight: 700;} 
    .l-r{color:#ff5577;} 
    .l-s{color:#00ff88;}
    
    .control-panel { 
        height:140px; 
        background: linear-gradient(135deg, #151515 0%, #1a1a1a 100%); 
        display:grid; 
        grid-template-columns: 1fr 180px 1fr; 
        align-items:center; 
        padding:0 20px;
        border-top: 2px solid #333;
    }
    .dpad { 
        display:grid; 
        grid-template-columns:repeat(3,1fr); 
        gap:8px; 
        direction:ltr; 
        width:140px; 
        margin:0 auto;
    }
    .mov { 
        height:40px; 
        background: linear-gradient(135deg, #333 0%, #444 100%); 
        color:white; 
        border:2px solid #555; 
        border-radius:8px; 
        font-size:20px; 
        cursor:pointer;
        transition: all 0.2s;
        font-family: inherit;
    }
    .mov:hover { 
        background: linear-gradient(135deg, #555 0%, #666 100%);
        border-color: #00ff88;
    }
    .mov:active { transform: scale(0.95);}
    .u{grid-column:2} .l{grid-row:2} .r{grid-row:2} .d{grid-row:2}
    
    /* Modal */
    .modal { 
        position:fixed; 
        inset:0; 
        background:rgba(0,0,0,0.95); 
        z-index:99; 
        display:none; 
        flex-direction:column; 
        align-items:center; 
        justify-content:center;
        animation: fadeIn 0.3s ease-out;
    }
    .big-btn { 
        padding:15px 40px; 
        font-size:22px; 
        cursor:pointer; 
        margin-top:30px; 
        font-weight:700;
        border-radius: 12px;
        border: none;
        transition: all 0.3s;
        font-family: inherit;
    }
    .big-btn:hover { transform: scale(1.1); }

    /* Responsive */
    @media (max-width: 768px) {
        .side { width: 100%; border-left: none; border-top: 2px solid #333; }
        .mid { flex-direction: column-reverse; }
        .control-panel { grid-template-columns: 1fr; }
    }

    /* Scrollbar */
    ::-webkit-scrollbar { width: 8px; }
    ::-webkit-scrollbar-track { background: #111; }
    ::-webkit-scrollbar-thumb { background: #333; border-radius: 4px;}
    ::-webkit-scrollbar-thumb:hover { background: #555; }
</style>
</head>
<body>

<div id="m-over" class="modal">
    <h1 style="color:#ff3366; font-size:70px; text-shadow: 0 0 30px #ff3366;">💀 GAME OVER</h1>
    <button class="big-btn" style="background:linear-gradient(135deg, #ff3366 0%, #cc0033 100%); color:white;" onclick="api('start')">נסה שוב</button>
</div>

<div id="m-win" class="modal">
    <h1 style="color:#ffaa00; font-size:70px; text-shadow: 0 0 30px #ffaa00;">🏆 VICTORY</h1>
    <button class="big-btn" style="background:linear-gradient(135deg, #ffaa00 0%, #ff8800 100%); color:black;" onclick="api('next')">קרב הבא</button>
</div>

<div class="top">
    <div class="player-info">
        <span style="font-size:40px" id="p-ico"></span>
        <div>
            <div id="p-name" style="font-weight:700; font-size:18px;"></div>
            <div style="font-size:14px; color:#aaa">
                HP: <span id="p-hp" style="color:#ff5577; font-weight:700"></span> | 
                ATK: <span id="p-atk" style="color:#00ff88; font-weight:700"></span>
            </div>
            <div class="hp-bar-container">
                <div class="hp-bar" id="p-hp-bar"></div>
            </div>
        </div>
    </div>
    <div class="badge">אויבים: <span id="cnt" style="color:#ff5577"></span></div>
</div>

<div class="mid">
    <div class="side">
        <small style="color:#00ff88; text-align:center; font-weight:700">📡 RADAR</small>
        <div class="grid" id="map"></div>
        
        <div class="stats-panel">
            <div style="text-align:center; color:#00ff88; font-weight:700; margin-bottom:10px;">📊 STATS</div>
            <div class="stat-row">
                <span class="stat-label">Kills</span>
                <span class="stat-value" id="stat-kills">0</span>
            </div>
            <div class="stat-row">
                <span class="stat-label">Bodies Possessed</span>
                <span class="stat-value" id="stat-poss">0</span>
            </div>
            <div class="stat-row">
                <span class="stat-label">Survival Time</span>
                <span class="stat-value" id="stat-time">0s</span>
            </div>
            <div class="stat-row">
                <span class="stat-label">Damage Dealt</span>
                <span class="stat-value" id="stat-dmg-d">0</span>
            </div>
            <div class="stat-row">
                <span class="stat-label">Damage Taken</span>
                <span class="stat-value" id="stat-dmg-t">0</span>
            </div>
        </div>
    </div>
    <div class="stage" id="room"></div>
</div>

<div class="log-panel" id="log"></div>

<div class="control-panel">
    <button onclick="api('start')" style="background:linear-gradient(135deg, #400 0%, #600 100%); border:none; color:#ff8888; padding:12px; border-radius:8px; cursor:pointer; font-weight:700; font-family:inherit;">🔄 Restart</button>
    <div class="dpad">
        <button class="mov u" onclick="api('move',[0,1])">⬆</button>
        <button class="mov l" onclick="api('move',[-1,0])">⬅</button>
        <button class="mov d" onclick="api('move',[0,-1])">⬇</button>
        <button class="mov r" onclick="api('move',[1,0])">➡</button>
    </div>
    <div style="text-align:center; color:#666; font-size:12px;">Use Arrow Keys or WASD</div>
</div>

<script>
const API="{{ api }}";
window.onload=()=> api('');

async function api(act, val=null){
    let r=await fetch(API,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({a:act,v:val})});
    let d=await r.json();
    
    // Screens
    document.getElementById("m-over").style.display = d.game_state.over && !d.game_state.win ? 'flex' : 'none';
    document.getElementById("m-win").style.display = d.game_state.win ? 'flex' : 'none';
    
    // Header
    let p=d.player;
    document.getElementById("p-ico").innerText=p.icon;
    document.getElementById("p-name").innerText=p.name;
    document.getElementById("p-hp").innerText=p.hp+"/"+p.max;
    document.getElementById("p-atk").innerText=p.atk;
    document.getElementById("cnt").innerText=d.game_state.rivals_left;
    
    // HP Bar
    let hpPct = (p.hp / p.max) * 100;
    let hpBar = document.getElementById("p-hp-bar");
    hpBar.style.width = hpPct + "%";
    hpBar.className = "hp-bar " + (hpPct > 66 ? "high" : (hpPct > 33 ? "mid" : ""));
    
    // Stats
    document.getElementById("stat-kills").innerText = d.stats.kills;
    document.getElementById("stat-poss").innerText = d.stats.possessions;
    document.getElementById("stat-time").innerText = d.stats.survival_time + "s";
    document.getElementById("stat-dmg-d").innerText = d.stats.damage_dealt;
    document.getElementById("stat-dmg-t").innerText = d.stats.damage_taken;
    
    // Map
    let mh="";
    d.map.forEach(row=>{
        row.forEach(c=> mh+=`<div class='cell ${c.c}'>${c.t}</div>`);
    });
    document.getElementById("map").innerHTML=mh;
    
    // Room
    let sh="";
    if(d.room_bots.length===0 && !d.room_corpse) sh="<div style='color:#555'>אין אויבים כאן.</div>";
    
    d.room_bots.forEach(b=>{
        let tierColor = b.tier === 4 ? '#ff3366' : (b.tier === 3 ? '#ff8800' : (b.tier === 2 ? '#00ff88' : '#666'));
        sh+=`<div class="card">
            <div class="tier-badge" style="border-color:${tierColor}; color:${tierColor}">T${b.tier}</div>
            <div class="c-icon">${b.icon}</div>
            <div style="font-size:13px;font-weight:700">${b.name}</div>
            <div style="color:#aaa;font-size:11px">${b.host_name}</div>
            <div style="color:#ff5577;font-size:13px; font-weight:700">❤️ ${b.hp}/${b.max}</div>
            <div style="color:#00ff88;font-size:11px">⚔️ ATK: ${b.atk}</div>
            <button class="btn-kill" onclick="api('atk','${b.id}')">⚔️ תקוף</button>
        </div>`;
    });
    
    if(d.room_corpse){
        let c=d.room_corpse;
        let tierColor = c.tier === 4 ? '#ff3366' : (c.tier === 3 ? '#ff8800' : (c.tier === 2 ? '#00ff88' : '#666'));
        sh+=`<div class="card corpse-card">
            <div class="tier-badge" style="border-color:${tierColor}; color:${tierColor}">T${c.tier}</div>
            <div class="c-icon">${c.icon}</div>
            <div style="color:#ffaa00; font-weight:700">${c.name}</div>
            <div style="font-size:11px; color:#888">(גופה)</div>
            <div style="color:#00ff88;font-size:12px; margin-top:5px">⚔️ ATK: ${c.atk}</div>
            <div style="color:#ff8888;font-size:12px">❤️ HP: ${c.max}</div>
            <button class="btn-swap" onclick="api('swap')">♻️ החלף גוף</button>
        </div>`;
    }
    document.getElementById("room").innerHTML=sh;
    
    // Log
    let lh="";
    d.log.slice().reverse().forEach(l=>{
        let c = l.type=='danger'?'l-r':(l.type=='gold'?'l-g':(l.type=='success'?'l-s':''));
        lh+=`<div class="msg ${c}">› ${l.text}</div>`;
    });
    document.getElementById("log").innerHTML=lh;
}

window.onkeydown=e=>{
    if(e.key=="ArrowUp" || e.key=="w" || e.key=="W") api('move',[0,1]);
    if(e.key=="ArrowDown" || e.key=="s" || e.key=="S") api('move',[0,-1]);
    if(e.key=="ArrowLeft" || e.key=="a" || e.key=="A") api('move',[-1,0]);
    if(e.key=="ArrowRight" || e.key=="d" || e.key=="D") api('move',[1,0]);
}
</script>
</body>
</html>
"""

if __name__ == "__main__":
    print("🦠 Parasite Arena Enhanced Running at http://localhost:5006")
    print("✨ Use Arrow Keys or WASD to move")
    app.run(port=5006, debug=True)
