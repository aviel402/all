import random
import uuid
import datetime
from flask import Flask, render_template_string, request, jsonify, session, url_for

app = Flask(__name__)
# מפתח קבוע לשמירה על יציבות
app.secret_key = 'red_code_fixed_v2'

# ==========================================
# 💾 מאגר נתונים (מאוזן יותר)
# ==========================================
PROGRAMS = {
    # תקיפה
    "brute_force": {"name": "כוח גס (BruteForce)", "cost_ram": 2, "dmg": 15, "risk": 4, "desc": "זול ומהיר."},
    "sql_inject": {"name": "הזרקת קוד (SQL)", "cost_ram": 4, "dmg": 40, "risk": 8, "desc": "נזק בינוני."},
    "rootkit": {"name": "השתלטות (Rootkit)", "cost_ram": 8, "dmg": 100, "risk": 15, "desc": "מכה קריטית."},
    
    # הגנה והסתרה
    "log_wiper": {"name": "מחק לוגים", "cost_ram": 4, "effect": "reduce_trace", "val": 15, "desc": "מוריד 15% מהמעקב."},
    "proxy_hop": {"name": "החלף IP", "cost_ram": 2, "effect": "reduce_trace", "val": 5, "desc": "פעולה מהירה להורדת מעקב."}
}

TARGETS_DB = [
    {"name": "קיוסק שכונתי", "def": 30, "reward": 50, "sec_level": 1},
    {"name": "משרד רואי חשבון", "def": 80, "reward": 150, "sec_level": 1},
    {"name": "שרת בנק הפועלים", "def": 250, "reward": 600, "sec_level": 2},
    {"name": "מאגר ביומטרי", "def": 600, "reward": 1800, "sec_level": 3},
    {"name": "כור בדימונה", "def": 2000, "reward": 10000, "sec_level": 4}
]

# ==========================================
# ⚙️ מנוע ההאקינג (מתוקן)
# ==========================================
class Engine:
    def __init__(self, state=None):
        if not state:
            self.reset_state()
        else:
            self.state = state

    def reset_state(self):
        self.state = {
            "bitcoin": 0,
            "ram": 10,
            "max_ram": 10,
            "cpu_lvl": 1,
            "trace": 0,
            "connected_to": None,
            "targets": [],
            "game_over": False,
            "log": [{"text": "מערכת RedCode אותחלה. מוכן לפעולה.", "type": "sys"}]
        }
        self.refresh_targets()

    def log(self, txt, type="info"): 
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        self.state["log"].insert(0, {"text": f"[{ts}] {txt}", "type": type})
        if len(self.state["log"]) > 25: self.state["log"].pop()

    def refresh_targets(self):
        self.state["targets"] = []
        for _ in range(4):
            t = random.choice(TARGETS_DB).copy()
            # וריאציה כדי שלא יהיה משעמם
            variance = random.uniform(0.9, 1.3)
            t["max_def"] = int(t["def"] * variance)
            t["def"] = t["max_def"]
            t["id"] = str(uuid.uuid4())[:8]
            self.state["targets"].append(t)

    # --- פעולות ---

    def connect(self, target_id):
        # מניעת חיבור כפול
        if self.state["connected_to"]: return 

        target = next((t for t in self.state["targets"] if t["id"] == target_id), None)
        if target:
            self.state["connected_to"] = target
            self.log(f"התחברות ל-{target['name']} הצליחה.", "sys")
        
    def disconnect(self):
        if not self.state["connected_to"]: return
        
        name = self.state["connected_to"]["name"]
        self.state["connected_to"] = None
        
        # תיקון קריטי: מילוי RAM בהתנתקות
        self.state["ram"] = self.state["max_ram"] 
        self.log(f"התנתקת מ-{name}. זיכרון RAM טוהר.", "info")

    def run_program(self, prog_key):
        # הגנה מפני ריצה כשכבר נפסלת
        if self.state["game_over"]: return

        prog = PROGRAMS[prog_key]
        
        # האם יש מספיק RAM?
        if self.state["ram"] < prog["cost_ram"]:
            self.log("שגיאה: אין מספיק זיכרון (RAM). התנתק כדי לטעון מחדש.", "error")
            return

        self.state["ram"] -= prog["cost_ram"]

        # --- מצב תקיפה (מחובר לשרת) ---
        if "dmg" in prog:
            if not self.state["connected_to"]:
                self.log("שגיאה: אינך מחובר לשום יעד.", "error")
                # מחזיר את ה-RAM כי הפעולה נכשלה
                self.state["ram"] += prog["cost_ram"]
                return

            target = self.state["connected_to"]
            damage = prog["dmg"] * self.state["cpu_lvl"]
            target["def"] -= damage
            
            # העלאת סיכון (TRACE)
            risk = prog["risk"]
            # אם השרת פרוץ כמעט לגמרי, הסיכון יורד קצת (בונוס)
            self.state["trace"] = min(100, self.state["trace"] + risk)
            
            self.log(f"הפעלת {prog['name']} >> נזק: {damage}", "hack")
            
            if target["def"] <= 0:
                self.hack_success(target)

        # --- מצב הגנה (הורדת Trace) ---
        elif "effect" in prog and prog["effect"] == "reduce_trace":
            reduction = prog["val"] * self.state["cpu_lvl"] # מעבד חזק מנקה טוב יותר
            self.state["trace"] = max(0, self.state["trace"] - reduction)
            self.log(f"ניקוי עקבות בוצע. מעקב נוכחי: {self.state['trace']}%", "success")

        # בדיקת הפסד
        if self.state["trace"] >= 100:
            self.state["game_over"] = True

    def hack_success(self, target):
        loot = target["reward"]
        self.state["bitcoin"] += loot
        
        self.log(f"🎉 פריצה הושלמה! הרווחת ₿{loot}", "gold")
        self.log("הקשר נותק אוטומטית למניעת זיהוי.", "info")
        
        # הסרה ורענון
        if target in self.state["targets"]:
            self.state["targets"].remove(target)
        
        self.state["connected_to"] = None
        self.state["ram"] = self.state["max_ram"] # פרס: מילוי RAM
        
        if not self.state["targets"]:
            self.refresh_targets()

    # --- חנות ---
    def upgrade(self, type):
        if type == "ram":
            cost = self.state["max_ram"] * 15 # מחיר עולה
            if self.state["bitcoin"] >= cost:
                self.state["bitcoin"] -= cost
                self.state["max_ram"] += 5
                self.state["ram"] = self.state["max_ram"] # מילוי מידי
                self.log(f"שודרג! זיכרון מקסימלי: {self.state['max_ram']}", "sys")
            else:
                self.log(f"אין מספיק כסף. נדרש: {cost}", "error")

        elif type == "cpu":
            cost = self.state["cpu_lvl"] * 250
            if self.state["bitcoin"] >= cost:
                self.state["bitcoin"] -= cost
                self.state["cpu_lvl"] += 1
                self.log(f"שודרג! מעבד רמה: {self.state['cpu_lvl']}", "sys")
            else:
                self.log(f"אין מספיק כסף. נדרש: {cost}", "error")

