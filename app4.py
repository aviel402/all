import random
import uuid
import datetime
from flask import Flask, render_template_string, request, jsonify, session, url_for

app = Flask(__name__)
app.secret_key = 'redcode_fix_final_v555'

# ==========================================
# 💾 נתונים (אותם נתונים, איזון קל)
# ==========================================
PROGRAMS = {
    # שינוי: הבהרה שחובה מספיק RAM
    "p1": {"name": "מכה קלה", "ram": 2, "dmg": 15, "risk": 4, "type": "atk", "desc": "דורש 2 RAM"},
    "p2": {"name": "הזרקת קוד", "ram": 4, "dmg": 40, "risk": 8, "type": "atk", "desc": "דורש 4 RAM"},
    "p3": {"name": "פריצה מלאה","ram": 8, "dmg": 100,"risk": 20,"type": "atk", "desc": "דורש 8 RAM"},
    
    "d1": {"name": "הסתר IP", "ram": 2, "heal": 5, "type": "def", "desc": "דורש 2 RAM"},
    "d2": {"name": "נקה לוגים", "ram": 5, "heal": 20, "type": "def", "desc": "דורש 5 RAM"}
}

# אותה רשימה גדולה שביקשת
TARGETS = [
    {"name": "ראוטר של שכן", "def": 10, "cash": 15},
    {"name": "בית קפה", "def": 20, "cash": 25},
    {"name": "פיצרייה מקומית", "def": 30, "cash": 40},
    {"name": "כספומט שכונתי", "def": 50, "cash": 80},
    {"name": "מערכת ניהול חנות", "def": 80, "cash": 120},
    {"name": "מחשב של מנהל בנק", "def": 120, "cash": 200},
    {"name": "רשת בית ספר תיכון", "def": 150, "cash": 250},
    {"name": "שרת של חברת שליחויות", "def": 180, "cash": 300},
    {"name": "מסד נתונים - רשת שיווק", "def": 250, "cash": 500},
    {"name": "שרתי חברת ביטוח", "def": 300, "cash": 700},
    {"name": "בנק דיגיטלי קטן", "def": 400, "cash": 1000},
    {"name": "רשת מלונות ארצית", "def": 500, "cash": 1500},
    {"name": "בקרה - רכבת קלה", "def": 700, "cash": 2200},
    {"name": "דאטה בייס - אשראי", "def": 900, "cash": 3000},
    {"name": "שרתי משרד החינוך", "def": 1200, "cash": 4000},
    {"name": "תחנת כוח אזורית", "def": 1500, "cash": 5500},
    {"name": "שרת משטרתי", "def": 2000, "cash": 8000},
    {"name": "מגדל פיקוח נתב\"ג", "def": 2500, "cash": 11000},
    {"name": "לוויין תקשורת", "def": 3500, "cash": 15000},
    {"name": "שרתי המוסד", "def": 5000, "cash": 25000},
    {"name": "מחשבי הבורסה", "def": 7500, "cash": 50000},
    {"name": "הבנק הפדרלי", "def": 10000, "cash": 80000},
    {"name": "שרתי הפנטגון", "def": 15000, "cash": 150000},
    {"name": "המחשב של אילון מאסק", "def": 25000, "cash": 300000}
]

