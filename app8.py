import random
import uuid
from flask import Flask, render_template_string, request, jsonify, session, url_for

app = Flask(__name__)
app.secret_key = 'royale_deathmatch_hardcore_v13'

# ==========================================
# 🧬 מאגר הלוחמים (המורחב)
# ==========================================
HOSTS = {
    # קלים
    "blob":    {"name": "עיסה", "icon": "🦠", "hp": 30, "atk": 4},
    "rat":     {"name": "עכברוש", "icon": "🐀", "hp": 40, "atk": 6},
    "scout":   {"name": "סייר", "icon": "🔫", "hp": 50, "atk": 8},
    
    # בינוניים
    "knight":  {"name": "אביר", "icon": "🛡️", "hp": 100, "atk": 15},
    "sniper":  {"name": "צלף", "icon": "🔭", "hp": 70, "atk": 25},
    "alien":   {"name": "חייזר", "icon": "👽", "hp": 90, "atk": 18},
    
    # כבדים
    "tank":    {"name": "טנק", "icon": "🚜", "hp": 200, "atk": 10},
    "demon":   {"name": "שד", "icon": "😈", "hp": 150, "atk": 25},
    "cyborg":  {"name": "קיבורג", "icon": "🤖", "hp": 120, "atk": 22},
    
    # בוסים
    "dragon":  {"name": "דרקון", "icon": "🐲", "hp": 300, "atk": 40},
    "titan":   {"name": "טיטאן", "icon": "🗿", "hp": 400, "atk": 30}
}

BOT_NAMES = ["קילר", "נינג'ה", "הצל", "וייפר", "גולגולת", "פנטום", "בלאק", "זאוס", "המשמיד"]

