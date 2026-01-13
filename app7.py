import random
import uuid
from flask import Flask, render_template_string, request, jsonify, session, url_for

app = Flask(__name__)
app.secret_key = 'space_commander_pro_v1'

# ==========================================
# 🛰️ הגדרות התחנה (DATABASE)
# ==========================================

SECTORS = {
    "N": {"name": "האנגר צפוני", "defense": 0, "max_def": 100},
    "S": {"name": "כור דרומי",   "defense": 20, "max_def": 100},
    "E": {"name": "מעבדות מזרח", "defense": 10, "max_def": 100},
    "W": {"name": "מגורים מערב", "defense": 10, "max_def": 100},
    "CORE": {"name": "ליבת הפיקוד", "defense": 1000, "max_def": 1000} # המטרה: להגן על זה
}

ALIENS = [
    {"name": "רחפן", "dmg": 5, "speed": 1},
    {"name": "משחית", "dmg": 15, "speed": 2},
    {"name": "אמא גדולה", "dmg": 40, "speed": 1}
]

# ==========================================
# ⚙️ מנוע המשחק (Logic Engine)
# ==========================================
class Engine:
    def __init__(self, state=None):
        if not state:
            self.state = {
                "energy": 100, "max_energy": 100,
                "oxygen": 100, "max_oxygen": 100,
                "day": 1,
                "sectors": SECTORS.copy(), # העתק של מצב החדרים
                "enemies": [], # [ {"type":..., "loc": "N", "hp": 20} ]
                "log": [{"text": "ברוך הבא, מפקד. המערכות יציבות... לבינתיים.", "type": "sys"}]
            }
        else:
            self.state = state

    def log(self, t, type="sys"): self.state["log"].append({"text": t, "type": type})

    # --- יצירת גל אויבים ---
    def spawn_wave(self):
        # ככל שהימים עוברים, יותר אויבים
        count = random.randint(1, self.state["day"] + 1)
        for _ in range(count):
            loc = random.choice(["N", "S", "E", "W"]) # מגיעים מהצדדים
            base_alien = random.choice(ALIENS)
            new_enemy = {
                "name": base_alien["name"],
                "dmg": base_alien["dmg"],
                "hp": 20 + (self.state["day"] * 5),
                "loc": loc
            }
            self.state["enemies"].append(new_enemy)
            sector_name = self.state["sectors"][loc]["name"]
            self.log(f"⚠️ זיהוי עוין: {new_enemy['name']} מתקרב מ{sector_name}!", "danger")

    # --- תור המשחק (החלק המרכזי) ---
    def next_turn(self):
        s = self.state
        s["energy"] = min(s["energy"] + 10, s["max_energy"]) # טעינה טבעית
        s["oxygen"] -= 2 # צריכת חמצן
        
        if s["oxygen"] <= 0:
            self.log("❌ החמצן אזל. הצוות נחנק.", "danger")
            return "dead"

        # 1. התקפת אויבים
        alive_enemies = []
        for e in s["enemies"]:
            loc = e["loc"]
            sec = s["sectors"][loc]
            
            # אם ההגנה בחדר ירדה ל-0, האויב מתקדם לליבה (CORE)
            if sec["defense"] <= 0 and loc != "CORE":
                self.log(f"🚨 {e['name']} פרץ את {sec['name']} ומתקדם לליבה!", "danger")
                e["loc"] = "CORE"
                sec["defense"] = 0 # מוודא שלא ירד מתחת לאפס
            
            # גרימת נזק למקום הנוכחי
            target = s["sectors"][e["loc"]]
            damage = e["dmg"]
            target["defense"] -= damage
            
            # האם האויב מת מהגנות אוטומטיות? (נניח שיש לייזרים חלשים)
            e["hp"] -= 5 
            
            if target["defense"] <= 0 and e["loc"] == "CORE":
                return "dead" # הליבה הושמדה
            
            if e["hp"] > 0:
                alive_enemies.append(e)
            else:
                self.log(f"🔫 {e['name']} חוסל ע'י מערכות ההגנה האוטומטיות.", "success")

        s["enemies"] = alive_enemies
        
        # גלים חדשים כל תור רביעי בערך
        if random.random() < 0.3 + (s["day"] * 0.05):
            self.spawn_wave()

        return "ok"

    # --- פעולות המפקד ---
    def action_fire(self, loc):
        cost = 25
        if self.state["energy"] >= cost:
            self.state["energy"] -= cost
            # פוגע בכל האויבים בסקטור הזה
            hits = 0
            survivors = []
            for e in self.state["enemies"]:
                if e["loc"] == loc:
                    e["hp"] -= 50
                    hits += 1
                    if e["hp"] > 0: survivors.append(e)
                    else: self.log(f"🎯 פיצוץ פלזמה השמיד את {e['name']} ב{loc}!", "success")
                else:
                    survivors.append(e)
            
            self.state["enemies"] = survivors
            
            room = self.state["sectors"][loc]["name"]
            if hits == 0: self.log(f"ירית ל-{room} אך לא היה שם אף אחד. בזבוז אנרגיה.", "warning")
        else:
            self.log("⚠️ אנרגיה נמוכה! לא ניתן לירות.", "warning")

    def action_repair(self, loc):
        cost = 15
        if self.state["energy"] >= cost:
            self.state["energy"] -= cost
            self.state["sectors"][loc]["defense"] = self.state["sectors"][loc]["max_def"]
            room = self.state["sectors"][loc]["name"]
            self.log(f"🔧 נשלחו רחפני תיקון ל{room}. ההגנה שוחזרה.", "info")
        else:
            self.log("⚠️ חסרה אנרגיה לתיקון.", "warning")

    def action_ventilate(self):
        cost = 30
        if self.state["energy"] >= cost:
            self.state["energy"] -= cost
            self.state["oxygen"] = min(self.state["oxygen"] + 40, 100)
            self.log("💨 מערכות האוורור הופעלו במלוא העוצמה.", "success")
        else:
            self.log("⚠️ אין מספיק חשמל להפעלת מסנני האוויר.", "warning")

