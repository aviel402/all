import random
import uuid
import datetime
from flask import Flask, render_template_string, request, jsonify, session, url_for

app = Flask(__name__)
# מפתח חדש וחזק למניעת התנגשויות
app.secret_key = 'cyber_hacker_final_v99'

# ==========================================
# 💾 מאגר הכלים והמטרות
# ==========================================
PROGRAMS = {
    # תוכנות התקפה (מורידות הגנה, מעלות סיכון)
    "p1": {"name": "מכה קלה", "ram": 2, "dmg": 15, "risk": 4, "type": "atk", "desc": "זול ומהיר."},
    "p2": {"name": "הזרקת קוד",  "ram": 4, "dmg": 40, "risk": 8, "type": "atk", "desc": "נזק כבד."},
    "p3": {"name": "פריצה","ram": 8, "dmg": 100,"risk": 20,"type": "atk", "desc": "נשק יום הדין."},
    
    # תוכנות הגנה (מורידות סיכון)
    "d1": {"name": "הסתר IP",    "ram": 2, "heal": 5, "type": "def", "desc": "מוריד 5% מעקב."},
    "d2": {"name": "נקה לוגים",   "ram": 5, "heal": 20, "type": "def", "desc": "מנקה 20% מעקב."}
}

# ===============================================
#          ספר המטרות - עולם הסייבר
# ===============================================

TARGETS = [
    # --- רמה 1: "שכונה דיגיטלית" (קלים מאוד) ---
    {"name": "ראוטר של שכן", "def": 10, "cash": 15},
    {"name": "בית קפה", "def": 20, "cash": 25},
    {"name": "פיצרייה מקומית", "def": 30, "cash": 40},
    {"name": "כספומט שכונתי", "def": 50, "cash": 80}

    # --- רמה 2: "עסקים קטנים" (קלים) ---
    {"name": "מערכת ניהול של חנות בגדים", "def": 80, "cash": 120},
    {"name": "מחשב של מנהל סניף בנק", "def": 120, "cash": 200},
    {"name": "רשת בית ספר תיכון", "def": 150, "cash": 250},
    {"name": "שרת של חברת שליחויות", "def": 180, "cash": 300}

    # --- רמה 3: "תאגידים בינוניים" (בינוני) ---
        {"name": "מאגר נתונים של רשת שיווק", "def": 250, "cash": 500},
        {"name": "שרתי חברת ביטוח", "def": 300, "cash": 700},
        {"name": "בנק דיגיטלי קטן", "def": 400, "cash": 1000},
        {"name": "רשת מלונות ארצית", "def": 500, "cash": 1500}

    # --- רמה 4: "תשתיות קריטיות" (קשה) ---
    {"name": "מערכת הבקרה של הרכבת הקלה", "def": 700, "cash": 2200},
    {"name": "מאגר מידע של חברת אשראי", "def": 900, "cash": 3000},
    {"name": "שרתי משרד ממשלתי (חינוך)", "def": 1200, "cash": 4000},
    {"name": "תחנת כוח אזורית", "def": 1500, "cash": 5500}

    # --- רמה 5: "ביטחון לאומי" (קשה מאוד) ---
    {"name": "שרת המידע של המשטרה", "def": 2000, "cash": 8000},
    {"name": "מערכת המכ'ם של שדה התעופה", "def": 2500, "cash": 11000},
    {"name": "לוויין תקשורת ממשלתי", "def": 3500, "cash": 15000},
    {"name": "שרתי המוסד", "def": 5000, "cash": 25000}

    # --- רמה 6: "הגדולים ביותר" (אגדי) ---
    {"name": "מחשבי הבורסה לניירות ערך", "def": 7500, "cash": 50000},
    {"name": "רשת הבנקים הבינלאומית", "def": 10000, "cash": 80000},
    {"name": "שרתי הפנטגון", "def": 15000, "cash": 150000},
    {"name": "המחשב המרכזי של אילון מאסק", "def": 25000, "cash": 300000}
]

