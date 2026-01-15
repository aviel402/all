import random
import uuid
import datetime
from flask import Flask, render_template_string, request, jsonify, session, url_for

app = Flask(__name__)
# מפתח חדש לאיפוס
app.secret_key = 'cyber_ops_final_fix_v3'

# ==========================================
# 💾 מאגר נתונים (DATABASE)
# ==========================================
PROGRAMS = {
    # התקפה
    "p_brute": {"name": "BRUTE_FORCE", "ram": 2, "dmg": 15, "risk": 3, "desc": "זול ומהיר."},
    "p_worm":  {"name": "SQL_WORM",    "ram": 4, "dmg": 35, "risk": 7, "desc": "נזק בינוני."},
    "p_nuke":  {"name": "ZERO_DAY",    "ram": 8, "dmg": 100, "risk": 20, "desc": "מכה קריטית."},
    
    # הגנה
    "d_clean": {"name": "LOG_CLEANER", "ram": 4, "heal_trace": 15, "desc": "-15% סיכון."},
    "d_proxy": {"name": "PROXY_CHAIN", "ram": 3, "heal_trace": 5, "desc": "-5% סיכון, זול."}
}

TARGETS = [
    {"name": "ATM שכונתי", "def": 30, "cash": 50, "sec": 1},
    {"name": "שרת בית ספר", "def": 80, "cash": 120, "sec": 1},
    {"name": "משרדי מס", "def": 250, "cash": 500, "sec": 2},
    {"name": "תאגיד סייבר", "def": 800, "cash": 1500, "sec": 3},
    {"name": "מחשב על צבאי", "def": 3000, "cash": 10000, "sec": 4}
]

# ==========================================
# ⚙️ לוגיקת משחק (Engine)
# ==========================================
class Engine:
    def __init__(self, state=None):
        if not state:
            self.reset_game()
        else:
            self.state = state

    def reset_game(self):
        self.state = {
            "money": 0,
            "ram": 10, "max_ram": 10,
            "cpu": 1,
            "trace": 0, "max_trace": 100,
            "active_conn": None,
            "targets": [],
            "game_over": False,
            "log": [{"time": self.now(), "txt": "SYSTEM ONLINE. Welcome, User.", "cls": "sys"}]
        }
        self.regen_targets()

    def now(self):
        return datetime.datetime.now().strftime("%H:%M:%S")

    def log(self, txt, cls="info"):
        self.state["log"].insert(0, {"time": self.now(), "txt": txt, "cls": cls})
        if len(self.state["log"]) > 30: self.state["log"].pop()

    def regen_targets(self):
        self.state["targets"] = []
        for _ in range(4):
            base = random.choice(TARGETS).copy()
            # קצת רנדומליות
            mult = random.uniform(0.9, 1.2)
            base["max_def"] = int(base["def"] * mult)
            base["def"] = base["max_def"]
            base["id"] = str(uuid.uuid4())
            self.state["targets"].append(base)

    # --- ACTIONS ---

    def connect(self, t_id):
        if self.state["game_over"]: return
        if self.state["active_conn"]: return

        tgt = next((t for t in self.state["targets"] if t["id"] == t_id), None)
        if tgt:
            self.state["active_conn"] = tgt
            self.log(f"Connection Established: {tgt['name']}", "sys")

    def disconnect(self):
        if not self.state["active_conn"]: return
        
        self.state["active_conn"] = None
        self.state["ram"] = self.state["max_ram"] # RESET RAM ON DISCONNECT (תיקון חשוב)
        self.log("Disconnected. RAM flushed & restored.", "sys")

    def run_prog(self, pid):
        if self.state["game_over"]: return
        prog = PROGRAMS[pid]
        
        # 1. בדיקת RAM
        if self.state["ram"] < prog["ram"]:
            self.log("ERROR: Insufficient RAM.", "err")
            return

        self.state["ram"] -= prog["ram"]

        # 2. האם תוכנת התקפה?
        if "dmg" in prog:
            tgt = self.state["active_conn"]
            if not tgt:
                self.log("Error: No connection target.", "err")
                self.state["ram"] += prog["ram"] # מחזיר עלות
                return
            
            # חישוב נזק
            dmg = prog["dmg"] * self.state["cpu"]
            tgt["def"] -= dmg
            
            # עליית סיכון (Trace)
            risk = prog["risk"]
            self.state["trace"] = min(100, self.state["trace"] + risk)
            
            self.log(f"Executing {prog['name']} >> Damage: {dmg}", "hack")
            
            # הצלחה?
            if tgt["def"] <= 0:
                reward = tgt["cash"]
                self.state["money"] += reward
                self.log(f"ACCESS GRANTED. Downloaded ${reward}", "win")
                
                # מחיקה ויצירה
                self.state["targets"].remove(tgt)
                self.state["active_conn"] = None
                self.state["ram"] = self.state["max_ram"] # פרס
                
                if not self.state["targets"]:
                    self.regen_targets()

        # 3. האם תוכנת הגנה?
        elif "heal_trace" in prog:
            heal = prog["heal_trace"] * self.state["cpu"]
            self.state["trace"] = max(0, self.state["trace"] - heal)
            self.log(f"Traces deleted. Risk lowered by {heal}%.", "def")

        # 4. בדיקת מוות
        if self.state["trace"] >= 100:
            self.state["game_over"] = True
            self.state["active_conn"] = None
            self.log("SYSTEM COMPROMISED. FBI DETECTED.", "err")

    def buy_upgrade(self, type):
        if self.state["game_over"]: return
        cost = 0
        if type == "ram":
            cost = self.state["max_ram"] * 20
            if self.state["money"] >= cost:
                self.state["money"] -= cost
                self.state["max_ram"] += 5
                self.state["ram"] = self.state["max_ram"]
                self.log(f"Upgrade Complete: RAM upgraded.", "win")
            else:
                self.log(f"Not enough credits. Need ${cost}", "err")
        elif type == "cpu":
            cost = self.state["cpu"] * 300
            if self.state["money"] >= cost:
                self.state["money"] -= cost
                self.state["cpu"] += 1
                self.log(f"Upgrade Complete: CPU upgraded.", "win")
            else:
                self.log(f"Not enough credits. Need ${cost}", "err")

