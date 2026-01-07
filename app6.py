import random
import uuid

# ==========================================
# ⚙️ איזור הגדרות ושליטה (ערוך כאן את המשחק!)
# ==========================================

# 1. רשימת החפצים והאפקטים שלהם
# type: 'heal' (ריפוי), 'stamina' (אנרגיה), 'gold' (כסף), 'xp' (ניסיון)
ITEM_DB = {
    "שיקוי חיים קטן": {"type": "heal", "val": 30, "desc": "נוזל אדום בטעם תות."},
    "תחבושת קרב":    {"type": "heal", "val": 50, "desc": "לעצור את הדימום."},
    "מנת אנרגיה":    {"type": "stamina", "val": 40, "desc": "חטיף עתיר קלוריות."},
    "קריסטל כוח":    {"type": "xp", "val": 100, "desc": "גביש שזורח באור כחול."},
    "מטבע זהב עתיק": {"type": "gold", "val": 50, "desc": "שווה הרבה כסף."},
    "יהלום":        {"type": "gold", "val": 200, "desc": "נוצץ ויקר ערך!"}
}

# 2. סוגי האזורים (ביומות)
# icon: האייקון שיופיע במפה
BIOME_DB = {
    "מסדרון חשוך":  {"icon": "⬛"},
    "יער מכושף":    {"icon": "🌲"},
    "חדר אוצר":     {"icon": "💰"},
    "בית קברות":    {"icon": "🪦"},
    "מקדש נטוש":    {"icon": "🏛️"},
    "לבה רותחת":    {"icon": "🌋"}
}

# 3. רשימת אויבים
# hp: חיים, atk: כוח התקפה, gold: כמה כסף נופל, xp: כמה ניסיון מקבלים
ENEMY_DB = [
    {"name": "גובלין ירוק", "icon": "👺", "hp": 20, "atk": 5, "gold": 10, "xp": 10},
    {"name": "שלד לוחם",    "icon": "💀", "hp": 35, "atk": 10, "gold": 25, "xp": 20},
    {"name": "זאב רפאים",   "icon": "🐺", "hp": 25, "atk": 8, "gold": 0,  "xp": 15},
    {"name": "דרקון קטן",   "icon": "🐲", "hp": 80, "atk": 15, "gold": 200, "xp": 100}
]

# 4. הגדרות איזון
START_HP = 100        # חיים בהתחלה
START_STAMINA = 100   # אנרגיה בהתחלה
MOVE_COST = 5         # עלות אנרגיה לצעד
ATTACK_COST = 8       # עלות אנרגיה להתקפה

# ==========================================
# (מכאן ומטה זה הקוד הטכני - אל תיגע אם לא חייב)
# ==========================================
from flask import Flask, render_template_string, request, jsonify, session, url_for
app = Flask(__name__)
app.secret_key = 'rpg_engine_ultimate_x99'

# --- מחולל עולם ---
class WorldGen:
    def create_room(self, x, y):
        if x == 0 and y == 0:
            return {"name": "נקודת התחלה", "type": "בסיס", "icon": "🏠", "enemy": None, "items": [], "gold": 0}

        biome_name = random.choice(list(BIOME_DB.keys()))
        biome_data = BIOME_DB[biome_name]
        
        # 35% סיכוי לאויב
        enemy = None
        if random.random() < 0.35:
            enemy_template = random.choice(ENEMY_DB)
            enemy = enemy_template.copy() # עותק ייחודי לחדר
            enemy["max_hp"] = enemy["hp"] # לשמירת הבר
        
        # 40% סיכוי לחפצים
        loot = []
        if random.random() < 0.4:
            item_name = random.choice(list(ITEM_DB.keys()))
            loot.append(item_name)
        
        return {
            "name": f"{biome_name}",
            "type": biome_name,
            "icon": biome_data["icon"],
            "enemy": enemy,
            "items": loot,
            "gold": random.randint(10, 50) if "אוצר" in biome_name else 0
        }

