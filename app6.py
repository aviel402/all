import random
import uuid
from flask import Flask, render_template_string, request, jsonify, session, url_for

app = Flask(__name__)
app.secret_key = 'platinum_rpg_interface_v99'

# ==========================================
# ⚙️ לוגיקה ותוכן
# ==========================================

# רשימת מקומות ואייקונים
BIOMES = [
    {"name": "יער העד", "icon": "🌲", "danger": 1},
    {"name": "מכרות הנחושת", "icon": "⛏️", "danger": 2},
    {"name": "מבצר הגולגולת", "icon": "💀", "danger": 4},
    {"name": "הרי הערפל", "icon": "🗻", "danger": 2},
    {"name": "אגם רעיל", "icon": "🤢", "danger": 3},
    {"name": "כפר נטוש", "icon": "🏚️", "danger": 1},
]

ENEMIES = [
    {"name": "גובלין סייר", "hp": 25, "atk": 5, "xp": 10},
    {"name": "אורק משוריין", "hp": 45, "atk": 12, "xp": 30},
    {"name": "שד צללים", "hp": 30, "atk": 15, "xp": 25},
    {"name": "דרקון שומר (בוס)", "hp": 120, "atk": 25, "xp": 200},
]

class WorldGen:
    def create_room(self, x, y):
        if x == 0 and y == 0:
            return {"name": "בסיס האם", "icon": "🏰", "enemy": None, "items": ["שיקוי"]}
        
        biome = random.choice(BIOMES)
        
        enemy = None
        if random.random() < 0.45:
            base = random.choice(ENEMIES)
            enemy = base.copy()
            
        items = []
        if random.random() < 0.5:
            items.append(random.choice(["שיקוי", "יהלום", "מטבע", "חרב חלודה"]))

        return {
            "name": biome["name"],
            "icon": biome["icon"],
            "enemy": enemy,
            "items": items
        }

class Engine:
    def __init__(self, state=None):
        if not state:
            self.state = {
                "x": 0, "y": 0,
                "stats": {"hp": 100, "max": 100, "gold": 0, "xp": 0, "lvl": 1},
                "inv": [],
                "map": {},
                "visited": ["0,0"],
                "log": [{"text": "התקבל אות חיים. אתה מוכן לקרב?", "type": "sys"}]
            }
            gen = WorldGen()
            self.state["map"]["0,0"] = gen.create_room(0,0)
        else:
            self.state = state

    def pos(self): return f"{self.state['x']},{self.state['y']}"
    
    def log(self, txt, t="game"): self.state["log"].append({"text": txt, "type": t})

    def move(self, dx, dy):
        self.state["x"] += dx
        self.state["y"] += dy
        
        k = self.pos()
        if k not in self.state["map"]:
            self.state["map"][k] = WorldGen().create_room(self.state['x'], self.state['y'])
        
        if k not in self.state["visited"]: self.state["visited"].append(k)
        
        r = self.state["map"][k]
        self.log(f"הגעת ל-{r['name']}", "game")
        if r["enemy"]: self.log(f"⚔️ אויב לפניך! {r['enemy']['name']}", "danger")

    def attack(self):
        r = self.state["map"][self.pos()]
        if not r["enemy"]:
            self.log("האזור נקי.", "info")
            return
        
        dmg = random.randint(10, 20) + self.state["stats"]["lvl"] * 2
        r["enemy"]["hp"] -= dmg
        self.log(f"פגעת ב-{r['enemy']['name']}! (-{dmg})", "success")
        
        if r["enemy"]["hp"] <= 0:
            reward = r["enemy"]["xp"]
            self.state["stats"]["gold"] += random.randint(5, 20)
            self.state["stats"]["xp"] += reward
            self.log(f"🏆 ניצחת! קיבלת {reward} נסיון.", "gold")
            r["enemy"] = None
            if self.state["stats"]["xp"] > self.state["stats"]["lvl"] * 50:
                self.state["stats"]["lvl"] += 1
                self.state["stats"]["max"] += 20
                self.state["stats"]["hp"] = self.state["stats"]["max"]
                self.log("⭐ עלית רמה!", "gold")
        else:
            p_dmg = r["enemy"]["atk"]
            self.state["stats"]["hp"] -= p_dmg
            self.log(f"נפגעת! (-{p_dmg})", "danger")

    def take(self):
        r = self.state["map"][self.pos()]
        if r["items"]:
            self.state["inv"].extend(r["items"])
            self.log(f"אספת: {', '.join(r['items'])}", "success")
            r["items"] = []
        else:
            self.log("אין כאן כלום.", "info")

    def heal(self):
        if "שיקוי" in self.state["inv"]:
            self.state["inv"].remove("שיקוי")
            self.state["stats"]["hp"] = self.state["stats"]["max"]
            self.log("שתית שיקוי והתרפאת לגמרי.", "success")
        else:
            self.log("אין לך שיקויים בתיק.", "danger")

    def get_map_grid(self):
        # בניית גריד למפה בגודל 5x5
        cx, cy = self.state["x"], self.state["y"]
        r = 2
        grid = []
        for dy in range(r, -r-1, -1):
            row = []
            for dx in range(-r, r+1):
                k = f"{cx+dx},{cy+dy}"
                if dx == 0 and dy == 0:
                    row.append({"c":"👤", "cls":"player"})
                elif k in self.state["visited"]:
                    rm = self.state["map"][k]
                    icon = "💀" if rm["enemy"] else rm["icon"]
                    row.append({"c":icon, "cls":"known"})
                else:
                    row.append({"c":"", "cls":"fog"})
            grid.append(row)
        return grid