# ==========================================
# ROUTES
# ==========================================
@app.route("/")
def home():
    if "uid" not in session: session["uid"] = str(uuid.uuid4())
    api_url = url_for("api")
    return render_template_string(UI, api=api_url)

@app.route("/api", methods=["POST"])
def api():
    try: eng = Engine(session.get("ops_game"))
    except: eng = Engine(None)
    
    req = request.json
    act = req.get("a")
    val = req.get("v")
    
    if act == "reset": eng.reset_game()
    elif act == "conn": eng.connect(val)
    elif act == "disc": eng.disconnect()
    elif act == "prog": eng.run_prog(val)
    elif act == "buy": eng.buy_upgrade(val)
    
    session["ops_game"] = eng.state
    return jsonify({"s": eng.state, "progs": PROGRAMS})

# ==========================================
# DESIGN & UI (CYBERPUNK GLASS)
# ==========================================
UI = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CYBER OPS</title>
<link href="https://fonts.googleapis.com/css2?family=Share+Tech+Mono&display=swap" rel="stylesheet">
<style>
    :root {
        --neon: #00ffc8;
        --neon-bad: #ff0055;
        --dark: #080a10;
        --panel: rgba(10, 20, 30, 0.9);
        --border: 1px solid rgba(0, 255, 200, 0.2);
    }
    
    * { box-sizing: border-box; user-select: none; }
    
    body {
        background: #020202; 
        background-image: linear-gradient(rgba(0, 255, 200, 0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0, 255, 200, 0.03) 1px, transparent 1px);
        background-size: 20px 20px;
        color: var(--neon);
        font-family: 'Share Tech Mono', monospace;
        margin: 0; height: 100vh; display: flex; flex-direction: column;
        overflow: hidden;
    }

    /* HEADER */
    header {
        height: 60px; display: flex; align-items: center; justify-content: space-between;
        padding: 0 20px; background: var(--panel); border-bottom: var(--border);
        box-shadow: 0 0 15px rgba(0, 255, 200, 0.1); z-index: 10;
    }
    .money { font-size: 24px; color: #ffbf00; text-shadow: 0 0 10px #ffbf00; }
    
    /* LAYOUT */
    .grid { flex: 1; display: grid; grid-template-columns: 280px 1fr 300px; gap: 10px; padding: 15px; overflow: hidden; }
    
    /* PANELS */
    .panel {
        background: var(--panel); border: var(--border); border-radius: 8px;
        display: flex; flex-direction: column; overflow: hidden; position: relative;
    }
    .panel h2 {
        margin: 0; padding: 10px; background: rgba(0,255,200,0.05); 
        font-size: 16px; border-bottom: var(--border); text-align: center;
        letter-spacing: 2px;
    }

    /* 1. STATS (Left) */
    .stat-row { padding: 15px; border-bottom: 1px dashed rgba(255,255,255,0.1); }
    .label { font-size: 12px; color: #88a; display: flex; justify-content: space-between;}
    .bar-bg { background: #111; height: 8px; margin-top: 5px; border-radius: 4px; overflow: hidden;}
    .bar-fill { height: 100%; transition: width 0.3s; background: var(--neon); }
    
    .shop-btn {
        width: 100%; background: transparent; border: 1px solid #446; color: #88a;
        padding: 10px; cursor: pointer; margin-top: 10px; transition: 0.2s; font-family: inherit;
    }
    .shop-btn:hover { border-color: var(--neon); color: var(--neon); background: rgba(0,255,200,0.1);}

    /* 2. TERMINAL (Middle) */
    .terminal { flex: 1; background: black; padding: 10px; font-size: 13px; overflow-y: auto; display: flex; flex-direction: column; gap: 4px;}
    .log-entry { opacity: 0.8; }
    .log-entry::before { content: "> "; color: #555; }
    .t-time { color: #555; font-size: 10px; margin-right: 5px; }
    .sys { color: #aaf; } .hack { color: #ffa; } .win { color: #0f0; } .err { color: #f55; } .def { color: #0ff; }

    /* 3. TARGETS (Right) */
    .target-list { flex: 1; overflow-y: auto; padding: 10px; }
    .target-card {
        background: #050505; border: 1px solid #334; padding: 10px; margin-bottom: 8px;
        cursor: pointer; transition: 0.2s; position: relative; overflow: hidden;
    }
    .target-card:hover { border-color: var(--neon); transform: translateX(-5px); }
    .t-name { font-weight: bold; font-size: 14px; }
    .t-sub { font-size: 11px; color: #777; display: flex; justify-content: space-between; margin-top: 5px;}
    
    /* 4. ACTIVE HACK (Replaces targets) */
    .hack-ui { display: none; flex-direction: column; height: 100%; padding: 10px; }
    .firewall-box { text-align: center; margin-bottom: 20px; }
    .firewall-hp { color: var(--neon-bad); font-size: 24px; font-weight: bold;}
    
    .deck { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; overflow-y: auto; }
    .prog-btn {
        background: rgba(0,0,0,0.5); border: 1px solid #334; color: #ccd;
        padding: 10px; cursor: pointer; text-align: center; transition: 0.1s;
    }
    .prog-btn:hover:not(:disabled) { border-color: white; background: rgba(255,255,255,0.05); }
    .prog-btn:disabled { opacity: 0.3; cursor: not-allowed; }
    
    .prog-name { display: block; font-weight: bold; font-size: 13px;}
    .prog-cost { font-size: 10px; color: #5aa; }
    
    .p-atk { border-color: #633; } .p-atk:hover:not(:disabled) { border-color: #f33; }
    .p-def { border-color: #244; } .p-def:hover:not(:disabled) { border-color: #48f; }

    .disc-btn { background: #311; color: #f55; border: 1px solid #500; margin-bottom: 10px; width: 100%; padding: 8px; cursor: pointer;}

    /* GLITCH EFFECT & OVERLAY */
    .game-over { 
        position: fixed; inset: 0; background: rgba(0,0,0,0.9); z-index: 99; 
        display: none; align-items: center; justify-content: center; flex-direction: column;
    }
    .glitch { font-size: 60px; color: red; text-shadow: 2px 2px 0px #0ff; animation: shake 0.5s infinite;}
    
    @keyframes shake { 0%{transform: translate(1px, 1px)} 50%{transform: translate(-1px, -2px)} 100%{transform: translate(0, 0)} }

    @media (max-width: 800px) {
        .grid { grid-template-columns: 1fr; grid-template-rows: auto 1fr auto; }
        .sidebar, .targets { height: 250px; }
    }
</style>
</head>
<body>

<div id="over-scr" class="game-over">
    <div class="glitch">SYSTEM FAILURE</div>
    <div style="color:white; margin:20px;">IP TRACED. CONNECTION TERMINATED.</div>
    <button onclick="api('reset')" style="background:var(--neon); border:none; padding:15px 30px; font-weight:bold; cursor:pointer;">REBOOT</button>
</div>

<header>
    <div>CYBER OPS <span style="font-size:10px; color:#555;">v2.4</span></div>
    <div class="money">$<span id="d-money">0</span></div>
</header>

<div class="grid">
    <!-- STATS -->
    <div class="panel">
        <h2>SYSTEM STATUS</h2>
        
        <div class="stat-row">
            <div class="label"><span>RISK LEVEL</span> <span id="d-trc">0%</span></div>
            <div class="bar-bg"><div id="b-trc" class="bar-fill" style="background:var(--neon-bad)"></div></div>
        </div>
        
        <div class="stat-row">
            <div class="label"><span>RAM AVAILABLE</span> <span id="d-ram">10/10</span></div>
            <div class="bar-bg"><div id="b-ram" class="bar-fill"></div></div>
        </div>
        
        <div class="stat-row">
            <div class="label">PROCESSOR: Lv.<span id="d-cpu">1</span></div>
        </div>

        <div style="margin-top:auto; padding:10px;">
            <button class="shop-btn" onclick="api('buy','ram')">BUY RAM (+5) $150+</button>
            <button class="shop-btn" onclick="api('buy','cpu')">BUY CPU (+x1) $300+</button>
        </div>
    </div>

    <!-- TERMINAL -->
    <div class="panel">
        <h2>TERMINAL_OUTPUT</h2>
        <div id="term" class="terminal"></div>
    </div>

    <!-- TARGETS -->
    <div class="panel">
        <h2>NETWORK TARGETS</h2>
        
        <!-- List Mode -->
        <div id="ui-list" class="target-list"></div>
        
        <!-- Hack Mode -->
        <div id="ui-hack" class="hack-ui">
            <button class="disc-btn" onclick="api('disc')">✖ ABORT CONNECTION</button>
            
            <div class="firewall-box">
                <div style="font-size:12px; color:#888;">FIREWALL STATUS</div>
                <div id="fw-hp" class="firewall-hp">100%</div>
                <div class="bar-bg" style="border-color:#500;"><div id="b-fw" class="bar-fill" style="background:red"></div></div>
            </div>
            
            <div id="prog-list" class="deck">
                <!-- Programs injected here -->
            </div>
        </div>
    </div>
</div>

<script>
const API = "{{ api }}";
let globalState = null;

window.onload = () => api('init');

async function api(a, v=null) {
    try {
        let res = await fetch(API, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({act:a, val:v})});
        let d = await res.json();
        
        if(d.s && d.s.game_over) {
            document.getElementById("over-scr").style.display = "flex";
            return;
        } else {
            document.getElementById("over-scr").style.display = "none";
        }

        render(d);
    } catch(e) { console.error(e); }
}

function render(d) {
    let s = d.state;
    globalState = s; // for tooltip logic maybe
    
    // Stats
    document.getElementById("d-money").innerText = s.money;
    document.getElementById("d-trc").innerText = s.trace + "%";
    document.getElementById("b-trc").style.width = s.trace + "%";
    
    document.getElementById("d-ram").innerText = s.ram + "/" + s.max_ram;
    let rp = (s.ram / s.max_ram) * 100;
    document.getElementById("b-ram").style.width = rp + "%";
    document.getElementById("d-cpu").innerText = s.cpu;

    // Log
    let t = document.getElementById("term");
    t.innerHTML = "";
    d.log.forEach(l => {
        t.innerHTML += `<div class="log-entry ${l.cls}"><span class="t-time">${l.time}</span> ${l.txt}</div>`;
    });

    // View Switching
    if(s.active_conn) {
        document.getElementById("ui-list").style.display = "none";
        document.getElementById("ui-hack").style.display = "flex";
        renderHack(s, d.programs);
    } else {
        document.getElementById("ui-list").style.display = "block";
        document.getElementById("ui-hack").style.display = "none";
        renderList(s.targets);
    }
}

function renderList(list) {
    let el = document.getElementById("ui-list");
    el.innerHTML = "";
    list.forEach(t => {
        el.innerHTML += `
        <div class="target-card" onclick="api('conn', '${t.id}')">
            <div class="t-name">${t.name}</div>
            <div class="t-sub">
                <span>🛡️ ${t.max_def}</span>
                <span style="color:#fc0">$${t.cash}</span>
            </div>
        </div>`;
    });
}

function renderHack(s, progs) {
    let t = s.active_conn;
    let pct = (t.def / t.max_def) * 100;
    document.getElementById("fw-hp").innerText = Math.ceil(pct) + "%";
    document.getElementById("b-fw").style.width = pct + "%";
    
    let grid = document.getElementById("prog-list");
    grid.innerHTML = "";
    
    for(let pid in progs) {
        let p = progs[pid];
        let typeClass = p.dmg ? "p-atk" : "p-def";
        let disabled = s.ram < p.ram ? "disabled" : "";
        
        grid.innerHTML += `
        <button class="prog-btn ${typeClass}" onclick="api('prog', '${pid}')" ${disabled}>
            <span class="prog-name">${p.name}</span>
            <span class="prog-cost">${p.ram} RAM</span>
        </button>`;
    }
}
</script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(port=5006, debug=True)
