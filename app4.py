import random
import uuid
import datetime
from flask import Flask, render_template_string, request, jsonify, session, url_for

app = Flask(__name__)
app.secret_key = 'hacker_elite_fixed_v88'

# ==========================================
# 🛑 חלק שלא שונה (שורות 13-64 מהקוד שלך) 🛑
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

TARGETS = [
    # --- רמה 1: "שכונה דיגיטלית" (קלים מאוד) ---
    {"name": "ראוטר של שכן", "def": 10, "cash": 15},
    {"name": "בית קפה", "def": 20, "cash": 25},
    {"name": "פיצרייה מקומית", "def": 30, "cash": 40},
    {"name": "כספומט שכונתי", "def": 50, "cash": 80},

    # --- רמה 2: "עסקים קטנים" (קלים) ---
    {"name": "מערכת ניהול חנות", "def": 80, "cash": 120},
    {"name": "מחשב של מנהל בנק", "def": 120, "cash": 200},
    {"name": "רשת בית ספר תיכון", "def": 150, "cash": 250},
    {"name": "שרת של חברת שליחויות", "def": 180, "cash": 300},

    # --- רמה 3: "תאגידים בינוניים" (בינוני) ---
    {"name": "מסד נתונים - רשת שיווק", "def": 250, "cash": 500},
    {"name": "שרתי חברת ביטוח", "def": 300, "cash": 700},
    {"name": "בנק דיגיטלי קטן", "def": 400, "cash": 1000},
    {"name": "רשת מלונות ארצית", "def": 500, "cash": 1500},

    # --- רמה 4: "תשתיות קריטיות" (קשה) ---
    {"name": "בקרה - רכבת קלה", "def": 700, "cash": 2200},
    {"name": "דאטה בייס - אשראי", "def": 900, "cash": 3000},
    {"name": "שרתי משרד החינוך", "def": 1200, "cash": 4000},
    {"name": "תחנת כוח אזורית", "def": 1500, "cash": 5500},

    # --- רמה 5: "ביטחון לאומי" (קשה מאוד) ---
    {"name": "שרת משטרתי", "def": 2000, "cash": 8000},
    {"name": "מגדל פיקוח נתב\"ג", "def": 2500, "cash": 11000},
    {"name": "לוויין תקשורת", "def": 3500, "cash": 15000},
    {"name": "שרתי המוסד", "def": 5000, "cash": 25000},

    # --- רמה 6: "הגדולים ביותר" (אגדי) ---
    {"name": "מחשבי הבורסה", "def": 7500, "cash": 50000},
    {"name": "הבנק הפדרלי", "def": 10000, "cash": 80000},
    {"name": "שרתי הפנטגון", "def": 15000, "cash": 150000},
    {"name": "המחשב של אילון מאסק", "def": 25000, "cash": 300000}
]

