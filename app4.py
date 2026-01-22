import random
import uuid
import datetime
from flask import Flask, render_template_string, request, jsonify, session, url_for

app = Flask(__name__)
# מפתח חדש לביטול שמירות ישנות
app.secret_key = 'cyber_ninja_final_edition_v99'

# ==========================================
# 💎 נתונים (קלים וכיפיים)
# ==========================================
PROGRAMS = {
    # שיפרתי את הנזק והורדתי עלות
    "kick": {"name": "בעיטת שרת", "cost": 2, "dmg": 30, "risk": 2, "type": "atk", "desc": "נזק מהיר"},
    "smash": {"name": "פטיש דיגיטלי", "cost": 4, "dmg": 80, "risk": 5, "type": "atk", "desc": "נזק כבד"},
    "god": {"name": "GOD MODE", "cost": 8, "dmg": 500, "risk": 10, "type": "atk", "desc": "מחיקת שרת מיידית"},
    
    # תוכנות הגנה חזקות
    "ghost": {"name": "רוח רפאים", "cost": 2, "heal": 20, "type": "def", "desc": "-20% סיכון"},
    "wipe": {"name": "פורמט לוגים", "cost": 5, "heal": 50, "type": "def", "desc": "-50% סיכון!"}
}

TARGETS_DB = [
    {"name": "Wi-Fi ציבורי", "hp": 20, "cash": 500},
    {"name": "מחשב גיימינג", "hp": 50, "cash": 1200},
    {"name": "כספומט", "hp": 100, "cash": 5000},
    {"name": "בנק אוף אמריקה", "hp": 500, "cash": 25000},
    {"name": "הבית הלבן", "hp": 2000, "cash": 100000},
    {"name": "אזור 51", "hp": 10000, "cash": 1000000}
]