class GameEngine:
    def __init__(self, state=None):
        if not state:
            self.reset()
        else:
            self.state = state

    def getTime(self):
        return datetime.datetime.now().strftime("%H:%M:%S")

    def reset(self):
        # תיקון: מתחילים עם 15 RAM במקום 10 כדי שיהיה יותר קל לשחק
        self.state = {
            "money": 0,
            "ram": 15, "max_ram": 15, 
            "cpu": 1,
            "trace": 0,
            "active_target": None, 
            "targets_list": [],
            "game_over": False,
            "log": [{"time": self.getTime(), "txt": "מערכת מוכנה.", "c": "sys"}]
        }
        self.load_all_targets()

    def log(self, txt, c="info"):
        self.state["log"].insert(0, {"time": self.getTime(), "txt": txt, "c": c})
        if len(self.state["log"]) > 25: self.state["log"].pop()

    def load_all_targets(self):
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
            self.log(f"מחובר ל-{t['name']}", "sys")

    def disconnect(self):
        if not self.state["active_target"]: return
        self.state["active_target"] = None
        self.state["ram"] = self.state["max_ram"] 
        self.log("התנתקת. RAM שוחרר.", "def")

    def execute(self, pid):
        if self.state["game_over"]: return
        prog = PROGRAMS[pid]
        
        # אם אין RAM, שום דבר לא קורה
        if self.state["ram"] < prog["ram"]:
            self.log("שגיאה: אין מספיק RAM! תתנתק כדי לחדש.", "err")
            return

        self.state["ram"] -= prog["ram"]
        
        if prog["type"] == "atk":
            tgt = self.state["active_target"]
            if not tgt: return
            
            dmg = prog["dmg"] * self.state["cpu"]
            tgt["def"] -= dmg
            self.state["trace"] = min(100, self.state["trace"] + prog["risk"])
            
            self.log(f"{prog['name']} הופעל >> נזק: {dmg}", "hack")
            
            if tgt["def"] <= 0:
                amount = tgt["cash"]
                self.state["money"] += amount
                self.log(f"פריצה הושלמה! ₪{amount} נכנסו.", "win")
                self.state["targets_list"].remove(tgt)
                self.state["active_target"] = None
                self.state["ram"] = self.state["max_ram"] # מילוי RAM כבונוס ניצחון
                
                if not self.state["targets_list"]:
                    self.log("כל המטרות חוסלו. סיימת את המשחק!", "win")

        elif prog["type"] == "def":
            heal = prog["heal"] * self.state["cpu"]
            self.state["trace"] = max(0, self.state["trace"] - heal)
            self.log(f"ניקוי עקבות בוצע.", "def")

        if self.state["trace"] >= 100:
            self.state["game_over"] = True
            self.state["active_target"] = None

    def buy(self, item):
        cost = 0
        if item == "ram":
            cost = self.state["max_ram"] * 10
            if self.state["money"] >= cost:
                self.state["money"] -= cost
                self.state["max_ram"] += 2
                self.state["ram"] = self.state["max_ram"]
                self.log(f"שדרוג RAM בוצע.", "win")
            else:
                self.log(f"חסר כסף ({cost})", "err")
        elif item == "cpu":
            cost = self.state["cpu"] * 250
            if self.state["money"] >= cost:
                self.state["money"] -= cost
                self.state["cpu"] += 1
                self.log(f"שדרוג CPU בוצע.", "win")
            else:
                self.log(f"חסר כסף ({cost})", "err")

# ==========================================
# SERVER
# ==========================================
@app.route("/")
def index():
    if "uid" not in session: session["uid"] = str(uuid.uuid4())
    api = url_for("handle")
    return render_template_string(HTML, api=api)

@app.route("/api", methods=["POST"])
def handle():
    try: eng = GameEngine(session.get("red_fixed_2"))
    except: eng = GameEngine(None)
    
    d = request.json
    act = d.get("a")
    val = d.get("v")
    
    if act == "reset": eng.reset()
    elif act == "conn": eng.connect(val)
    elif act == "disc": eng.disconnect()
    elif act == "exec": eng.execute(val)
    elif act == "buy": eng.buy(val)
    
    session["red_fixed_2"] = eng.state
    
    return jsonify({"s": eng.state, "progs": PROGRAMS})

