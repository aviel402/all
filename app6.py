import random
import uuid
from flask import Flask, render_template_string, request, jsonify, session, url_for

app = Flask(__name__)
app.secret_key = 'dm_pro_fixed_v7'

# ==========================================
# 📘 מאגר נתונים (DATABASE)
# ==========================================

ITEMS_DB = {
    "שיקוי חיים": {"type": "heal", "val": 40, "desc": "מרפא 40 נקודות חיים"},
    "תחבושת": {"type": "heal", "val": 15, "desc": "עוצר דימום קל"},
    "מנת קרב": {"type": "heal", "val": 10, "desc": "אוכל יבש אך מזין"},
    "רימון רעל": {"type": "dmg_item", "val": 30, "desc": "זורק על האויב"},
    "שיקוי כוח": {"type": "buff", "val": 5, "desc": "מגביר נזק זמנית"},
    "יהלום": {"type": "sell", "val": 100, "desc": "שווה הרבה כסף"},
    "מפתח ברזל": {"type": "key", "val": 0, "desc": "פותח דלתות"},

    # --- תוספות ---

    "שיקוי חיים גדול": {"type": "heal", "val": 80, "desc": "מרפא 80 נקודות חיים"},
    "שיקוי חיים אגדי": {"type": "heal", "val": 150, "desc": "מרפא 150 נקודות חיים"},
    "תחבושת מתקדמת": {"type": "heal", "val": 30, "desc": "עוצר דימום ומרפא יותר"},
    "ארוחת לוחם": {"type": "heal", "val": 25, "desc": "ארוחה חמה שנותנת הרבה אנרגיה"},

    "רימון אש": {"type": "dmg_item", "val": 40, "desc": "פיצוץ אש חזק"},
    "רימון קרח": {"type": "dmg_item", "val": 35, "desc": "מקפיא את האויב"},
    "רימון הלם": {"type": "dmg_item", "val": 20, "desc": "מבלבל את האויב"},

    "שיקוי כוח גדול": {"type": "buff", "val": 10, "desc": "מגביר נזק משמעותית"},
    "שיקוי מהירות": {"type": "buff", "val": 7, "desc": "מגביר מהירות תגובה"},
    "שיקוי הגנה": {"type": "buff", "val": 7, "desc": "מגביר הגנה זמנית"},

    "אודם": {"type": "sell", "val": 60, "desc": "אבן אדומה יקרה"},
    "ספיר": {"type": "sell", "val": 80, "desc": "אבן כחולה נדירה"},
    "אזמרגד": {"type": "sell", "val": 90, "desc": "אבן ירוקה נוצצת"},

    "מפתח זהב": {"type": "key", "val": 0, "desc": "פותח דלתות זהב"},
    "מפתח עתיק": {"type": "key", "val": 0, "desc": "פותח שערים עתיקים"},
    "כרטיס גישה": {"type": "key", "val": 0, "desc": "כרטיס לפתיחת דלת אלקטרונית"}
}


ENEMIES = [
    {"name": "גובלין ירוק", "hp": 30, "max": 30, "atk": 5, "xp": 10, "loot": ["מנת קרב"]},
    {"name": "אורק משוריין", "hp": 60, "max": 60, "atk": 12, "xp": 40, "loot": ["שיקוי חיים", "מטבע"]},
    {"name": "שלד", "hp": 40, "max": 40, "atk": 8, "xp": 20, "loot": ["תחבושת"]},
    {"name": "בוס דרקון", "hp": 200, "max": 200, "atk": 25, "xp": 500, "loot": ["יהלום", "שיקוי כוח"]},

    # --- תוספות ---

    {"name": "עכביש ענק", "hp": 35, "max": 35, "atk": 7, "xp": 15, "loot": ["רימון רעל"]},
    {"name": "זאב פראי", "hp": 45, "max": 45, "atk": 9, "xp": 25, "loot": ["מנת קרב"]},
    {"name": "שד אש", "hp": 80, "max": 80, "atk": 15, "xp": 60, "loot": ["רימון אש", "שיקוי הגנה"]},
    {"name": "רוח עתיקה", "hp": 50, "max": 50, "atk": 10, "xp": 45, "loot": ["שיקוי מהירות"]},
    {"name": "אביר שחור", "hp": 100, "max": 100, "atk": 18, "xp": 120, "loot": ["שיקוי כוח גדול", "מפתח זהב"]},

    {"name": "מלך הגובלינים", "hp": 120, "max": 120, "atk": 20, "xp": 180, "loot": ["אודם", "שיקוי חיים גדול"]},
    {"name": "גולם אבן", "hp": 150, "max": 150, "atk": 22, "xp": 220, "loot": ["אזמרגד"]},
    {"name": "נחש רעל", "hp": 55, "max": 55, "atk": 11, "xp": 35, "loot": ["רימון רעל"]},
    {"name": "שומר השער", "hp": 130, "max": 130, "atk": 19, "xp": 200, "loot": ["מפתח עתיק"]},
    {"name": "טיטאן ברזל", "hp": 250, "max": 250, "atk": 30, "xp": 600, "loot": ["יהלום", "שיקוי חיים אגדי"]}
]