# ==========================================
# ⚙️ מנוע משחק קליל
# ==========================================
class Engine:
    def __init__(self, state=None):
        if not state:
            self.reset()
        else:
            self.state = state

    def log(self, txt, type="info"):
        self.state["log"].insert(0, {"text": txt, "type": type})
        if len(self.state["log"]) > 15: self.state["log"].pop()

    def reset(self):
        self.state = {
            "money": 0,
            "ram": 20, "max_ram": 20, # מתחילים עם המון RAM
            "cpu": 1,
            "risk": 0,
            "target": None,
            "list": [],
            "game_over": False,
            "log": [{"text": "מערכת מוכנה. בהצלחה.", "type": "sys"}]
        }
        self.fill_list()

    def fill_list(self):
        self.state["list"] = []
        for t in TARGETS_DB:
            # מעתיקים ויוצרים מזהה
            new_t = t.copy()
            new_t["id"] = str(uuid.uuid4())
            new_t["max_hp"] = t["hp"]
            self.state["list"].append(new_t)

    # --- Actions ---

    def connect(self, t_id):
        t = next((x for x in self.state["list"] if x["id"] == t_id), None)
        if t:
            self.state["target"] = t
            self.log(f"התחברת ל-{t['name']}", "sys")

    def disconnect(self):
        self.state["target"] = None
        self.state["ram"] = self.state["max_ram"]
        self.log("התנתקת. RAM התמלא.", "sys")

    def execute(self, key):
        if self.state["game_over"]: return
        
        prog = PROGRAMS[key]
        if self.state["ram"] < prog["cost"]:
            self.log("חסר RAM! תתנתק רגע.", "err")
            return

        self.state["ram"] -= prog["cost"]
        
        if prog["type"] == "atk":
            t = self.state["target"]
            if not t: return # הגנה
            
            dmg = prog["dmg"] * self.state["cpu"]
            t["hp"] -= dmg
            
            self.state["risk"] += prog["risk"] # עולה לאט
            
            self.log(f"התקפה מוצלחת! -{dmg} לשרת.", "atk")
            
            if t["hp"] <= 0:
                reward = t["cash"]
                self.state["money"] += reward
                self.log(f"👑 שרת נפל! הרווחת ${reward}", "win")
                self.state["list"].remove(t)
                self.state["target"] = None
                self.state["ram"] = self.state["max_ram"] # פרס
                
                if len(self.state["list"]) == 0:
                    self.fill_list() # מביא חדשים

        elif prog["type"] == "def":
            heal = prog["heal"] * self.state["cpu"]
            self.state["risk"] = max(0, self.state["risk"] - heal)
            self.log("הורדת פרופיל. סיכון ירד.", "def")

        # בדיקת הפסד (רק ב-100 עגול)
        if self.state["risk"] >= 100:
            self.state["game_over"] = True

    def buy(self, type):
        if self.state["game_over"]: return
        
        cost = 0
        if type == "ram":
            cost = 100 * (self.state["max_ram"] // 5)
            if self.state["money"] >= cost:
                self.state["money"] -= cost
                self.state["max_ram"] += 10 # קונים המון בבת אחת
                self.state["ram"] = self.state["max_ram"]
                self.log("שדרוג RAM בוצע.", "win")
            else:
                self.log(f"חסר כסף ({cost})", "err")
                
        elif type == "cpu":
            cost = 500 * self.state["cpu"]
            if self.state["money"] >= cost:
                self.state["money"] -= cost
                self.state["cpu"] += 1
                self.log("שדרוג מעבד בוצע.", "win")
            else:
                self.log(f"חסר כסף ({cost})", "err")

# ==========================================
# SERVER
# ==========================================
@app.route("/")
def home():
    if "uid" not in session: session["uid"] = str(uuid.uuid4())
    api = url_for("update")
    return render_template_string(HTML, api=api)

@app.route("/update", methods=["POST"])
def update():
    try: eng = Engine(session.get("ninja_game"))
    except: eng = Engine(None)
    
    d = request.json
    a = d.get("a")
    v = d.get("v")
    
    if a == "reset": eng.reset()
    elif a == "conn": eng.connect(v)
    elif a == "disc": eng.disconnect()
    elif a == "run": eng.execute(v)
    elif a == "buy": eng.buy(v)
    
    session["ninja_game"] = eng.state
    
    return jsonify({
        "s": eng.state, 
        "progs": PROGRAMS
    })

# ==========================================
# CLIENT UI (CyberWave)
# ==========================================
HTML = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CYBER NINJA</title>
<link href="https://fonts.googleapis.com/css2?family=Exo+2:wght@400;700&display=swap" rel="stylesheet">
<style>
    /* CSS STYLE */
    * { box-sizing: border-box; }
    
    :root {
        --bg: #0d0221;
        --card: #19053d;
        --neon-p: #a239ea; /* Purple */
        --neon-b: #5bc0eb; /* Blue */
        --neon-y: #fde24f; /* Yellow */
        --text: #e0fbfc;
    }
    
    body {
        background: var(--bg);
        background: linear-gradient(135deg, #0d0221 0%, #260c45 100%);
        color: var(--text);
        font-family: 'Exo 2', sans-serif;
        margin: 0; height: 100vh;
        display: flex; flex-direction: column; overflow: hidden;
    }

    /* Header */
    .top-bar {
        background: rgba(0,0,0,0.3); padding: 10px 20px;
        display: flex; justify-content: space-between; align-items: center;
        border-bottom: 2px solid var(--neon-p);
        box-shadow: 0 0 15px var(--neon-p);
    }
    .money-badge {
        font-size: 24px; color: var(--neon-y); font-weight: bold;
        text-shadow: 0 0 10px rgba(253, 226, 79, 0.5);
    }

    /* Layout */
    .content {
        flex: 1; display: grid; grid-template-columns: 250px 1fr 300px;
        gap: 15px; padding: 15px; overflow: hidden;
    }
    
    .panel {
        background: var(--card); border-radius: 12px;
        border: 1px solid rgba(162, 57, 234, 0.3);
        display: flex; flex-direction: column; padding: 15px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
    }
    
    h3 { margin: 0 0 10px 0; color: var(--neon-b); text-align: center; border-bottom: 1px dashed var(--neon-b); padding-bottom: 5px; }

    /* Bars */
    .meter { height: 10px; background: #000; border-radius: 5px; overflow: hidden; margin-bottom: 5px;}
    .fill { height: 100%; transition: width 0.3s ease; }
    
    .label { display: flex; justify-content: space-between; font-size: 14px; margin-bottom: 3px; }

    /* Terminal */
    .terminal-box { 
        flex: 1; overflow-y: auto; background: rgba(0,0,0,0.4); 
        border-radius: 8px; padding: 10px; font-family: monospace; font-size: 13px; 
    }
    .msg { margin-bottom: 4px; border-left: 3px solid transparent; padding-left: 5px; }
    .msg.sys { border-color: #aaa; color: #ccc; }
    .msg.err { border-color: red; background: rgba(255,0,0,0.1); color: #faa; }
    .msg.win { border-color: gold; color: gold; font-weight: bold; }
    .msg.atk { border-color: var(--neon-p); color: #d0f; }

    /* Buttons */
    .shop-btn {
        width: 100%; padding: 10px; margin-top: 5px; background: rgba(255,255,255,0.05);
        border: 1px solid var(--neon-b); color: var(--neon-b); border-radius: 6px; cursor: pointer;
    }
    .shop-btn:hover { background: var(--neon-b); color: #000; }

    /* Targets List */
    .scroll-list { flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 8px; }
    
    .card {
        background: rgba(0,0,0,0.2); border: 1px solid #444; border-radius: 8px;
        padding: 10px; cursor: pointer; transition: 0.2s; display: flex; justify-content: space-between; align-items: center;
    }
    .card:hover { border-color: var(--neon-y); transform: scale(1.02); background: rgba(255,255,255,0.05); }
    .t-title { font-weight: bold; font-size: 15px; }
    .t-sub { font-size: 12px; color: #aaa; }

    /* Hack UI */
    .hack-controls { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; flex: 1; overflow-y: auto; }
    .skill-btn {
        padding: 15px; border: none; border-radius: 8px; cursor: pointer;
        color: white; font-weight: bold; display: flex; flex-direction: column; align-items: center; justify-content: center;
        transition: 0.1s;
    }
    .skill-btn:disabled { opacity: 0.3; cursor: not-allowed; filter: grayscale(1); }
    .skill-btn:active { transform: scale(0.95); }
    
    .btn-atk { background: linear-gradient(135deg, #a239ea, #5900b3); box-shadow: 0 4px 0 #3a0075;}
    .btn-def { background: linear-gradient(135deg, #00b4db, #0083b0); box-shadow: 0 4px 0 #005f80;}
    .btn-exit { background: #d00; color: white; border: none; padding: 10px; width: 100%; border-radius: 6px; cursor: pointer; font-weight:bold; margin-bottom: 10px;}

    /* Game Over */
    .modal {
        position: fixed; inset: 0; background: rgba(0,0,0,0.95); z-index: 99;
        display: none; align-items: center; justify-content: center; flex-direction: column;
    }
    .game-over-txt { font-size: 60px; color: #f06; text-shadow: 0 0 20px #f06; animation: float 3s infinite;}
    
    @keyframes float { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-10px)}}
    
    @media(max-width:800px) { .content { grid-template-columns: 1fr; grid-template-rows: auto 200px auto; }}
</style>
</head>
<body>

<div id="end-screen" class="modal">
    <div class="game-over-txt">GAME OVER</div>
    <p>נתפסת על חם.</p>
    <button onclick="api('reset')" style="font-size:24px; padding:10px 40px; background:#f06; border:none; color:white; border-radius:10px; cursor:pointer;">נסה שוב</button>
</div>

<div class="top-bar">
    <div style="font-weight:900; font-size:20px; letter-spacing:1px;">CYBER NINJA <span style="font-size:12px; font-weight:normal; opacity:0.6">v2088</span></div>
    <div class="money-badge">$<span id="ui-money">0</span></div>
</div>

<div class="content">
    
    <!-- LEFT: Stats & Shop -->
    <div class="panel">
        <h3>מצב מערכת</h3>
        
        <div style="margin-bottom:15px">
            <div class="label"><span>⚠️ סיכון</span><span id="txt-risk">0%</span></div>
            <div class="meter"><div class="fill" id="bar-risk" style="background:#ff2a6d; width:0%"></div></div>
        </div>
        
        <div style="margin-bottom:15px">
            <div class="label"><span>🔋 RAM</span><span id="txt-ram">20/20</span></div>
            <div class="meter"><div class="fill" id="bar-ram" style="background:#05d9e8; width:100%"></div></div>
        </div>
        
        <div style="text-align:center; font-size:14px; margin-bottom:10px; color:#ccc;">
            מעבד רמה <span id="ui-cpu" style="color:#fff; font-weight:bold;">1</span>
        </div>

        <div style="margin-top:auto">
            <button class="shop-btn" onclick="api('buy','ram')">+RAM</button>
            <button class="shop-btn" onclick="api('buy','cpu')">+CPU</button>
        </div>
    </div>

    <!-- CENTER: Terminal -->
    <div class="panel">
        <h3>יומן פעולות</h3>
        <div class="terminal-box" id="log-box"></div>
    </div>

    <!-- RIGHT: Gameplay -->
    <div class="panel">
        <h3>רשת יעדים</h3>
        
        <!-- List -->
        <div id="view-list" class="scroll-list"></div>
        
        <!-- Hack -->
        <div id="view-hack" style="display:none; height:100%; flex-direction:column;">
            <div style="display:flex; justify-content:space-between; margin-bottom:5px;">
                <span id="t-name" style="font-weight:bold; color:var(--neon-y)">TARGET</span>
                <span id="t-hp" style="font-size:12px">100/100</span>
            </div>
            
            <div class="meter" style="border:1px solid var(--neon-y); margin-bottom:15px;">
                <div class="fill" id="bar-hp" style="background:var(--neon-y); width:100%"></div>
            </div>
            
            <button class="btn-exit" onclick="api('disc')">🔌 התנתק לחידוש RAM</button>
            
            <div class="hack-controls" id="prog-btns"></div>
        </div>
    </div>

</div>

<script>
    const API = "{{ api }}";
    
    // Auto start
    window.onload = ()=> api('reset'); // Start fresh

    async function api(act, val=null) {
        try {
            let res = await fetch(API, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({a:act, v:val})});
            let d = await res.json();
            
            if(d.s.game_over) document.getElementById("end-screen").style.display="flex";
            else document.getElementById("end-screen").style.display="none";

            render(d.s, d.progs);
        } catch(e) { console.error(e); }
    }

    function render(s, progs) {
        // Values
        document.getElementById("ui-money").innerText = s.money.toLocaleString();
        document.getElementById("ui-cpu").innerText = s.cpu;
        document.getElementById("txt-risk").innerText = s.risk + "%";
        document.getElementById("bar-risk").style.width = s.risk + "%";
        
        document.getElementById("txt-ram").innerText = s.ram + " / " + s.max_ram;
        document.getElementById("bar-ram").style.width = (s.ram/s.max_ram)*100 + "%";

        // Log
        let lb = document.getElementById("log-box");
        lb.innerHTML = "";
        s.log.forEach(l => {
            lb.innerHTML += `<div class="msg ${l.type}">> ${l.text}</div>`;
        });

        // Views
        if(s.target) {
            document.getElementById("view-list").style.display="none";
            document.getElementById("view-hack").style.display="flex";
            
            let t = s.target;
            document.getElementById("t-name").innerText = t.name;
            let hp = (t.hp / t.max_hp) * 100;
            document.getElementById("bar-hp").style.width = hp + "%";
            document.getElementById("t-hp").innerText = t.hp;
            
            let h="";
            for(let k in progs) {
                let p = progs[k];
                let dis = s.ram < p.cost ? "disabled" : "";
                let cls = p.type=="atk" ? "btn-atk" : "btn-def";
                
                h += `<button class="skill-btn ${cls}" ${dis} onclick="api('run','${k}')">
                    <span>${p.name}</span>
                    <small style="opacity:0.8">${p.desc}</small>
                    <small style="color:yellow; margin-top:5px">-${p.cost} RAM</small>
                </button>`;
            }
            document.getElementById("prog-btns").innerHTML = h;
            
        } else {
            document.getElementById("view-list").style.display="flex";
            document.getElementById("view-hack").style.display="none";
            
            let h="";
            if(s.list.length == 0) h = "<div style='text-align:center; padding:20px'>מערכת מחפשת יעדים חדשים...</div>";
            
            s.list.forEach(t => {
                h += `<div class="card" onclick="api('conn','${t.id}')">
                    <div>
                        <div class="t-title">${t.name}</div>
                        <div class="t-sub">HP: ${t.hp} | שווי: $${t.cash}</div>
                    </div>
                    <div style="font-size:20px; color:var(--neon-b)">➔</div>
                </div>`;
            });
            document.getElementById("view-list").innerHTML = h;
        }
    }
</script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(port=5006, debug=True)
