import random
import uuid
import time
from flask import Flask, render_template_string, request, jsonify, session, url_for

app = Flask(__name__)
app.secret_key = 'hebrew_hacker_final_v1'

# ==========================================
# 💾 מאגר נתונים (עברית מלאה)
# ==========================================
PROGRAMS = {
    "brute_force": {"name": "כוח גס (BruteForce)", "cost_ram": 2, "dmg": 10, "risk": 5, "desc": "התקפה רועשת ומהירה."},
    "sql_inject": {"name": "הזרקת קוד (SQL)", "cost_ram": 4, "dmg": 25, "risk": 10, "desc": "חדירה למסדי נתונים."},
    "rootkit": {"name": "השתלטות (Rootkit)", "cost_ram": 8, "dmg": 60, "risk": 20, "desc": "מחיקת שרת מוחלטת."},
    "log_wiper": {"name": "מחק עקבות", "cost_ram": 5, "effect": "reduce_trace", "val": 20, "desc": "מנקה לוגים (מוריד מעקב)."},
    "proxy_hop": {"name": "פרוקסי (IP Hop)", "cost_ram": 3, "effect": "reduce_trace", "val": 10, "desc": "מסתיר את המיקום שלך."}
}

TARGETS_DB = [
    {"name": "פיצרייה שכונתית", "def": 20, "reward": 50, "sec_level": 1},
    {"name": "שרת העירייה", "def": 50, "reward": 120, "sec_level": 1},
    {"name": "בנק לאומי - כספת", "def": 200, "reward": 800, "sec_level": 2},
    {"name": "מאגר נתונים משטרתי", "def": 500, "reward": 2000, "sec_level": 3},
    {"name": "המוסד (שרת סודי)", "def": 1500, "reward": 10000, "sec_level": 4}
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
                "ram": 10,       
                "max_ram": 10,
                "cpu_lvl": 1,    
                
                # סטטוס
                "trace": 0,      # מד מעקב משטרתי (0-100)
                "connected_to": None,
                
                # עולם
                "targets": [],   
                "log": [{"text": "מערכת RedCode v9.0 אותחלה...", "type": "sys"}]
            }
            self.refresh_targets()
        else:
            self.state = state

    def log(self, txt, type="info"): 
        import datetime
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        self.state["log"].insert(0, {"text": f"[{ts}] {txt}", "type": type})
        if len(self.state["log"]) > 20: self.state["log"].pop()

    def refresh_targets(self):
        self.state["targets"] = []
        for _ in range(3):
            t = random.choice(TARGETS_DB).copy()
            t["max_def"] = int(t["def"] * random.uniform(0.8, 1.2))
            t["def"] = t["max_def"]
            t["id"] = str(uuid.uuid4())[:8]
            self.state["targets"].append(t)

    def connect(self, target_id):
        if self.state["connected_to"]:
            self.log("שגיאה: אתה כבר מחובר. התנתק קודם.", "error")
            return

        target = next((t for t in self.state["targets"] if t["id"] == target_id), None)
        if target:
            self.state["connected_to"] = target
            self.log(f"מתחבר אל: {target['name']}...", "sys")
            self.log("החיבור הצליח. חומת אש זוהתה.", "success")
        
    def disconnect(self):
        if not self.state["connected_to"]: return
        
        self.log(f"מנתק חיבור משרת: {self.state['connected_to']['name']}...", "sys")
        self.state["connected_to"] = None
        self.state["ram"] = self.state["max_ram"] 
        self.log("מערכת במצב המתנה. זיכרון RAM נוקה.", "info")

    def run_program(self, prog_key):
        if not self.state["connected_to"]:
            if prog_key in ["log_wiper", "proxy_hop"]:
                self.run_defense(prog_key)
                return
            else:
                self.log("שגיאה: אין חיבור לשרת.", "error")
                return

        prog = PROGRAMS[prog_key]
        target = self.state["connected_to"]

        if self.state["ram"] < prog["cost_ram"]:
            self.log("⚠️ שגיאת זיכרון: חסר RAM!", "error")
            return

        self.state["ram"] -= prog["cost_ram"]

        if "dmg" in prog:
            damage = prog["dmg"] * self.state["cpu_lvl"]
            target["def"] -= damage
            self.state["trace"] += prog["risk"]
            
            self.log(f"מריץ {prog['name']} >> נזק לשרת: {damage}", "hack")
            
            if target["def"] <= 0:
                self.hack_success(target)

        elif "effect" in prog:
            if prog["effect"] == "reduce_trace":
                self.state["trace"] = max(0, self.state["trace"] - prog["val"])
                self.log(f"טשטוש עקבות בוצע. רמת סיכון: {self.state['trace']}%", "success")

        if self.state["trace"] >= 100:
            return "game_over"

        return "ok"

    def run_defense(self, prog_key):
        prog = PROGRAMS[prog_key]
        if self.state["ram"] < prog["cost_ram"]:
            self.log("אין מספיק RAM.", "error")
            return
        
        self.state["ram"] -= prog["cost_ram"]
        if prog["effect"] == "reduce_trace":
            self.state["trace"] = max(0, self.state["trace"] - prog["val"])
            self.log(f"המחשב נוקה. רמת סיכון: {self.state['trace']}%", "success")

    def hack_success(self, target):
        loot = target["reward"]
        self.state["bitcoin"] += loot
        self.log(f"גישה מלאה אושרה! הסיסמאות בידינו.", "gold")
        self.log(f"💰 {loot} ביטקוין הועברו לארנק.", "gold")
        
        self.state["targets"].remove(target)
        self.state["connected_to"] = None
        self.state["ram"] = self.state["max_ram"]
        
        if not self.state["targets"]:
            self.refresh_targets()

    def upgrade(self, type):
        cost = 0
        if type == "ram":
            cost = self.state["max_ram"] * 10
            if self.state["bitcoin"] >= cost:
                self.state["bitcoin"] -= cost
                self.state["max_ram"] += 5
                self.state["ram"] = self.state["max_ram"]
                self.log(f"שדרוג בוצע: זיכרון גדל ל-{self.state['max_ram']}GB", "sys")
            else:
                self.log("אין מספיק כסף בחשבון.", "error")

        elif type == "cpu":
            cost = self.state["cpu_lvl"] * 500
            if self.state["bitcoin"] >= cost:
                self.state["bitcoin"] -= cost
                self.state["cpu_lvl"] += 1
                self.log(f"שדרוג בוצע: מעבד רמה {self.state['cpu_lvl']}", "sys")
            else:
                self.log("אין מספיק כסף בחשבון.", "error")

