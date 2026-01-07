import random
import uuid

# ==========================================
# 🌌 מאגר התוכן העצום (ה"מוח" של המשחק)
# ==========================================

# 1. דמויות (NPCs) - אנשים שפוגשים
NPC_DB = [
    {"name": "סוחר נודד", "icon": "👳", "role": "trade", "lines": ["יש לי סחורה נדירה בשבילך.", "הדרכים מסוכנות היום, חבר.", "תן לי זהב, אתן לך חיים."], "gift": "שיקוי חיים"},
    {"name": "זקן מטורף", "icon": "🤪", "role": "talk", "lines": ["הם מסתכלים עלינו מהקירות!", "אל תאמין למפה! המפה משקרת!", "ראיתי את הסוף... הוא ירוק."], "gift": None},
    {"name": "אביר פצוע", "icon": "🤕", "role": "quest", "lines": ["המפלצת שם לקחה לי את החרב...", "עזור לי... בבקשה...", "כבוד הוא מותרות של העשירים."], "gift": "מטבע זהב"},
    {"name": "רובוט עתיק", "icon": "🤖", "role": "info", "lines": ["ביפ בופ. המערכת קורסת.", "סוללה חלשה. זקוק לטעינה.", "שגיאה 404: תקווה לא נמצאה."], "gift": "סוללה"},
    {"name": "צללית מסתורית", "icon": "🕵️", "role": "scam", "lines": ["רוצה לראות קסם?", "החיים הם רק אשליה.", "תבחר קלף."], "gift": None}
]

# 2. אירועים (מה קורה כשנכנסים לחדר)
EVENTS = [
    {"msg": "⚠️ דרכת על מלכודת קוצים!", "effect": "dmg", "val": 10},
    {"msg": "✨ קרן אור מאירה עליך ומחדשת כוחות.", "effect": "heal", "val": 20},
    {"msg": "💀 מצאת גופה של הרפתקן קודם. יש לו קצת כסף בכיס.", "effect": "gold", "val": 30},
    {"msg": "🕸️ נכנסת לקורי עכביש דביקים. איבדת זמן ואנרגיה.", "effect": "stamina", "val": -20},
    {"msg": "📜 מצאת פתק ישן: 'אל תרד למטה'.", "effect": "none", "val": 0},
    {"msg": "🌧️ החל גשם חומצי דק. זה שורף!", "effect": "dmg", "val": 5}
]

# 3. מחולל שמות מקומות (שילובים)
PLACE_PREFIX = ["מקדש", "בונקר", "יער", "מרתף", "מגדל", "ביוב", "ארמון", "מעבדת"]
PLACE_SUFFIX = ["הנשכחים", "המוות", "הזמן", "הקריסטל", "הצללים", "הדמים", "החוכמה"]

# 4. אויבים (רגילים + בוסים)
ENEMIES = [
    {"name": "עכברוש ענק", "icon": "🐀", "hp": 15, "atk": 3, "gold": 5, "xp": 10},
    {"name": "זומבי", "icon": "🧟", "hp": 30, "atk": 8, "gold": 15, "xp": 25},
    {"name": "שדון אש", "icon": "👺", "hp": 25, "atk": 12, "gold": 40, "xp": 35},
    {"name": "רוח רפאים", "icon": "👻", "hp": 40, "atk": 10, "gold": 0, "xp": 50},
    {"name": "מלך הגולגולת (בוס)", "icon": "☠️", "hp": 120, "atk": 25, "gold": 500, "xp": 200}
]

# 5. חפצים
ITEMS = {
    "שיקוי חיים": {"type": "heal", "val": 40},
    "סוללה": {"type": "stamina", "val": 50},
    "מגילת כוח": {"type": "xp", "val": 100},
    "יהלום": {"type": "gold", "val": 200}
}


# ==========================================
# מנוע המשחק (ENGINE)
# ==========================================
from flask import Flask, render_template_string, request, jsonify, session, url_for
app = Flask(__name__)
app.secret_key = 'rpg_infinite_world_gen'