# ==========================================
# ⚙️ מנוע הזירה
# ==========================================
class Engine:
    def __init__(self, state=None):
        if not state or "wins" not in state:
            # התחלה חדשה לגמרי
            self.state = {
                "wins": 0, # מונה ניצחונות
                "game_over": False
            }
            self.init_match()
        else:
            self.state = state

    def log(self, t, type="game"): 
        self.state["log"].append({"text": t, "type": type})
        if len(self.state["log"]) > 30: self.state["log"].pop(0)

    def pos(self): return f"{self.state['x']},{self.state['y']}"

    def init_match(self):
        # אתחול משחקון חדש
        self.state["x"] = 0
        self.state["y"] = 0
        self.state["host"] = "scout" # מתחילים כסייר
        self.state["hp"] = 50
        self.state["max_hp"] = 50
        self.state["game_over"] = False
        
        self.state["map_radius"] = 7 # גודל 15x15 (-7 עד 7)
        self.state["rivals"] = []
        self.state["corpses"] = {} # גופות על הרצפה
        self.state["visited"] = ["0,0"]
        self.state["log"] = [{"text": f"הקרב מתחיל! ניצחונות עד כה: {self.state['wins']}", "type": "gold"}]

        # יצירת בוטים (כמות עולה לפי ניצחונות)
        num_bots = 6 + self.state["wins"]
        
        for _ in range(num_bots):
            h_type = random.choice(list(HOSTS.keys()))
            bot = {
                "name": random.choice(BOT_NAMES) + f"-{random.randint(10,99)}",
                "host": h_type,
                "hp": HOSTS[h_type]["hp"],
                "max": HOSTS[h_type]["hp"],
                "atk": HOSTS[h_type]["atk"],
                "icon": HOSTS[h_type]["icon"],
                "x": random.randint(-7, 7),
                "y": random.randint(-7, 7)
            }
            # לוודא שלא נופל על השחקן
            if bot["x"]==0 and bot["y"]==0: bot["x"]=1
            self.state["rivals"].append(bot)

    # === AI TURN ===
    def process_ai(self):
        px, py = self.state["x"], self.state["y"]
        alive_bots = []
        
        for bot in self.state["rivals"]:
            # הבוט זז
            dx = random.choice([-1,0,1])
            dy = random.choice([-1,0,1])
            bot["x"] = max(-7, min(7, bot["x"]+dx))
            bot["y"] = max(-7, min(7, bot["y"]+dy))
            
            # אם פגש את השחקן -> קרב!
            if bot["x"] == px and bot["y"] == py and not self.state["game_over"]:
                # בוט תוקף את השחקן
                dmg = bot["atk"] + random.randint(-2, 2)
                self.state["hp"] -= dmg
                self.log(f"⚔️ {bot['name']} תקף אותך! (-{dmg})", "danger")
                if self.state["hp"] <= 0:
                    self.state["hp"] = 0
                    self.state["game_over"] = True
                    self.log("❌ מתת! נפסלת. המשחק נגמר.", "critical")
            
            alive_bots.append(bot)
            
        self.state["rivals"] = alive_bots
        
        # בדיקת ניצחון
        if len(self.state["rivals"]) == 0 and not self.state["game_over"]:
            self.state["wins"] += 1
            self.state["game_over"] = True # אבל מסוג ניצחון
            self.log(f"🏆 ניצחת בזירה! היריבים חוסלו. ניקוד: {self.state['wins']}", "gold")

    # === פעולות שחקן ===
    def move(self, dx, dy):
        if self.state["game_over"]: return

        nx = max(-7, min(7, self.state["x"] + dx))
        ny = max(-7, min(7, self.state["y"] + dy))
        
        self.state["x"] = nx
        self.state["y"] = ny
        
        if self.pos() not in self.state["visited"]: 
            self.state["visited"].append(self.pos())
            
        self.process_ai() # הבוטים זזים

    def attack(self, bot_idx):
        if self.state["game_over"]: return
        
        pos = self.pos()
        # סינון בוטים בחדר שלי
        room_bots = []
        for i, b in enumerate(self.state["rivals"]):
            if f"{b['x']},{b['y']}" == pos:
                room_bots.append((i, b)) # שומר אינדקס מקורי ובוט
        
        if bot_idx >= len(room_bots): return # הגנה משגיאה
        
        # זיהוי בוט
        real_idx, bot = room_bots[bot_idx]
        
        # תקיפה
        my_atk = HOSTS[self.state["host"]]["atk"]
        dmg = my_atk + random.randint(0, 5)
        bot["hp"] -= dmg
        self.log(f"פגעת ב-{bot['name']} (-{dmg})", "success")
        
        if bot["hp"] <= 0:
            self.log(f"💀 חיסלת את {bot['name']}! הגופה שלו כאן.", "gold")
            # הופך לגופה על הרצפה
            self.state["corpses"][pos] = {
                "type": bot["host"],
                "hp": HOSTS[bot["host"]]["hp"], # פוטנציאל חיים חדש
                "max": HOSTS[bot["host"]]["hp"]
            }
            # מסיר מהרשימה החיה
            self.state["rivals"].pop(real_idx)
        
        # תור האויבים (כולל זה שהתקפת אם שרד)
        self.process_ai()

    def swap_body(self):
        if self.state["game_over"]: return
        
        pos = self.pos()
        corpse = self.state["corpses"].get(pos)
        
        if not corpse:
            self.log("אין כאן גופה להשתלט עליה.", "sys")
            return
            
        # החלפת גוף
        new_type = corpse["type"]
        new_hp = corpse["max"] # מקבל גוף מלא ובריא!
        
        self.state["host"] = new_type
        self.state["hp"] = new_hp
        self.state["max_hp"] = new_hp
        
        self.log(f"🧬 עברת לגוף חדש: {HOSTS[new_type]['name']}!", "success")
        
        # הגופה הקודמת נעלמת (או הופכת לגופה הישנה שלי? בוא נעשה שהיא נעלמת)
        del self.state["corpses"][pos]
        self.process_ai()

    def get_ui(self):
        pos = self.pos()
        
        # 1. מיני-מפה (רדיוס 2 -> מראה 5x5 מתוך ה-15x15)
        grid = []
        cx, cy = self.state["x"], self.state["y"]
        
        for dy in range(2, -3, -1):
            row = []
            for dx in range(-2, 3):
                tx, ty = cx + dx, cy + dy
                k = f"{tx},{ty}"
                icon = "⬛"
                cls = "fog"
                
                # גבולות זירה
                if tx < -7 or tx > 7 or ty < -7 or ty > 7:
                    icon = "🚧"
                    cls = "wall"
                elif dx==0 and dy==0:
                    icon = HOSTS[self.state["host"]]["icon"]
                    cls = "me"
                elif k in self.state["visited"] or (abs(dx)<=1 and abs(dy)<=1):
                    # בדיקת בוטים
                    has_bot = any(b for b in self.state["rivals"] if b["x"]==tx and b["y"]==ty)
                    # בדיקת גופות
                    has_corpse = k in self.state["corpses"]
                    
                    if has_bot:
                        icon = "👿"
                        cls = "danger"
                    elif has_corpse:
                        icon = "⚰️"
                        cls = "loot"
                    else:
                        icon = "⬜"
                        cls = "empty"
                        
                row.append({"i":icon, "c":cls})
            grid.append(row)

        # 2. אויבים בחדר (רק החיים)
        room_bots = [b for b in self.state["rivals"] if f"{b['x']},{b['y']}" == pos]
        bots_data = []
        for b in room_bots:
            bots_data.append({
                "name": b["name"],
                "type_name": HOSTS[b["host"]]["name"],
                "icon": b["icon"],
                "hp": b["hp"],
                "max": b["max"]
            })
            
        # 3. האם יש גופה בחדר?
        corpse_here = self.state["corpses"].get(pos)
        corpse_data = None
        if corpse_here:
            h = HOSTS[corpse_here["type"]]
            corpse_data = {"name": h["name"], "icon": h["icon"], "max": h["hp"]}

        # בדיקת סוף משחק
        status = "play"
        if self.state["hp"] <= 0: status = "lost"
        elif len(self.state["rivals"]) == 0: status = "won"

        return {
            "map": grid,
            "log": self.state["log"],
            "bots": bots_data,
            "corpse": corpse_data,
            "status": status,
            "wins": self.state["wins"],
            "player": {
                "name": HOSTS[self.state["host"]]["name"],
                "icon": HOSTS[self.state["host"]]["icon"],
                "hp": self.state["hp"],
                "max": self.state["max_hp"]
            },
            "coords": f"({self.state['x']}, {self.state['y']})"
        }

