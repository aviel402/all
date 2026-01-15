import random
import uuid
from flask import Flask, render_template_string, request, jsonify, session, url_for

app = Flask(__name__)
app.secret_key = 'body_snatcher_royale_v1'

# ==========================================
# 🧬 מאגר גופים (Classes)
# ==========================================
CLASSES = {
    # חלשים
    "rat":     {"name": "עכברוש", "icon": "🐀", "hp": 30, "atk": 5, "desc": "מהיר וחלש"},
    "drone":   {"name": "רחפן", "icon": "🛸", "hp": 40, "atk": 8, "desc": "טכנולוגי"},
    
    # בינוניים
    "soldier": {"name": "חייל", "icon": "👮", "hp": 100, "atk": 15, "desc": "לוחם מיומן"},
    "ninja":   {"name": "מתנקש", "icon": "🥷", "hp": 70, "atk": 25, "desc": "נזק גבוה"},
    "alien":   {"name": "חייזר", "icon": "👽", "hp": 90, "atk": 18, "desc": "טכנולוגיה זרה"},

    # חזקים
    "tank":    {"name": "רובוט כבד", "icon": "🤖", "hp": 150, "atk": 20, "desc": "שריון כבד"},
    "beast":   {"name": "מפלצת", "icon": "👹", "hp": 180, "atk": 22, "desc": "פרא אדם"},
    
    # אגדי
    "dragon":  {"name": "דרקון", "icon": "🐲", "hp": 250, "atk": 40, "desc": "המלך של הזירה"}
}

# שמות לבוטים כדי שירגיש חי
BOT_NAMES = ["סלייר", "וויפר", "נמסיס", "גולגולת", "זירו", "אומגה", "רפאים", "בלאזה"]