# ==========================================
# ⚙️ מנוע המשחק
# ==========================================
class GameEngine:
    def __init__(self, state=None):
        if not state:
            self.reset()
        else:
            self.state = state

    def reset(self):
        self.state = {
            "money": 0,
            "ram": 10, "max_ram": 10,
            "cpu": 1,
            "trace": 0,
            "active_target": None, # האובייקט המחובר
            "targets_list": [],
            "game_over": False,
            "log": [{"time": self.getTime(), "txt": "מערכת פריצה מוכנה", "c": "sys"}]
        }
        self.generate_targets()

    def getTime(self):
        return datetime.datetime.now().strftime("%H:%M:%S")

    def log(self, txt, c="info"):
        self.state["log"].insert(0, {"time": self.getTime(), "txt": txt, "c": c})
        if len(self.state["log"]) > 20: self.state["log"].pop()

    def generate_targets(self):
        self.state["targets_list"] = []
        for _ in range(4):
            base = random.choice(TARGETS).copy()
            # וריאציה כדי שכל משחק יהיה שונה
            mod = random.uniform(0.9, 1.2)
            base["max_def"] = int(base["def"] * mod)
            base["def"] = base["max_def"]
            base["id"] = str(uuid.uuid4())
            self.state["targets_list"].append(base)

    # --- לוגיקת פעולות ---

    def connect(self, target_id):
        if self.state["active_target"]: return # כבר מחובר
        
        # חיפוש היעד ברשימה
        t = next((i for i in self.state["targets_list"] if i["id"] == target_id), None)
        if t:
            self.state["active_target"] = t
            self.log(f"Connection established to: {t['name']}", "sys")

    def disconnect(self):
        if not self.state["active_target"]: return
        
        # ניתוק מחזיר RAM מלא! (תיקון חשוב)
        self.state["active_target"] = None
        self.state["ram"] = self.state["max_ram"]
        self.log("Disconnected. Memory buffer flushed (RAM 100%).", "sys")

    def execute(self, prog_key):
        if self.state["game_over"]: return
        
        prog = PROGRAMS[prog_key]
        
        # 1. בדיקת RAM
        if self.state["ram"] < prog["ram"]:
            self.log("Error: Not enough RAM. Disconnect to recharge.", "err")
            return

        self.state["ram"] -= prog["ram"]

        # 2. הרצה (תקיפה או הגנה)
        target = self.state["active_target"]
        
        if prog["type"] == "atk":
            if not target: 
                self.log("No target connected.", "err")
                self.state["ram"] += prog["ram"] # החזרת RAM אם אין מטרה
                return
                
            dmg = prog["dmg"] * self.state["cpu"]
            target["def"] -= dmg
            
            # עליה ברמת הסיכון
            self.state["trace"] = min(100, self.state["trace"] + prog["risk"])
            self.log(f"Running {prog['name']} >> Damage: {dmg}", "hack")
            
            # בדיקת פריצה מוצלחת
            if target["def"] <= 0:
                reward = target["cash"]
                self.state["money"] += reward
                self.log(f"ACCESS GRANTED! Stolen: ${reward}", "win")
                
                # ניתוק אוטומטי ומחיקת המטרה
                self.state["targets_list"].remove(target)
                self.state["active_target"] = None
                self.state["ram"] = self.state["max_ram"]
                
                if not self.state["targets_list"]: self.generate_targets()

        elif prog["type"] == "def":
            heal = prog["heal"] * self.state["cpu"]
            self.state["trace"] = max(0, self.state["trace"] - heal)
            self.log(f"Trace logs scrubbed. Security -{heal}%", "def")

        # 3. בדיקת משטרה (Game Over)
        if self.state["trace"] >= 100:
            self.state["game_over"] = True
            self.state["active_target"] = None
            self.log("!! SIGNAL TRACED BY FBI !! TERMINATING...", "err")

    def buy(self, item):
        if self.state["game_over"]: return
        
        cost = 0
        if item == "ram":
            cost = self.state["max_ram"] * 25
            if self.state["money"] >= cost:
                self.state["money"] -= cost
                self.state["max_ram"] += 5
                self.state["ram"] = self.state["max_ram"]
                self.log(f"RAM Upgraded to {self.state['max_ram']}GB", "sys")
            else:
                self.log(f"Insufficient funds. Need ${cost}", "err")
                
        elif item == "cpu":
            cost = self.state["cpu"] * 400
            if self.state["money"] >= cost:
                self.state["money"] -= cost
                self.state["cpu"] += 1
                self.log(f"CPU Upgraded to Level {self.state['cpu']}", "sys")
            else:
                self.log(f"Insufficient funds. Need ${cost}", "err")

