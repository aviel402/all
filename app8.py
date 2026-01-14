import random
import uuid
from flask import Flask, render_template_string, request, jsonify, session, url_for

app = Flask(__name__)
# מפתח חדש לאיפוס מוחלט של באגים קודמים
app.secret_key = 'parasite_evo_v9_map_ai'

# ==========================================
# 🧬 מסד נתונים ביולוגי
# ==========================================
HOSTS = {
    "blob": {"name": "עיסה ירוקה", "icon": "🦠", "hp": 10, "atk": 1, "desc": "חלש. חייב גוף מיד."},
    "rat": {"name": "עכברוש מעבדה", "icon": "🐀", "hp": 15, "atk": 3, "desc": "חלש אבל מהיר."},
    "scientist": {"name": "מדען מבוהל", "icon": "👨‍🔬", "hp": 30, "atk": 5, "desc": "יכול להשתמש במחשבים."},
    "soldier": {"name": "חייל קומנדו", "icon": "👮", "hp": 80, "atk": 15, "desc": "לוחם מיומן עם נשק."},
    "beast": {"name": "ניסוי שנכשל", "icon": "👹", "hp": 120, "atk": 25, "desc": "מפלצת שרירים רצחנית."},
    "cyborg": {"name": "קיבורג אבטיפוס", "icon": "🤖", "hp": 60, "atk": 20, "desc": "חצי מכונה, קטלני."}
}