# ==========================================
# SERVER ROUTES
# ==========================================
@app.route("/")
def index():
    if "uid" not in session: session["uid"] = str(uuid.uuid4())
    return render_template_string(HTML, api=url_for("update"))

@app.route("/update", methods=["POST"])
def update():
    try: eng = Engine(session.get("dm_royale"))
    except: eng = Engine(None)
    
    d = request.json
    act = d.get("a")
    val = d.get("v")
    
    if act == "new_game": eng = Engine(None) # איפוס כללי
    elif act == "next_match": eng.init_match() # סיבוב הבא (עם שמירת ניקוד)
    elif act == "move": eng.move(*val)
    elif act == "attack": eng.attack(val)
    elif act == "swap": eng.swap_body()
    
    session["dm_royale"] = eng.state
    return jsonify(eng.get_ui())

# ==========================================
# HTML UI
# ==========================================
HTML = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ARENA DM</title>
<style>
    body { background:#111; color:#eee; font-family:'Segoe UI',sans-serif; margin:0; display:flex; flex-direction:column; height:100vh; overflow:hidden;}
    
    /* Top Bar */
    .bar { background:#222; padding:10px; display:flex; justify-content:space-between; align-items:center; border-bottom:2px solid #f90;}
    .stat { background:#333; padding:5px 10px; border-radius:5px; font-weight:bold; }
    
    /* Layout */
    .box { flex:1; display:flex; padding:10px; gap:10px;}
    .side { width:140px; display:flex; flex-direction:column; gap:10px; align-items:center;}
    .main { flex:1; background:#181818; border:1px solid #333; border-radius:8px; padding:15px; display:flex; flex-direction:column; overflow-y:auto;}
    
    /* Map */
    .grid { display:grid; gap:2px; background:#000; padding:2px; border:1px solid #555;}
    .row { display:flex; gap:2px; }
    .cell { width:25px; height:25px; display:flex; align-items:center; justify-content:center; font-size:14px;}
    .me { background:#0f0; border:1px solid white;}
    .fog { background:#111; }
    .wall { background:#300; }
    .empty { background:#222; }
    .danger { background:#f00; animation:b 0.5s infinite;}
    .loot { background:gold; color:black;}
    
    @keyframes b { 50%{opacity:0.5}}

    /* Cards */
    .card-list { display:flex; flex-wrap:wrap; gap:10px; justify-content:center;}
    .card { background:#282828; padding:10px; border-radius:6px; border:1px solid #444; width:120px; text-align:center;}
    .c-icon { font-size:35px; }
    .c-hp { color:#f55; font-weight:bold; font-size:12px;}
    .atk-btn { width:100%; background:#822; color:white; border:none; padding:5px; margin-top:5px; cursor:pointer; border-radius:4px;}
    
    .corpse-card { border:2px dashed gold; background:#222; }
    .swap-btn { width:100%; background:gold; color:black; font-weight:bold; border:none; padding:5px; cursor:pointer;}

    /* Logs & Controls */
    .log-area { height:120px; background:#000; border-top:1px solid #333; padding:10px; overflow-y:auto; font-size:12px; font-family:monospace;}
    .controls { height:120px; background:#1a1a1a; display:grid; grid-template-columns: 2fr 1fr; align-items:center; padding:0 20px;}
    
    .pad { display:grid; grid-template-columns:repeat(3,1fr); gap:5px; width:120px; margin:0 auto; direction:ltr;}
    .btn { background:#444; color:white; border:1px solid #666; height:35px; cursor:pointer; font-size:18px; border-radius:4px;}
    .btn:active { background:#666;}
    
    /* Overlay */
    .over { position:fixed; inset:0; background:rgba(0,0,0,0.9); z-index:99; display:none; flex-direction:column; justify-content:center; align-items:center; }
</style>
</head>
<body>

<!-- End Screens -->
<div id="scr-lose" class="over" style="color:red">
    <h1 style="font-size:50px">💀 נפסלת!</h1>
    <p>הדמות שלך מתה. המשחק נגמר.</p>
    <button onclick="api('new_game')" style="padding:15px; font-size:20px;">התחל מההתחלה</button>
</div>

<div id="scr-win" class="over" style="color:gold">
    <h1 style="font-size:50px">🏆 המנצח!</h1>
    <p>חיסלת את כולם בזירה.</p>
    <button onclick="api('next_match')" style="padding:15px; font-size:20px;">לקרב הבא (רמה קשה)</button>
</div>

<div class="bar">
    <div style="display:flex; align-items:center; gap:10px;">
        <span style="font-size:30px;" id="p-ico">?</span>
        <div>
            <div id="p-name" style="font-weight:bold">...</div>
            <div style="color:#f55; font-size:12px;">HP: <span id="p-hp">0</span></div>
        </div>
    </div>
    <div class="stat">ניצחונות: <span id="score" style="color:gold">0</span></div>
</div>

<div class="box">
    <div class="side">
        <div style="color:#888; font-size:10px;">R.A.D.A.R (4x4 view)</div>
        <div class="grid" id="grid"></div>
        <div style="margin-top:10px; font-size:10px; text-align:center;">מיקום: <span id="crd"></span></div>
    </div>
    
    <div class="main">
        <!-- Live Enemies -->
        <div class="card-list" id="bots"></div>
        
        <!-- Corpse -->
        <div id="corpse-area" style="margin-top:20px; border-top:1px solid #333; padding-top:10px; display:none;">
            <div style="font-size:12px; color:gold; margin-bottom:5px;">גופה ניתנת להחלפה:</div>
            <div class="card corpse-card">
                <div class="c-icon" id="c-ico">💀</div>
                <div style="font-weight:bold" id="c-name">...</div>
                <div style="color:#aaa; font-size:10px;">HP מלא</div>
                <button class="swap-btn" onclick="api('swap')">🧬 קח גוף</button>
            </div>
        </div>
    </div>
</div>

<div class="log-area" id="logs"></div>

<div class="controls">
    <button onclick="api('new_game')" style="background:#500; border:none; color:white; padding:10px; cursor:pointer;">🏳️ ויתור / ריסט</button>
    
    <div class="pad">
        <button class="btn" style="grid-column:2" onclick="api('move',[0,1])">⬆</button>
        <button class="btn" style="grid-column:1; grid-row:2" onclick="api('move',[-1,0])">⬅</button>
        <button class="btn" style="grid-column:2; grid-row:2" onclick="api('move',[0,-1])">⬇</button>
        <button class="btn" style="grid-column:3; grid-row:2" onclick="api('move',[1,0])">➡</button>
    </div>
</div>

<script>
    const API_URL = "{{ api }}";
    
    window.onload = () => api('init');

    async function api(act, val=null){
        let r = await fetch(API_URL, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({a:act, v:val})});
        let d = await r.json();
        
        if(d.status === "lost") { document.getElementById("scr-lose").style.display="flex"; return; }
        else document.getElementById("scr-lose").style.display="none";
        
        if(d.status === "won") { document.getElementById("scr-win").style.display="flex"; return; }
        else document.getElementById("scr-win").style.display="none";

        // Player
        document.getElementById("p-ico").innerText = d.player.icon;
        document.getElementById("p-name").innerText = d.player.name;
        document.getElementById("p-hp").innerText = d.player.hp + " / " + d.player.max;
        document.getElementById("score").innerText = d.wins;
        document.getElementById("crd").innerText = d.coords;

        // Map
        let gh="";
        d.map.forEach(row=>{
            gh+=`<div class="row">`;
            row.forEach(c=> gh+=`<div class="cell ${c.cls}">${c.i}</div>`);
            gh+=`</div>`;
        });
        document.getElementById("grid").innerHTML = gh;

        // Enemies
        let bh="";
        if(d.bots.length==0) bh="<div style='color:#555'>השטח נקי מאויבים.</div>";
        d.bots.forEach((b,i)=>{
            bh+=`<div class="card">
                <div class="c-icon">${b.icon}</div>
                <div>${b.name}</div>
                <div style="font-size:10px; color:#888">(${b.type_name})</div>
                <div class="c-hp">${b.hp}/${b.max} HP</div>
                <button class="atk-btn" onclick="api('attack',${i})">⚔️ חיסול</button>
            </div>`;
        });
        document.getElementById("bots").innerHTML = bh;

        // Corpse
        if(d.corpse) {
            document.getElementById("corpse-area").style.display = "block";
            document.getElementById("c-ico").innerText = d.corpse.icon;
            document.getElementById("c-name").innerText = d.corpse.name;
        } else {
            document.getElementById("corpse-area").style.display = "none";
        }

        // Logs
        let lh="";
        d.log.slice().reverse().forEach(l=> lh+=`<div><span style="color:${l.type=='danger'?'red':l.type=='gold'?'gold':'#888'}">></span> ${l.text}</div>`);
        document.getElementById("logs").innerHTML = lh;
    }
    
    window.onkeydown = e => {
        if(e.key=="ArrowUp") api('move',[0,1]);
        if(e.key=="ArrowDown") api('move',[0,-1]);
        if(e.key=="ArrowLeft") api('move',[-1,0]);
        if(e.key=="ArrowRight") api('move',[1,0]);
    };
</script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(port=5006, debug=True)
