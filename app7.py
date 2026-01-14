import random
import uuid
from flask import Flask, render_template_string, request, jsonify, session, url_for

app = Flask(__name__)
# שיניתי מפתח כדי לאפס הכל
app.secret_key = 'hebrew_commander_full_fix_v11' 

# ==========================================
# 🛰️ נתוני התחנה
# ==========================================

SECTORS = {
    "N": {"name": "האנגר צפוני", "defense": 0, "max_def": 100},
    "S": {"name": "כור דרומי",   "defense": 20, "max_def": 100},
    "E": {"name": "מעבדות מזרח", "defense": 10, "max_def": 100},
    "W": {"name": "נשקייה מערב", "defense": 10, "max_def": 100},
    "CORE": {"name": "ליבת הפיקוד", "defense": 1000, "max_def": 1000} 
}

ALIENS = [
    {"name": "רחפן עוקץ", "dmg": 5, "speed": 1},
    {"name": "משחית כבד", "dmg": 15, "speed": 2},
    {"name": "מלכת הכוורת", "dmg": 40, "speed": 1}
]

# ==========================================
# ⚙️ מנוע המשחק
# ==========================================
class Engine:
    def __init__(self, state=None):
        if not state:
            self.state = {
                "energy": 100, "max_energy": 100,
                "oxygen": 100, "max_oxygen": 100,
                "day": 1,
                "sectors": SECTORS.copy(),
                "enemies": [],
                "log": [{"text": "המערכות אותחלו בהצלחה. ממתין לפקודות, המפקד.", "type": "sys"}]
            }
        else:
            self.state = state

    def log(self, t, type="sys"): 
        self.state["log"].append({"text": t, "type": type})

    def spawn_wave(self):
        count = random.randint(1, self.state["day"] + 1)
        for _ in range(count):
            loc = random.choice(["N", "S", "E", "W"])
            base = random.choice(ALIENS)
            enemy = {
                "name": base["name"],
                "dmg": base["dmg"],
                "hp": 20 + (self.state["day"] * 5),
                "loc": loc
            }
            self.state["enemies"].append(enemy)
            sector_name = self.state["sectors"][loc]["name"]
            self.log(f"⚠️ חדירה! {enemy['name']} זוהה ב-{sector_name}!", "danger")

    def next_turn(self):
        s = self.state
        s["energy"] = min(s["energy"] + 10, s["max_energy"]) 
        s["oxygen"] -= 3
        
        if s["oxygen"] <= 0:
            self.log("❌ אזל החמצן. התחנה אבדה.", "danger")
            return "dead"

        # אויבים תוקפים
        alive = []
        for e in s["enemies"]:
            loc = e["loc"]
            sec = s["sectors"][loc]
            
            # אם החדר נפרץ (הגנה 0) - האויב מתקדם לליבה
            if sec["defense"] <= 0 and loc != "CORE":
                self.log(f"🚨 {sec['name']} נפל! האויב נע לליבה.", "danger")
                e["loc"] = "CORE"
                sec["defense"] = 0
            
            # נזק לחדר הנוכחי
            target = s["sectors"][e["loc"]]
            target["defense"] -= e["dmg"]
            
            # הגנות אוטומטיות (נזק פסיבי לאויב)
            e["hp"] -= 5 
            
            if target["defense"] <= 0 and e["loc"] == "CORE":
                return "dead"
            
            if e["hp"] > 0:
                alive.append(e)
            else:
                self.log(f"🔫 צריחים אוטומטיים חיסלו את {e['name']}.", "success")

        s["enemies"] = alive
        
        # סיכוי לגל חדש (עולה עם הימים)
        if random.random() < 0.3 + (s["day"] * 0.05):
            self.spawn_wave()

        return "ok"

    def action_fire(self, loc):
        if self.state["energy"] >= 25:
            self.state["energy"] -= 25
            hits = 0
            survivors = []
            for e in self.state["enemies"]:
                if e["loc"] == loc:
                    e["hp"] -= 50
                    hits += 1
                    if e["hp"] > 0: survivors.append(e)
                    else: self.log(f"🚀 פגעת וחיסלת את {e['name']}!", "success")
                else:
                    survivors.append(e)
            self.state["enemies"] = survivors
            
            # לוגיקה למקרה שיורים על ריק
            sec_name = self.state["sectors"][loc]["name"]
            if hits == 0: self.log(f"ירית על {sec_name} סתם. בזבוז אנרגיה.", "sys")
        else:
            self.log("⚡ חסרה אנרגיה לירי! (25 נדרש)", "danger")

    def action_repair(self, loc):
        if self.state["energy"] >= 15:
            self.state["energy"] -= 15
            # תיקון מלא
            self.state["sectors"][loc]["defense"] = self.state["sectors"][loc]["max_def"]
            nm = self.state["sectors"][loc]["name"]
            self.log(f"🔧 בוצע תיקון חירום ב-{nm}.", "info")
        else:
            self.log("⚡ חסרה אנרגיה לתיקון! (15 נדרש)", "danger")

    def action_ventilate(self):
        if self.state["energy"] >= 30:
            self.state["energy"] -= 30
            self.state["oxygen"] = min(self.state["oxygen"] + 40, 100)
            self.log("💨 החלפת אוויר בוצעה. חמצן עלה.", "success")
        else:
            self.log("⚡ חסרה אנרגיה לאוורור! (30 נדרש)", "danger")

    def action_wait(self):
        self.log("⏳ המתנה (צבירת אנרגיה)...", "sys")