# ==========================================
# שרת
# ==========================================
@app.route("/")
def index():
    if "uid" not in session: session["uid"] = str(uuid.uuid4())
    api = url_for("update")
    return render_template_string(HTML, api=api)

@app.route("/api/update", methods=["POST"])
def update():
    try:
        # Load engine
        eng = Engine(session.get("game_cmd"))
    except:
        eng = Engine(None) # auto reset

    data = request.json or {}
    act = data.get("action") # fire / repair / vent / wait
    target = data.get("target") # N / S / E / W

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
        eng.log("⏳ המתנת תור אחד...", "sys")
        status = eng.next_turn()

    # בדיקת הפסד
    if status == "dead" or eng.state["sectors"]["CORE"]["defense"] <= 0:
        return jsonify({"dead": True, "day": eng.state["day"]})

    session["game_cmd"] = eng.state
    
    return jsonify({
        "stats": {
            "energy": eng.state["energy"],
            "oxy": eng.state["oxygen"],
            "day": eng.state["day"]
        },
        "sectors": eng.state["sectors"],
        "enemies_count": len(eng.state["enemies"]),
        "log": eng.state["log"]
    })

# ==========================================
# FRONTEND - COMMANDER INTERFACE
# ==========================================
HTML = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>PROXIMA COMMAND</title>
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&display=swap" rel="stylesheet">
<style>
    :root {
        --bg: #050a14;
        --ui-dark: #0f192b;
        --neon-blue: #00f3ff;
        --neon-red: #ff2a2a;
        --neon-green: #2aff5d;
        --ui-border: 1px solid rgba(0, 243, 255, 0.3);
    }
    
    body { background: var(--bg); color: var(--neon-blue); font-family: 'Orbitron', sans-serif; margin:0; height:100vh; overflow:hidden; display:flex; flex-direction:column;}
    
    /* === TOP BAR (Resource) === */
    .top-deck {
        display:grid; grid-template-columns: 1fr 1fr 1fr;
        padding: 15px; border-bottom: 2px solid var(--neon-blue);
        background: rgba(0,20,40,0.8);
        box-shadow: 0 0 20px rgba(0, 243, 255, 0.2);
    }
    .meter { background: #000; border: 1px solid #333; height: 20px; position:relative; margin-top:5px; border-radius: 4px; overflow:hidden;}
    .fill { height:100%; width:100%; transition: 0.3s; }
    .label { font-size: 0.9rem; font-weight:bold; display:flex; justify-content:space-between;}
    
    /* === MAIN LAYOUT (RADAR) === */
    .command-center {
        flex: 1; position: relative;
        display: flex; align-items: center; justify-content: center;
        background-image: 
            radial-gradient(circle, rgba(0, 243, 255, 0.05) 1px, transparent 1px),
            linear-gradient(rgba(0, 243, 255, 0.03) 1px, transparent 1px);
        background-size: 30px 30px, 100% 30px;
    }
    
    /* בניית מפה בצורת פלוס */
    .station-grid {
        display: grid;
        grid-template-areas: 
            ". N ."
            "W C E"
            ". S .";
        gap: 15px;
        transform: scale(1.1);
    }
    
    .sector {
        width: 120px; height: 100px;
        background: rgba(0,0,0,0.8);
        border: 2px solid #334;
        display: flex; flex-direction: column; align-items: center; justify-content: space-between;
        padding: 10px; cursor: pointer;
        transition: 0.2s;
        position: relative;
    }
    .sector:hover { border-color: var(--neon-blue); box-shadow: 0 0 15px var(--neon-blue); }
    .sector.danger { border-color: var(--neon-red); animation: pulse 1s infinite; }
    .sector-name { font-size: 0.8rem; color: #aaa; }
    
    .hp-bar { width: 100%; height: 5px; background: #333; margin-top: 5px; }
    .hp-val { width: 100%; height: 100%; background: var(--neon-green); transition:0.3s;}
    
    .btn-act { width:100%; padding:5px; margin-top:2px; font-size:0.7rem; cursor:pointer; border:none; color:white; font-weight:bold; font-family:inherit;}
    .btn-fire { background: rgba(200, 50, 50, 0.7); }
    .btn-repair { background: rgba(50, 150, 200, 0.7); }

    /* CORE - במרכז */
    .sec-c { grid-area: C; border-color: gold; box-shadow: 0 0 30px rgba(255,215,0,0.2); width:140px; height:120px;}
    .sec-n { grid-area: N; }
    .sec-s { grid-area: S; }
    .sec-e { grid-area: E; }
    .sec-w { grid-area: W; }

    /* === BOTTOM (LOGS & GLOBAL) === */
    .console {
        height: 200px;
        background: #020408;
        border-top: 2px solid #333;
        display: grid; grid-template-columns: 2fr 1fr;
        font-family: 'Consolas', monospace;
    }
    .logs { padding: 15px; overflow-y: auto; font-size: 0.9rem; border-left: 1px solid #222; }
    .log-line { margin-bottom: 5px; border-right: 3px solid transparent; padding-right:5px;}
    .sys { color: #88c; }
    .danger { color: #f55; border-color:#f55; background: rgba(50,0,0,0.3);}
    .success { color: #5f5; border-color:#5f5;}
    
    .global-controls {
        display: flex; flex-direction: column; gap: 10px; padding: 20px; align-items: center; justify-content: center;
    }
    .big-btn {
        width: 100%; padding: 15px; font-size: 1rem; cursor: pointer;
        background: transparent; color: var(--neon-blue); border: 2px solid var(--neon-blue);
        text-transform: uppercase; font-family: inherit; font-weight: bold;
        transition: 0.2s;
    }
    .big-btn:hover { background: var(--neon-blue); color: black; }
    
    @keyframes pulse { 50% { border-color: transparent; box-shadow:none;} }

</style>
</head>
<body>

<div class="top-deck">
    <div>
        <div class="label">⚡ ENERGY <span id="val-en">100%</span></div>
        <div class="meter"><div class="fill" id="bar-en" style="background:var(--neon-blue)"></div></div>
    </div>
    <div style="text-align:center">
        <h2 style="margin:0; text-shadow:0 0 10px white;">PROXIMA II</h2>
        <div style="font-size:0.8rem; color:#aaa;">DAY <span id="val-day">1</span> | ALERT LVL: HIGH</div>
    </div>
    <div>
        <div class="label">💨 OXYGEN <span id="val-oxy">100%</span></div>
        <div class="meter"><div class="fill" id="bar-oxy" style="background:#0ff"></div></div>
    </div>
</div>

<div class="command-center">
    <div class="station-grid">
        <!-- SECTOR NORTH -->
        <div class="sector sec-n" id="sec-N">
            <span class="sector-name">NORTH HANGAR</span>
            <div class="hp-bar"><div class="hp-fill" id="hp-N"></div></div>
            <button class="btn-act btn-fire" onclick="act('fire','N')">🔥 YALA (25⚡)</button>
            <button class="btn-act btn-repair" onclick="act('repair','N')">🔧 FIX (15⚡)</button>
        </div>

        <!-- SECTOR WEST -->
        <div class="sector sec-w" id="sec-W">
            <span class="sector-name">WEST WING</span>
            <div class="hp-bar"><div class="hp-fill" id="hp-W"></div></div>
            <button class="btn-act btn-fire" onclick="act('fire','W')">🔥 FIRE</button>
            <button class="btn-act btn-repair" onclick="act('repair','W')">🔧 FIX</button>
        </div>

        <!-- CORE CENTER -->
        <div class="sector sec-c">
            <strong style="color:gold">CORE</strong>
            <div style="font-size:30px">☢️</div>
            <div class="hp-bar" style="height:10px;"><div class="hp-fill" id="hp-CORE" style="background:gold"></div></div>
        </div>

        <!-- SECTOR EAST -->
        <div class="sector sec-e" id="sec-E">
            <span class="sector-name">EAST LABS</span>
            <div class="hp-bar"><div class="hp-fill" id="hp-E"></div></div>
            <button class="btn-act btn-fire" onclick="act('fire','E')">🔥 FIRE</button>
            <button class="btn-act btn-repair" onclick="act('repair','E')">🔧 FIX</button>
        </div>

        <!-- SECTOR SOUTH -->
        <div class="sector sec-s" id="sec-S">
            <span class="sector-name">SOUTH REACTOR</span>
            <div class="hp-bar"><div class="hp-fill" id="hp-S"></div></div>
            <button class="btn-act btn-fire" onclick="act('fire','S')">🔥 FIRE</button>
            <button class="btn-act btn-repair" onclick="act('repair','S')">🔧 FIX</button>
        </div>
    </div>
</div>

<div class="console">
    <div class="logs" id="log-box">
        <div class="log-line sys">INITIALIZING DEFENSE SYSTEMS... ONLINE.</div>
    </div>
    <div class="global-controls">
        <button class="big-btn" onclick="act('wait')" style="border-color:#aaa; color:#aaa;">⌛ WAIT TURN (+10⚡)</button>
        <button class="big-btn" onclick="act('vent')" style="border-color:#0f0; color:#0f0;">💨 VENTILATE (-30⚡)</button>
        <button class="big-btn" onclick="act('reset')" style="font-size:0.8rem; border:none; color:red">ABORT / RESET</button>
    </div>
</div>

<script>
    const API = "{{ api }}";

    async function act(action, target=null) {
        let res = await fetch(API, {
            method:'POST', headers:{'Content-Type':'application/json'},
            body: JSON.stringify({action:action, target:target})
        });
        let d = await res.json();

        if (d.dead) {
            alert("GAME OVER! התחנה הושמדה ביום " + d.day);
            act("reset");
            return;
        }

        // 1. Resources
        updateBar("en", d.stats.energy);
        updateBar("oxy", d.stats.oxy);
        document.getElementById("val-day").innerText = d.stats.day;

        // 2. Sectors status
        for (const [key, sec] of Object.entries(d.sectors)) {
            let hpPct = (sec.defense / sec.max_def) * 100;
            let elBar = document.getElementById("hp-"+key);
            if(elBar) elBar.style.width = hpPct + "%";
            
            // שינוי צבע לפי נזק
            if(hpPct < 30) elBar.style.backgroundColor = "red";
            else elBar.style.backgroundColor = (key=="CORE") ? "gold" : "#2aff5d";
            
            // אפקט אדום לחדר כולו אם הוא מותקף או הרוס
            if(document.getElementById("sec-"+key)) {
                if (hpPct < 100) document.getElementById("sec-"+key).style.borderColor = "orange";
                if (hpPct < 50) document.getElementById("sec-"+key).classList.add("danger");
                else document.getElementById("sec-"+key).classList.remove("danger");
            }
        }

        // 3. Logs
        let l = document.getElementById("log-box");
        l.innerHTML = "";
        d.log.reverse().forEach(ln => { // הכי חדש למעלה
            l.innerHTML += `<div class='log-line ${ln.type}'>${ln.text}</div>`;
        });
    }

    function updateBar(id, val) {
        document.getElementById("bar-"+id).style.width = val + "%";
        document.getElementById("val-"+id).innerText = val + "%";
        // שינוי צבע בקריסה
        if(val < 20) document.getElementById("bar-"+id).style.backgroundColor = "red";
        else if (id=="en") document.getElementById("bar-"+id).style.backgroundColor = "var(--neon-blue)";
        else document.getElementById("bar-"+id).style.backgroundColor = "#0ff";
    }
</script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(port=5006, debug=True)