BIOMES = [
    {"name": "צינוק טחוב", "icon": "⛓️"}, {"name": "מעבדה נטושה", "icon": "🧪"},
    {"name": "נשקייה", "icon": "⚔️"}, {"name": "אולם גדול", "icon": "🏛️"},

    # --- תוספות ---

    {"name": "מערה קפואה", "icon": "❄️"},
    {"name": "יער אפל", "icon": "🌲"},
    {"name": "מדבר חרוך", "icon": "🏜️"},
    {"name": "מקדש עתיק", "icon": "🗿"},
    {"name": "ספרייה אסורה", "icon": "📚"},
    {"name": "מרתף מוצף", "icon": "💧"},
    {"name": "מגדל קוסמים", "icon": "🔮"},
    {"name": "כלא נטוש", "icon": "🚪"},
    {"name": "מעבה הביצה", "icon": "🐸"},
    {"name": "מצפה כוכבים", "icon": "🌌"}
]


# ==========================================
# ⚙️ מנוע משחק
# ==========================================
class Engine:
    def __init__(self, state=None):
        if not state:
            self.state = {
                "x": 0, "y": 0,
                "stats": {"hp": 100, "max": 100, "gold": 0, "lvl": 1, "atk_bonus": 0},
                "inv": ["שיקוי חיים"], # חפץ התחלתי
                "map": {},
                "visited": ["0,0"],
                "log": [{"text": "המשחק התחיל. חפש נשק ואספקה.", "type": "sys"}]
            }
            # חדר התחלה
            self.create_room(0, 0, force_safe=True)
        else:
            self.state = state

    def pos(self): return f"{self.state['x']},{self.state['y']}"
    
    def log(self, txt, t="game"): self.state["log"].append({"text": txt, "type": t})

    def create_room(self, x, y, force_safe=False):
        k = f"{x},{y}"
        if k in self.state["map"]: return # החדר כבר קיים

        if force_safe:
            self.state["map"][k] = {"name": "חדר בטוח", "icon":"🏠", "enemy": None, "items": []}
            return

        # יצירה אקראית
        biome = random.choice(BIOMES)
        enemy = None
        
        # 40% סיכוי לאויב
        if random.random() < 0.4:
            base = random.choice(ENEMIES)
            enemy = base.copy() # העתק כדי שנוכל להוריד לו חיים בנפרד
        
        items = []
        if random.random() < 0.5:
            items.append(random.choice(list(ITEMS_DB.keys())))

        self.state["map"][k] = {
            "name": biome["name"],
            "icon": biome["icon"],
            "enemy": enemy,
            "items": items
        }

    # --- תנועה ---
    def move(self, dx, dy):
        self.state["y"] += dx
        self.state["z"] += dy
        k = self.pos()
        
        # אם החדר לא קיים, יוצרים אותו
        self.create_room(self.state["x"], self.state["y"])
        if k not in self.state["visited"]: self.state["visited"].append(k)
        
        r = self.state["map"][k]
        
        # לוגיקה חכמה להודעות
        self.log(f"נכנסת ל{r['name']}.", "game")
        if r["enemy"]:
            e = r["enemy"]
            self.log(f"⚠️ {e['name']} (HP: {e['hp']}) חוסם את הדרך!", "danger")
        if r["items"]:
            self.log(f"🔎 על הרצפה: {', '.join(r['items'])}", "success")

    # --- התקפה ---
    def attack(self):
        r = self.state["map"][self.pos()]
        if not r["enemy"]:
            self.log("אין במי לתקוף.", "info")
            return
        
        player_dmg = random.randint(8, 15) + self.state["stats"]["atk_bonus"]
        enemy = r["enemy"]
        
        # שחקן תוקף
        enemy["hp"] -= player_dmg
        self.log(f"פגעת ב-{enemy['name']} והורדת {player_dmg}.", "success")
        
        # בדיקת מוות אויב
        if enemy["hp"] <= 0:
            self.log(f"💀 ה-{enemy['name']} מת!", "gold")
            # שלל
            gold = random.randint(5, 20)
            self.state["stats"]["gold"] += gold
            if enemy.get("loot"):
                r["items"].extend(enemy["loot"])
            
            r["enemy"] = None # הסרת אויב
        else:
            # אויב תוקף חזרה
            e_dmg = max(1, enemy["atk"] - random.randint(0, 2))
            self.state["stats"]["hp"] -= e_dmg
            self.log(f"האויב נשך אותך! (-{e_dmg} ❤️)", "danger")

    # --- איסוף חפצים ---
    def take(self):
        r = self.state["map"][self.pos()]
        if not r["items"]:
            self.log("אין כאן כלום לאסוף.", "info")
            return
        
        for item in r["items"]:
            self.state["inv"].append(item)
        
        self.log(f"לקחת: {', '.join(r['items'])}", "success")
        r["items"] = [] # רוקן רצפה

    # --- שימוש בחפצים מהתיק ---
    def use_item(self, item_name):
        if item_name not in self.state["inv"]: return
        
        effect = ITEMS_DB.get(item_name)
        if not effect:
            self.log("אי אפשר להשתמש בזה.", "info")
            return

        used = False
        if effect["type"] == "heal":
            # לא מרפאים אם החיים מלאים
            if self.state["stats"]["hp"] >= self.state["stats"]["max"]:
                self.log("אתה בריא לחלוטין.", "info")
                return
            
            self.state["stats"]["hp"] = min(self.state["stats"]["max"], self.state["stats"]["hp"] + effect["val"])
            self.log(f"השתמשת ב{item_name}. בריאות עלתה!", "success")
            used = True
            
        elif effect["type"] == "buff":
            self.state["stats"]["atk_bonus"] += effect["val"]
            self.log(f"הרגשת כוח זורם בגופך! (+{effect['val']} נזק)", "gold")
            used = True
            
        elif effect["type"] == "dmg_item":
            # אפשר להשתמש רק אם יש אויב
            r = self.state["map"][self.pos()]
            if r["enemy"]:
                r["enemy"]["hp"] -= effect["val"]
                self.log(f"זרקת {item_name}! האויב נפגע ב-{effect['val']}.", "success")
                if r["enemy"]["hp"] <= 0:
                    self.log("האויב הושמד עקב הפגיעה!", "gold")
                    r["enemy"] = None
                used = True
            else:
                self.log("אין אויב בחדר לזרוק עליו את זה.", "info")

        if used:
            self.state["inv"].remove(item_name)

    def get_ui_data(self):
        # הכנת מידע מסודר ל-FrontEnd
        k = self.pos()
        r = self.state["map"][k]
        
        return {
            "hp": self.state["stats"]["hp"],
            "max_hp": self.state["stats"]["max"],
            "gold": self.state["stats"]["gold"],
            "inv": self.state["inv"],
            "log": self.state["log"],
            
            # פרטי חדר
            "room_name": r["name"],
            "items_on_floor": r["items"], # רשימה מה יש ברצפה
            "enemy_data": r["enemy"], # אם יש אויב, שולח את כל הסטטוס שלו (שם, מקס, נוכחי)
            
            # מפה קטנה
            "map_grid": self.render_minimap()
        }

    def render_minimap(self):
        # מפה 3x3
        grid = []
        cx, cy = self.state["x"], self.state["y"]
        for dy in range(1, -2, -1): # שורות
            row = []
            for dx in range(-1, 2): # עמודות
                pos = f"{cx+dx},{cy+dy}"
                val = ""
                cls = "fog"
                
                if dx==0 and dy==0: 
                    val = "😎" 
                    cls = "player"
                elif pos in self.state["visited"]:
                    rm = self.state["map"][pos]
                    # אם יש אויב במפה - סימן אדום
                    val = "💀" if rm["enemy"] else rm["icon"]
                    cls = "known"
                
                row.append({"val":val, "cls":cls})
            grid.append(row)
        return grid

