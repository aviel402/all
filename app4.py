import random
import uuid
import time
from flask import Flask, render_template_string, request, jsonify, session, url_for

app = Flask(__name__)
app.secret_key = 'hacker_elite_v1'

# ==========================================
# 💾 מאגר נתונים (תוכנות וחומרה)
# ==========================================
PROGRAMS = {
    "brute_force": {"name": "Brute Force v1", "cost_ram": 2, "dmg": 10, "risk": 5, "desc": "התקפה רועשת ומהירה."},
    "sql_inject": {"name": "SQL Injection", "cost_ram": 4, "dmg": 25, "risk": 10, "desc": "חדירה למסד נתונים."},
    "rootkit": {"name": "Rootkit Zero", "cost_ram": 8, "dmg": 60, "risk": 20, "desc": "השתלטות מוחלטת."},
    "log_wiper": {"name": "Log Wiper", "cost_ram": 5, "effect": "reduce_trace", "val": 20, "desc": "מוחק עקבות. מוריד Trace."},
    "proxy_hop": {"name": "Proxy Hop", "cost_ram": 3, "effect": "reduce_trace", "val": 10, "desc": "מסתיר את ה-IP."}
}

TARGETS_DB = [
    {"name": "Local Pizza Shop", "def": 20, "reward": 50, "sec_level": 1},
    {"name": "City Library", "def": 50, "reward": 120, "sec_level": 1},
    {"name": "Bank of America", "def": 200, "reward": 800, "sec_level": 2},
    {"name": "Gov. Secure DB", "def": 500, "reward": 2000, "sec_level": 3},
    {"name": "NSA Black Server", "def": 1500, "reward": 10000, "sec_level": 4}
]

