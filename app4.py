import random
import uuid
import datetime
from flask import Flask, render_template_string, request, jsonify, session, url_for

app = Flask(__name__)
# מפתח סודי חדש
app.secret_key = 'hacker_money_fixed_v12' 

# ==========================================
# 🛑 חלק הנתונים
# ==========================================
PROGRAMS = {
    # תוכנות התקפה
    "p1": {"name": "מכה קלה", "ram": 2, "dmg": 20, "risk": 4, "type": "atk", "desc": "נזק קטן ומהיר"},
    "p2": {"name": "הזרקת קוד",  "ram": 4, "dmg": 50, "risk": 8, "type": "atk", "desc": "נזק בינוני"},
    "p3": {"name": "פריצה מלאה","ram": 8, "dmg": 120,"risk": 20,"type": "atk", "desc": "נזק אדיר!"},
    
    # תוכנות הגנה
    "d1": {"name": "הסתר IP",    "ram": 2, "heal": 10, "type": "def", "desc": "-10% מעקב"},
    "d2": {"name": "נקה לוגים",   "ram": 5, "heal": 25, "type": "def", "desc": "-25% מעקב"}
}

TARGETS = [
    # הכפלתי את כל הסכומים ב-10 לפי הבקשה שלך
    {"name": "ראוטר של שכן", "def": 10, "cash": 150},
    {"name": "בית קפה", "def": 20, "cash": 250},
    {"name": "פיצרייה מקומית", "def": 30, "cash": 400},
    {"name": "כספומט שכונתי", "def": 50, "cash": 800},
    {"name": "מערכת ניהול חנות", "def": 80, "cash": 1200},
    {"name": "מחשב של מנהל בנק", "def": 120, "cash": 2000},
    {"name": "רשת בית ספר", "def": 150, "cash": 2500},
    {"name": "חברת שליחויות", "def": 180, "cash": 3000},
    {"name": "רשת שיווק", "def": 250, "cash": 5000},
    {"name": "חברת ביטוח", "def": 300, "cash": 7000},
    {"name": "בנק דיגיטלי", "def": 400, "cash": 10000},
    {"name": "מלונות דן", "def": 500, "cash": 15000},
    {"name": "רכבת ישראל", "def": 700, "cash": 22000},
    {"name": "חברת אשראי", "def": 900, "cash": 30000},
    {"name": "משרד החינוך", "def": 1200, "cash": 40000},
    {"name": "תחנת כוח", "def": 1500, "cash": 55000},
    {"name": "מטה המשטרה", "def": 2000, "cash": 80000},
    {"name": "מגדל פיקוח", "def": 2500, "cash": 110000},
    {"name": "לוויין ריגול", "def": 3500, "cash": 150000},
    {"name": "המוסד", "def": 5000, "cash": 250000},
    {"name": "מחשבי הבורסה", "def": 7500, "cash": 500000},
    {"name": "בנק מרכזי", "def": 10000, "cash": 800000},
    {"name": "הפנטגון", "def": 15000, "cash": 1500000},
    {"name": "SpaceX Mainframe", "def": 25000, "cash": 3000000}
]