class WorldGen:
    def create_room(self, x, y):
        # 10% סיכוי לאירוע מיוחד במקום חדר רגיל
        is_event = random.random() < 0.15
        
        # שם גנרטיבי
        name = f"{random.choice(PLACE_PREFIX)} {random.choice(PLACE_SUFFIX)}"
        
        # בחירת תוכן
        npc = None
        enemy = None
        event = None
        loot = []

        if is_event:
            event = random.choice(EVENTS)
            name = "אזור תקרית"
        else:
            # 25% סיכוי ל-NPC
            if random.random() < 0.25:
                base_npc = random.choice(NPC_DB)
                npc = base_npc.copy() # עותק כדי לשמור על שיחות
            
            # אם אין NPC, אולי יש אויב? (40%)
            elif random.random() < 0.4:
                enemy = random.choice(ENEMIES).copy()
            
            # 50% סיכוי לחפצים
            if random.random() < 0.5:
                loot.append(random.choice(list(ITEMS.keys())))

        return {
            "name": name,
            "type": "event" if is_event else "room",
            "icon": "⚠️" if is_event else random.choice(["🌲","🏚️","🏯","🌑","🛤️"]),
            "enemy": enemy,
            "npc": npc,
            "items": loot,
            "event_data": event,
            "gold": random.randint(0, 30)
        }

class Engine:
    def __init__(self, state=None):
        if not state:
            self.state = {
                "x": 0, "y": 0,
                "stats": {"hp": 100, "max_hp": 100, "st": 100, "max_st": 100, "xp": 0, "lvl": 1, "gold": 0},
                "inv": [],
                "map": {},
                "visited": ["0,0"],
                "log": [{"text": "התעוררת בעולם חדש ואינסופי.", "type": "sys"}]
            }
            # חדר ראשון
            self.state["map"]["0,0"] = {"name": "כפר התחלתי", "type":"safe", "icon":"⛺", "npc": None, "enemy":None, "items":[], "gold":0, "event_data":None}
        else:
            self.state = state
        
        self.gen = WorldGen()

    def key(self): return f"{self.state['x']},{self.state['y']}"

    def move(self, dx, dy):
        s = self.state["stats"]
        if s["st"] <= 0:
            self.log("😪 אתה תשוש מדי! (תנוח R)", "warn")
            return
        
        s["st"] -= 2 # עלות צעד
        self.state["x"] += dx
        self.state["y"] += dy
        k = self.key()
        
        # יצירת עולם פרוצדורלית
        new_place = False
        if k not in self.state["map"]:
            self.state["map"][k] = self.gen.create_room(self.state['x'], self.state['y'])
            new_place = True
        
        if k not in self.state["visited"]: self.state["visited"].append(k)
        
        r = self.state["map"][k]
        self.log(f"הגעת ל: {r['name']}", "sys")
        
        # טיפול באירועים אוטומטיים
        if r.get("event_data"):
            ev = r["event_data"]
            self.log(ev["msg"], "info")
            if ev["effect"] == "dmg": s["hp"] -= ev["val"]
            if ev["effect"] == "heal": s["hp"] = min(s["hp"] + ev["val"], s["max_hp"])
            if ev["effect"] == "stamina": s["st"] += ev["val"]
            if ev["effect"] == "gold": s["gold"] += ev["val"]
            r["event_data"] = None # האירוע קורה רק פעם אחת
            
        if r["npc"]: self.log(f"👤 {r['npc']['name']} עומד כאן.", "info")
        if r["enemy"]: self.log(f"⚔️ {r['enemy']['name']} חוסם את הדרך!", "danger")

    def interact(self):
        r = self.state["map"][self.key()]
        
        if not r["npc"]:
            self.log("אין כאן עם מי לדבר.", "game")
            return
        
        npc = r["npc"]
        line = random.choice(npc["lines"])
        self.log(f"🗣️ {npc['name']}: \"{line}\"", "game")
        
        # אם יש לו מתנה ועוד לא לקחנו
        if npc.get("gift"):
            self.state["inv"].append(npc["gift"])
            self.log(f"{npc['name']} נתן לך: {npc['gift']}!", "success")
            npc["gift"] = None # המתנה נלקחה
            
    def attack(self):
        r = self.state["map"][self.key()]
        s = self.state["stats"]
        
        if not r["enemy"]:
            self.log("אין אויבים בחדר.", "info")
            return

        enemy = r["enemy"]
        
        # השחקן תוקף
        dmg = random.randint(5, 15) + s["lvl"]
        enemy["hp"] -= dmg
        self.log(f"⚔️ פגעת ב-{enemy['name']} ({dmg} נזק)", "success")
        
        if enemy["hp"] <= 0:
            self.log(f"💀 ניצחת! {enemy['gold']} זהב נאספו.", "gold")
            s["gold"] += enemy["gold"]
            s["xp"] += enemy["xp"]
            r["enemy"] = None
            self.check_lvl()
        else:
            # אויב תוקף
            edmg = enemy["atk"] - random.randint(0,2)
            s["hp"] -= edmg
            self.log(f"🩸 נפגעת! -{edmg} חיים", "danger")

    def take(self):
        r = self.state["map"][self.key()]
        took = False
        if r["items"]:
            for i in r["items"]: self.state["inv"].append(i)
            self.log(f"לקחת: {', '.join(r['items'])}", "success")
            r["items"] = []
            took = True
        if r["gold"] > 0:
            self.state["stats"]["gold"] += r["gold"]
            self.log(f"מצאת שקית עם {r['gold']} זהב.", "gold")
            r["gold"] = 0
            took = True
            
        if not took: self.log("לא מצאת שום דבר שימושי.", "game")

    def rest(self):
        s = self.state["stats"]
        s["hp"] = min(s["hp"]+15, s["max_hp"])
        s["st"] = s["max_st"]
        self.log("🏕️ הקמת מחנה ונחת. האנרגיה התמלאה.", "sys")

    def check_lvl(self):
        s = self.state["stats"]
        req = s["lvl"] * 100
        if s["xp"] >= req:
            s["lvl"] += 1
            s["max_hp"] += 20
            s["hp"] = s["max_hp"]
            self.log(f"🆙 עלית רמה! אתה רמה {s['lvl']}!", "gold")

    def log(self, t, tp): self.state["log"].append({"text": t, "type": tp})

    # מפה בסיסית לרקע
    def render_map(self):
        cx, cy = self.state["x"], self.state["y"]
        r = 2
        html = "<div class='grid'>"
        for dy in range(r, -r - 1, -1):
            html += "<div class='row'>"
            for dx in range(-r, r + 1):
                k = f"{cx+dx},{cy+dy}"
                cell = "<span class='fog'>☁️</span>"
                if dx==0 and dy==0: cell="<span class='player'>🤠</span>"
                elif k in self.state["visited"]:
                    room = self.state["map"][k]
                    icon = "💀" if room["enemy"] else room["icon"]
                    if room["npc"]: icon = "🙂"
                    cell=f"<span class='room'>{icon}</span>"
                html+=f"<div class='cell'>{cell}</div>"
            html += "</div>"
        html += "</div>"
        return html