# ==========================================
# ⚙️ מנוע ההאקינג
# ==========================================
class Engine:
    def __init__(self, state=None):
        if not state:
            self.state = {
                # משאבים
                "bitcoin": 0,
                "ram": 10,       # משמש כ"אנרגיה" לתורות
                "max_ram": 10,
                "cpu_lvl": 1,    # מכפיל נזק
                
                # סטטוס נוכחי
                "trace": 0,      # מד מעקב משטרתי (0-100)
                "connected_to": None, # האם אני מחובר לשרת כרגע?
                
                # עולם
                "targets": [],   # רשימת מטרות פעילות
                "log": [{"text": "M.A.T.R.I.X OS v9.2 Loaded...", "type": "sys"}]
            }
            self.refresh_targets()
        else:
            self.state = state

    def log(self, txt, type="info"): 
        # מוסיף שעה למראה מקצועי
        import datetime
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        self.state["log"].insert(0, {"text": f"[{ts}] {txt}", "type": type}) # חדש למעלה
        if len(self.state["log"]) > 20: self.state["log"].pop()

    def refresh_targets(self):
        # מגריל 3 מטרות רנדומליות
        self.state["targets"] = []
        for _ in range(3):
            t = random.choice(TARGETS_DB).copy()
            # קצת גיוון במספרים
            t["max_def"] = int(t["def"] * random.uniform(0.8, 1.2))
            t["def"] = t["max_def"]
            t["id"] = str(uuid.uuid4())[:8]
            self.state["targets"].append(t)

    # --- פעולות ---

    def connect(self, target_id):
        if self.state["connected_to"]:
            self.log("שגיאה: כבר מחובר לשרת. התנתק קודם.", "error")
            return

        target = next((t for t in self.state["targets"] if t["id"] == target_id), None)
        if target:
            self.state["connected_to"] = target
            self.log(f"CONNECTING TO {target['name']} [IP: 192.168.X.X]...", "sys")
            self.log("החיבור בוצע. חומת האש פעילה.", "success")
        
    def disconnect(self):
        if not self.state["connected_to"]: return
        
        self.log(f"DISCONNECTING from {self.state['connected_to']['name']}...", "sys")
        self.state["connected_to"] = None
        self.state["ram"] = self.state["max_ram"] # זיכרון מתנקה בהתנתקות
        self.log("מערכת ב-Idle. זיכרון RAM שוחרר.", "info")

    def run_program(self, prog_key):
        if not self.state["connected_to"]:
            # אם מנסים להריץ תוכנות הגנה בלי להיות מחוברים (מנקים Trace מהבית)
            if prog_key in ["log_wiper", "proxy_hop"]:
                self.run_defense(prog_key)
                return
            else:
                self.log("שגיאה: אין יעד. התחבר לשרת קודם.", "error")
                return

        prog = PROGRAMS[prog_key]
        target = self.state["connected_to"]

        # בדיקת RAM
        if self.state["ram"] < prog["cost_ram"]:
            self.log("⚠️ זיכרון RAM לא מספיק להרצת התוכנה!", "error")
            return

        self.state["ram"] -= prog["cost_ram"]

        # 1. תוכנות התקפה
        if "dmg" in prog:
            damage = prog["dmg"] * self.state["cpu_lvl"]
            target["def"] -= damage
            self.state["trace"] += prog["risk"]
            
            self.log(f"Running {prog['name']} >> Uploading payload... Hit: {damage}", "hack")
            
            if target["def"] <= 0:
                self.hack_success(target)

        # 2. תוכנות הגנה (תוך כדי פריצה)
        elif "effect" in prog:
            if prog["effect"] == "reduce_trace":
                self.state["trace"] = max(0, self.state["trace"] - prog["val"])
                self.log(f"Trace scrubbed. Current Level: {self.state['trace']}%", "success")

        # בדיקת כשלון (משטרה)
        if self.state["trace"] >= 100:
            return "game_over"

        return "ok"

    def run_defense(self, prog_key):
        # הרצת כלים בבית
        prog = PROGRAMS[prog_key]
        if self.state["ram"] < prog["cost_ram"]:
            self.log("אין מספיק RAM.", "error")
            return
        
        self.state["ram"] -= prog["cost_ram"]
        if prog["effect"] == "reduce_trace":
            self.state["trace"] = max(0, self.state["trace"] - prog["val"])
            self.log(f"Logs Cleaned. Trace: {self.state['trace']}%", "success")

    def hack_success(self, target):
        loot = target["reward"]
        self.state["bitcoin"] += loot
        self.log(f"ACCESS GRANTED! Root privileges obtained.", "gold")
        self.log(f"העברת {loot} BTC לחשבון מוצפן.", "gold")
        
        # מסירים את המטרה ומנתקים
        self.state["targets"].remove(target)
        self.state["connected_to"] = None
        self.state["ram"] = self.state["max_ram"]
        
        # רענון מטרות אם נגמר
        if not self.state["targets"]:
            self.refresh_targets()

    # --- חנות שדרוגים ---
    def upgrade(self, type):
        cost = 0
        if type == "ram":
            cost = self.state["max_ram"] * 10
            if self.state["bitcoin"] >= cost:
                self.state["bitcoin"] -= cost
                self.state["max_ram"] += 5
                self.state["ram"] = self.state["max_ram"]
                self.log(f"UPGRADE: RAM הוגדל ל-{self.state['max_ram']}GB", "sys")
            else:
                self.log("העברה נדחתה. אין מספיק כסף.", "error")

        elif type == "cpu":
            cost = self.state["cpu_lvl"] * 500
            if self.state["bitcoin"] >= cost:
                self.state["bitcoin"] -= cost
                self.state["cpu_lvl"] += 1
                self.log(f"UPGRADE: מעבד שודרג לרמה {self.state['cpu_lvl']}", "sys")
            else:
                self.log("אין מספיק כסף למעבד חדש.", "error")

# ==========================================
# SERVER
# ==========================================
@app.route("/")
def index():
    if "uid" not in session: session["uid"] = str(uuid.uuid4())
    return render_template_string(HTML, api=url_for("action"))

@app.route("/action", methods=["POST"])
def action():
    try: eng = Engine(session.get("hacker_save"))
    except: eng = Engine(None)
    
    d = request.json
    act = d.get("act")
    val = d.get("val")
    
    status = "ok"
    
    if act == "connect": eng.connect(val)
    elif act == "disconnect": eng.disconnect()
    elif act == "run": status = eng.run_program(val)
    elif act == "buy": eng.upgrade(val)
    elif act == "reset": eng = Engine(None)
    
    if status == "game_over":
        return jsonify({"game_over": True})

    session["hacker_save"] = eng.state
    
    return jsonify({
        "log": eng.state["log"],
        "state": eng.state,
        "programs": PROGRAMS
    })