# ==========================================
# WEB SETUP
# ==========================================
@app.route("/")
def index():
    if "uid" not in session: session["uid"] = str(uuid.uuid4())
    # שימוש בכתובת דינמית כדי למנוע את הבעיה בלאוצ'ר
    api_url = url_for("handle_action")
    return render_template_string(HTML, api=api_url)

@app.route("/action", methods=["POST"])
def handle_action():
    try: 
        # טוען משחק או מתחיל חדש אם המידע נשבר
        eng = Engine(session.get("hacker_il_fixed"))
    except: 
        eng = Engine(None)
    
    d = request.json
    act = d.get("act")
    val = d.get("val")
    
    if act == "reset": eng.reset_state()
    elif act == "connect": eng.connect(val)
    elif act == "disconnect": eng.disconnect()
    elif act == "run": eng.run_program(val)
    elif act == "buy": eng.upgrade(val)
    
    session["hacker_il_fixed"] = eng.state
    
    return jsonify({
        "log": eng.state["log"],
        "state": eng.state,
        "programs": PROGRAMS
    })

# ==========================================
# UI - אותו עיצוב, מנוע חדש
# ==========================================
HTML = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Red Code Pro</title>
<link href="https://fonts.googleapis.com/css2?family=Rubik:wght@400;700&family=Courier+Prime&display=swap" rel="stylesheet">
<style>
    :root { --green: #00ff41; --dark: #0d0d0d; --panel: #111; --border: #222; --red: #ff3333; --gold: #ffd700;}
    
    body { background: #050505; color: var(--green); font-family: 'Courier Prime', monospace; margin: 0; height: 100vh; display: flex; overflow: hidden; font-size: 16px;}
    
    /* LEFT SIDEBAR (STATS) */
    .sidebar { width: 300px; border-left: 2px solid var(--border); display: flex; flex-direction: column; padding: 20px; background: #080808; gap:20px;}
    
    .title-box { text-align: center; border-bottom: 2px solid var(--green); padding-bottom: 10px; margin-bottom: 10px;}
    h1 { margin: 0; font-family: 'Rubik', sans-serif; letter-spacing: 1px;}

    .meter-container { margin-bottom: 15px; }
    .meter-label { display: flex; justify-content: space-between; font-size: 14px; margin-bottom: 5px; color:#888;}
    .meter-bg { width: 100%; height: 12px; background: #222; border: 1px solid #444; border-radius: 2px;}
    .meter-fill { height: 100%; width: 0%; transition: 0.3s; background: var(--green); }
    .trace { background: var(--red); box-shadow: 0 0 10px var(--red); }
    
    .money-box { margin-top: auto; border: 1px solid var(--gold); padding: 15px; border-radius: 5px; text-align: center; }
    .money-val { font-size: 30px; font-weight: bold; color: var(--gold); text-shadow: 0 0 5px #a88d00;}
    
    .shop-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 10px; }
    .shop-btn { background: #1a1a00; border: 1px solid #666; color: #ccb; padding: 5px; cursor: pointer; font-family: inherit;}
    .shop-btn:hover { border-color: var(--gold); color: white;}

    /* RIGHT MAIN */
    .main { flex: 1; display: flex; flex-direction: column; padding: 20px; position: relative;}
    
    /* TERMINAL */
    .terminal { flex: 1; border: 1px solid var(--border); background: #000; padding: 15px; overflow-y: auto; display: flex; flex-direction: column; margin-bottom: 20px; font-family:'Courier New'; border-radius: 5px;}
    .log-line { margin-bottom: 4px; border-bottom: 1px solid #111; padding-bottom: 2px; }
    .sys { color: #5f5; } .error { color: #f55; } .hack { color: #ffeb3b; } .gold { color: var(--gold); font-weight: bold;}

    /* LIST OR HACK */
    .viewport { height: 200px; border-top: 2px solid var(--border); padding-top: 15px; overflow-y:auto;}
    
    .server-card { background: var(--panel); padding: 12px; margin-bottom: 8px; border: 1px solid #333; border-radius: 4px; display:flex; justify-content:space-between; align-items:center; cursor: pointer; transition: 0.2s;}
    .server-card:hover { border-color: var(--green); transform: translateX(-5px); }
    
    .active-hack-ui { display:none; flex-direction:column; gap: 10px; height: 100%;}
    
    .hack-header { display: flex; justify-content: space-between; align-items: center; color: white; background: #222; padding: 10px; border-radius: 4px;}
    .firewall-bg { width: 100%; height: 8px; background: #400; margin-top: 10px; }
    .firewall-fill { height: 100%; width: 100%; background: var(--red); transition: 0.2s; }
    
    .deck { display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; flex: 1;}
    .card-btn { 
        background: #0a1a0a; border: 1px solid #2d4d2d; color: #afa; border-radius: 6px;
        display: flex; flex-direction: column; align-items: center; justify-content: center;
        cursor: pointer; transition: 0.1s; text-align: center;
    }
    .card-btn:hover { background: #153515; border-color: #0f0; }
    .card-btn strong { font-size: 14px; margin-bottom: 4px;}
    .card-btn small { font-size: 11px; color: #7a7;}
    .def { border-color: #44a; color: #aaf; background: #0a0a20;}
    .def:hover { border-color: #88f; background: #1a1a40;}

    /* GAME OVER OVERLAY */
    .overlay { position: fixed; top:0; left:0; width:100%; height:100%; background: black; display:none; flex-direction:column; justify-content:center; align-items:center; z-index:99;}
    .overlay h1 { font-size: 80px; color: red; text-shadow: 0 0 30px red; margin:0;}
    .reset-btn { font-size: 20px; padding: 15px 40px; background: red; color: black; border: none; cursor: pointer; margin-top: 20px; font-weight: bold;}

</style>
</head>
<body>

<!-- GAME OVER SCREEN -->
<div id="over-scr" class="overlay">
    <h1>נחשפת!</h1>
    <div style="font-size:20px; color:#555">ה-IP שלך נשרף. כוחות ביטחון בדרך.</div>
    <button class="reset-btn" onclick="api('reset')">נסה מחדש</button>
</div>

<!-- SIDEBAR -->
<div class="sidebar">
    <div class="title-box">
        <h1>RED CODE</h1>
        <small style="color:#666">TERMINAL v3.5</small>
    </div>
    
    <div class="meter-container">
        <div class="meter-label"><span>🛑 סיכון (Trace)</span> <span id="v-trc">0%</span></div>
        <div class="meter-bg"><div class="meter-fill trace" id="b-trc"></div></div>
    </div>
    
    <div class="meter-container">
        <div class="meter-label"><span>🧠 זיכרון (RAM)</span> <span id="v-ram">10/10</span></div>
        <div class="meter-bg"><div class="meter-fill" id="b-ram"></div></div>
    </div>
    
    <div class="money-box">
        <div class="coin-val">₿<span id="v-btc">0</span></div>
        <div style="font-size:12px; color:#555;">ארנק קריפטו לא מזוהה</div>
        <div style="margin-top:10px; font-size:14px; border-top:1px dashed #444; padding-top:5px;">
            מעבד רמה: <span id="v-cpu" style="color:white">1</span>
        </div>
        
        <div class="shop-grid">
            <button class="shop-btn" onclick="api('buy','ram')">+5 RAM</button>
            <button class="shop-btn" onclick="api('buy','cpu')">+1 CPU</button>
        </div>
    </div>
</div>

<!-- MAIN CONTENT -->
<div class="main">
    <div class="terminal" id="term"></div>
    
    <div class="viewport">
        <!-- SERVER LIST VIEW -->
        <div id="view-list" style="display:block;">
            <div style="color:#666; margin-bottom:10px;">שרתים זמינים לפריצה:</div>
            <div id="servers-container"></div>
        </div>
        
        <!-- HACKING VIEW -->
        <div id="view-hack" class="active-hack-ui">
            <div class="hack-header">
                <span id="target-name" style="font-weight:bold; color:#0f0;">TARGET</span>
                <button onclick="api('disconnect')" style="background:none; border:1px solid #f55; color:#f55; padding:5px 10px; cursor:pointer;">✖ התנתק (נקה RAM)</button>
            </div>
            
            <div class="meter-bg" style="border-color:#f00; margin-top:-5px;">
                <div id="target-hp" class="firewall-fill"></div>
            </div>
            <div style="text-align:left; font-size:12px; color:#f55;">FIREWALL STATUS</div>
            
            <div class="deck">
                <button class="card-btn" onclick="api('run','brute_force')"><strong>BruteForce</strong><small>2 RAM / נמוך</small></button>
                <button class="card-btn" onclick="api('run','sql_inject')"><strong>SQL Inject</strong><small>4 RAM / בינוני</small></button>
                <button class="card-btn" onclick="api('run','rootkit')"><strong>ROOTKIT</strong><small>8 RAM / גבוה</small></button>
                <button class="card-btn def" onclick="api('run','proxy_hop')"><strong>Proxy IP</strong><small>-5 Trace</small></button>
                <button class="card-btn def" onclick="api('run','log_wiper')"><strong>Log Wipe</strong><small>-15 Trace</small></button>
            </div>
        </div>
    </div>
</div>

<script>
    const API = "{{ api }}";
    
    // Auto start
    window.onload = () => api("init");

    async function api(act, val=null) {
        let res = await fetch(API, {
            method:'POST', headers:{'Content-Type':'application/json'},
            body:JSON.stringify({act: act, val: val})
        });
        let d = await res.json();
        let s = d.state;

        // 1. GAME OVER CHECK
        if(s.game_over) {
            document.getElementById("over-scr").style.display = "flex";
            return;
        } else {
            document.getElementById("over-scr").style.display = "none";
        }

        // 2. STATS UPDATE
        updateMeter("ram", s.ram, s.max_ram);
        updateMeter("trc", s.trace, 100);
        document.getElementById("v-btc").innerText = s.bitcoin;
        document.getElementById("v-cpu").innerText = s.cpu_lvl;

        // 3. LOG UPDATE
        let t = document.getElementById("term");
        t.innerHTML = "";
        d.log.forEach(ln => {
            t.innerHTML += `<div class="log-line ${ln.type}">> ${ln.text}</div>`;
        });

        // 4. VIEW TOGGLE
        if(s.connected_to) {
            document.getElementById("view-list").style.display = "none";
            document.getElementById("view-hack").style.display = "flex";
            
            // Update Hack View
            let t = s.connected_to;
            document.getElementById("target-name").innerText = ">> " + t.name;
            let hp = (t.def / t.max_def) * 100;
            document.getElementById("target-hp").style.width = hp + "%";
            
        } else {
            document.getElementById("view-list").style.display = "block";
            document.getElementById("view-hack").style.display = "none";
            
            // Build Server List
            let sl = document.getElementById("servers-container");
            sl.innerHTML = "";
            s.targets.forEach(sv => {
                sl.innerHTML += `
                <div class="server-card" onclick="api('connect','${sv.id}')">
                    <div>
                        <strong>${sv.name}</strong><br>
                        <small style="color:#777">הגנה: ${sv.max_def} | קופה: ₿${sv.reward}</small>
                    </div>
                    <div style="font-size:20px; color:#0f0;">⌨</div>
                </div>`;
            });
        }
    }

    function updateMeter(id, val, max) {
        document.getElementById("v-"+id).innerText = (id==='trc') ? val+"%" : val+"/"+max;
        let pct = (val / max) * 100;
        document.getElementById("b-"+id).style.width = pct + "%";
    }
</script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(port=5006, debug=True)