class Engine:
    def __init__(self, state=None):
        if not state:
            self.state = {
                # נתוני שחקן
                "x": 0, "y": 0,
                "type": "soldier", # מתחילים כחייל
                "hp": 100, "max": 100,
                "dead": False,
                "kills": 0,
                
                # זירה
                "rivals": [], 
                "corpses": {}, # גופות על הרצפה: "x,y": "dragon"
                "map_bound": 7, # רדיוס 7 = מפה 15X15
                "log": [{"text": "נכנסת לזירה. חסל, קח גוף, שרוד.", "type": "sys"}]
            }
            self.init_world()
        else:
            self.state = state

    def pos(self): return f"{self.state['x']},{self.state['y']}"
    
    def log(self, txt, t="game"): 
        self.state["log"].insert(0, {"text": txt, "type": t})
        if len(self.state["log"]) > 30: self.state["log"].pop()

    def init_world(self):
        # 10 בוטים מפוזרים
        for i in range(10):
            ctype = random.choice(["rat", "drone", "soldier", "ninja", "alien"]) # מתחילים בינוני
            self.state["rivals"].append({
                "id": str(uuid.uuid4()),
                "name": random.choice(BOT_NAMES),
                "type": ctype,
                "hp": CLASSES[ctype]["hp"],
                "max": CLASSES[ctype]["hp"],
                "x": random.randint(-7, 7),
                "y": random.randint(-7, 7)
            })
            
        # לפעמים יש בוס (דרקון/רובוט) שמסתובב כבר
        if random.random() < 0.5:
            ctype = random.choice(["tank", "dragon", "beast"])
            self.state["rivals"].append({
                "id": str(uuid.uuid4()),
                "name": "המחסל",
                "type": ctype,
                "hp": CLASSES[ctype]["hp"],
                "max": CLASSES[ctype]["hp"],
                "x": random.randint(-7, 7),
                "y": random.randint(-7, 7)
            })

    # === מכניקת בוטים (AI) ===
    def process_ai(self):
        px, py = self.state["x"], self.state["y"]
        survivors = []
        
        for bot in self.state["rivals"]:
            # הבוט זז
            dx = random.choice([-1, 0, 1])
            dy = random.choice([-1, 0, 1])
            bot["x"] = max(-7, min(7, bot["x"] + dx))
            bot["y"] = max(-7, min(7, bot["y"] + dy))
            
            # אם בוט הגיע למשבצת שלי -> תוקף אותי
            if bot["x"] == px and bot["y"] == py and not self.state["dead"]:
                atk = CLASSES[bot["type"]]["atk"]
                dmg = max(1, atk + random.randint(-2, 2))
                self.state["hp"] -= dmg
                self.log(f"⚔️ {bot['name']} תקף אותך! (-{dmg})", "danger")
                
                if self.state["hp"] <= 0:
                    self.state["hp"] = 0
                    self.state["dead"] = True
                    self.log("💀 נהרגת. המשחק נגמר.", "critical")
            
            survivors.append(bot)
        
        self.state["rivals"] = survivors

    # === פעולות שחקן ===
    def move(self, dx, dy):
        if self.state["dead"]: return

        nx = self.state["x"] + dx
        ny = self.state["y"] + dy
        
        # גבולות מפה 15X15
        if nx < -7 or nx > 7 or ny < -7 or ny > 7:
            self.log("⛔ גבול הזירה.", "sys")
            return

        self.state["x"] = nx
        self.state["y"] = ny
        
        # בדיקה אם יש משהו בחדר
        pos = self.pos()
        corpse = self.state["corpses"].get(pos)
        
        found_enemy = False
        for b in self.state["rivals"]:
            if b["x"] == nx and b["y"] == ny:
                enemy_type = CLASSES[b["type"]]
                self.log(f"⚠️ נתקלת ב-{b['name']} ({enemy_type['name']})!", "danger")
                found_enemy = True
        
        if not found_enemy:
            msg = "שטח פנוי."
            if corpse:
                c_name = CLASSES[corpse]["name"]
                msg = f"יש כאן גופת {c_name}. אתה יכול לקחת אותה."
            self.log(msg, "game" if not corpse else "success")

        self.process_ai() # תור העולם

    def attack(self):
        if self.state["dead"]: return
        
        px, py = self.state["x"], self.state["y"]
        pos = self.pos()
        
        my_stats = CLASSES[self.state["type"]]
        targets = [b for b in self.state["rivals"] if b["x"]==px and b["y"]==py]
        
        if not targets:
            self.log("אין כאן אויבים.", "info")
            return
        
        # תוקפים את הראשון
        target = targets[0]
        dmg = my_stats["atk"] + random.randint(0, 5)
        target["hp"] -= dmg
        
        self.log(f"🔥 תקפת את {target['name']} (-{dmg})", "success")
        
        if target["hp"] <= 0:
            # הרגת אותו!
            self.state["rivals"].remove(target) # מסירים מהרשימה
            self.state["corpses"][pos] = target["type"] # הגופה נופלת
            self.state["kills"] += 1
            self.log(f"🏆 חיסלת אותו! גופת {CLASSES[target['type']]['name']} זמינה.", "gold")
        else:
            # הוא עדיין חי ותוקף בתור ה-AI הבא
            pass
            
        self.process_ai()

    def swap_body(self):
        if self.state["dead"]: return
        
        pos = self.pos()
        corpse_type = self.state["corpses"].get(pos)
        
        if not corpse_type:
            self.log("אין כאן גופה להחלפה.", "sys")
            return
            
        # ביצוע החלפה
        old_type = self.state["type"]
        self.state["type"] = corpse_type
        
        # כשעוברים לגוף חדש - מקבלים אותו "חדש" (חיים מלאים)
        new_stats = CLASSES[corpse_type]
        self.state["hp"] = new_stats["hp"]
        self.state["max"] = new_stats["hp"]
        
        # הגופה הקודמת נשארת (או נעלמת? נניח נעלמת כדי למנוע ספאם)
        del self.state["corpses"][pos]
        
        self.log(f"🧬 העברת תודעה! עזבת את ה-{CLASSES[old_type]['name']} ועברת ל-{new_stats['name']}.", "gold")

    def get_ui(self):
        # בניית רדאר מוגדל (רדיוס 2 -> 5x5)
        grid = []
        r = 2 
        cx, cy = self.state["x"], self.state["y"]
        
        for dy in range(r, -r-1, -1):
            row = []
            for dx in range(-r, r+1):
                tx, ty = cx+dx, cy+dy
                k = f"{tx},{ty}"
                cell = "⬛"
                cls = "fog"
                
                # גבול
                if tx < -7 or tx > 7 or ty < -7 or ty > 7:
                    cell = "🚫"
                    cls = "wall"
                elif dx==0 and dy==0:
                    cell = CLASSES[self.state["type"]]["icon"]
                    cls = "player"
                else:
                    # בודקים אם יש בוט
                    has_bot = False
                    for b in self.state["rivals"]:
                        if b["x"]==tx and b["y"]==ty:
                            cell = "👹"
                            cls = "enemy"
                            has_bot = True
                            break
                    
                    if not has_bot:
                        # בודקים גופה
                        if k in self.state["corpses"]:
                            c_type = self.state["corpses"][k]
                            cell = "💀"
                            cls = "corpse"
                        else:
                            cell = "⬜"
                            cls = "empty"
                
                row.append({"c": cell, "cl": cls})
            grid.append(row)

        # נתוני סצנה נוכחית (האם יש גופה?)
        corpse_here = self.state["corpses"].get(self.pos())
        corpse_data = None
        if corpse_here:
            corpse_data = CLASSES[corpse_here]

        # בדיקת ניצחון
        win = (len(self.state["rivals"]) == 0)

        return {
            "player": self.state,
            "meta": CLASSES[self.state["type"]],
            "map": grid,
            "log": self.state["log"],
            "corpse": corpse_data,
            "win": win,
            "enemies_count": len(self.state["rivals"])
        }