# ==========================================
# UI - THE MATRIX STYLE
# ==========================================
HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CYBER-HEIST</title>
<link href="https://fonts.googleapis.com/css2?family=VT323&display=swap" rel="stylesheet">
<style>
    :root { --green: #0f0; --dim-green: #004400; --bg: #000; --red: #f00; --yellow: #ff0;}
    body { background: var(--bg); color: var(--green); font-family: 'VT323', monospace; margin: 0; height: 100vh; display: flex; overflow: hidden; font-size: 20px;}
    
    /* Layout */
    .left-panel { width: 300px; border-right: 1px solid var(--dim-green); display: flex; flex-direction: column; padding: 10px; }
    .main-panel { flex: 1; display: flex; flex-direction: column; padding: 20px; position: relative;}
    
    /* Bars */
    .bar-box { margin-bottom: 15px; }
    .label { display: flex; justify-content: space-between; margin-bottom: 2px;}
    .progress-bg { width: 100%; height: 20px; background: #111; border: 1px solid var(--dim-green); }
    .progress-fill { height: 100%; width: 0%; transition: 0.3s; background: var(--green); }
    .trace-fill { background: var(--red); }
    
    /* Target List */
    .server-list { flex: 1; overflow-y: auto; }
    .server-card { 
        border: 1px dashed var(--dim-green); padding: 10px; margin-bottom: 10px; cursor: pointer; transition: 0.1s;
        display: flex; justify-content: space-between; align-items: center;
    }
    .server-card:hover { background: #001100; border-color: var(--green); }
    .server-name { font-weight: bold; font-size: 1.1em;}
    .locked { color: var(--red); } .open { color: var(--green); }

    /* Central Terminal */
    .terminal { flex: 1; border: 2px solid var(--green); padding: 10px; background: #000500; overflow-y: auto; display: flex; flex-direction: column-reverse; margin-bottom: 20px; box-shadow: 0 0 10px var(--dim-green); }
    .line { margin-bottom: 2px; }
    .line.sys { color: #55ff55; }
    .line.error { color: #ff5555; }
    .line.hack { color: #ffff55; }
    .line.gold { color: gold; text-shadow: 0 0 5px gold; }

    /* Action Deck (Programs) */
    .deck { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 10px; height: 120px;}
    .program-btn { 
        background: #001100; border: 1px solid var(--green); color: var(--green); 
        cursor: pointer; font-family: inherit; font-size: 18px; padding: 5px;
        display: flex; flex-direction: column; align-items: center; justify-content: center;
        text-transform: uppercase;
    }
    .program-btn:hover { background: var(--green); color: black; }
    .program-btn:disabled { opacity: 0.3; cursor: not-allowed; border-color: #333; color: #555; background:black;}
    
    /* Danger Overlay */
    .busted { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: black; color: red; display: none; align-items: center; justify-content: center; flex-direction: column; font-size: 40px; z-index: 99;}
    
    .status-active { border: 1px solid gold; padding: 10px; margin-bottom: 20px; display: none; }
    
</style>
</head>
<body>

<div id="busted-screen" class="busted">
    <div>⚠️ CONNECTION TERMINATED</div>
    <div style="font-size: 20px; margin-top:20px;">FBI IS AT YOUR DOOR.</div>
    <button onclick="send('reset')" style="background:red; color:black; font-family:inherit; font-size:24px; border:none; margin-top:20px; cursor:pointer;">REBOOT SYSTEM</button>
</div>

<div class="left-panel">
    <div style="text-align:center; margin-bottom:20px; font-size:24px; text-shadow: 0 0 5px var(--green);">NET_RUNNER</div>
    
    <!-- Stats -->
    <div class="bar-box">
        <div class="label"><span>TRACE (משטרה)</span> <span id="txt-trace">0%</span></div>
        <div class="progress-bg"><div class="progress-fill trace-fill" id="bar-trace"></div></div>
    </div>
    
    <div class="bar-box">
        <div class="label"><span>RAM (פעולות)</span> <span id="txt-ram">10/10</span></div>
        <div class="progress-bg"><div class="progress-fill" id="bar-ram"></div></div>
    </div>
    
    <div style="border-top:1px solid #333; padding-top:10px; margin-top:10px;">
        <div style="color:gold; font-size:24px;">₿ <span id="txt-btc">0.00</span></div>
        <div style="font-size:16px; color:#aaa">CPU LEVEL: <span id="txt-cpu">1</span></div>
    </div>

    <!-- Upgrade Shop -->
    <div style="margin-top:auto;">
        <button class="program-btn" onclick="send('buy','ram')" style="width:100%; margin-bottom:5px;">
            <small>UPGRADE RAM</small>
        </button>
        <button class="program-btn" onclick="send('buy','cpu')" style="width:100%;">
            <small>UPGRADE CPU</small>
        </button>
    </div>
</div>

<div class="main-panel">
    <!-- Active Target Info -->
    <div class="status-active" id="active-panel">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <span>TARGET: <strong id="t-name">...</strong></span>
            <button onclick="send('disconnect')" style="background:red; border:none; color:white; cursor:pointer; font-family:inherit;">[X] DISCONNECT</button>
        </div>
        <div class="progress-bg" style="margin-top:10px; border-color:gold;">
            <div class="progress-fill" id="bar-firewall" style="background:gold; width:100%"></div>
        </div>
        <div style="text-align:right; font-size:14px; color:gold;">FIREWALL INTEGRITY</div>
    </div>

    <div class="terminal" id="term"></div>
    
    <!-- Modes: Server List VS Attack Deck -->
    <div id="mode-select" class="server-list"></div>
    
    <div id="mode-hack" class="deck" style="display:none;">
        <button class="program-btn" onclick="send('run','brute_force')">
            BRUTE FORCE
            <small style="font-size:12px">2 RAM | Med Risk</small>
        </button>
        <button class="program-btn" onclick="send('run','sql_inject')">
            SQL INJECT
            <small style="font-size:12px">4 RAM | High DMG</small>
        </button>
        <button class="program-btn" onclick="send('run','rootkit')">
            ROOTKIT
            <small style="font-size:12px">8 RAM | MAX DMG</small>
        </button>
        <button class="program-btn" onclick="send('run','log_wiper')" style="color:#aaf; border-color:#aaf">
            LOG WIPER
            <small style="font-size:12px">-20% TRACE</small>
        </button>
        <button class="program-btn" onclick="send('run','proxy_hop')" style="color:#aaf; border-color:#aaf">
            PROXY HOP
            <small style="font-size:12px">-10% TRACE</small>
        </button>
    </div>
</div>

<script>
    const API = "{{ api }}";
    
    window.onload = ()=> send('init');

    async function send(act, val=null){
        let res = await fetch(API, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({act:act, val:val})});
        let d = await res.json();
        
        if(d.game_over) {
            document.getElementById("busted-screen").style.display = "flex";
            return;
        } else {
            document.getElementById("busted-screen").style.display = "none";
        }

        let s = d.state;
        
        // 1. Logs
        let t = document.getElementById("term");
        t.innerHTML = "";
        d.log.forEach(line => {
            t.innerHTML += `<div class="line ${line.type}">> ${line.text}</div>`;
        });

        // 2. Stats
        document.getElementById("txt-trace").innerText = s.trace + "%";
        document.getElementById("bar-trace").style.width = s.trace + "%";
        
        document.getElementById("txt-ram").innerText = s.ram + "/" + s.max_ram;
        let ramPct = (s.ram / s.max_ram)*100;
        document.getElementById("bar-ram").style.width = ramPct + "%";
        
        document.getElementById("txt-btc").innerText = s.bitcoin;
        document.getElementById("txt-cpu").innerText = s.cpu_lvl;

        // 3. UI Mode Switcher
        if (s.connected_to) {
            // HACKING MODE
            document.getElementById("mode-select").style.display = "none";
            document.getElementById("mode-hack").style.display = "grid";
            document.getElementById("active-panel").style.display = "block";
            
            // Active target update
            let trg = s.connected_to;
            document.getElementById("t-name").innerText = trg.name;
            let fwPct = (trg.def / trg.max_def) * 100;
            document.getElementById("bar-firewall").style.width = fwPct + "%";
            
        } else {
            // SELECTION MODE
            document.getElementById("mode-select").style.display = "block";
            document.getElementById("mode-hack").style.display = "none";
            document.getElementById("active-panel").style.display = "none";
            
            // Build list
            let listHTML = "";
            s.targets.forEach(t => {
                listHTML += `
                <div class="server-card" onclick="send('connect', '${t.id}')">
                    <div>
                        <div class="server-name">${t.name}</div>
                        <div style="font-size:14px; color:#555">Firewall: ${t.max_def} | Loot: ${t.reward} BTC</div>
                    </div>
                    <div class="open">CONNECT ></div>
                </div>`;
            });
            document.getElementById("mode-select").innerHTML = listHTML;
        }
    }
</script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(port=5006, debug=True)