# ==========================================
# SERVER
# ==========================================
@app.route("/")
def index():
    if "uid" not in session: session["uid"] = str(uuid.uuid4())
    # תיקון כתובת דינמית ל-JS
    return render_template_string(HTML, api=url_for("update"))

@app.route("/api/update", methods=["POST"])
def update():
    d = request.json
    try: 
        # טוען משחק או יוצר חדש אם נשבר
        eng = Engine(session.get("game_cmd"))
    except: 
        eng = Engine(None)

    act = d.get("action")
    target = d.get("target") # N, S, E, W

    status = "ok"

    if act == "reset":
        eng = Engine(None)
    elif act == "fire":
        eng.action_fire(target)
        status = eng.next_turn()
    elif act == "repair":
        eng.action_repair(target)
        status = eng.next_turn()
    elif act == "vent":
        eng.action_ventilate()
        status = eng.next_turn()
    elif act == "wait":
        eng.action_wait()
        status = eng.next_turn()

    # בדיקת הפסד
    if status == "dead":
        return jsonify({"dead": True, "day": eng.state["day"]})

    # בדיקת אם עבר יום (כל 10 תורות נגיד? או פשוט משאירים רציף)
    # נגדיל יום אקראית לשם הפשטות כשהתורות מתקדמים
    if random.random() < 0.1: 
        eng.state["day"] += 1
        eng.log(f"☀️ יום {eng.state['day']} החל. התקפות מתחזקות.", "sys")

    session["game_cmd"] = eng.state
    
    return jsonify({
        "stats": {
            "energy": eng.state["energy"],
            "oxy": eng.state["oxygen"],
            "day": eng.state["day"]
        },
        "sectors": eng.state["sectors"],
        "log": eng.state["log"]
    })