# ==========================================
# ⚙️ מנוע
# ==========================================
class GameEngine:
    def __init__(self, state=None):
        if not state:
            self.reset()
        else:
            self.state = state

    def getTime(self):
        return datetime.datetime.now().strftime("%H:%M:%S")

    def reset(self):
        self.state = {
            "money": 0,
            "ram": 15, "max_ram": 15, # יותר RAM
            "cpu": 1,
            "trace": 0,
            "active_target": None, 
            "targets_list": [],
            "game_over": False,
            "log": [{"time": self.getTime(), "txt": "מערכת הופעלה.", "c": "sys"}]
        }
        self.load_all_targets()

    def log(self, txt, c="info"):
        self.state["log"].insert(0, {"time": self.getTime(), "txt": txt, "c": c})
        if len(self.state["log"]) > 30: self.state["log"].pop()

    def load_all_targets(self):
        # טוען את כולם מיד, לא רק 5
        self.state["targets_list"] = []
        for t in TARGETS:
            base = t.copy()
            base["max_def"] = int(base["def"] * random.uniform(0.9, 1.1))
            base["def"] = base["max_def"]
            base["id"] = str(uuid.uuid4())
            self.state["targets_list"].append(base)

    def connect(self, t_id):
        if self.state["active_target"]: return
        t = next((i for i in self.state["targets_list"] if i["id"] == t_id), None)
        if t:
            self.state["active_target"] = t
            self.log(f"התחברות ל: {t['name']}", "sys")

    def disconnect(self):
        if not self.state["active_target"]: return
        self.state["active_target"] = None
        self.state["ram"] = self.state["max_ram"] 
        self.log("התנתקת. RAM שוחזר.", "def")

    def execute(self, pid):
        if self.state["game_over"]: return
        prog = PROGRAMS[pid]
        
        if self.state["ram"] < prog["ram"]:
            self.log("אין מספיק RAM! התנתק כדי למלא.", "err")
            return

        self.state["ram"] -= prog["ram"]
        
        # תקיפה
        if prog["type"] == "atk":
            tgt = self.state["active_target"]
            if not tgt: return
            
            dmg = prog["dmg"] * self.state["cpu"]
            tgt["def"] -= dmg
            self.state["trace"] = min(100, self.state["trace"] + prog["risk"])
            
            self.log(f"{prog['name']} פגע (-{dmg})", "hack")
            
            # בדיקת ניצחון בפריצה
            if tgt["def"] <= 0:
                amount = tgt["cash"]
                self.state["money"] += amount
                self.log(f"💰 הצלחה! לקחת ₪{amount}", "win")
                self.state["targets_list"].remove(tgt)
                self.state["active_target"] = None
                self.state["ram"] = self.state["max_ram"] # בונוס מילוי RAM
                
        # הגנה
        elif prog["type"] == "def":
            heal = prog["heal"] * self.state["cpu"]
            self.state["trace"] = max(0, self.state["trace"] - heal)
            self.log(f"הורדת סיכון ב-{heal}%", "def")

        # הפסד
        if self.state["trace"] >= 100:
            self.state["game_over"] = True
            self.state["active_target"] = None

    def buy(self, item):
        cost = 0
        if item == "ram":
            cost = self.state["max_ram"] * 10
            if self.state["money"] >= cost:
                self.state["money"] -= cost
                self.state["max_ram"] += 3
                self.state["ram"] = self.state["max_ram"]
                self.log(f"RAM שודרג ל-{self.state['max_ram']}GB", "win")
            else:
                self.log(f"חסר כסף ({cost})", "err")
        elif item == "cpu":
            cost = self.state["cpu"] * 250
            if self.state["money"] >= cost:
                self.state["money"] -= cost
                self.state["cpu"] += 1
                self.log(f"CPU שודרג לרמה {self.state['cpu']}", "win")
            else:
                self.log(f"חסר כסף ({cost})", "err")

# ==========================================
# SERVER ROUTING
# ==========================================
@app.route("/")
def index():
    if "uid" not in session: session["uid"] = str(uuid.uuid4())
    return render_template_string(HTML, api=url_for("handle_post"))

@app.route("/api", methods=["POST"])
def handle_post():
    try: eng = GameEngine(session.get("redcode_final"))
    except: eng = GameEngine(None)
    
    d = request.json
    a = d.get("a")
    v = d.get("v")
    
    if a == "reset": eng.reset()
    elif a == "conn": eng.connect(v)
    elif a == "disc": eng.disconnect()
    elif a == "exec": eng.execute(v)
    elif a == "buy": eng.buy(v)
    
    session["redcode_final"] = eng.state
    
    return jsonify({"s": eng.state, "progs": PROGRAMS})