class Engine:
    def __init__(self, state=None):
        if not state or "host" not in state:
            self.state = {
                "x": 0, "y": 0,
                "host": "blob",
                "hp": 10,
                "max_hp": 10,
                "is_dead": False, # מצב "רוח" ללא גוף
                "map": {},
                "visited": ["0,0"],
                "log": [{"text": "המיכל נשבר. אתה בחוץ. תמצא גוף או שתמות.", "type": "sys"}]
            }
            # חדר התחלה קל
            self.create_room(0, 0, force="rat")
        else:
            self.state = state

    def pos(self): return f"{self.state['x']},{self.state['y']}"
    
    def log(self, txt, t="game"): self.state["log"].append({"text": txt, "type": t})

    def create_room(self, x, y, force=None):
        k = f"{x},{y}"
        if k in self.state["map"]: return

        enemies = []
        if force:
            types = [force]
        else:
            # אויבים רנדומליים ומתחזקים
            pool = ["rat", "scientist", "scientist", "soldier", "soldier", "beast", "cyborg"]
            count = random.randint(1, 3)
            types = [random.choice(pool) for _ in range(count)]

        for t in types:
            base = HOSTS[t]
            enemies.append({
                "type": t,
                "name": base["name"],
                "icon": base["icon"],
                "hp": base["hp"],
                "max": base["hp"],
                "atk": base["atk"]
            })

        self.state["map"][k] = {"enemies": enemies}

    # === AI TURN: אויבים תוקפים אותך ===
    def enemies_turn(self):
        if self.state["is_dead"]: return # לא תוקפים רוח

        room = self.state["map"][self.pos()]
        for enemy in room["enemies"]:
            # סיכוי של 70% שהאויב יתקוף
            if random.random() < 0.7:
                dmg = enemy["atk"] + random.randint(-2, 2)
                dmg = max(1, dmg)
                
                self.state["hp"] -= dmg
                self.log(f"🩸 {enemy['name']} תקף אותך! נפגעת ב-{dmg}.", "danger")
                
                if self.state["hp"] <= 0:
                    self.die()
                    break # מפסיקים התקפות אם כבר מתת

    def die(self):
        self.state["hp"] = 0
        self.state["is_dead"] = True
        self.log("🚨 הגוף המארח הושמד! אתה נפלט החוצה!", "critical")
        self.log("בחר גוף חדש מיד (כפתור פלישה ירוק)!", "critical")

    # === ACTIONS ===
    
    def move(self, dx, dy):
        if self.state["is_dead"]:
            self.log("בלי גוף פיזי אתה לא יכול לעזוב את החדר.", "warning")
            return

        self.state["x"] += dx
        self.state["y"] += dy
        self.create_room(self.state["x"], self.state["y"])
        
        # עדכון ביקור
        pos = self.pos()
        if pos not in self.state["visited"]: self.state["visited"].append(pos)
        
        room = self.state["map"][pos]
        count = len(room["enemies"])
        self.log(f"הגעת לחדר חדש. יש כאן {count} מטרות פוטנציאליות.", "game")
        
        # בסוף תנועה - האויבים תוקפים (אמבוש)
        self.enemies_turn()

    def attack(self, idx):
        if self.state["is_dead"]: return 

        room = self.state["map"][self.pos()]
        if idx >= len(room["enemies"]): return

        enemy = room["enemies"][idx]
        my_stats = HOSTS[self.state["host"]]
        
        # אני תוקף
        my_dmg = my_stats["atk"] + random.randint(0, 5)
        enemy["hp"] -= my_dmg
        self.log(f"תקפת את {enemy['name']} (-{my_dmg})", "success")

        if enemy["hp"] <= 0:
            self.log(f"{enemy['name']} מת. הגופה לא שמישה יותר.", "info")
            room["enemies"].pop(idx)
        
        # תור האויבים
        self.enemies_turn()

    def infect(self, idx):
        if not self.state["is_dead"]: 
            self.log("הגוף שלך עדיין חי. אי אפשר לעבור.", "sys")
            return

        room = self.state["map"][self.pos()]
        target = room["enemies"][idx]
        
        # השתלטות
        old_name = target["name"]
        self.state["host"] = target["type"]
        self.state["hp"] = target["hp"] # מקבלים את הבריאות הנוכחית שלו
        self.state["max_hp"] = target["max"]
        self.state["is_dead"] = False
        
        # המארח מפסיק להיות אויב
        room["enemies"].pop(idx)
        
        self.log(f"🧬 בוצע מיזוג עצבי! אתה עכשיו שולט ב-{old_name}.", "bio")

    # === MAP RENDERER ===
    def get_map_grid(self):
        grid = []
        cx, cy = self.state["x"], self.state["y"]
        
        for dy in range(1, -2, -1):
            row = []
            for dx in range(-1, 2):
                k = f"{cx+dx},{cy+dy}"
                icon = "⬛"
                cls = "fog"
                
                if dx == 0 and dy == 0:
                    icon = "🦠" # אני
                    cls = "me"
                elif k in self.state["visited"]:
                    r = self.state["map"][k]
                    # אם יש אויבים בחדר ההוא - הצג סימן סכנה
                    icon = "💀" if len(r["enemies"]) > 0 else "⬜"
                    cls = "visited"
                
                row.append({"icon":icon, "cls":cls})
            grid.append(row)
        return grid

# ==========================================
# WEB
# ==========================================
@app.route("/")
def index():
    if "uid" not in session: session["uid"] = str(uuid.uuid4())
    api = url_for("game_loop")
    return render_template_string(UI, api=api)

@app.route("/game/loop", methods=["POST"])
def game_loop():
    try: eng = Engine(session.get("gp_save"))
    except: eng = Engine(None)

    data = request.json or {}
    a = data.get("a")
    v = data.get("v")

    if a == "reset": eng = Engine(None)
    elif a == "move": eng.move(*v)
    elif a == "attack": eng.attack(v)
    elif a == "infect": eng.infect(v)

    session["gp_save"] = eng.state
    
    # שליפת נתונים לתצוגה
    curr_host = HOSTS[eng.state["host"]]
    curr_room = eng.state["map"][eng.pos()]
    
    return jsonify({
        "log": eng.state["log"],
        "map": eng.get_map_grid(),
        "enemies": curr_room["enemies"],
        "player": {
            "name": curr_host["name"],
            "icon": curr_host["icon"],
            "desc": curr_host["desc"],
            "hp": eng.state["hp"],
            "max": eng.state["max_hp"] if "max_hp" in eng.state else curr_host["hp"],
            "dead": eng.state["is_dead"]
        },
        "pos": eng.pos()
    })