# ==========================================
# WEB
# ==========================================
@app.route("/")
def index():
    if "uid" not in session: session["uid"] = str(uuid.uuid4())
    api = url_for("game_loop")
    return render_template_string(HTML, api=api)

@app.route("/api", methods=["POST"])
def game_loop():
    try: eng = Engine(session.get("br_surv_save"))
    except: eng = Engine(None)
    
    d = request.json
    act = d.get("a")
    val = d.get("v")
    
    if act == "reset": eng = Engine(None)
    elif act == "move": eng.move(*val)
    elif act == "attack": eng.attack()
    elif act == "swap": eng.swap_body()
    
    session["br_surv_save"] = eng.state
    return jsonify(eng.get_ui())

# ==========================================
# UI HTML
# ==========================================
HTML = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ARENA: BODY SNATCHER</title>
<style>
    body { background: #121212; color: #eee; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; display:flex; flex-direction:column; height:100vh; overflow:hidden;}
    
    /* Top Bar */
    .header { background:#1e1e1e; padding:10px; display:flex; justify-content:space-between; align-items:center; border-bottom:2px solid #333; height: 70px;}
    .stat-pill { background:#252525; padding:5px 10px; border-radius:15px; font-size:14px; border:1px solid #444; }
    
    .hp-box { width: 100%; height:8px; background:#333; margin-top:5px; border-radius:4px; overflow:hidden; }
    .hp-bar { height:100%; background:#f44; transition:0.3s; width:100%; }

    /* Middle */
    .viewport { flex:1; display:flex; padding:10px; gap:10px; overflow:hidden;}
    
    .radar-container { width:150px; background:#000; border:1px solid #444; display:flex; flex-direction:column; align-items:center; justify-content:center; padding:5px;}
    .grid { display:grid; gap:2px; }
    .row { display:flex; gap:2px; }
    .cell { width:25px; height:25px; display:flex; align-items:center; justify-content:center; font-size:16px; border-radius:3px; background:#111;}
    .player { background: #28a745; border:1px solid lime;}
    .enemy { background: #dc3545; animation: blink 1s infinite;}
    .corpse { background: #555; color: #aaa; border:1px solid #777;}
    .wall { opacity:0; }
    .fog { background: #000; }
    .empty { background:#181818; }

    .info-area { flex:1; background:#181818; border-radius:8px; padding:15px; display:flex; flex-direction:column; position:relative;}
    .logs { flex:1; overflow-y:auto; font-size:13px; font-family: monospace;}
    .msg { margin-bottom:4px; border-bottom:1px solid #222; padding-bottom:2px;}
    .danger { color:#f88; } .gold { color:gold; } .success{ color:#8f8;}

    /* Special Notification Box */
    .notify-box { 
        margin-top:10px; background:#332020; border:1px solid #522; padding:10px; border-radius:5px; 
        display:none; flex-direction:row; align-items:center; justify-content:space-between;
    }
    
    /* Controls */
    .controls { height: 160px; background:#1b1b1b; padding:10px; border-top:2px solid #333; display:grid; grid-template-columns: 2fr 1fr; align-items:center;}
    
    .d-pad { display:grid; grid-template-columns:repeat(3, 1fr); gap:5px; width:120px; direction:ltr; margin:0 auto;}
    .btn { background:#333; border:1px solid #555; color:white; height:40px; border-radius:5px; cursor:pointer; font-size:20px; }
    .btn:active{ background:#555; }
    .u{grid-column:2} .l{grid-column:1; grid-row:2} .d{grid-column:2; grid-row:2} .r{grid-column:3; grid-row:2}

    .actions { display:grid; grid-template-columns:1fr; gap:10px; padding:0 20px;}
    .act-btn { height: 60px; background: #b71c1c; color: white; border:none; font-size:18px; font-weight:bold; border-radius:8px; cursor:pointer; border-bottom:4px solid #700;}
    .act-btn:active { transform:translateY(2px); border-bottom-width:0; }
    .swap-btn { background: #f9a825; border-color: #c77e0b; display:none; height:40px; font-size:14px;} /* Hidden by default */

    /* OVERLAY */
    .overlay { position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.9); color:red; display:none; flex-direction:column; justify-content:center; align-items:center; z-index:99;}
    .win-overlay { color: gold; }

    @keyframes blink { 50%{opacity:0.5}}
</style>
</head>
<body id="body">

<div id="end-screen" class="overlay">
    <h1 id="end-title">GAME OVER</h1>
    <p id="end-msg">נהרגת.</p>
    <button onclick="s('reset')" style="padding:15px 30px; font-size:20px; cursor:pointer;">שחק שוב</button>
</div>

<div class="header">
    <div style="display:flex; align-items:center; gap:10px;">
        <span style="font-size:35px; background:#000; border-radius:50%; border:2px solid #555; width:50px; height:50px; text-align:center;" id="p-icon">?</span>
        <div>
            <div id="p-name" style="font-weight:bold; font-size:1.1rem;">...</div>
            <div style="font-size:12px; color:#aaa" id="p-class">...</div>
        </div>
    </div>
    
    <div style="text-align:right; width:120px;">
        <div class="hp-box"><div class="hp-bar" id="hp-bar"></div></div>
        <div style="display:flex; justify-content:space-between; font-size:11px; margin-top:2px;">
            <span id="hp-txt">0/0</span>
            <span style="color:#f55">יריבים: <span id="rivals-count">0</span></span>
        </div>
    </div>
</div>

<div class="viewport">
    <div class="radar-container">
        <small style="color:#aaa; margin-bottom:5px;">R.A.D.A.R</small>
        <div class="grid" id="map-target"></div>
    </div>
    
    <div class="info-area">
        <div class="logs" id="log-target"></div>
        
        <!-- Corpse Found UI -->
        <div class="notify-box" id="swap-ui">
            <div>
                <div>🦴 מצאת גופה: <strong id="corpse-name"></strong></div>
                <div style="font-size:11px; color:#aaa" id="corpse-desc"></div>
            </div>
            <button class="act-btn swap-btn" id="btn-swap" onclick="s('swap')">החלף גוף!</button>
        </div>
    </div>
</div>

<div class="controls">
    <div class="actions">
        <button class="act-btn" onclick="s('attack')">⚔️ תקוף אויב קרוב</button>
    </div>
    
    <div class="d-pad">
        <button class="btn u" onclick="s('move',[0,1])">⬆</button>
        <button class="btn l" onclick="s('move',[-1,0])">⬅</button>
        <button class="btn d" onclick="s('move',[0,-1])">⬇</button>
        <button class="btn r" onclick="s('move',[1,0])">➡</button>
    </div>
</div>

<script>
    const API = "{{ api }}";
    
    window.onload = ()=> s('init');

    async function s(act, val=null) {
        let res = await fetch(API, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({a:act, v:val})});
        let d = await res.json();
        
        // 1. GAME OVER CHECK
        let ov = document.getElementById("end-screen");
        if(d.player.dead){
            ov.style.display="flex";
            ov.classList.remove("win-overlay");
            document.getElementById("end-title").innerText="YOU DIED";
            document.getElementById("end-msg").innerText="הגוף שלך הושמד סופית.";
        } else if (d.win){
            ov.style.display="flex";
            ov.classList.add("win-overlay");
            document.getElementById("end-title").innerText="VICTORY!";
            document.getElementById("end-msg").innerText="אתה השליט היחיד של הזירה.";
        } else {
            ov.style.display="none";
        }

        // 2. HUD
        document.getElementById("p-icon").innerText = d.meta.icon;
        document.getElementById("p-name").innerText = d.meta.name;
        document.getElementById("p-class").innerText = d.meta.desc;
        document.getElementById("rivals-count").innerText = d.enemies_count;
        
        let hpP = (d.player.hp / d.player.max)*100;
        document.getElementById("hp-bar").style.width = hpP+"%";
        document.getElementById("hp-txt").innerText = d.player.hp + "/" + d.player.max;

        // 3. LOGS
        let l = document.getElementById("log-target");
        l.innerHTML="";
        d.log.forEach(m => l.innerHTML += `<div class="msg ${m.type}">${m.text}</div>`);

        // 4. MAP
        let mh="";
        d.map.forEach(row=>{
            mh+=`<div class="row">`;
            row.forEach(c => mh+=`<div class="cell ${c.cl}">${c.c}</div>`);
            mh+=`</div>`;
        });
        document.getElementById("map-target").innerHTML=mh;

        // 5. CORPSE / SWAP UI
        if(d.corpse){
            document.getElementById("swap-ui").style.display = "flex";
            document.getElementById("btn-swap").style.display = "block";
            document.getElementById("corpse-name").innerText = d.corpse.name + " " + d.corpse.icon;
            document.getElementById("corpse-desc").innerText = "HP מקסימלי: " + d.corpse.hp;
        } else {
            document.getElementById("swap-ui").style.display = "none";
        }
    }
    
    window.onkeydown = e => {
        if(e.key=="ArrowUp") s('move',[0,1]);
        if(e.key=="ArrowDown") s('move',[0,-1]);
        if(e.key=="ArrowLeft") s('move',[-1,0]);
        if(e.key=="ArrowRight") s('move',[1,0]);
        if(e.key==" ") s('attack');
        if(e.key=="Enter") s('swap');
    }
</script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(port=5006, debug=True)