# ==========================================
# שרת
# ==========================================
@app.route("/")
def index():
    if "uid" not in session: session["uid"] = str(uuid.uuid4())
    # כתובת לולאה חזרה
    home_url = "/" 
    api = url_for("process")
    return render_template_string(HTML, api=api, home=home_url)

@app.route("/game/process", methods=["POST"])
def process():
    d = request.json
    try:
        eng = Engine(session.get("game"))
    except:
        eng = Engine(None)

    act = d.get("action")
    val = d.get("val")

    # בדיקת מוות
    if eng.state["stats"]["hp"] <= 0 and act != "reset":
        return jsonify({"dead": True})

    if act == "move": eng.move(*val)
    elif act == "attack": eng.attack()
    elif act == "take": eng.take()
    elif act == "use": eng.use_item(val)
    elif act == "reset": eng = Engine(None)

    session["game"] = eng.state
    return jsonify(eng.get_ui_data())

# ==========================================
# HTML + CSS + JS (PRO VERSION)
# ==========================================
HTML = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
<title>Dungeon Master</title>
<style>
    /* CSS BASE */
    :root { --bg:#111; --panel:#1c1c1c; --acc:#d4af37; --danger:#ef5350; }
    body { background: var(--bg); color: #eee; margin: 0; font-family: system-ui; display: flex; flex-direction: column; height: 100vh; overflow:hidden;}
    
    /* === HEADER: Stats & Title === */
    header { background: #222; padding: 10px; display: flex; justify-content: space-between; border-bottom: 2px solid #333;}
    .stat-badge { background: #333; padding: 5px 10px; border-radius: 5px; font-size: 14px; font-weight: bold;}
    
    /* === MIDDLE: Content === */
    .viewport { flex: 1; display: grid; grid-template-columns: 2fr 1fr; gap: 5px; padding: 10px; overflow: hidden; }
    
    /* Log Area */
    .log-container { background: #151515; border-radius: 8px; border: 1px solid #333; padding: 15px; overflow-y: auto; display:flex; flex-direction:column; gap:5px;}
    .msg { padding: 8px; border-radius: 4px; font-size: 14px; line-height: 1.4; border-right: 3px solid #444; background:rgba(255,255,255,0.02);}
    .sys { text-align: center; color: #888; border: none; font-size:12px; }
    .danger { border-color: red; background: rgba(255,0,0,0.1); }
    .success { border-color: lime; color: #afa; }
    .gold { border-color: gold; color: gold; }

    /* Side Panel: Map & Room Info */
    .side-panel { display: flex; flex-direction: column; gap: 10px; }
    
    .room-card { background: var(--panel); border: 1px solid #444; border-radius: 8px; padding: 10px; text-align: center; }
    .floor-items { margin-top: 5px; font-size: 12px; color: #aaa; background: #111; padding: 5px; border-radius: 4px; display:none;}
    .floor-items.active { display: block; border: 1px solid lime; color: lime;}

    .enemy-bar-box { display:none; background: #300; padding: 10px; border-radius: 5px; border: 1px solid red; margin-bottom:10px; text-align:center;}
    .hp-track { width: 100%; height: 10px; background: #500; border-radius: 5px; overflow: hidden; margin-top: 5px;}
    .hp-fill { height: 100%; background: #f00; width: 100%; transition: 0.3s;}

    /* Minimap Grid */
    .map-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 2px; margin: 0 auto; width: 120px; }
    .map-cell { width: 38px; height: 38px; background: #000; display: flex; align-items: center; justify-content: center; font-size: 20px; border-radius: 4px; }
    .map-cell.player { border: 2px solid #0f0; background: #030; }
    .map-cell.known { background: #2a2a2a; }

    /* Inventory (Hidden by default) */
    .inv-modal { display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.9); z-index:99; justify-content:center; align-items:center;}
    .inv-box { background:#222; width:300px; padding:20px; border-radius:10px; border:2px solid gold; display:flex; flex-direction:column; gap:5px; max-height:80vh; overflow-y:auto;}
    .use-btn { background: #333; color: white; padding: 10px; border: 1px solid #555; width: 100%; text-align: right; cursor: pointer; }
    .use-btn:hover { background: #444; border-color: gold;}

    /* === BOTTOM: Controls === */
    .controls { height: 180px; background: var(--panel); border-top: 2px solid #444; padding: 10px; display: grid; grid-template-columns: 1fr 150px 1fr; gap: 10px; align-items: center;}
    
    /* D-PAD FIX: Enforce LTR so arrows are visually correct */
    .d-pad { direction: ltr; display: grid; grid-template-columns: repeat(3, 1fr); gap: 5px; width: 140px; margin: 0 auto; }
    .btn { background: #333; color: #fff; border: 1px solid #555; border-radius: 8px; font-size: 20px; height: 45px; cursor: pointer; display: flex; align-items: center; justify-content: center;}
    .btn:active { background: #555; transform: scale(0.95); }
    
    .up { grid-column: 2; grid-row: 1; }
    .down { grid-column: 2; grid-row: 2; }
    .left { grid-column: 1; grid-row: 2; }
    .right { grid-column: 3; grid-row: 2; }

    .main-actions { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; height: 100%; align-content: center;}
    .act-btn { height: 60px; font-weight: bold; font-size: 16px; border: none; border-radius: 8px; cursor: pointer; color:white; }
    
    .btn-atk { background: #922; border-bottom: 4px solid #500; }
    .btn-take { background: #274; border-bottom: 4px solid #142; }
    .btn-inv { background: #860; border-bottom: 4px solid #640; grid-column: span 2; height: 40px; }

</style>
</head>
<body>

<!-- TOP -->
<header>
    <div>RPG PRO</div>
    <div style="display:flex; gap:10px;">
        <span class="stat-badge">❤️ <span id="hp">100</span></span>
        <span class="stat-badge">💰 <span id="gold">0</span></span>
    </div>
    <a href="{{ home }}" style="color:#aaa; font-size:12px; text-decoration:none;">יציאה</a>
</header>

<!-- VIEWPORT -->
<div class="viewport">
    
    <!-- LEFT: Map & Enemy Status -->
    <div class="side-panel">
        <div class="map-grid" id="map-target"></div>
        
        <div class="room-card">
            <div id="loc-name" style="font-weight:bold; color: #d4af37">טוען...</div>
            <!-- חיווי לרצפה -->
            <div id="floor-indicator" class="floor-items">
                יש חפצים על הרצפה!<br>
                <span id="floor-list"></span>
            </div>
        </div>

        <!-- חיווי אויב - מוסתר כברירת מחדל -->
        <div id="enemy-box" class="enemy-bar-box">
            <strong id="en-name">מפלצת</strong>
            <div style="font-size:12px; color:#aaa"><span id="en-hp">0</span>/<span id="en-max">0</span></div>
            <div class="hp-track"><div id="en-fill" class="hp-fill"></div></div>
        </div>
    </div>

    <!-- RIGHT: LOG -->
    <div class="log-container" id="log-box"></div>
</div>

<!-- INVENTORY MODAL -->
<div class="inv-modal" id="inv-modal">
    <div class="inv-box">
        <h3 style="margin:0; text-align:center;">🎒 תיק ציוד</h3>
        <small style="text-align:center; color:#777">לחץ לשימוש</small>
        <div id="inv-list"></div>
        <button onclick="toggleInv()" style="margin-top:10px; padding:10px;">סגור</button>
    </div>
</div>

<!-- CONTROLS -->
<div class="controls">
    <div class="main-actions">
        <button class="act-btn btn-atk" onclick="send('attack')">⚔️ תקיפה</button>
        <button class="act-btn btn-take" onclick="send('take')">✋ אסוף</button>
        <button class="act-btn btn-inv" onclick="toggleInv()">🎒 פתח תיק</button>
    </div>

    <!-- LTR Enforced D-PAD -->
    <div class="d-pad">
        <button class="btn up" onclick="send('move', [0,1])">⬆️</button>
        <button class="btn left" onclick="send('move', [-1,0])">⬅️</button>
        <button class="btn down" onclick="send('move', [0,-1])">⬇️</button>
        <button class="btn right" onclick="send('move', [1,0])">➡️</button>
    </div>
    
    <div style="display:flex; justify-content:center; align-items:center;">
        <button onclick="send('reset')" style="background:#444; border:none; color:#aaa; padding:10px; cursor:pointer; border-radius:5px;">♻️ ריסט</button>
    </div>
</div>

<script>
    const API = "{{ api }}";
    
    // Auto start
    window.onload = () => send('init');

    async function send(act, val=null) {
        if(act=='use') toggleInv(); // Close inv on use

        try {
            let res = await fetch(API, {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({action: act, val: val})
            });
            let d = await res.json();

            if (d.dead) { alert("מתת!"); send('reset'); return; }

            // 1. Logs
            let logBox = document.getElementById("log-box");
            logBox.innerHTML = "";
            d.log.forEach(msg => {
                logBox.innerHTML += `<div class="msg ${msg.type}">${msg.text}</div>`;
            });
            logBox.scrollTop = logBox.scrollHeight;

            // 2. Map
            let mapH = "";
            d.map_grid.forEach(row => {
                row.forEach(c => mapH += `<div class='map-cell ${c.cls}'>${c.val}</div>`);
            });
            document.getElementById("map-target").innerHTML = mapH;

            // 3. Status
            document.getElementById("hp").innerText = `${d.hp}/${d.max_hp}`;
            document.getElementById("gold").innerText = d.gold;
            document.getElementById("loc-name").innerText = d.room_name;

            // 4. Enemy Bar
            let eBox = document.getElementById("enemy-box");
            if (d.enemy_data) {
                eBox.style.display = "block";
                document.getElementById("en-name").innerText = d.enemy_data.name;
                document.getElementById("en-hp").innerText = d.enemy_data.hp;
                document.getElementById("en-max").innerText = d.enemy_data.max;
                let pct = (d.enemy_data.hp / d.enemy_data.max) * 100;
                document.getElementById("en-fill").style.width = pct + "%";
            } else {
                eBox.style.display = "none";
            }

            // 5. Items on floor indicator
            let floorBox = document.getElementById("floor-indicator");
            if (d.items_on_floor.length > 0) {
                floorBox.classList.add("active");
                document.getElementById("floor-list").innerText = d.items_on_floor.join(", ");
            } else {
                floorBox.classList.remove("active");
            }

            // 6. Inventory Logic
            let invL = document.getElementById("inv-list");
            invL.innerHTML = "";
            if (d.inv.length === 0) invL.innerHTML = "<div style='color:#555; text-align:center;'>תיק ריק</div>";
            else {
                d.inv.forEach(it => {
                    invL.innerHTML += `<button class="use-btn" onclick="send('use', '${it}')">${it} ⚡</button>`;
                });
            }

        } catch(e) { console.log(e); }
    }

    function toggleInv() {
        let el = document.getElementById("inv-modal");
        el.style.display = (el.style.display == "flex") ? "none" : "flex";
    }
    
    // Keybinds
    window.addEventListener('keydown', (e) => {
        let k = e.key;
        if(k=="ArrowUp") send('move',[0,1]);
        if(k=="ArrowDown") send('move',[0,-1]);
        if(k=="ArrowLeft") send('move',[-1,0]);
        if(k=="ArrowRight") send('move',[1,0]);
        if(k==" " || k=="Enter") send('attack');
        if(k=="e") send('take');
    });
</script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(port=5006, debug=True)
