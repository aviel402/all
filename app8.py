import random
import uuid
import math
from flask import Flask, render_template_string, request, jsonify, session, url_for

app = Flask(__name__)
# מפתח קבוע כדי למנוע ניתוקים באמצע משחק
app.secret_key = 'arena_fixed_stable_v20'

# ==========================================
# 🧬 מאגר גופים עצום (20+ סוגים)
# ==========================================
HOSTS = {
    # חלשים
    "blob":    {"name": "עיסה", "icon": "🦠", "hp": 25, "atk": 4},
    "fly":     {"name": "זבוב", "icon": "🪰", "hp": 10, "atk": 1},
    "rat":     {"name": "עכברוש", "icon": "🐀", "hp": 35, "atk": 6},
    "spider":  {"name": "עכביש", "icon": "🕷️", "hp": 30, "atk": 8},

    # לוחמים
    "soldier": {"name": "חייל", "icon": "👮", "hp": 100, "atk": 15},
    "wolf":    {"name": "זאב", "icon": "🐺", "hp": 70, "atk": 12},
    "ninja":   {"name": "נינג'ה", "icon": "🥷", "hp": 60, "atk": 25},
    "alien":   {"name": "חייזר", "icon": "👽", "hp": 90, "atk": 18},
    "boxer":   {"name": "מתאגרף", "icon": "🥊", "hp": 120, "atk": 14},

    # כבדים
    "robot":   {"name": "רובוט", "icon": "🤖", "hp": 150, "atk": 22},
    "tank":    {"name": "טנק", "icon": "🚜", "hp": 250, "atk": 10},
    "demon":   {"name": "שד", "icon": "👺", "hp": 180, "atk": 28},

    # בוסים
    "dragon":  {"name": "דרקון", "icon": "🐲", "hp": 400, "atk": 50},
    "rex":     {"name": "דינוזאור", "icon": "🦖", "hp": 350, "atk": 45}
}

BOT_PREFIX = ["סוכן", "לוחם", "צייד", "צל", "מחסל", "טורף", "שומר", "גלאי"]