# --- מנוע משחק ---
class Engine:
    def __init__(self, state=None):
        if not state:
            self.state = {
                "x": 0, "y": 0,
                "stats": {"hp": START_HP, "max_hp": START_HP, "st": START_STAMINA, "max_st": START_STAMINA, "xp": 0, "lvl": 1, "gold": 0},
                "inv": [],
                "map": {},
                "visited": ["0,0"],
                "log": [{"text": "המסע מתחיל. השתמש במקלדת כדי לשלוט בדמות.", "type": "sys"}]
            }
            # יצירת חדר התחלה
            self.gen = WorldGen()
            self.state["map"]["0,0"] = self.gen.create_room(0,0)
        else:
            self.state = state
            self.gen = WorldGen()

    def pos_key(self): return f"{self.state['x']},{self.state['y']}"

    # פעולות
    def move(self, dx, dy):
        s = self.state["stats"]
        if s["st"] < MOVE_COST:
            self.log("😪 אין לך כוח לזוז! תנוח קצת (מקש R).", "warn")
            return
        
        s["st"] -= MOVE_COST
        self.state["x"] += dx
        self.state["y"] += dy
        k = self.pos_key()

        is_new = False
        if k not in self.state["map"]:
            self.state["map"][k] = self.gen.create_room(self.state['x'], self.state['y'])
            is_new = True
        
        if k not in self.state["visited"]: self.state["visited"].append(k)
        
        r = self.state["map"][k]
        msg = f"הגעת אל: {r['name']}"
        self.log(msg, "game")
        
        if r["enemy"]: self.log(f"⚔️ אויב בחדר! {r['enemy']['name']}", "danger")
        if r["items"]: self.log(f"✨ מצאת: {', '.join(r['items'])}", "success")

    def attack(self):
        r = self.state["map"][self.pos_key()]
        s = self.state["stats"]
        
        if not r["enemy"]:
            self.log("אין במי לתקוף כאן.", "info")
            return
        
        if s["st"] < ATTACK_COST:
            self.log("אין לך אנרגיה להתקפה! (נוח R)", "warn")
            return
        
        enemy = r["enemy"]
        
        # חישוב נזק: רמה * 4 + קוביה 1-10
        dmg = (s["lvl"] * 4) + random.randint(1, 10)
        s["st"] -= ATTACK_COST
        
        enemy["hp"] -= dmg
        self.log(f"💥 נתת מכה בעוצמה של {dmg}!", "game")
        
        if enemy["hp"] <= 0:
            self.log(f"💀 ניצחון! {enemy['name']} הובס.", "success")
            # פרסים
            reward_gold = enemy["gold"]
            reward_xp = enemy["xp"]
            s["gold"] += reward_gold
            s["xp"] += reward_xp
            self.log(f"קיבלת {reward_gold} זהב ו-{reward_xp} ניסיון.", "gold")
            r["enemy"] = None
            self.check_level_up()
        else:
            # אויב מחזיר
            p_dmg = max(1, enemy["atk"] - random.randint(0, 2))
            s["hp"] -= p_dmg
            self.log(f"💢 האויב תקף חזרה! ירדו {p_dmg} חיים.", "danger")

    def take(self):
        r = self.state["map"][self.pos_key()]
        found = False
        if r["items"]:
            for i in r["items"]:
                self.state["inv"].append(i)
                found = True
            self.log(f"אספת: {', '.join(r['items'])}", "success")
            r["items"] = []
            
        if r["gold"] > 0:
            self.state["stats"]["gold"] += r["gold"]
            self.log(f"מצאת שק של {r['gold']} מטבעות זהב!", "gold")
            r["gold"] = 0
            found = True
            
        if not found: self.log("אין כאן שום דבר שימושי.", "info")

    def rest(self):
        s = self.state["stats"]
        s["hp"] = min(s["hp"] + 10, s["max_hp"])
        s["st"] = min(s["st"] + 40, s["max_st"])
        self.log("💤 נחת וחידשת כוחות.", "info")

    def use(self, item_name):
        if item_name not in self.state["inv"]: return
        
        data = ITEM_DB.get(item_name)
        s = self.state["stats"]
        
        if data["type"] == "heal":
            s["hp"] = min(s["hp"] + data["val"], s["max_hp"])
        elif data["type"] == "stamina":
            s["st"] = min(s["st"] + data["val"], s["max_st"])
        elif data["type"] == "xp":
            s["xp"] += data["val"]
            self.check_level_up()
        
        self.state["inv"].remove(item_name)
        self.log(f"השתמשת ב-{item_name}: {data['desc']}", "success")

    def check_level_up(self):
        s = self.state["stats"]
        req = s["lvl"] * 50
        if s["xp"] >= req:
            s["lvl"] += 1
            s["max_hp"] += 20
            s["hp"] = s["max_hp"]
            s["max_st"] += 10
            self.log(f"🆙 עלית לרמה {s['lvl']}! נהיית חזק יותר.", "gold")

    def log(self, txt, type):
        self.state["log"].append({"text": txt, "type": type})

    # --- רנדור מפה ---
    def render_map(self):
        cx, cy = self.state["x"], self.state["y"]
        r = 2 # רדיוס
        html = "<div class='grid'>"
        for dy in range(r, -r - 1, -1):
            html += "<div class='row'>"
            for dx in range(-r, r + 1):
                tx, ty = cx+dx, cy+dy
                k = f"{tx},{ty}"
                cell = "<span class='fog'>☁️</span>"
                
                if dx==0 and dy==0:
                    cell = "<span class='player'>😎</span>"
                elif k in self.state["visited"]:
                    room = self.state["map"][k]
                    icon = room["icon"]
                    if room["enemy"]: icon = "👿"
                    cell = f"<span class='room'>{icon}</span>"
                
                html += f"<div class='cell'>{cell}</div>"
            html += "</div>"
        html += "</div>"
        return html