# ==========================================
# שרת WEB
# ==========================================

@app.route("/")
def home():
    if "uid" not in session: session["uid"] = str(uuid.uuid4())
    # כתובת חזרה לראשי - מניח שהלובי שלך בכתובת השורש
    main_menu_url = "/" 
    api_url = url_for("update")
    return render_template_string(UI, api=api_url, home=main_menu_url)

@app.route("/api/update", methods=["POST"])
def update():
    data = request.json or {}
    act = data.get("a")
    val = data.get("v")
    
    try:
        eng = Engine(session.get("game"))
    except:
        eng = Engine(None) # Auto repair save

    if act == "move": eng.move(*val)
    elif act == "atk": eng.attack()
    elif act == "take": eng.take()
    elif act == "heal": eng.heal()
    elif act == "reset": eng = Engine(None)

    session["game"] = eng.state
    
    room = eng.state["map"][eng.pos()]
    
    return jsonify({
        "log": eng.state["log"],
        "map": eng.get_map_grid(),
        "stats": eng.state["stats"],
        "inv": eng.state["inv"],
        "loc": room["name"]
    })

# ==========================================
# עיצוב UI (פלטינום)
# ==========================================
UI = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>RPG Platinum</title>
<style>
    :root {
        --bg: #09090b;
        --panel: #18181b;
        --border: #27272a;
        --accent: #6366f1; /* Indigo */
        --accent-glow: rgba(99, 102, 241, 0.2);
        --text: #e4e4e7;
        --danger: #ef4444;
        --success: #22c55e;
    }
    
    body { background: var(--bg); color: var(--text); font-family: 'Segoe UI', system-ui, sans-serif; margin: 0; display: flex; flex-direction: column; height: 100vh; overflow: hidden;}
    
    /* === HEADER === */
    header {
        height: 60px; background: var(--panel); border-bottom: 1px solid var(--border);
        display: flex; align-items: center; justify-content: space-between; padding: 0 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1); z-index: 10;
    }
    
    .logo { font-weight: 900; font-size: 1.2rem; color: var(--accent); letter-spacing: 1px; }
    .exit-btn { background: #333; color: #aaa; border: none; padding: 8px 15px; border-radius: 6px; cursor: pointer; font-size: 0.9rem; text-decoration:none;}
    .exit-btn:hover { background: #444; color: white; }

    /* === LAYOUT GRID === */
    .dashboard {
        flex: 1; display: grid; 
        grid-template-columns: 3fr 2fr; /* 60% סיפור, 40% נתונים */
        gap: 2px; background: var(--border);
        overflow: hidden;
    }

    /* === LEFT PANEL (LOG) === */
    .log-panel {
        background: var(--bg);
        display: flex; flex-direction: column;
        overflow: hidden; position: relative;
    }
    
    .room-title {
        text-align: center; padding: 10px; font-weight: bold; font-size: 1.1rem;
        background: rgba(255,255,255,0.02); border-bottom: 1px solid var(--border);
        color: var(--accent);
    }

    .logs {
        flex: 1; overflow-y: auto; padding: 20px;
        display: flex; flex-direction: column; gap: 8px;
    }
    
    .msg { padding: 10px; border-radius: 8px; background: #131315; border-right: 3px solid #333; animation: popIn 0.3s; line-height: 1.5;}
    .msg.sys { text-align: center; border: none; background: transparent; font-size: 0.8rem; color: #666; margin-top: 10px;}
    .msg.game { border-color: #555; }
    .msg.danger { border-color: var(--danger); background: rgba(239, 68, 68, 0.1); }
    .msg.success { border-color: var(--success); background: rgba(34, 197, 94, 0.1); }
    .msg.gold { border-color: gold; color: gold; font-weight: bold;}

    /* === RIGHT PANEL (STATS & MAP) === */
    .info-panel {
        background: #111;
        display: flex; flex-direction: column;
        border-right: 1px solid var(--border);
    }
    
    .stats-bar {
        padding: 15px; display: grid; gap: 8px;
        background: #1a1a1a; border-bottom: 1px solid var(--border);
    }
    .stat { display: flex; justify-content: space-between; font-size: 0.9rem; color: #aaa; }
    .val { color: white; font-weight: bold; font-family: monospace; }

    .map-box {
        flex: 1; display: flex; align-items: center; justify-content: center;
        background: #000; padding: 20px;
    }
    .map-grid { display: grid; gap: 4px; grid-template-columns: repeat(5, 1fr); background: #111; padding: 10px; border-radius: 12px; border: 1px solid #333;}
    .cell {
        width: 32px; height: 32px; display: flex; align-items: center; justify-content: center;
        border-radius: 4px; font-size: 18px; background: #050505; transition: 0.2s;
    }
    .cell.known { background: #222; }
    .cell.player { background: var(--accent); box-shadow: 0 0 10px var(--accent); z-index:2; border: 1px solid white;}
    .cell.fog { opacity: 0; }

    .inventory {
        height: 100px; padding: 15px; border-top: 1px solid var(--border);
        overflow-y: auto; background: #161616;
    }
    .inv-item { display: inline-block; padding: 4px 8px; background: #333; margin: 2px; border-radius: 4px; font-size: 0.8rem; }

    /* === BOTTOM CONTROLS === */
    .control-deck {
        height: 200px; background: #121214; border-top: 1px solid var(--border);
        padding: 15px;
        display: grid; 
        grid-template-columns: 200px 1fr 200px;
        gap: 20px;
        align-items: center; justify-content: center;
    }

    /* D-PAD (Directional Arrows) */
    .d-pad {
        display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px;
        width: 140px; margin: 0 auto;
        direction: ltr; /* קריטי - מבטיח שחץ ימין יהיה מימין */
    }
    .btn {
        background: #27272a; border: none; border-bottom: 4px solid #111; color: #fff;
        border-radius: 8px; cursor: pointer; display: flex; align-items: center; justify-content: center;
        font-size: 1.5rem; height: 45px; transition: 0.1s;
    }
    .btn:active { transform: translateY(4px); border-bottom-width: 0; background: #3f3f46; }
    
    .up { grid-column: 2; }
    .left { grid-column: 1; grid-row: 2; }
    .down { grid-column: 2; grid-row: 2; }
    .right { grid-column: 3; grid-row: 2; }

    /* Actions Middle */
    .actions { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; max-width: 400px; width: 100%; margin: 0 auto;}
    .big-btn { 
        height: 100%; min-height: 80px; font-size: 1.2rem; font-weight: bold;
        background: linear-gradient(145deg, #27272a, #18181b); border: 1px solid #333;
        box-shadow: 0 4px 0 #000;
    }
    .btn-atk { background: #7f1d1d; border-color: #991b1b; color: #fca5a5; }
    .btn-heal { background: #064e3b; border-color: #065f46; color: #6ee7b7; }
    .btn-take { background: #713f12; border-color: #854d0e; color: #fde047; grid-column: span 2;}

    .util-btn { font-size: 0.9rem; padding: 10px; }

    @keyframes popIn { from{opacity:0; transform: translateY(5px);} to{opacity:1;}}
    
    /* Mobile Responsive */
    @media (max-width: 768px) {
        .dashboard { grid-template-columns: 1fr; grid-template-rows: 1fr 200px; }
        .info-panel { display: none; } /* מובייל - מחביאים סטטים או מעבירים למודאל */
        .control-deck { grid-template-columns: 1fr; gap: 10px; height: auto; padding-bottom: 20px;}
        .d-pad { margin-bottom: 10px; order: 2;}
        .actions { order: 1; }
    }
</style>
</head>
<body>

<header>
    <div class="logo">🚀 EXPLORER PRO</div>
    <a href="{{ home }}" class="exit-btn">🏠 חזרה לתפריט</a>
</header>

<div class="dashboard">
    <!-- צד ימין: לוג -->
    <div class="log-panel">
        <div class="room-title" id="room-name">...</div>
        <div class="logs" id="log-container"></div>
    </div>

    <!-- צד שמאל: נתונים -->
    <div class="info-panel">
        <div class="map-box">
            <div class="map-grid" id="map-target"></div>
        </div>
        
        <div class="stats-bar">
            <div class="stat"><span>❤️ בריאות</span> <span class="val" id="hp">100/100</span></div>
            <div class="stat"><span>⭐ רמה</span> <span class="val" id="lvl">1</span></div>
            <div class="stat"><span>🪙 זהב</span> <span class="val" id="gold" style="color:gold">0</span></div>
        </div>

        <div class="inventory">
            <div style="color:#666; font-size:0.8rem; margin-bottom:5px">תיק ציוד:</div>
            <div id="inv-target">ריק</div>
        </div>
        
        <button onclick="send('reset')" style="background:#522; color:white; border:none; padding:10px; width:100%; cursor:pointer;">⚠️ איפוס משחק</button>
    </div>
</div>

<!-- בקרה תחתונה -->
<div class="control-deck">
    
    <!-- פד שליטה (דמוי גויסטיק) -->
    <div class="d-pad">
        <button class="btn up" onclick="send('move',[0,1])">⬆️</button>
        <button class="btn left" onclick="send('move',[-1,0])">⬅️</button>
        <button class="btn down" onclick="send('move',[0,-1])">⬇️</button>
        <button class="btn right" onclick="send('move',[1,0])">➡️</button>
    </div>

    <!-- כפתורי פעולה מרכזיים -->
    <div class="actions">
        <button class="btn big-btn btn-atk" onclick="send('atk')">⚔️ תקוף!</button>
        <button class="btn big-btn btn-heal" onclick="send('heal')">💊 ריפוי</button>
        <button class="btn big-btn btn-take" onclick="send('take')">✋ אסוף הכל</button>
    </div>
    
    <!-- צד שלישי (ריק לאיזון או כפתורים נוספים) -->
    <div style="display:none"></div>

</div>

<script>
    const API = "{{ api }}";
    
    document.addEventListener("DOMContentLoaded", () => send("init"));

    async function send(act, val=null) {
        try {
            let res = await fetch(API, {
                method:'POST', headers:{'Content-Type':'application/json'},
                body: JSON.stringify({a: act, v: val})
            });
            let d = await res.json();
            
            // עדכון כותרת וחדר
            document.getElementById("room-name").innerText = d.loc;
            
            // עדכון לוגים
            let l = document.getElementById("log-container");
            l.innerHTML = "";
            d.log.forEach(msg => {
                let div = document.createElement("div");
                div.className = "msg " + msg.type;
                div.innerText = msg.text;
                l.appendChild(div);
            });
            l.scrollTop = l.scrollHeight;

            // עדכון סטטים
            document.getElementById("hp").innerText = d.stats.hp + "/" + d.stats.max;
            document.getElementById("gold").innerText = d.stats.gold;
            document.getElementById("lvl").innerText = d.stats.lvl;

            // עדכון מפה
            let mapHTML = "";
            d.map.forEach(row => {
                row.forEach(c => {
                    mapHTML += `<div class='cell ${c.cls}'>${c.c}</div>`;
                });
            });
            document.getElementById("map-target").innerHTML = mapHTML;

            // עדכון תיק
            let invDiv = document.getElementById("inv-target");
            if (d.inv.length === 0) invDiv.innerText = "ריק";
            else {
                invDiv.innerHTML = "";
                d.inv.forEach(item => {
                    invDiv.innerHTML += `<span class='inv-item'>${item}</span>`;
                });
            }

        } catch (e) { console.error(e); }
    }
    
    // מקשי מקלדת
    window.addEventListener('keydown', (e) => {
        let k = e.key;
        if(k === "ArrowUp" || k === "w") send('move', [0,1]);
        if(k === "ArrowDown" || k === "s") send('move', [0,-1]);
        if(k === "ArrowRight" || k === "d") send('move', [1,0]);
        if(k === "ArrowLeft" || k === "a") send('move', [-1,0]);
        if(k === " " || k === "Enter") send('atk');
        if(k === "q") send('heal');
        if(k === "e") send('take');
    });
</script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(port=5006, debug=True)