# ==========================================
# FLASK SERVER
# ==========================================
@app.route("/")
def index():
    if "uid" not in session: session["uid"] = str(uuid.uuid4())
    api = url_for("api")
    return render_template_string(HTML, api=api)

@app.route("/api", methods=["POST"])
def api():
    try: 
        eng = GameEngine(session.get("cyb_v3"))
    except: 
        eng = GameEngine(None) # Safe reset

    d = request.json or {}
    act = d.get("a")
    val = d.get("v")

    if act == "init": pass 
    elif act == "reset": eng.reset()
    elif act == "conn": eng.connect(val)
    elif act == "disc": eng.disconnect()
    elif act == "exec": eng.execute(val)
    elif act == "buy": eng.buy(val)

    session["cyb_v3"] = eng.state
    
    return jsonify({
        "s": eng.state, 
        "progs": PROGRAMS
    })

# ==========================================
# CLIENT (HTML/CSS/JS)
# ==========================================
HTML = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>RED_CODE_TERMINAL</title>
<link href="https://fonts.googleapis.com/css2?family=Share+Tech+Mono&display=swap" rel="stylesheet">
<style>
    :root { 
        --prim: #0f0; --dim: #004400; --bg: #050505; --panel: #0a0a0a;
        --warn: #ffcc00; --danger: #ff0044; --border: 1px solid #0f0;
    }
    
    body {
        background: var(--bg); color: var(--prim);
        font-family: 'Share Tech Mono', monospace;
        margin: 0; height: 100vh; display: flex; flex-direction: column; overflow: hidden;
    }
    
    /* CRT EFFECT OVERLAY */
    .crt::before {
        content: " "; display: block; position: absolute; top: 0; left: 0; bottom: 0; right: 0;
        background: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.25) 50%), linear-gradient(90deg, rgba(255, 0, 0, 0.06), rgba(0, 255, 0, 0.02), rgba(0, 0, 255, 0.06));
        z-index: 2; background-size: 100% 2px, 3px 100%; pointer-events: none;
    }

    /* TOP BAR */
    .header {
        height: 60px; border-bottom: var(--border); padding: 0 20px; display: flex; 
        justify-content: space-between; align-items: center; background: #001100;
        box-shadow: 0 0 15px var(--dim); z-index: 3;
    }
    .money { font-size: 24px; color: var(--warn); text-shadow: 0 0 5px var(--warn);}

    /* GRID LAYOUT */
    .grid { flex: 1; display: grid; grid-template-columns: 260px 1fr 280px; gap: 10px; padding: 10px; position: relative; z-index: 1;}

    /* BOXES */
    .box { border: var(--border); background: rgba(0,10,0,0.8); display: flex; flex-direction: column; padding: 10px; overflow: hidden;}
    .title { background: var(--dim); padding: 5px; text-align: center; font-weight: bold; margin-bottom: 10px;}

    /* BARS */
    .bar-row { margin-bottom: 15px; }
    .label { display: flex; justify-content: space-between; font-size: 12px; margin-bottom: 2px;}
    .bar-track { height: 12px; background: #111; border: 1px solid #333; width: 100%;}
    .bar-fill { height: 100%; background: var(--prim); width: 0%; transition: 0.3s; }
    .trace-fill { background: var(--danger); box-shadow: 0 0 8px var(--danger);}

    /* TERMINAL */
    .log-view { flex: 1; overflow-y: auto; font-size: 14px; display: flex; flex-direction: column; gap: 4px; border-top: 1px solid #333; padding-top: 5px;}
    .l-entry { opacity: 0.8; }
    .l-entry::before { content: "> "; color: #555; }
    .t-time { font-size: 10px; color: #666; margin-right: 5px; }
    .sys { color: #8cf; } .err { color: #f55; } .win { color: #5f5; } .hack { color: #ffeb3b; }

    /* LIST */
    .target-card { border: 1px dashed #005500; padding: 8px; margin-bottom: 5px; cursor: pointer; transition: 0.2s; display:flex; justify-content:space-between; align-items:center;}
    .target-card:hover { background: #002200; border-color: #0f0; }
    .locked { color: #aaa; pointer-events: none; opacity: 0.5; }

    /* HACK INTERFACE */
    .hack-area { display: none; flex-direction: column; height: 100%; }
    .prog-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 5px; margin-top: auto;}
    .btn { background: #001100; border: 1px solid #004400; color: #0a0; padding: 10px; cursor: pointer; text-align: center; }
    .btn:hover:not(:disabled) { border-color: #0f0; color: #0f0; background: #002200;}
    .btn:disabled { opacity: 0.3; cursor: not-allowed; filter: grayscale(1); }
    .p-atk { border-color: #630; color: #ca0; } .p-atk:hover { background: #210; border-color: #f80;}
    .p-def { border-color: #036; color: #6bf; } .p-def:hover { background: #012; border-color: #0af;}

    /* SHOP BUTTONS */
    .shop { margin-top: auto; display: flex; gap: 5px; }
    .s-btn { flex: 1; border: 1px solid #444; background: transparent; color: #888; cursor: pointer; padding: 5px; font-size: 12px; }
    .s-btn:hover { border-color: gold; color: gold; }

    /* MODAL */
    .modal { position: fixed; inset: 0; background: rgba(0,0,0,0.95); z-index: 100; display: none; align-items: center; justify-content: center; flex-direction: column; color: red;}
    .glitch { font-size: 50px; text-shadow: 2px 0 blue, -2px 0 red; animation: glitch 0.2s infinite; }
    
    @keyframes glitch { 0%{transform: translate(0)} 20%{transform: translate(-2px, 2px)} 40%{transform: translate(-2px, -2px)} 60%{transform: translate(2px, 2px)} 80%{transform: translate(2px, -2px)} 100%{transform: translate(0)} }

    @media(max-width:800px) { .grid { grid-template-columns: 1fr; } }
</style>
</head>
<body class="crt">

<div id="m-lose" class="modal">
    <div class="glitch">CONNECTION LOST</div>
    <div style="color:white; margin:20px">IP נחשף. כוחות משטרה בדרך.</div>
    <button onclick="api('reset')" style="border:2px solid red; background:black; color:red; padding:15px 30px; font-size:20px; cursor:pointer;">SYSTEM REBOOT</button>
</div>

<header>
    <div>CYBER_OPS_V4</div>
    <div class="money">$<span id="v-cash">0</span></div>
</header>

<div class="grid">
    
    <!-- LEFT: STATS -->
    <div class="box">
        <div class="title">SYSTEM_STATUS</div>
        
        <div class="bar-row">
            <div class="label"><span>TRACE_LEVEL</span> <span id="t-trace">0%</span></div>
            <div class="bar-track"><div id="b-trace" class="bar-fill trace-fill"></div></div>
        </div>
        
        <div class="bar-row">
            <div class="label"><span>RAM_BUFFER</span> <span id="t-ram">10/10</span></div>
            <div class="bar-track"><div id="b-ram" class="bar-fill"></div></div>
        </div>
        
        <div class="label" style="margin-top:10px;">CPU_SPEED: Lv <span id="v-cpu" style="color:gold">1</span></div>

        <div class="shop">
            <button class="s-btn" onclick="api('buy','ram')">UPG RAM (25$ xMax)</button>
            <button class="s-btn" onclick="api('buy','cpu')">UPG CPU (400$ xLv)</button>
        </div>
    </div>

    <!-- MIDDLE: TERMINAL -->
    <div class="box" style="flex:2;">
        <div class="title">ROOT_TERMINAL</div>
        <div id="logs" class="log-view"></div>
    </div>

    <!-- RIGHT: TARGETS -->
    <div class="box">
        <div class="title">NETWORK</div>
        
        <!-- List Mode -->
        <div id="list-ui"></div>
        
        <!-- Hack Mode -->
        <div id="hack-ui" class="hack-area">
            <div style="border-bottom:1px solid #333; padding-bottom:10px; margin-bottom:10px; display:flex; justify-content:space-between; align-items:center;">
                <span id="tgt-name" style="color:var(--warn)">...</span>
                <button onclick="api('disc')" style="background:none; border:1px solid #f00; color:#f00; cursor:pointer;">[X] EXIT</button>
            </div>
            
            <div style="font-size:12px; color:#555">FIREWALL</div>
            <div class="bar-track" style="margin-bottom:10px; border-color:var(--warn);"><div id="tgt-bar" class="bar-fill" style="background:var(--warn);"></div></div>
            
            <div class="prog-grid" id="progs"></div>
        </div>
    </div>

</div>

<script>
    const API = "{{ api }}";
    
    window.onload = ()=> api('init');

    async function api(act, val=null) {
        let res = await fetch(API, {
            method:'POST', headers:{'Content-Type':'application/json'},
            body: JSON.stringify({a:act, v:val})
        });
        let d = await res.json();
        
        if (d.s.game_over) {
            document.getElementById("m-lose").style.display = "flex";
            return;
        } else {
            document.getElementById("m-lose").style.display = "none";
        }

        render(d.s, d.progs);
    }

    function render(s, progs) {
        // Stats
        document.getElementById("v-cash").innerText = s.money;
        document.getElementById("t-trace").innerText = s.trace + "%";
        document.getElementById("b-trace").style.width = s.trace + "%";
        
        document.getElementById("t-ram").innerText = s.ram + "/" + s.max_ram;
        document.getElementById("b-ram").style.width = (s.ram/s.max_ram)*100 + "%";
        document.getElementById("v-cpu").innerText = s.cpu;

        // Log
        let lbox = document.getElementById("logs");
        lbox.innerHTML = "";
        s.log.forEach(l => {
            lbox.innerHTML += `<div class="l-entry ${l.c}"><span class="t-time">${l.time}</span> ${l.txt}</div>`;
        });

        // Toggle Views
        if(s.active_target) {
            document.getElementById("list-ui").style.display="none";
            document.getElementById("hack-ui").style.display="flex";
            renderHack(s, progs);
        } else {
            document.getElementById("list-ui").style.display="block";
            document.getElementById("hack-ui").style.display="none";
            renderList(s.targets_list);
        }
    }

    function renderList(list) {
        let h = "";
        list.forEach(t => {
            h += `<div class="target-card" onclick="api('conn', '${t.id}')">
                <div>
                    <div style="font-weight:bold">${t.name}</div>
                    <div style="font-size:12px; color:#555">HP: ${t.max_def} | Loot: $${t.cash}</div>
                </div>
                <div style="color:lime">></div>
            </div>`;
        });
        document.getElementById("list-ui").innerHTML = h;
    }

    function renderHack(s, progs) {
        let t = s.active_target;
        document.getElementById("tgt-name").innerText = t.name;
        document.getElementById("tgt-bar").style.width = (t.def / t.max_def) * 100 + "%";
        
        let h = "";
        for(let k in progs) {
            let p = progs[k];
            let cls = (p.type === "atk") ? "p-atk" : "p-def";
            let dis = (s.ram < p.ram) ? "disabled" : "";
            
            h += `<button class="btn ${cls}" ${dis} onclick="api('exec', '${k}')">
                <div style="font-weight:bold">${p.name}</div>
                <div style="font-size:10px">${p.ram} RAM | ${p.desc}</div>
            </button>`;
        }
        document.getElementById("progs").innerHTML = h;
    }
</script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(port=5006, debug=True)