# ==========================================
# WEB
# ==========================================
@app.route("/")
def index():
    if "uid" not in session: session["uid"] = str(uuid.uuid4())
    api = url_for("action")
    return render_template_string(HTML, api=api)

@app.route("/action", methods=["POST"])
def action():
    try: eng = Engine(session.get("hacker_il"))
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

    session["hacker_il"] = eng.state
    
    return jsonify({
        "log": eng.state["log"],
        "state": eng.state,
        "programs": PROGRAMS
    })

# ==========================================
# ממשק משתמש - האקר ישראלי
# ==========================================
HTML = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>קוד אדום</title>
<link href="https://fonts.googleapis.com/css2?family=Heebo:wght@400;700&family=Courier+Prime&display=swap" rel="stylesheet">
<style>
    :root { --green: #0f0; --dim-green: #003300; --bg: #050505; --red: #ff3333; --gold: #ffd700;}
    body { background: var(--bg); color: var(--green); font-family: 'Courier Prime', monospace; margin: 0; height: 100vh; display: flex; overflow: hidden; font-size: 18px;}
    
    /* Layout: Sidebar Right (Hebrew), Main Left */
    .sidebar { width: 280px; border-left: 1px solid var(--dim-green); display: flex; flex-direction: column; padding: 15px; background: #0a0a0a; }
    .main-view { flex: 1; display: flex; flex-direction: column; padding: 20px; position: relative;}
    
    h1 { margin:0 0 20px 0; text-align:center; font-family: 'Heebo', sans-serif; letter-spacing: 2px; text-shadow: 0 0 10px var(--green);}

    /* Stats Bars */
    .stat-box { margin-bottom: 20px; }
    .stat-label { display: flex; justify-content: space-between; font-size: 14px; margin-bottom: 5px; color:#aaa;}
    .bar-bg { width: 100%; height: 15px; background: #222; border: 1px solid #444; }
    .bar-fill { height: 100%; width: 0%; transition: 0.3s; background: var(--green); }
    .trace-bar { background: var(--red); }
    
    /* Money & Info */
    .wallet { border-top: 1px solid #333; padding-top: 15px; margin-top: auto; }
    .coin-val { color: var(--gold); font-size: 28px; font-weight: bold;}
    
    /* Lists & Terminals */
    .server-list { flex: 1; overflow-y: auto; display:flex; flex-direction:column; gap:10px; }
    .server-card { 
        background: #0d0d0d; border: 1px solid #333; padding: 10px; cursor: pointer; transition: 0.2s;
        display: flex; justify-content: space-between; align-items: center; border-radius:4px;
    }
    .server-card:hover { border-color: var(--green); background: #111; }
    .svr-info { font-size: 14px; color: #777; }
    
    .terminal { flex: 1; border: 1px solid #333; padding: 15px; background: #000; overflow-y: auto; display: flex; flex-direction: column; margin-bottom: 20px; font-family:'Courier New', Courier, monospace;}
    .line { margin-bottom: 4px; border-bottom: 1px solid #111; padding-bottom: 2px;}
    .sys { color: #5f5; } .error { color: #f55; } .hack { color: #ff5; } .gold { color: gold; }

    /* Action Buttons Grid */
    .deck { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 10px; height: 130px; }
    .hack-btn { 
        background: #0a1a0a; border: 1px solid #2a4a2a; color: #aea; 
        cursor: pointer; padding: 5px; display: flex; flex-direction: column; align-items: center; justify-content: center;
        font-family: 'Heebo', sans-serif; transition:0.1s;
    }
    .hack-btn:hover { background: #1a3a1a; border-color: var(--green); }
    .hack-btn strong { font-size: 16px; display:block; margin-bottom:4px;}
    .hack-btn small { font-size: 12px; color: #777;}
    
    .def-btn { border-color: #337; background: #0a0a1a; color: #aad;}
    .def-btn:hover { border-color: #55f; }

    /* Active Attack Panel */
    .attack-panel { border: 2px solid var(--red); padding: 15px; margin-bottom: 15px; background: #1a0505; display:none;}
    .fw-label { display:flex; justify-content:space-between; color: var(--red); font-weight:bold; font-size:14px; margin-bottom:5px;}
    .fw-bar-bg { background: #300; width: 100%; height: 10px; }
    .fw-bar-fill { background: var(--red); width: 100%; height: 100%; transition:0.2s;}

    /* Game Over */
    .busted-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: #000; z-index: 99; display:none; flex-direction:column; justify-content:center; align-items:center; color:red;}
</style>
</head>
<body>

<div id="game-over" class="busted-overlay">
    <h1 style="font-size:60px; text-shadow:0 0 20px red;">נתפסת!</h1>
    <p>ה-IP שלך נחשף. המשטרה בדרך.</p>
    <button onclick="send('reset')" style="background:red; color:black; font-size:24px; border:none; padding:10px 30px; cursor:pointer; font-weight:bold;">אתחול מערכת מחדש</button>
</div>

<div class="sidebar">
    <h1>🕵️ קוד אדום</h1>
    
    <div class="stat-box">
        <div class="stat-label"><span>🚨 מעקב משטרתי</span> <span id="val-trace">0%</span></div>
        <div class="bar-bg"><div class="bar-fill trace-fill" id="bar-trace"></div></div>
    </div>
    
    <div class="stat-box">
        <div class="stat-label"><span>🧠 זיכרון (RAM)</span> <span id="val-ram">10/10</span></div>
        <div class="bar-bg"><div class="bar-fill" id="bar-ram"></div></div>
    </div>
    
    <div class="wallet">
        <div class="stat-label">ארנק מוצפן:</div>
        <div class="coin-val">₿ <span id="val-btc">0.0</span></div>
        <div style="font-size:14px; color:#666; margin-top:5px;">עוצמת מעבד: Lv <span id="val-cpu">1</span></div>
        
        <div style="display:grid; gap:5px; margin-top:15px;">
            <button class="hack-btn" onclick="send('buy','ram')" style="width:100%">שדרג זיכרון (+5)</button>
            <button class="hack-btn" onclick="send('buy','cpu')" style="width:100%">שדרג מעבד (x1)</button>
        </div>
    </div>
</div>

<div class="main-view">
    <!-- Active Attack HUD -->
    <div class="attack-panel" id="atk-hud">
        <div class="fw-label">
            <span>🔴 יעד תקיפה: <span id="tgt-name">...</span></span>
            <button onclick="send('disconnect')" style="background:none; border:1px solid red; color:red; cursor:pointer;">[ נתק מגע ]</button>
        </div>
        <div class="fw-bar-bg"><div class="fw-bar-fill" id="bar-fw"></div></div>
        <div style="text-align:right; font-size:12px; color:#f55; margin-top:2px;">חומת אש</div>
    </div>

    <!-- TERMINAL -->
    <div class="terminal" id="console"></div>
    
    <!-- SELECTION OR ACTION -->
    <div id="list-mode" class="server-list"></div>
    
    <div id="hack-mode" class="deck" style="display:none;">
        <button class="hack-btn" onclick="send('run','brute_force')"><strong>👊 כוח גס</strong><small>2 RAM | סיכון נמוך</small></button>
        <button class="hack-btn" onclick="send('run','sql_inject')"><strong>💉 הזרקת SQL</strong><small>4 RAM | נזק בינוני</small></button>
        <button class="hack-btn" onclick="send('run','rootkit')"><strong>👑 השתלטות</strong><small>8 RAM | נזק קריטי</small></button>
        <button class="hack-btn def-btn" onclick="send('run','proxy_hop')"><strong>👻 הסתר IP</strong><small>-10% מעקב</small></button>
        <button class="hack-btn def-btn" onclick="send('run','log_wiper')"><strong>🧹 נקה לוגים</strong><small>-20% מעקב</small></button>
    </div>
</div>

<script>
    const API = "{{ api }}";
    window.onload = ()=> send('init');

    async function send(act, val=null) {
        let res = await fetch(API, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({act:act, val:val})});
        let d = await res.json();
        
        if (d.game_over) {
            document.getElementById("game-over").style.display = "flex";
            return;
        } else {
            document.getElementById("game-over").style.display = "none";
        }

        let s = d.state;
        
        // 1. Stats Update
        document.getElementById("val-trace").innerText = s.trace + "%";
        document.getElementById("bar-trace").style.width = s.trace + "%";
        
        document.getElementById("val-ram").innerText = s.ram + "/" + s.max_ram;
        let ramPct = (s.ram / s.max_ram) * 100;
        document.getElementById("bar-ram").style.width = ramPct + "%";
        
        document.getElementById("val-btc").innerText = s.bitcoin;
        document.getElementById("val-cpu").innerText = s.cpu_lvl;

        // 2. Terminal Log
        let con = document.getElementById("console");
        con.innerHTML = "";
        d.log.forEach(l => {
            con.innerHTML += `<div class="line ${l.type}">${l.text}</div>`;
        });

        // 3. Mode Switching
        if (s.connected_to) {
            // HACKING MODE
            document.getElementById("list-mode").style.display = "none";
            document.getElementById("hack-mode").style.display = "grid";
            document.getElementById("atk-hud").style.display = "block";
            
            let t = s.connected_to;
            document.getElementById("tgt-name").innerText = t.name;
            let fw = (t.def / t.max_def) * 100;
            document.getElementById("bar-fw").style.width = fw + "%";
            
        } else {
            // LIST MODE
            document.getElementById("list-mode").style.display = "flex";
            document.getElementById("hack-mode").style.display = "none";
            document.getElementById("atk-hud").style.display = "none";
            
            let html = "";
            s.targets.forEach(t => {
                html += `
                <div class="server-card" onclick="send('connect', '${t.id}')">
                    <div>
                        <div style="font-weight:bold">${t.name}</div>
                        <div class="svr-info">הגנה: ${t.max_def} | רווח צפוי: ₿${t.reward}</div>
                    </div>
                    <div style="color:var(--green); font-size:20px;">></div>
                </div>`;
            });
            document.getElementById("list-mode").innerHTML = html;
        }
    }
</script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(port=5006, debug=True)