# ==========================================
# UI FIX
# ==========================================
HTML = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>RedCode OS</title>
<link href="https://fonts.googleapis.com/css2?family=Rubik:wght@400;700&family=Share+Tech+Mono&display=swap" rel="stylesheet">
<style>
    /* הגדרות צבע לאדום */
    :root { 
        --neon: #ff0000; 
        --dim: #330000; 
        --bg: #000; 
        --panel: #080202; 
        --border: 1px solid #aa0000; 
        --red: #ff3333; 
        --gold: #ffd700;
        --white: #eee;
    }
    
    * { box-sizing: border-box; }
    
    body {
        background: var(--bg); color: var(--neon);
        font-family: 'Rubik', sans-serif;
        margin: 0; height: 100vh; display: flex; flex-direction: column; overflow: hidden;
    }
    
    /* CRT Lines */
    body::before { 
        content:""; position:absolute; top:0; left:0; width:100%; height:100%; 
        background: repeating-linear-gradient(0deg, rgba(255,0,0,0.03), rgba(255,0,0,0.03) 1px, transparent 1px, transparent 2px); 
        pointer-events: none; z-index:9; 
    }

    /* HEADER */
    .top { 
        height: 60px; border-bottom: var(--border); background: #1a0000; 
        display: flex; align-items: center; justify-content: space-between; padding: 0 20px; z-index:10;
    }
    .brand { font-family: 'Share Tech Mono'; font-size: 24px; letter-spacing: 2px; text-shadow: 0 0 10px red; }
    .cash { font-size: 20px; color: var(--gold); }

    /* GRID FIX: Uses flexbox correctly inside grid to prevent overflow issues */
    .grid { flex: 1; display: grid; grid-template-columns: 260px 1fr 300px; gap: 10px; padding: 10px; position: relative; z-index: 5; overflow:hidden;}
    .col { display: flex; flex-direction: column; gap: 10px; height: 100%; overflow: hidden;}
    
    .box { 
        background: rgba(20, 0, 0, 0.9); border: var(--border); 
        display: flex; flex-direction: column; padding: 10px; 
        flex: 1; overflow: hidden; /* This fixes the scroll leak */
        position: relative; border-radius: 4px; box-shadow: 0 0 10px rgba(255, 0, 0, 0.1); 
    }
    .box h3 { 
        margin: 0 0 10px 0; font-size: 16px; border-bottom: 1px solid #500; 
        padding-bottom: 5px; color: #a55; text-align: center; font-family: 'Share Tech Mono';
    }

    /* Bars */
    .bar-wrap { margin-bottom: 15px; }
    .lbl { display: flex; justify-content: space-between; font-size: 12px; margin-bottom: 2px; }
    .trck { width: 100%; height: 12px; background: #100; border: 1px solid #500; direction: ltr; }
    .fill { height: 100%; width: 0%; transition: width 0.3s; background: var(--neon); box-shadow: 0 0 5px var(--neon);}
    .trace-f { background: #fff; box-shadow: 0 0 8px white; } 

    /* Terminal */
    .term { flex: 1; font-family: 'Share Tech Mono', monospace; font-size: 14px; overflow-y: auto; color: #ccc; }
    .ln { margin-bottom: 4px; padding-bottom: 4px; border-bottom: 1px solid #200; }
    .ts { color: #555; font-size: 10px; margin-right: 5px; float: left;}
    .sys { color: #f88; } .err { color: #fff; background:#500; } .hack { color: #fd0; } .win { color: #0f0; } .def { color:#aaf; }

    /* === LIST SCROLL FIX === */
    .list { overflow-y: auto; flex: 1; padding-right: 5px; display: block; height: 100%;}
    
    ::-webkit-scrollbar { width: 5px; }
    ::-webkit-scrollbar-track { background: #100; }
    ::-webkit-scrollbar-thumb { background: #500; }
    
    .item { 
        padding: 12px; border: 1px dashed #500; margin-bottom: 5px; cursor: pointer; transition: 0.2s; 
        display: flex; justify-content: space-between; align-items: center; 
    }
    .item:hover { background: #200; border-color: var(--neon); transform:translateX(-5px); }
    
    /* Hacking Screen */
    .active-ui { display: none; flex-direction: column; height: 100%; }
    .deck { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; flex: 1; align-content: start; overflow-y: auto; margin-top:10px;}
    
    .prog { 
        background: #100; border: 1px solid #500; padding: 15px; cursor: pointer; 
        color: #fdd; text-align: center; font-family: 'Rubik'; font-size: 16px;
        display:flex; flex-direction:column; justify-content:center;
    }
    /* כפתור מושבת */
    .prog:disabled { opacity: 0.2; cursor: not-allowed; border: 1px solid #333; color: #555; background: black; }
    .prog:hover:not(:disabled) { background: #300; border-color: var(--neon); color: #fff; }
    
    .def-card { border-color: #33a; color: #ccf; } 
    .def-card:hover:not(:disabled) { border-color:#88f; background: #002; }

    .shop { display: flex; gap: 5px; margin-top: auto; }
    .buy-btn { flex: 1; background: #100; border: 1px solid #500; color: #a88; padding: 8px; cursor: pointer; font-size: 11px; }
    .buy-btn:hover { color: gold; border-color: gold; background:#210; }

    .overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.95); z-index: 99; display: none; align-items: center; justify-content: center; flex-direction: column; color: red;}
</style>
</head>
<body>

<div id="scr-over" class="overlay">
    <h1 style="font-size: 50px; text-shadow: 0 0 20px red;">המערכת נפרצה!</h1>
    <button onclick="api('reset')" style="background: red; border: none; padding: 10px 30px; font-weight: bold; cursor: pointer; font-size: 18px;">אתחול מערכת</button>
</div>

<div class="top">
    <div class="brand">RedCode <span style="font-size:12px;color:#555">v6.0</span></div>
    <div class="cash">₪<span id="v-cash">0</span></div>
</div>

<div class="grid">
    <!-- צד ימין (סטטוסים) -->
    <div class="col" style="flex:0 0 250px"> <!-- קובע גודל קבוע לסטטוסים -->
        <div class="box">
            <h3>STATUS</h3>
            <div class="bar-wrap">
                <div class="lbl"><span>סיכון (Trace)</span> <span id="l-trace">0%</span></div>
                <div class="trck"><div id="b-trace" class="fill trace-f"></div></div>
            </div>
            <div class="bar-wrap">
                <div class="lbl"><span>זיכרון (RAM)</span> <span id="l-ram">10/10</span></div>
                <div class="trck"><div id="b-ram" class="fill"></div></div>
            </div>
            <div style="text-align: center; margin-bottom: 20px;">
                מעבד: <span id="v-cpu" style="color:#fff; font-weight:bold;">1</span>
            </div>
            <div class="shop">
                <button class="buy-btn" onclick="api('buy','ram')">+RAM (₪<span id="c-ram">?</span>)</button>
                <button class="buy-btn" onclick="api('buy','cpu')">+CPU (₪<span id="c-cpu">?</span>)</button>
            </div>
        </div>
    </div>

    <!-- אמצע (טרמינל) -->
    <div class="col" style="flex:1">
        <div class="box">
            <h3>TERMINAL</h3>
            <div id="term" class="term"></div>
        </div>
    </div>

    <!-- שמאל (רשת) -->
    <div class="col" style="flex:0 0 300px">
        <div class="box">
            <h3>NETWORK</h3>
            <div id="ui-list" class="list"></div>
            
            <div id="ui-hack" class="active-ui">
                <div style="display:flex; justify-content:space-between; margin-bottom:5px;">
                    <strong id="tgt-nm" style="color:#fa0">Target</strong>
                    <button onclick="api('disc')" style="background:none; border:1px solid #f00; color:#f00; cursor:pointer;">[נתק]</button>
                </div>
                <div class="trck" style="border-color:#555; margin-bottom:10px;"><div id="b-fw" class="fill" style="background:#fa0; width:100%"></div></div>
                <div class="deck" id="progs"></div>
            </div>
        </div>
    </div>
</div>

<script>
    const API = "{{ api }}";
    window.onload = ()=> api('init');

    async function api(a, v=null){
        try {
            let res = await fetch(API, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({a:a, v:v})});
            let d = await res.json();
            
            if(d.s.game_over) document.getElementById("scr-over").style.display = "flex";
            else document.getElementById("scr-over").style.display = "none";

            render(d.s, d.progs);
        } catch(e){ console.log(e); }
    }

    function render(s, progs){
        document.getElementById("v-cash").innerText = s.money;
        document.getElementById("l-trace").innerText = s.trace + "%";
        document.getElementById("b-trace").style.width = s.trace + "%";
        document.getElementById("l-ram").innerText = s.ram + "/" + s.max_ram;
        document.getElementById("b-ram").style.width = (s.ram/s.max_ram)*100 + "%";
        document.getElementById("v-cpu").innerText = s.cpu;
        
        // Prices
        document.getElementById("c-ram").innerText = s.max_ram * 10;
        document.getElementById("c-cpu").innerText = s.cpu * 250;

        let tm = document.getElementById("term");
        tm.innerHTML = "";
        s.log.forEach(l => tm.innerHTML += `<div class="ln ${l.c}"><span class="ts">${l.time}</span> ${l.txt}</div>`);

        if(s.active_target) {
            document.getElementById("ui-list").style.display="none";
            document.getElementById("ui-hack").style.display="flex";
            
            let t = s.active_target;
            document.getElementById("tgt-nm").innerText = t.name;
            let hp = (t.def / t.max_def)*100;
            document.getElementById("b-fw").style.width = hp + "%";
            
            let html="";
            for(let k in progs){
                let p = progs[k];
                let cls = (p.type === "def") ? "def-card" : "";
                
                // התיקון הקריטי: משבית כפתורים שאין להם מספיק RAM
                let disabled = (s.ram < p.ram) ? "disabled" : "";
                
                html += `<button class="prog ${cls}" ${disabled} onclick="api('exec','${k}')">
                    <span style="font-weight:bold">${p.name}</span>
                    <small>${p.ram} RAM | ${p.desc}</small>
                </button>`;
            }
            document.getElementById("progs").innerHTML = html;
        } else {
            document.getElementById("ui-list").style.display="block";
            document.getElementById("ui-hack").style.display="none";
            
            let html="";
            s.targets_list.forEach(t => {
                html += `<div class="item" onclick="api('conn','${t.id}')">
                    <div>
                        <div style="font-weight:bold">${t.name}</div>
                        <span style="font-size:11px; color:#a55">הגנה: ${t.max_def} | ₪${t.cash}</span>
                    </div>
                    <div style="color:red; font-size:20px;">➜</div>
                </div>`;
            });
            document.getElementById("ui-list").innerHTML = html;
        }
    }
</script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(port=5006, debug=True)