# ==========================================
# ⚙️ מנוע המשחק המתוקן
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
            "ram": 10, "max_ram": 10,
            "cpu": 1,
            "trace": 0,
            "active_target": None, 
            "targets_list": [],
            "game_over": False,
            "log": [{"time": self.getTime(), "txt": "המערכת מוכנה.", "c": "sys"}]
        }
        self.generate_targets()

    def log(self, txt, c="info"):
        self.state["log"].insert(0, {"time": self.getTime(), "txt": txt, "c": c})
        if len(self.state["log"]) > 25: self.state["log"].pop()

    def generate_targets(self):
        self.state["targets_list"] = []
        # בוחרים 5 מטרות רנדומליות מכל הרשימה הענקית
        # (אפשר לשכלל שייבחר לפי הרמה הנוכחית של המעבד, אבל כרגע רנדומלי לחלוטין כמו שביקשת)
        for _ in range(5):
            base = random.choice(TARGETS).copy()
            base["max_def"] = int(base["def"] * random.uniform(0.9, 1.1))
            base["def"] = base["max_def"]
            base["id"] = str(uuid.uuid4())
            self.state["targets_list"].append(base)

    # --- Actions ---

    def connect(self, t_id):
        if self.state["active_target"]: return
        t = next((i for i in self.state["targets_list"] if i["id"] == t_id), None)
        if t:
            self.state["active_target"] = t
            self.log(f"התחברות ל-{t['name']} בוצעה.", "sys")

    def disconnect(self):
        if not self.state["active_target"]: return
        self.state["active_target"] = None
        # ✅ תיקון: מילוי RAM ביציאה
        self.state["ram"] = self.state["max_ram"] 
        self.log("התנתקת. RAM שוחרר והתמלא.", "def")

    def execute(self, pid):
        if self.state["game_over"]: return
        prog = PROGRAMS[pid]
        
        # ✅ תיקון: בדיקת חוסר RAM
        if self.state["ram"] < prog["ram"]:
            self.log("שגיאה: אין מספיק זיכרון! (התנתק כדי למלא)", "err")
            return

        self.state["ram"] -= prog["ram"]
        
        if prog["type"] == "atk":
            tgt = self.state["active_target"]
            if not tgt:
                self.state["ram"] += prog["ram"] # החזר אם אין מטרה
                return
            
            dmg = prog["dmg"] * self.state["cpu"]
            tgt["def"] -= dmg
            self.state["trace"] = min(100, self.state["trace"] + prog["risk"])
            
            self.log(f"הרצת {prog['name']}... נזק: {dmg}", "hack")
            
            # בדיקת ניצחון
            if tgt["def"] <= 0:
                amount = tgt["cash"]
                self.state["money"] += amount
                self.log(f"הצלחה! השגת ₪{amount}", "win")
                self.state["targets_list"].remove(tgt)
                self.state["active_target"] = None
                self.state["ram"] = self.state["max_ram"] # מילוי RAM כבונוס
                
                if not self.state["targets_list"]:
                    self.generate_targets()

        elif prog["type"] == "def":
            # הגנה אפשרית גם בלי להיות מחובר
            heal = prog["heal"] * self.state["cpu"]
            self.state["trace"] = max(0, self.state["trace"] - heal)
            self.log(f"ניקוי עקבות בוצע. (-{heal}% סיכון)", "def")

        # בדיקת הפסד
        if self.state["trace"] >= 100:
            self.state["game_over"] = True
            self.state["active_target"] = None

    def buy(self, item):
        # ✅ תיקון: בדיקה שיש כסף לפני קנייה
        cost = 0
        if item == "ram":
            cost = self.state["max_ram"] * 10
            if self.state["money"] >= cost:
                self.state["money"] -= cost
                self.state["max_ram"] += 2
                self.state["ram"] = self.state["max_ram"]
                self.log(f"RAM שודרג ל-{self.state['max_ram']}GB", "win")
            else:
                self.log(f"חסר כסף! (צריך ₪{cost})", "err")
        elif item == "cpu":
            cost = self.state["cpu"] * 250
            if self.state["money"] >= cost:
                self.state["money"] -= cost
                self.state["cpu"] += 1
                self.log(f"CPU שודרג לרמה {self.state['cpu']}", "win")
            else:
                self.log(f"חסר כסף! (צריך ₪{cost})", "err")

# ==========================================
# APP ROUTES
# ==========================================
@app.route("/")
def index():
    if "uid" not in session: session["uid"] = str(uuid.uuid4())
    api = url_for("api_handle")
    return render_template_string(HTML, api=api)

@app.route("/api", methods=["POST"])
def api_handle():
    try: eng = GameEngine(session.get("hacker_il_final"))
    except: eng = GameEngine(None)
    
    d = request.json
    act = d.get("a")
    val = d.get("v")
    
    if act == "reset": eng.reset()
    elif act == "conn": eng.connect(val)
    elif act == "disc": eng.disconnect()
    elif act == "exec": eng.execute(val)
    elif act == "buy": eng.buy(val)
    
    session["hacker_il_final"] = eng.state
    
    return jsonify({"s": eng.state, "progs": PROGRAMS})