# --- FLASK ROUTES ---
@app.route("/")
def index():
    if "uid" not in session: session["uid"] = str(uuid.uuid4())
    return render_template_string(HTML)

@app.route("/action", methods=["POST"])
def action():
    data = request.json
    act = data.get("act")
    val = data.get("val")
    
    eng = Engine(session.get("game"))
    
    if eng.state["stats"]["hp"] <= 0 and act != "reset":
        return jsonify({"dead": True})

    if act == "move": eng.move(*val)
    elif act == "attack": eng.attack()
    elif act == "take": eng.take()
    elif act == "rest": eng.rest()
    elif act == "use": eng.use(val)
    elif act == "reset": 
        session.clear()
        return jsonify({"reload": True})
    
    session["game"] = eng.state
    
    # מידע ללקוח
    r = eng.state["map"][eng.pos_key()]
    return jsonify({
        "log": eng.state["log"],
        "hud": eng.render_map(),
        "stats": eng.state["stats"],
        "inv": eng.state["inv"],
        "loc": r["name"]
    })

# --- CLIENT (HTML/JS) ---
HTML = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>RPG PRO</title>
<link href="https://fonts.googleapis.com/css2?family=Varela+Round&display=swap" rel="stylesheet">
<style>
    body { background: #1a1a1a; color: white; font-family: 'Varela Round', sans-serif; margin:0; display:flex; height:100vh; overflow:hidden;}
    .sidebar { width: 320px; background: #222; border-left: 2px solid #444; padding:15px; display:flex; flex-direction:column; gap:15px;}
    .main { flex:1; display:flex; flex-direction:column; background: #111;}
    
    /* Stats */
    .bars { background: #333; padding:10px; border-radius:8px;}
    .bar-row { display:flex; justify-content:space-between; margin-bottom:5px; font-size:14px;}
    .stat-val { font-weight:bold; font-family:monospace;}
    
    /* Map */
    .map-box { background: #000; padding:10px; border-radius:8px; border:1px solid #555; display:flex; justify-content:center;}
    .grid { display:flex; flex-direction:column; gap:2px; }
    .row { display:flex; gap:2px; }
    .cell { width:35px; height:35px; display:flex; align-items:center; justify-content:center; background:#111; font-size:20px; border-radius:4px;}
    .room { background:#333; } 
    .player { background:#004400; border:1px solid lime;}
    
    /* Log */
    .log { flex:1; overflow-y:auto; padding:20px; display:flex; flex-direction:column; gap:8px;}
    .msg { padding:8px 12px; border-radius:6px; background:rgba(255,255,255,0.05); animation: fade 0.3s; max-width:80%;}
    .game { border-right:3px solid #ccc; }
    .sys { text-align:center; font-size:12px; color:#666; width:100%;}
    .danger { background:rgba(255,0,0,0.2); border:1px solid #800;}
    .success { color:#6f6;}
    .gold { color: gold; }
    .warn { color: orange; }

    /* Controls */
    .ctrl-grid { display:grid; grid-template-columns: 1fr 1fr; gap:10px;}
    button { background: #333; color:#ddd; border:none; padding:15px; border-radius:6px; cursor:pointer; font-weight:bold; font-family:inherit; transition:0.1s;}
    button:active { background:#555; transform:scale(0.98);}
    button span { display:block; font-size:10px; color:#888; margin-top:3px;}
    
    .atk-btn { background:#500;} .atk-btn:hover { background:#700;}
    .inv-item { width:100%; text-align:right; margin-bottom:5px; background:#444; border:1px solid #666; padding:8px;}

    @keyframes fade { from{opacity:0; transform:translateY(5px);} to{opacity:1;}}
</style>
</head>
<body>

<div class="main">
    <div style="background:#222; padding:10px; text-align:center; border-bottom:1px solid #444;" id="loc-title">טוען...</div>
    <div class="log" id="log-target"></div>
</div>

<div class="sidebar">
    <div class="map-box" id="map-target"></div>
    
    <div class="bars">
        <div class="bar-row"><span style="color:#f55">❤️ בריאות</span> <span id="hp" class="stat-val"></span></div>
        <div class="bar-row"><span style="color:#5ef">⚡ אנרגיה</span> <span id="st" class="stat-val"></span></div>
        <div class="bar-row"><span style="color:gold">🪙 זהב</span> <span id="gold" class="stat-val"></span></div>
        <div class="bar-row"><span style="color:#d8f">⭐ רמה</span> <span id="lvl" class="stat-val"></span></div>
    </div>
    
    <div class="ctrl-grid">
        <button onclick="req('move',[0,1])">⬆️<span>צפון (W)</span></button>
        <button class="atk-btn" onclick="req('attack')">⚔️<span>תקוף (SPACE)</span></button>
        
        <button onclick="req('move',[1,0])">➡️<span>מזרח (D)</span></button>
        <button onclick="req('move',[-1,0])">⬅️<span>מערב (A)</span></button>
        
        <button onclick="req('take')">✋<span>אסוף (E)</span></button>
        <button onclick="req('move',[0,-1])">⬇️<span>דרום (S)</span></button>
        
        <button onclick="req('rest')">💤<span>נוח (R)</span></button>
        <button onclick="toggleInv()">🎒<span>תיק (I)</span></button>
    </div>
    <button onclick="req('reset')" style="background:#522; font-size:12px; padding:5px;">מחק משחק והתחל מחדש</button>
</div>

<!-- INVENTORY MODAL (Hidden) -->
<div id="inv-panel" style="display:none; position:fixed; inset:0; background:rgba(0,0,0,0.9); z-index:9; flex-direction:column; align-items:center; justify-content:center;">
    <div style="background:#222; padding:20px; width:300px; border-radius:10px; border:2px solid gold;">
        <h3>🎒 התיק שלך</h3>
        <div id="inv-list" style="max-height:200px; overflow-y:auto; margin-bottom:10px;"></div>
        <button onclick="toggleInv()">סגור</button>
    </div>
</div>

<script>
    document.addEventListener("DOMContentLoaded", ()=> req('look'));

    async function req(act, val=null) {
        if(act=='attack') document.querySelector('.main').style.backgroundColor="#200";
        setTimeout(()=> document.querySelector('.main').style.backgroundColor="#111", 100);

        let res = await fetch('/action', {
            method:'POST', headers:{'Content-Type':'application/json'},
            body: JSON.stringify({act:act, val:val})
        });
        let d = await res.json();
        
        if(d.dead) { alert("מתת!"); req('reset'); return; }
        if(d.reload) location.reload();
        
        // Update Logs
        let lbox = document.getElementById("log-target");
        lbox.innerHTML = "";
        d.log.forEach(l => {
            lbox.innerHTML += `<div class='msg ${l.type}'>${l.text}</div>`;
        });
        lbox.scrollTop = lbox.scrollHeight;
        
        // Update Stats & Map
        if(d.stats) {
            document.getElementById("hp").innerText = `${d.stats.hp}/${d.stats.max_hp}`;
            document.getElementById("st").innerText = `${d.stats.st}/${d.stats.max_st}`;
            document.getElementById("gold").innerText = d.stats.gold;
            document.getElementById("lvl").innerText = d.stats.lvl;
        }
        if(d.hud) document.getElementById("map-target").innerHTML = d.hud;
        if(d.loc) document.getElementById("loc-title").innerText = d.loc;

        // Inventory list
        let invDiv = document.getElementById("inv-list");
        invDiv.innerHTML = "";
        if(d.inv && d.inv.length > 0){
            d.inv.forEach(item => {
                invDiv.innerHTML += `<button class="inv-item" onclick="req('use','${item}')">${item}</button>`;
            });
        } else {
            invDiv.innerHTML = "<p>התיק ריק...</p>";
        }
    }
    
    function toggleInv(){
        let el = document.getElementById("inv-panel");
        el.style.display = (el.style.display=="none") ? "flex" : "none";
    }

    // מקלדת (KEYBINDINGS)
    document.addEventListener("keydown", (e) => {
        let k = e.key.toLowerCase();
        if(k=='w' || k=='arrowup') req('move',[0,1]);
        if(k=='s' || k=='arrowdown') req('move',[0,-1]);
        if(k=='a' || k=='arrowleft') req('move',[-1,0]);
        if(k=='d' || k=='arrowright') req('move',[1,0]);
        if(k==' ' || k=='f') req('attack');
        if(k=='e') req('take');
        if(k=='r') req('rest');
        if(k=='i') toggleInv();
    });
</script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(port=5006, debug=True)