# --- FLASK ---
@app.route("/")
def index():
    if "uid" not in session: session["uid"] = str(uuid.uuid4())
    return render_template_string(HTML)

@app.route("/action", methods=["POST"])
def act():
    data = request.json
    eng = Engine(session.get("game"))
    
    if eng.state["stats"]["hp"] <= 0 and data["act"] != "reset":
         return jsonify({"dead":True})

    if data["act"] == "move": eng.move(*data["val"])
    elif data["act"] == "talk": eng.interact()
    elif data["act"] == "attack": eng.attack()
    elif data["act"] == "take": eng.take()
    elif data["act"] == "rest": eng.rest()
    elif data["act"] == "reset": 
        session.clear()
        return jsonify({"reload":True})

    session["game"] = eng.state
    return jsonify({
        "log": eng.state["log"],
        "hud": eng.render_map(),
        "stats": eng.state["stats"],
        "inv": eng.state["inv"],
        "loc": eng.state["map"][eng.key()]["name"]
    })

# --- CLIENT ---
HTML = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ENDLESS RPG</title>
<style>
    body { background: #121212; color: white; font-family: sans-serif; margin:0; display:flex; height:100vh; overflow:hidden;}
    .sidebar { width: 300px; background: #1e1e1e; border-left: 2px solid #333; padding:10px; display:flex; flex-direction:column; gap:10px;}
    .main { flex:1; display:flex; flex-direction:column; background: #000;}
    
    .stats-box { background:#2a2a2a; padding:10px; border-radius:5px; font-size:0.9rem;}
    .stat-row { display:flex; justify-content:space-between; margin-bottom:4px;}
    
    .map-container { display:flex; justify-content:center; background:#000; padding:10px; border:1px solid #444; border-radius:5px;}
    .grid { display:flex; flex-direction:column; gap:2px; }
    .row { display:flex; gap:2px; }
    .cell { width:40px; height:40px; display:flex; align-items:center; justify-content:center; background:#222; border-radius:4px; font-size:20px;}
    .player { background:#2e7d32; border:1px solid lime;}
    
    .log { flex:1; overflow-y:auto; padding:20px; font-size:16px;}
    .msg { margin-bottom:5px; padding:5px; border-radius:4px;}
    .sys { color: #81d4fa; font-size:12px; text-align:center;}
    .danger { background: rgba(255,0,0,0.2); border:1px solid red; }
    .success { color: #69f0ae; }
    .game { color: #fff; }
    .gold { color: #ffd740; }
    .warn { color: orange; }

    .controls { display:grid; grid-template-columns: repeat(2, 1fr); gap:10px; padding:10px; background:#1e1e1e;}
    button { padding:15px; border:none; background:#333; color:white; border-radius:5px; cursor:pointer; font-weight:bold; font-size:16px; transition:0.2s;}
    button:active { background:#555; transform:scale(0.98); }
    button span { font-size:12px; color:#aaa; display:block;}
    
    .atk-btn { background:#b71c1c; }
    .talk-btn { background:#0d47a1; }
    
</style>
</head>
<body>

<div class="main">
    <div style="background:#222; padding:10px; text-align:center; color:#ccc;" id="loc-title">טוען...</div>
    <div class="log" id="log-t"></div>
    <div class="controls">
        <button onclick="doAct('move',[0,1])">⬆️<span>צפון (W)</span></button>
        <button class="atk-btn" onclick="doAct('attack')">⚔️<span>תקוף (SPACE)</span></button>
        <button onclick="doAct('move',[1,0])">➡️<span>מזרח (D)</span></button>
        <button class="talk-btn" onclick="doAct('talk')">💬<span>דבר (T)</span></button>
        <button onclick="doAct('move',[-1,0])">⬅️<span>מערב (A)</span></button>
        <button onclick="doAct('take')">✋<span>אסוף (E)</span></button>
        <button onclick="doAct('move',[0,-1])">⬇️<span>דרום (S)</span></button>
        <button onclick="doAct('rest')">💤<span>נוח (R)</span></button>
    </div>
</div>

<div class="sidebar">
    <div class="map-container" id="map-t"></div>
    
    <div class="stats-box">
        <div class="stat-row"><span>❤️ חיים</span><span id="hp" style="color:#ef5350"></span></div>
        <div class="stat-row"><span>⚡ אנרגיה</span><span id="st" style="color:#42a5f5"></span></div>
        <div class="stat-row"><span>🪙 זהב</span><span id="gold" style="color:#ffd740"></span></div>
        <div class="stat-row"><span>⭐ רמה</span><span id="lvl" style="color:#ab47bc"></span></div>
    </div>

    <div style="flex:1; background:#222; padding:10px; border-radius:5px; overflow-y:auto;">
        <strong>🎒 התיק שלך:</strong>
        <div id="inv-t" style="margin-top:5px; font-size:12px; color:#aaa;">ריק</div>
    </div>
    
    <button onclick="doAct('reset')" style="background:#522; font-size:12px;">איפוס משחק</button>
</div>

<script>
    document.addEventListener("DOMContentLoaded", ()=> doAct('look'));

    async function doAct(act, val=null) {
        let res = await fetch('/action', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({act, val})});
        let d = await res.json();
        
        if(d.dead) { alert("Game Over"); location.reload(); return; }
        if(d.reload) location.reload();

        // Render Stats
        document.getElementById("hp").innerText = `${d.stats.hp}/${d.stats.max_hp}`;
        document.getElementById("st").innerText = d.stats.st;
        document.getElementById("gold").innerText = d.stats.gold;
        document.getElementById("lvl").innerText = d.stats.lvl;
        
        // Render Map
        document.getElementById("map-t").innerHTML = d.hud;
        document.getElementById("loc-title").innerText = d.loc;

        // Inventory
        let i_html = d.inv.length ? d.inv.join(", ") : "ריק";
        document.getElementById("inv-t").innerText = i_html;

        // Log
        let lb = document.getElementById("log-t");
        lb.innerHTML = "";
        d.log.forEach(l => {
            lb.innerHTML += `<div class='msg ${l.type}'>${l.text}</div>`;
        });
        lb.scrollTop = lb.scrollHeight;
    }

    document.onkeydown = function(e) {
        let k = e.key.toLowerCase();
        if(k=='w'||k=='arrowup') doAct('move',[0,1]);
        if(k=='s'||k=='arrowdown') doAct('move',[0,-1]);
        if(k=='a'||k=='arrowleft') doAct('move',[-1,0]);
        if(k=='d'||k=='arrowright') doAct('move',[1,0]);
        if(k==' '||k=='f') doAct('attack');
        if(k=='t') doAct('talk');
        if(k=='e') doAct('take');
        if(k=='r') doAct('rest');
    };
</script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(port=5006, debug=True)