# ==========================================
# FRONTEND UI
# ==========================================
UI = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>PARASITE EVO</title>
<style>
    body { background: #080a04; color: #cfc; font-family: 'Courier New', monospace; margin: 0; display:flex; flex-direction:column; height:100vh;}
    
    /* Top: Player & Map */
    .top-panel { background: #12180d; padding: 10px; display:flex; justify-content:space-between; align-items:center; border-bottom: 2px solid #3c3; box-shadow:0 0 15px rgba(50,200,50,0.2);}
    
    .player-info { display:flex; gap:10px; align-items:center;}
    .big-icon { font-size: 35px; background:#000; padding:5px; border-radius:50%; border:2px solid #3c3; width:50px; height:50px; text-align:center; }
    
    .hp-bar { width: 100px; height: 12px; background: #333; border:1px solid #555; margin-top:5px; }
    .hp-fill { height:100%; background: #f33; width:100%; transition:0.3s; }
    
    /* MAP Radar */
    .radar { display: grid; grid-template-rows: repeat(3, 1fr); gap: 2px; border:1px solid #252; padding:2px; background:black;}
    .radar-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 2px;}
    .dot { width: 15px; height: 15px; display:flex; align-items:center; justify-content:center; font-size:10px; cursor:default;}
    .fog { background: #111; }
    .me { background: #3c3; box-shadow:0 0 5px #3c3; }
    .visited { background: #222; border:1px solid #333; color:red;}

    /* MAIN STAGE */
    .stage { flex:1; display:flex; flex-direction:column; padding:10px; overflow:hidden;}
    
    .enemy-grid { 
        flex:1; display:flex; flex-wrap:wrap; gap:10px; overflow-y:auto; 
        align-content: flex-start; justify-content:center; padding:10px;
    }
    
    .card { 
        width: 100px; height: 130px; background: #151a10; border: 1px solid #2a4020; 
        border-radius: 6px; padding: 5px; text-align:center;
        display:flex; flex-direction:column; justify-content:space-between;
        position:relative; transition:0.2s;
    }
    .card:hover { border-color: #5f5; transform:scale(1.05);}
    .e-icon { font-size: 30px; }
    
    .btn-act { border:none; padding:5px; color:white; cursor:pointer; font-weight:bold; border-radius:4px; font-family:inherit;}
    .atk { background: #722; }
    .inf { background: #282; border:1px solid #4f4; animation: blink 1s infinite;}

    /* DEAD MODE OVERLAY */
    .dead-fx { 
        position:fixed; top:0; left:0; width:100%; height:100%; 
        border:5px solid red; pointer-events:none; 
        box-shadow: inset 0 0 100px rgba(255,0,0,0.2); 
        display:none; z-index:99;
    }

    /* CONTROLS */
    .controls { 
        height: 140px; background: #0e120b; border-top: 1px solid #333;
        display: grid; grid-template-columns: 2fr 1fr;
    }
    
    .log-box { 
        overflow-y:auto; padding:10px; font-size:12px; color:#aaa; 
        border-left: 1px solid #222;
    }
    .msg { margin-bottom:3px; padding-bottom:3px; border-bottom:1px solid #111; }
    .critical { color: yellow; background:#500; font-weight:bold;}
    .danger { color: #f55; }
    .success { color: #5f5; }
    .bio { color: #0ff; }

    .nav-pad { 
        display:grid; grid-template-columns:repeat(3, 1fr); gap:5px; padding:10px; 
        direction:ltr; /* קריטי לחיצים */
        align-items: center; justify-items: center;
    }
    .nav-btn { 
        width: 100%; height: 100%; font-size: 20px; background: #1a2215; 
        color: #6a6; border: 1px solid #2c3e20; cursor: pointer; border-radius:6px;
    }
    .nav-btn:active { background: #3c3; color:black;}
    
    .up { grid-column:2; grid-row:1;}
    .left { grid-column:1; grid-row:2;}
    .down { grid-column:2; grid-row:2;}
    .right { grid-column:3; grid-row:2;}

    @keyframes blink { 50% { opacity:0.6;} }
</style>
</head>
<body>

<div id="red-screen" class="dead-fx"></div>

<div class="top-panel">
    <div class="player-info">
        <div class="big-icon" id="p-icon">🦠</div>
        <div>
            <div id="p-name" style="font-weight:bold;">טוען...</div>
            <div class="hp-bar"><div class="hp-fill" id="hp-val"></div></div>
            <div style="font-size:10px;" id="p-desc">...</div>
        </div>
    </div>
    
    <!-- Mini Map -->
    <div class="radar" id="map-target"></div>
</div>

<div class="stage">
    <div style="font-size:11px; color:#555; text-align:center;">חדר נוכחי - אויבים:</div>
    <div class="enemy-grid" id="scene"></div>
</div>

<div class="controls">
    <div class="log-box" id="log-list"></div>
    <div class="nav-pad">
        <button class="nav-btn up" onclick="send('move', [0,1])">▲</button>
        <button class="nav-btn left" onclick="send('move', [-1,0])">◀</button>
        <button class="nav-btn down" onclick="send('move', [0,-1])">▼</button>
        <button class="nav-btn right" onclick="send('move', [1,0])">▶</button>
    </div>
</div>

<script>
    const API = "{{ api }}";
    
    window.onload = () => send('');

    async function send(act, val=null) {
        let res = await fetch(API, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({a:act, v:val})});
        let d = await res.json();
        
        let p = d.player;
        
        // 1. Player Status
        document.getElementById('p-icon').innerText = p.icon;
        document.getElementById('p-name').innerText = p.dead ? "תודעה טהורה (מת)" : p.name;
        document.getElementById('p-desc').innerText = p.dead ? "בחר מארח!" : p.desc;
        let hpPct = (p.hp / p.max) * 100;
        document.getElementById('hp-val').style.width = hpPct + "%";
        document.getElementById('hp-val').style.background = p.dead ? "transparent" : "#f33";

        // 2. Dead FX
        document.getElementById('red-screen').style.display = p.dead ? "block" : "none";
        
        // 3. Map
        let mapHTML = "";
        d.map.forEach(row => {
            mapHTML += `<div class="radar-row">`;
            row.forEach(c => mapHTML += `<div class="dot ${c.cls}">${c.icon}</div>`);
            mapHTML += `</div>`;
        });
        document.getElementById("map-target").innerHTML = mapHTML;

        // 4. Scene (Enemies)
        let sc = document.getElementById("scene");
        sc.innerHTML = "";
        if (d.enemies.length === 0) {
            sc.innerHTML = "<span style='color:#343; margin-top:20px'>...השטח פנוי...</span>";
        } else {
            d.enemies.forEach((e, i) => {
                // לוגיקה חכמה לכפתור
                let btnTxt = "⚔️ תקוף";
                let btnFn = "attack";
                let cls = "atk";
                
                if (p.dead) {
                    btnTxt = "🧬 השתלט";
                    btnFn = "infect";
                    cls = "inf";
                }
                
                let html = `
                <div class="card">
                    <div class="e-icon">${e.icon}</div>
                    <div style="font-weight:bold; font-size:12px;">${e.name}</div>
                    <div style="color:#d55; font-size:11px;">${e.hp} HP</div>
                    <button class="btn-act ${cls}" onclick="send('${btnFn}', ${i})">${btnTxt}</button>
                </div>
                `;
                sc.innerHTML += html;
            });
        }

        // 5. Logs
        let lb = document.getElementById("log-list");
        lb.innerHTML = "";
        d.log.reverse().forEach(l => {
            lb.innerHTML += `<div class="msg ${l.type}">${l.text}</div>`;
        });
    }
</script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(port=5006, debug=True)