# ==========================================
# ⚙️ מנוע יציב (STABLE ENGINE)
# ==========================================
class Engine:
    def __init__(self, state=None):
        if not state or "wins" not in state:
            self.state = {
                "wins": 0,
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
        self.state["host"] = "soldier" # מתחילים חזק כדי לשרוד
        self.state["hp"] = 100
        self.state["max_hp"] = 100
        
        # אתחול עולם
        self.state["map_bound"] = 15 # גודל -15 עד 15
        self.state["rivals"] = [] # רשימת בוטים
        self.state["corpses"] = {} # גופות: מפתח "x,y"
        self.state["visited"] = ["0,0"]
        
        self.state["game_over"] = False
        self.state["won_match"] = False
        
        bot_count = 75 # כמות הבוטים
        self.state["log"] = [{"text": f"הקרב מתחיל! {bot_count} אויבים במפה.", "type": "gold"}]

        types = list(HOSTS.keys())
        for i in range(bot_count):
            h_type = random.choice(types)
            # סיכוי קטן מאוד לבוסים בהתחלה
            if HOSTS[h_type]["hp"] > 200 and random.random() > 0.1: h_type = "rat"

            bx = random.randint(-15, 15)
            by = random.randint(-15, 15)
            # וודא שהבוט לא מתחיל על השחקן
            if bx==0 and by==0: bx=5

            bot = {
                "id": str(uuid.uuid4()), # מזהה ייחודי קריטי למניעת באגים
                "name": f"{random.choice(BOT_PREFIX)}-{random.randint(10,99)}",
                "host": h_type,
                "hp": HOSTS[h_type]["hp"],
                "max": HOSTS[h_type]["hp"],
                "atk": HOSTS[h_type]["atk"],
                "x": bx,
                "y": by
            }
            self.state["rivals"].append(bot)

    # === AI System ===
    def process_turn(self):
        if self.state["game_over"]: return

        px, py = self.state["x"], self.state["y"]
        next_generation = []
        loc_map = {} # מיפוי מי נמצא איפה

        # 1. תזוזת בוטים
        for bot in self.state["rivals"]:
            # אם הבוט קרוב לשחקן (3 צעדים), הוא רודף
            dx = 0; dy = 0
            if abs(bot["x"]-px) <= 4 and abs(bot["y"]-py) <= 4:
                dx = 1 if bot["x"] < px else (-1 if bot["x"] > px else 0)
                dy = 1 if bot["y"] < py else (-1 if bot["y"] > py else 0)
            else:
                dx = random.choice([-1,0,1])
                dy = random.choice([-1,0,1])
            
            # וידוא גבולות מפה לבוט
            bot["x"] = max(-15, min(15, bot["x"] + dx))
            bot["y"] = max(-15, min(15, bot["y"] + dy))
            
            # קיבוץ לפי מיקומים לקרבות
            k = self.pos_key(bot["x"], bot["y"])
            if k not in loc_map: loc_map[k] = []
            loc_map[k].append(bot)

        # 2. קרבות בחדרים
        for pos, bots in loc_map.items():
            
            # א. האם השחקן בחדר הזה?
            if pos == self.pos_key(px, py):
                for b in bots:
                    # בוט תוקף שחקן
                    dmg = b["atk"] + random.randint(-2, 2)
                    self.state["hp"] -= max(1, dmg)
                    self.log(f"⚔️ {b['name']} ({HOSTS[b['host']]['name']}) תקף אותך! -{dmg}❤️", "danger")
            
            # ב. קרב בין בוטים (רק 2 נלחמים בכל פעם)
            if len(bots) > 1:
                atkr = bots[0]
                trgt = bots[1]
                trgt["hp"] -= atkr["atk"] # התקפה
                
                # אם יעד מת -> הופך לגופה, נמחק מרשימת החיים
                if trgt["hp"] <= 0:
                    self.state["corpses"][pos] = {"type": trgt["host"], "max": trgt["max"]}
                    # בוט מת לא נכנס לרשימה הבאה (next_generation)
                    trgt["dead_flag"] = True # מסמנים למחיקה

        # 3. סינון מתים ויצירת רשימה מעודכנת
        for bot in self.state["rivals"]:
            if bot.get("dead_flag"): continue # בוט שמת בתור הזה
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

    # === פעולות ===
    
    def move(self, dx, dy):
        if self.state["game_over"]: return
        
        # בדיקת גבולות לשחקן
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
        # מקבל ID במקום אינדקס כדי למנוע טעויות בזיהוי!
        if self.state["game_over"]: return
        
        px, py = self.state["x"], self.state["y"]
        
        # מציאת הבוט ברשימה לפי ה-ID
        target = next((b for b in self.state["rivals"] if b["id"] == bot_id), None)
        
        if not target:
            self.log("המטרה ברחה או מתה.", "sys")
            return
            
        # בדיקה שהוא איתי בחדר
        if target["x"] != px or target["y"] != py:
            self.log("המטרה רחוקה מדי.", "sys")
            return

        # ביצוע התקפה
        my_atk = HOSTS[self.state["host"]]["atk"]
        dmg = my_atk + random.randint(0, 5)
        target["hp"] -= dmg
        self.log(f"פגעת ב-{target['name']} (-{dmg})", "success")
        
        if target["hp"] <= 0:
            self.log(f"💀 חיסלת את {target['name']}!", "gold")
            # הופך לגופה
            self.state["corpses"][self.pos_key(px, py)] = {
                "type": target["host"],
                "max": target["max"]
            }
            # מוחק אותו מרשימת הבוטים
            self.state["rivals"].remove(target)
        
        self.process_turn()

    def swap_body(self):
        if self.state["game_over"]: return
        
        pos = self.pos_key(self.state["x"], self.state["y"])
        if pos not in self.state["corpses"]: return
        
        corpse = self.state["corpses"][pos]
        
        self.state["host"] = corpse["type"]
        self.state["max_hp"] = corpse["max"]
        self.state["hp"] = corpse["max"] # ריפוי מלא!
        
        del self.state["corpses"][pos]
        self.log(f"🧬 השתלת תודעה ל-{HOSTS[corpse['type']]['name']}.", "success")
        
        self.process_turn()

    # === ממשק ===
    def get_ui(self):
        px, py = self.state["x"], self.state["y"]
        
        # 1. יצירת מפה (4x4 = 9 משבצות רוחב)
        grid = []
        for dy in range(4, -5, -1):
            row = []
            for dx in range(-4, 5):
                tx, ty = px+dx, py+dy
                k = self.pos_key(tx, ty)
                
                cls = "fog"
                txt = ""
                
                # גבולות עולם
                if tx < -15 or tx > 15 or ty < -15 or ty > 15:
                    cls = "wall"
                    txt = "🧱"
                
                # שחקן
                elif dx==0 and dy==0:
                    cls = "me"
                    txt = "🤠"
                
                # אזור מוכר או קרוב
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

        # 2. אויבים בחדר
        room_bots = []
        for b in self.state["rivals"]:
            if b["x"] == px and b["y"] == py:
                room_bots.append({
                    "id": b["id"], # שולחים ID לדפדפן כדי שהתקיפה תהיה מדוייקת
                    "name": b["name"],
                    "host_name": HOSTS[b["host"]]["name"],
                    "icon": HOSTS[b["host"]]["icon"],
                    "hp": b["hp"], "max": b["max"]
                })
        
        # 3. גופה בחדר
        corpse = None
        if self.pos_key(px,py) in self.state["corpses"]:
            c = self.state["corpses"][self.pos_key(px,py)]
            corpse = {
                "name": HOSTS[c["type"]]["name"],
                "icon": HOSTS[c["type"]]["icon"],
                "max": c["max"]
            }

        return {
            "map": grid,
            "log": self.state["log"],
            "player": {
                "name": HOSTS[self.state["host"]]["name"],
                "icon": HOSTS[self.state["host"]]["icon"],
                "hp": self.state["hp"], "max": self.state["max_hp"]
            },
            "room_bots": room_bots,
            "room_corpse": corpse,
            "game_state": {
                "over": self.state["game_over"],
                "win": self.state["won_match"],
                "rivals_left": len(self.state["rivals"]),
                "wins": self.state["wins"]
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
    try: eng = Engine(session.get("dm_fix"))
    except: eng = Engine(None)
    
    req = request.json
    a = req.get("a")
    v = req.get("v")
    
    if a=="start": eng = Engine(None) # Hard reset
    elif a=="next": eng.start_match() # New round
    elif a=="move": eng.move(*v)
    elif a=="atk": eng.attack(v) # v is now the ID string
    elif a=="swap": eng.swap_body()
    
    session["dm_fix"] = eng.state
    return jsonify(eng.get_ui())

# ==========================================
# UI
# ==========================================
HTML = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Arena Deathmatch</title>
<style>
    * { box-sizing:border-box; user-select:none;}
    body { background:#0a0a0a; color:#ccc; margin:0; height:100vh; display:flex; flex-direction:column; font-family:sans-serif; overflow:hidden;}
    
    /* HUD */
    .top { height:60px; background:#111; border-bottom:1px solid #333; display:flex; justify-content:space-between; align-items:center; padding:0 15px;}
    .badge { background:#222; padding:5px 10px; border-radius:4px; font-weight:bold;}
    
    /* Layout */
    .mid { flex:1; display:flex; overflow:hidden;}
    .side { width:220px; background:#0e0e0e; border-left:1px solid #333; padding:10px; display:flex; flex-direction:column; align-items:center;}
    .stage { flex:1; padding:20px; overflow-y:auto; display:flex; flex-wrap:wrap; align-content:flex-start; justify-content:center; gap:10px; background: radial-gradient(#222, #000);}
    
    /* Map Grid */
    .grid { display:grid; grid-template-columns:repeat(9, 1fr); gap:1px; background:#222; border:1px solid #444; width:200px; height:200px;}
    .cell { width:100%; aspect-ratio:1; background:#000; display:flex; align-items:center; justify-content:center; font-size:10px;}
    .me { background:#0a0; box-shadow:0 0 5px lime; z-index:2;}
    .danger { background:#a00; }
    .loot { background:#a80; color:black;}
    .wall { background:#400; }
    
    /* Entities */
    .card { width:110px; height:140px; background:#1a1a1a; border:1px solid #444; border-radius:6px; display:flex; flex-direction:column; align-items:center; padding:5px; text-align:center;}
    .c-icon { font-size:35px;}
    .btn-kill { width:100%; margin-top:auto; background:#800; border:none; color:white; padding:5px; border-radius:4px; cursor:pointer;}
    .btn-swap { width:100%; margin-top:auto; background:gold; border:none; color:black; font-weight:bold; padding:8px; border-radius:4px; cursor:pointer;}
    
    /* Logs & Controls */
    .log-panel { height:120px; background:#000; border-top:1px solid #333; padding:10px; overflow-y:auto; font-size:13px; font-family:monospace;}
    .l-g{color:gold} .l-r{color:#f55} .l-s{color:#5f5}
    
    .control-panel { height:130px; background:#151515; display:grid; grid-template-columns: 1fr 160px 1fr; align-items:center; padding:0 20px;}
    .dpad { display:grid; grid-template-columns:repeat(3,1fr); gap:5px; direction:ltr; width:120px; margin:0 auto;}
    .mov { height:35px; background:#333; color:white; border:1px solid #555; border-radius:4px; font-size:18px; cursor:pointer;}
    .mov:active { background:#555;}
    .u{grid-column:2} .l{grid-row:2} .r{grid-row:2} .d{grid-row:2}
    
    /* Modal */
    .modal { position:fixed; inset:0; background:rgba(0,0,0,0.9); z-index:99; display:none; flex-direction:column; align-items:center; justify-content:center;}
    .big-btn { padding:15px 30px; font-size:22px; cursor:pointer; margin-top:20px; font-weight:bold;}
</style>
</head>
<body>

<div id="m-over" class="modal">
    <h1 style="color:red; font-size:60px">GAME OVER</h1>
    <button class="big-btn" style="background:red; border:none;" onclick="api('start')">נסה שוב</button>
</div>

<div id="m-win" class="modal">
    <h1 style="color:gold; font-size:60px">🏆 VICTORY</h1>
    <button class="big-btn" style="background:gold; border:none;" onclick="api('next')">קרב הבא</button>
</div>

<div class="top">
    <div style="display:flex; align-items:center; gap:10px;">
        <span style="font-size:30px" id="p-ico"></span>
        <div>
            <div id="p-name" style="font-weight:bold"></div>
            <div style="font-size:12px; color:#f66">HP: <span id="p-hp"></span></div>
        </div>
    </div>
    <div class="badge">בוטים נותרו: <span id="cnt" style="color:red"></span></div>
</div>

<div class="mid">
    <div class="side">
        <small style="color:lime">RADAR 9x9</small>
        <div class="grid" id="map"></div>
    </div>
    <div class="stage" id="room"></div>
</div>

<div class="log-panel" id="log"></div>

<div class="control-panel">
    <button onclick="api('start')" style="background:#400; border:none; color:salmon; padding:5px;">Restart</button>
    <div class="dpad">
        <button class="mov u" onclick="api('move',[0,1])">⬆</button>
        <button class="mov l" onclick="api('move',[-1,0])">⬅</button>
        <button class="mov d" onclick="api('move',[0,-1])">⬇</button>
        <button class="mov r" onclick="api('move',[1,0])">➡</button>
    </div>
    <div></div>
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
    document.getElementById("cnt").innerText=d.game_state.rivals_left;
    
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
        sh+=`<div class="card">
            <div class="c-icon">${b.icon}</div>
            <div style="font-size:12px;font-weight:bold">${b.name}</div>
            <div style="color:#aaa;font-size:10px">${b.host_name}</div>
            <div style="color:#f55;font-size:12px">${b.hp}/${b.max} HP</div>
            <button class="btn-kill" onclick="api('atk','${b.id}')">תקוף</button>
        </div>`;
    });
    
    if(d.room_corpse){
        let c=d.room_corpse;
        sh+=`<div class="card" style="border-color:gold">
            <div class="c-icon">${c.icon}</div>
            <div style="color:gold">${c.name}</div>
            <div style="font-size:10px">(גופה)</div>
            <button class="btn-swap" onclick="api('swap')">♻️ החלף</button>
        </div>`;
    }
    document.getElementById("room").innerHTML=sh;
    
    // Log
    let lh="";
    d.log.slice().reverse().forEach(l=>{
        let c = l.type=='danger'?'l-r':(l.type=='gold'?'l-g':(l.type=='success'?'l-s':''));
        lh+=`<div class="msg ${c}">> ${l.text}</div>`;
    });
    document.getElementById("log").innerHTML=lh;
}

window.onkeydown=e=>{
    if(e.key=="ArrowUp")api('move',[0,1]);
    if(e.key=="ArrowDown")api('move',[0,-1]);
    if(e.key=="ArrowLeft")api('move',[-1,0]);
    if(e.key=="ArrowRight")api('move',[1,0]);
}
</script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(port=5006, debug=True)