# ==========================================
# UI (Green Neon Matrix Style)
# ==========================================
HTML = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>RedCode OS</title>
<!-- חיבור נכון לפונט דיגיטלי -->
<link href="https://fonts.googleapis.com/css2?family=Rubik:wght@400;700&family=Share+Tech+Mono&display=swap" rel="stylesheet">
<style>
    :root { 
        --neon: #0f0; --dim: #002200; --bg: #000; --panel: #050505; 
        --border: 1px solid #0f0; --red: #ff3333; --gold: #ffd700;
    }
    body { background: var(--bg); color: var(--neon); font-family: 'Rubik', sans-serif; margin: 0; height: 100vh; display: flex; flex-direction: column; overflow: hidden; }
    
    /* CRT Scanlines */
    body::before { content:""; position:absolute; top:0; left:0; width:100%; height:100%; background: repeating-linear-gradient(0deg, rgba(0,0,0,0.1), rgba(0,0,0,0.1) 1px, transparent 1px, transparent 2px); pointer-events: none; z-index:9; }

    /* Header */
    .top { height: 60px; border-bottom: var(--border); background: #020202; display: flex; align-items: center; justify-content: space-between; padding: 0 20px; z-index:10;}
    .brand { font-family: 'Share Tech Mono'; font-size: 24px; letter-spacing: 2px; }
    .cash { font-size: 20px; color: var(--gold); text-shadow: 0 0 5px var(--gold);}

    /* Main Grid */
    .grid { flex: 1; display: grid; grid-template-columns: 260px 1fr 280px; gap: 10px; padding: 10px; overflow: hidden; }
    .col { display: flex; flex-direction: column; gap: 10px; height: 100%; }
    
    .box { background: rgba(0, 15, 0, 0.9); border: 1px solid #004400; display: flex; flex-direction: column; padding: 10px; position: relative; border-radius: 4px; box-shadow: 0 0 10px rgba(0, 255, 0, 0.05); }
    .box h3 { margin: 0 0 10px 0; font-size: 16px; border-bottom: 1px solid #004400; padding-bottom: 5px; color: #aaa; text-align: center; font-family: 'Share Tech Mono';}

    /* Bars */
    .bar-wrap { margin-bottom: 15px; }
    .lbl { display: flex; justify-content: space-between; font-size: 12px; margin-bottom: 2px; }
    .trck { width: 100%; height: 10px; background: #111; border: 1px solid #333; direction: ltr; /* Fix bar direction */ }
    .fill { height: 100%; width: 0%; transition: width 0.3s; background: var(--neon); }
    .trace-f { background: var(--red); box-shadow: 0 0 8px var(--red); }

    /* Terminal */
    .term { flex: 1; font-family: 'Share Tech Mono', monospace; font-size: 14px; overflow-y: auto; color: #ccc; }
    .line { margin-bottom: 4px; border-bottom: 1px solid #111; padding-bottom: 2px; }
    .ts { color: #444; font-size: 10px; margin-right: 5px; }
    .sys { color: #0aa; } .err { color: #f44; } .hack { color: #ff0; } .win { color: #0f0; font-weight:bold; }

    /* Target List */
    .list { overflow-y: auto; flex: 1; }
    .item { padding: 10px; border: 1px dashed #004400; margin-bottom: 5px; cursor: pointer; transition: 0.2s; display: flex; justify-content: space-between; align-items: center; }
    .item:hover { background: #001100; border-color: #0f0; }
    
    /* Active Hack */
    .active-ui { display: none; flex-direction: column; height: 100%; }
    .deck { display: grid; grid-template-columns: 1fr 1fr; gap: 5px; flex: 1; align-content: start; overflow-y: auto; }
    .prog { 
        background: #001; border: 1px solid #004400; padding: 10px; cursor: pointer; 
        color: #8f8; text-align: center; font-family: 'Rubik';
    }
    .prog:hover { background: #002200; border-color: #0f0; color: #fff; }
    .prog small { display: block; font-size: 10px; color: #555; margin-top: 3px; }
    
    /* Shop */
    .shop { display: flex; gap: 5px; margin-top: auto; }
    .buy-btn { flex: 1; background: #000; border: 1px solid #444; color: #888; padding: 8px; cursor: pointer; font-size: 11px; }
    .buy-btn:hover { color: gold; border-color: gold; }

    /* Responsive */
    @media (max-width: 900px) {
        .grid { grid-template-columns: 1fr; grid-template-rows: auto 1fr auto; }
    }
    
    /* Game Over */
    .overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.95); z-index: 99; display: none; align-items: center; justify-content: center; flex-direction: column; color: red;}
</style>
</head>
<body>

<div id="scr-over" class="overlay">
    <h1 style="font-size: 50px; text-shadow: 0 0 20px red;">מערכת נפרצה</h1>
    <p>המשטרה בדרך אליך.</p>
    <button onclick="api('reset')" style="background: red; border: none; padding: 10px 30px; font-weight: bold; cursor: pointer; font-size: 18px;">נסה שוב</button>
</div>

<div class="top">
    <div class="brand">RedCode OS <span style="font-size:12px;color:#555">v4.0</span></div>
    <div class="cash">₪<span id="v-cash">0</span></div>
</div>

<div class="grid">
    <!-- LEFT -->
    <div class="col">
        <div class="box" style="height: 100%;">
            <h3>STATUS</h3>
            
            <div class="bar-wrap">
                <div class="lbl"><span>סיכון (Trace)</span> <span id="l-trace">0%</span></div>
                <div class="trck"><div class="fill trace-f" id="b-trace"></div></div>
            </div>
            
            <div class="bar-wrap">
                <div class="lbl"><span>זיכרון (RAM)</span> <span id="l-ram">10/10</span></div>
                <div class="trck"><div class="fill" id="b-ram"></div></div>
            </div>
            
            <div style="text-align: center; margin-bottom: 20px;">
                מעבד (CPU): <span id="v-cpu" style="color:#fff; font-weight:bold;">1</span>
            </div>

            <div class="shop">
                <button class="buy-btn" onclick="api('buy','ram')">+RAM (₪<span id="c-ram">?</span>)</button>
                <button class="buy-btn" onclick="api('buy','cpu')">+CPU (₪<span id="c-cpu">?</span>)</button>
            </div>
        </div>
    </div>

    <!-- MID -->
    <div class="col">
        <div class="box" style="flex:1;">
            <h3>TERMINAL_OUTPUT</h3>
            <div id="term" class="term"></div>
        </div>
    </div>

    <!-- RIGHT -->
    <div class="col">
        <div class="box" style="flex:1;">
            <h3>TARGET_NETWORK</h3>
            
            <!-- LIST -->
            <div id="ui-list" class="list"></div>
            
            <!-- HACK -->
            <div id="ui-hack" class="active-ui">
                <div style="display:flex; justify-content:space-between; margin-bottom:5px;">
                    <strong id="tgt-nm" style="color:yellow">Target</strong>
                    <button onclick="api('disc')" style="background:none; border:1px solid red; color:red; cursor:pointer;">[נתק]</button>
                </div>
                
                <div class="trck" style="border-color:red; margin-bottom:10px;"><div id="b-def" class="fill" style="background:red; width:100%"></div></div>
                
                <div class="deck" id="progs"></div>
            </div>
        </div>
    </div>
</div>

<script>
    const API = "{{ api }}";
    
    window.onload = ()=> api('init');

    async function api(a, v=null){
        let r = await fetch(API, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({a:a, v:v})});
        let d = await res.json();
        render(d.s, d.progs);
    }

    function render(s, progs){
        // Game Over
        document.getElementById("scr-over").style.display = s.game_over ? "flex" : "none";

        // Values
        document.getElementById("v-cash").innerText = s.money;
        document.getElementById("l-trace").innerText = s.trace + "%";
        document.getElementById("b-trace").style.width = s.trace + "%";
        document.getElementById("l-ram").innerText = s.ram + "/" + s.max_ram;
        document.getElementById("b-ram").style.width = (s.ram/s.max_ram)*100 + "%";
        document.getElementById("v-cpu").innerText = s.cpu;
        
        // Shop prices
        document.getElementById("c-ram").innerText = s.max_ram * 10;
        document.getElementById("c-cpu").innerText = s.cpu * 250;

        // Terminal
        let tm = document.getElementById("term");
        tm.innerHTML = "";
        s.log.forEach(l => tm.innerHTML += `<div class="line ${l.c}"><span class="ts">${l.time}</span> ${l.txt}</div>`);

        // Views
        if(s.active_target) {
            document.getElementById("ui-list").style.display="none";
            document.getElementById("ui-hack").style.display="flex";
            
            // Hack UI
            let t = s.active_target;
            document.getElementById("tgt-nm").innerText = t.name;
            let hp = (t.def / t.max_def)*100;
            document.getElementById("b-def").style.width = hp + "%";
            
            // Programs
            let html="";
            for(let k in progs){
                let p = progs[k];
                html += `<button class="prog" onclick="api('exec','${k}')">
                    ${p.name}
                    <small>RAM: ${p.ram} | ${p.desc}</small>
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
                        <strong>${t.name}</strong><br>
                        <span style="font-size:11px; color:#666">הגנה: ${t.max_def} | קופה: ₪${t.cash}</span>
                    </div>
                    <div style="color:lime">></div>
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