# ==========================================
# FRONTEND - עיצוב חלל עברי
# ==========================================
HTML = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>COMMANDER IL</title>
<style>
    body { background: #0b0f19; color: #00f3ff; font-family: monospace; margin: 0; height: 100vh; display: flex; flex-direction: column; overflow:hidden;}
    
    /* TOP BAR */
    .hud { 
        background: #111; padding: 15px; border-bottom: 2px solid #00f3ff; 
        display: flex; justify-content: space-between; align-items: center;
        box-shadow: 0 0 20px rgba(0, 243, 255, 0.2);
    }
    .bar-box { width: 100px; text-align: center; }
    .bar { height: 10px; background: #333; margin-top: 5px; border:1px solid #555; }
    .fill { height: 100%; transition: 0.3s; width: 100%; }
    
    /* GAME AREA */
    .station { 
        flex: 1; display: grid; 
        grid-template-areas: 
            ". N ."
            "W C E"
            ". S .";
        gap: 15px; align-items: center; justify-content: center;
        transform: scale(0.9);
    }
    
    .room {
        width: 140px; height: 110px;
        background: rgba(0,20,40,0.8); border: 2px solid #446;
        display: flex; flex-direction: column; justify-content: space-between; padding: 10px;
        text-align: center; transition: 0.2s; position: relative;
    }
    .room:hover { border-color: white; box-shadow: 0 0 15px #fff; }
    
    /* Grid Positions */
    .r-n { grid-area: N; } 
    .r-s { grid-area: S; } 
    .r-e { grid-area: E; } 
    .r-w { grid-area: W; } 
    .r-c { grid-area: C; border-color: gold; height: 130px; width: 160px; box-shadow: 0 0 20px rgba(255,215,0,0.1);}

    /* Inner Room UI */
    .hp-strip { height: 6px; background: #222; margin-bottom: 5px; width: 100%;}
    .hp-val { height: 100%; background: #0f0; width: 100%; transition: 0.2s;}
    
    .btn { 
        width: 100%; border: none; padding: 4px; margin-top: 2px; 
        font-family: inherit; font-weight: bold; cursor: pointer; color: white;
    }
    .btn-fire { background: #d32f2f; }
    .btn-fix { background: #1976d2; }
    .btn-wait { background: #333; color: #aaa; border: 1px solid #555;}
    
    .danger-glow { animation: pulse 1s infinite; border-color: red; }
    @keyframes pulse { 50% { box-shadow: 0 0 20px red; background: rgba(50,0,0,0.5); } }

    /* LOG & CONTROLS */
    .bottom-panel { height: 220px; background: #050508; border-top: 2px solid #333; display: grid; grid-template-columns: 2fr 1fr;}
    .logs { padding: 15px; overflow-y: auto; font-size: 14px; border-left: 1px solid #333;}
    .log-line { margin-bottom: 4px; padding-bottom: 2px; border-bottom: 1px solid #111; }
    
    .sys-controls { padding: 20px; display: flex; flex-direction: column; gap: 10px; justify-content: center; }
    .big-btn { padding: 15px; background: transparent; border: 1px solid #00f3ff; color: #00f3ff; cursor: pointer; font-size: 14px;}
    .big-btn:hover { background: #00f3ff; color: black; }

    /* Colors */
    .sys { color: #88c; } .danger { color: #f55; } .success { color: #5f5; } .info { color: #fd0; }

</style>
</head>
<body>

<div class="hud">
    <div class="bar-box">
        ⚡ חשמל <span id="txt-en">100</span>%
        <div class="bar"><div id="bar-en" class="fill" style="background:#00f3ff"></div></div>
    </div>
    <div style="font-size:20px; font-weight:bold; letter-spacing:2px; text-shadow:0 0 10px white;">
        PROXIMA STATION
        <div style="font-size:12px; font-weight:normal; color:#aaa; margin-top:5px;">יום הפיקוד: <span id="day-val">1</span></div>
    </div>
    <div class="bar-box">
        💨 חמצן <span id="txt-ox">100</span>%
        <div class="bar"><div id="bar-ox" class="fill" style="background:#00ff9d"></div></div>
    </div>
</div>

<div class="station">
    <!-- North -->
    <div class="room r-n" id="room-N">
        <div>האנגר צפון</div>
        <div class="hp-strip"><div class="hp-val" id="hp-N"></div></div>
        <button class="btn btn-fire" onclick="act('fire', 'N')">🔥 אש (25⚡)</button>
        <button class="btn btn-fix" onclick="act('repair', 'N')">🔧 תיקון (15⚡)</button>
    </div>

    <!-- West -->
    <div class="room r-w" id="room-W">
        <div>נשקייה מערב</div>
        <div class="hp-strip"><div class="hp-val" id="hp-W"></div></div>
        <button class="btn btn-fire" onclick="act('fire', 'W')">🔥 אש</button>
        <button class="btn btn-fix" onclick="act('repair', 'W')">🔧 תיקון</button>
    </div>

    <!-- CORE -->
    <div class="room r-c" id="room-CORE">
        <div style="color:gold; font-weight:bold;">הליבה</div>
        <div style="font-size:30px;">☢️</div>
        <div class="hp-strip"><div class="hp-val" id="hp-CORE" style="background:gold"></div></div>
    </div>

    <!-- East -->
    <div class="room r-e" id="room-E">
        <div>מעבדות מזרח</div>
        <div class="hp-strip"><div class="hp-val" id="hp-E"></div></div>
        <button class="btn btn-fire" onclick="act('fire', 'E')">🔥 אש</button>
        <button class="btn btn-fix" onclick="act('repair', 'E')">🔧 תיקון</button>
    </div>

    <!-- South -->
    <div class="room r-s" id="room-S">
        <div>כור דרום</div>
        <div class="hp-strip"><div class="hp-val" id="hp-S"></div></div>
        <button class="btn btn-fire" onclick="act('fire', 'S')">🔥 אש</button>
        <button class="btn btn-fix" onclick="act('repair', 'S')">🔧 תיקון</button>
    </div>
</div>

<div class="bottom-panel">
    <div class="logs" id="logbox"></div>
    
    <div class="sys-controls">
        <button class="big-btn" onclick="act('wait')">⌛ המתן (טען ⚡)</button>
        <button class="big-btn" onclick="act('vent')" style="border-color:#0f0; color:#0f0;">💨 אוורר חמצן (-30⚡)</button>
        <button class="btn btn-wait" onclick="act('reset')" style="font-size:10px; border:none; background:none; color:red">⚠ איפוס מערכות</button>
    </div>
</div>

<script>
    const API = "{{ api }}";

    async function act(action, target=null) {
        try {
            let res = await fetch(API, {
                method: 'POST', 
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({action:action, target:target})
            });
            let d = await res.json();

            if (d.dead) {
                alert("GAME OVER! התחנה נפלה ביום " + d.day);
                act("reset"); return;
            }

            // עדכון משאבים
            updateBar('en', d.stats.energy);
            updateBar('ox', d.stats.oxy);
            document.getElementById('day-val').innerText = d.stats.day;

            // עדכון חדרים
            for (let k in d.sectors) {
                let sec = d.sectors[k];
                let elHp = document.getElementById("hp-"+k);
                let pct = (sec.defense / sec.max_def) * 100;
                
                if(elHp) elHp.style.width = pct + "%";
                
                // שינוי צבע הבר בקריסה
                if (pct < 30) elHp.style.backgroundColor = "red";
                else if (k === "CORE") elHp.style.backgroundColor = "gold";
                else elHp.style.backgroundColor = "#0f0";

                // אפקט אזעקה אם החדר מותקף (פחות מ-100% הגנה)
                let roomEl = document.getElementById("room-"+k);
                if (roomEl) {
                    if (pct < 100) roomEl.classList.add("danger-glow");
                    else roomEl.classList.remove("danger-glow");
                }
            }

            // לוג
            let lb = document.getElementById("logbox");
            lb.innerHTML = "";
            d.log.reverse().forEach(l => {
                lb.innerHTML += `<div class="log-line ${l.type}">${l.text}</div>`;
            });

        } catch(e) { console.error(e); }
    }

    function updateBar(id, val) {
        document.getElementById("txt-"+id).innerText = val;
        document.getElementById("bar-"+id).style.width = val + "%";
        if(val < 20) document.getElementById("bar-"+id).style.backgroundColor = "red";
    }
    
    // התחלה
    window.onload = () => { act('init'); }; // סתם קריאה ראשונית לרענון מסך
</script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(port=5006, debug=True)