# ==========================================
# UI HTML (Red Matrix Style Fixes)
# ==========================================
HTML = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>RedCode</title>
<link href="                                                       ;700&family=Share+Tech+Mono&display=swap" rel="stylesheet">
<style>
    /* RESET */
    * { box-sizing: border-box; }
    
    body {
        background: #000; color: #f00; font-family: 'Rubik', sans-serif;
        margin: 0; height: 100vh; display: flex; flex-direction: column; overflow: hidden;
    }
    
    /* CRT Lines */
    body::before { 
        content:""; position:absolute; top:0; left:0; width:100%; height:100%; 
        background: repeating-linear-gradient(0deg, rgba(255,0,0,0.03), rgba(255,0,0,0.03) 1px, transparent 1px, transparent 2px); 
        pointer-events: none; z-index:9; 
    }

    /* HEADER */
    .top { height: 60px; background: #080000; display: flex; align-items: center; justify-content: space-between; padding: 0 20px; border-bottom: 2px solid #f00; z-index:10;}
    .title { font-family: 'Share Tech Mono'; font-size: 26px; text-shadow: 0 0 8px red;}
    .money { font-size: 22px; color: gold;}

    /* GRID LAYOUT */
    .grid { flex: 1; display: grid; grid-template-columns: 260px 1fr 300px; gap: 5px; padding: 5px; overflow:hidden;}
    
    .panel { background: rgba(20, 0, 0, 0.95); border: 1px solid #900; display:flex; flex-direction:column; padding:10px; overflow:hidden;}
    .head { border-bottom:1px solid #500; padding-bottom:5px; text-align:center; font-family:'Share Tech Mono'; color:#a55; margin-bottom:10px;}

    /* BARS */
    .bar-row { margin-bottom: 10px; }
    .label { display:flex; justify-content:space-between; font-size:12px; margin-bottom:3px; color:#888;}
    .track { width:100%; height:14px; background:#100; border:1px solid #500; direction:ltr;}
    .fill { height:100%; width:0%; transition: width 0.2s; background:#f00; box-shadow:0 0 5px red;}
    .trace-c { background:#fff; }

    /* TARGET LIST */
    .list-area { overflow-y: auto; flex:1; padding-right:5px;}
    /* SCROLLBAR */
    ::-webkit-scrollbar { width:6px; }
    ::-webkit-scrollbar-track { background:#100; }
    ::-webkit-scrollbar-thumb { background:#600; border-radius:3px; }

    .item { 
        padding: 10px; margin-bottom: 5px; border: 1px dashed #500; 
        background:#050000; cursor:pointer; display:flex; justify-content:space-between; align-items:center;
    }
    .item:hover { background: #200; border-color: #f00; }
    .iname { font-weight:bold; font-size:14px;}
    .isub { font-size:11px; color:#a66; }

    /* HACK AREA */
    .active-ui { display:none; flex-direction:column; height:100%; }
    
    .hack-info { background:#200; padding:10px; border:1px solid #f00; margin-bottom:10px; border-radius:4px; text-align:center;}
    
    .deck { display:grid; grid-template-columns:1fr 1fr; gap:8px; overflow-y:auto;}
    
    /* התיקון הגדול לכפתורים */
    .prog { 
        padding:15px; border:1px solid #500; background:#100; color:#faa; 
        cursor:pointer; font-weight:bold; font-size:14px; display:block; width:100%;
        font-family: inherit; margin:0; /* מחיקת ריווח ברירת מחדל */
    }
    .prog:hover:not(:disabled) { background:#400; border-color:#f00; color:#fff;}
    .prog:disabled { opacity:0.3; cursor:not-allowed; background:black;}
    
    /* TERMINAL */
    .logs { flex:1; overflow-y:auto; font-family:'Courier New'; font-size:13px; color:#ccc;}
    .ln { margin-bottom:3px; border-bottom:1px solid #200; padding-bottom:2px;}
    .tm { font-size:10px; color:#555; margin-left:5px;}
    .win { color:#0f0; } .err { background:#500; color:white; } .hack{color:#fe0} .def{color:#0ef}

    /* MODAL */
    .modal { position:fixed; inset:0; background:rgba(0,0,0,0.95); display:none; flex-direction:column; justify-content:center; align-items:center; z-index:99; color:red;}
    .btn-res { padding:15px 30px; font-size:20px; background:red; border:none; cursor:pointer; font-weight:bold; margin-top:20px;}

    @media(max-width:800px) { .grid{ grid-template-columns:1fr; grid-template-rows: auto 1fr auto; } }
</style>
</head>
<body>

<div id="scr-over" class="modal">
    <h1 style="font-size:60px">נלכדת!</h1>
    <p>המשטרה בדרך. פרטי החשבון נחשפו.</p>
    <button class="btn-res" onclick="api('reset')">התחל מחדש</button>
</div>

<div class="top">
    <div class="brand">REDCODE 2.0</div>
    <div class="cash">₪<span id="v-cash">0</span></div>
</div>

<div class="grid">
    <!-- LEFT STATS -->
    <div class="panel">
        <div class="head">SYSTEM</div>
        <div class="bar-row">
            <div class="lbl"><span>סיכון</span><span id="t-trc">0%</span></div>
            <div class="track"><div class="fill trace-c" id="b-trc" style="background:#fff"></div></div>
        </div>
        <div class="bar-row">
            <div class="lbl"><span>זיכרון</span><span id="t-ram">15/15</span></div>
            <div class="track"><div class="fill" id="b-ram"></div></div>
        </div>
        <div style="margin-top:auto; display:flex; gap:5px;">
            <button class="prog" onclick="api('buy','ram')" style="font-size:11px;">+RAM</button>
            <button class="prog" onclick="api('buy','cpu')" style="font-size:11px;">+CPU</button>
        </div>
    </div>

    <!-- MIDDLE LOGS -->
    <div class="panel">
        <div class="head">TERMINAL</div>
        <div id="logs" class="logs"></div>
    </div>

    <!-- RIGHT TARGETS -->
    <div class="panel">
        <div class="head">NETWORK</div>
        
        <!-- List Mode -->
        <div id="mode-list" class="list-area"></div>
        
        <!-- Hack Mode -->
        <div id="mode-hack" class="active-ui">
            <div class="hack-info">
                <h3 id="tg-name" style="margin:0; color:#fa0">...</h3>
                <div class="track" style="height:5px; margin-top:5px; border-color:#fa0"><div id="b-fw" class="fill" style="background:#fa0; width:100%"></div></div>
                <div style="font-size:10px; margin-top:5px;">
                    <span onclick="api('disc')" style="color:red; cursor:pointer; text-decoration:underline;">[ התנתקות חירום ]</span>
                </div>
            </div>
            
            <div class="deck" id="prog-grid"></div>
        </div>
    </div>
</div>

<script>
    const API = "{{ api }}";
    window.onload = ()=> api('init');

    async function api(a, v=null){
        try{
            let res = await fetch(API, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({a:a, v:v})});
            let d = await res.json();
            
            if(d.s.game_over) document.getElementById("scr-over").style.display="flex";
            else document.getElementById("scr-over").style.display="none";

            render(d.s, d.progs);
        } catch(e) { console.error(e); }
    }

    function render(s, progs) {
        document.getElementById("v-cash").innerText = s.money;
        
        document.getElementById("t-trc").innerText = s.trace+"%";
        document.getElementById("b-trc").style.width = s.trace+"%";
        
        document.getElementById("t-ram").innerText = s.ram + "/" + s.max_ram;
        document.getElementById("b-ram").style.width = (s.ram/s.max_ram)*100+"%";

        // Log
        let lbox = document.getElementById("logs");
        lbox.innerHTML = "";
        s.log.forEach(l => lbox.innerHTML += `<div class="ln ${l.c}"><span class="tm">${l.time}</span> ${l.txt}</div>`);

        if(s.active_target) {
            document.getElementById("mode-list").style.display="none";
            document.getElementById("mode-hack").style.display="flex";
            
            let t = s.active_target;
            document.getElementById("tg-name").innerText = t.name;
            let hp = (t.def/t.max_def)*100;
            document.getElementById("b-fw").style.width = hp + "%";
            
            let html = "";
            for(let k in progs) {
                let p = progs[k];
                // אם אין ראם, כפתור מנוטרל
                let dis = s.ram < p.ram ? "disabled" : "";
                
                html += `<button class="prog" ${dis} onclick="api('exec','${k}')">
                    ${p.name}<br>
                    <small style="color:#777">${p.desc}</small>
                </button>`;
            }
            document.getElementById("prog-grid").innerHTML = html;
            
        } else {
            document.getElementById("mode-list").style.display="block";
            document.getElementById("mode-hack").style.display="none";
            
            let html = "";
            s.targets_list.forEach(t => {
                html += `<div class="item" onclick="api('conn','${t.id}')">
                    <div>
                        <div class="iname">${t.name}</div>
                        <div class="isub">הגנה: ${t.max_def} | ₪${t.cash}</div>
                    </div>
                    <div>></div>
                </div>`;
            });
            document.getElementById("mode-list").innerHTML = html;
        }
    }
</script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(port=5006, debug=True)
