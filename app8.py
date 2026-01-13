import random
import uuid
from flask import Flask, render_template_string, request, jsonify, session, url_for

app = Flask(__name__)
# שינוי השם כאן מוחק אוטומטית את ההיסטוריה הישנה שתקעה את המשחק
app.secret_key = 'parasite_omega_v5_fix'

# ==========================================
# 🧬 מאגר גופים (Hosts Data)
# ==========================================
HOSTS = {
    "blob": {"name": "עיסה ירוקה", "icon": "🦠", "hp": 10, "atk": 1, "desc": "חלש מאוד. חייב למצוא גוף."},
    "rat": {"name": "עכברוש", "icon": "🐀", "hp": 20, "atk": 3, "desc": "מהיר וזריז."},
    "dog": {"name": "כלב שמירה", "icon": "🐕", "hp": 40, "atk": 8, "desc": "נושך חזק."},
    "guard": {"name": "שומר", "icon": "👮", "hp": 80, "atk": 15, "desc": "חמוש ומסוכן."},
    "robot": {"name": "רובוט קרב", "icon": "🤖", "hp": 60, "atk": 12, "desc": "שריון חזק, לא מרגיש כאב."},
    "boss": {"name": "המנהל", "icon": "🤵", "hp": 150, "atk": 25, "desc": "המטרה הסופית."}
}

class GameEngine:
    def __init__(self, state=None):
        # מנגנון הגנה: אם אין STATE או שהוא שבור, יוצרים חדש
        if not state or "host" not in state:
            self.reset_game()
        else:
            self.state = state

    def reset_game(self):
        self.state = {
            "x": 0, "y": 0,
            "host": "blob", # מתחילים כעיסה
            "hp": 10, 
            "is_dead": False, # מצב רוח רפאים
            "map": {},
            "visited": ["0,0"],
            "log": [{"text": "התעוררת במעבדה. אתה חייב למצוא גוף מארח!", "type": "sys"}]
        }
        # יצירת חדר ראשון עם עכברוש כדי שיהיה קל להתחיל
        self.create_room(0, 0, force="rat")

    def pos(self): return f"{self.state['x']},{self.state['y']}"
    
    def log(self, txt, t="game"): self.state["log"].append({"text": txt, "type": t})

    def create_room(self, x, y, force=None):
        k = f"{x},{y}"
        if k in self.state["map"]: return

        enemies = []
        if force:
            types = [force]
        else:
            # אויבים אקראיים
            pool = ["rat", "rat", "dog", "guard", "robot"]
            if random.random() < 0.2: pool.append("boss")
            count = random.randint(1, 2)
            types = [random.choice(pool) for _ in range(count)]

        for t in types:
            data = HOSTS[t]
            enemies.append({
                "type": t,
                "name": data["name"],
                "icon": data["icon"],
                "hp": data["hp"],
                "max": data["hp"],
                "atk": data["atk"]
            })

        self.state["map"][k] = {"enemies": enemies}

    # --- מכניקת תנועה ---
    def move(self, dx, dy):
        if self.state["is_dead"]:
            self.log("הגוף שלך מושמד! אתה חייב להשתלט על מישהו כאן כדי לזוז.", "danger")
            return

        self.state["x"] += dx
        self.state["y"] += dy
        self.create_room(self.state["x"], self.state["y"])
        
        self.log(f"הגעת לחדר {self.pos()}", "game")
        
        # תיאור אויבים
        room = self.state["map"][self.pos()]
        if not room["enemies"]:
            self.log("החדר ריק.", "info")
        else:
            names = [e["name"] for e in room["enemies"]]
            self.log(f"יש כאן: {', '.join(names)}", "warning")

    # --- מכניקת קרב ---
    def attack(self, idx):
        if self.state["is_dead"]: return # מת לא יכול לתקוף

        room = self.state["map"][self.pos()]
        if not room["enemies"] or idx >= len(room["enemies"]): return

        target = room["enemies"][idx]
        my_stats = HOSTS[self.state["host"]]
        
        # אני תוקף
        dmg = my_stats["atk"] + random.randint(0, 5)
        target["hp"] -= dmg
        self.log(f"תקפת את {target['name']} ({dmg} נזק).", "success")

        # בדיקת מוות אויב
        if target["hp"] <= 0:
            self.log(f"{target['name']} מת. הגופה שלו לא שמישה.", "sys")
            room["enemies"].pop(idx)
            return

        # אויב תוקף חזרה
        e_dmg = target["atk"] + random.randint(-2, 2)
        self.state["hp"] -= e_dmg
        
        if self.state["hp"] <= 0:
            self.state["hp"] = 0
            self.state["is_dead"] = True
            self.log("🚨 הגוף שלך מת! אתה טפיל חשוף! (בחר אויב כדי להשתלט)", "danger")
        else:
            self.log(f"{target['name']} החזיר מכה! ירדו {e_dmg} חיים.", "warning")

    # --- המכניקה הייחודית: השתלטות (Parasite) ---
    def infect(self, idx):
        # מותר רק כשאני "מת" (רוח)
        if not self.state["is_dead"]: 
            self.log("אתה לא יכול לעבור גוף כשהנוכחי בחיים.", "info")
            return

        room = self.state["map"][self.pos()]
        if idx >= len(room["enemies"]): return

        target = room["enemies"][idx]
        
        # ביצוע ההחלפה
        self.state["host"] = target["type"]
        self.state["hp"] = target["hp"] # מקבלים את החיים שלו
        self.state["is_dead"] = False # חזרנו לחיים!
        
        old_name = target["name"]
        room["enemies"].pop(idx) # האויב הזה נעלם כי הוא עכשיו אני
        
        self.log(f"🧬 פלישה מוצלחת! השתלטת על ה-{old_name}.", "success")
        self.log(f"כוחות חדשים: {HOSTS[self.state['host']]['desc']}", "sys")


# ==========================================
# WEB & ROUTING
# ==========================================
@app.route("/")
def index():
    if "uid" not in session: session["uid"] = str(uuid.uuid4())
    api = url_for("game_loop") # תיקון כתובת
    return render_template_string(UI, api=api)

@app.route("/game/loop", methods=["POST"])
def game_loop():
    try:
        eng = GameEngine(session.get("game_data"))
    except:
        eng = GameEngine(None) # שגיאה? התחל מחדש

    data = request.json or {}
    act = data.get("a")
    val = data.get("v")

    if act == "move": eng.move(*val)
    elif act == "attack": eng.attack(val)
    elif act == "infect": eng.infect(val)
    elif act == "reset": eng.reset_game()

    session["game_data"] = eng.state
    
    room = eng.state["map"][eng.pos()]
    my_data = HOSTS[eng.state["host"]]
    
    return jsonify({
        "log": eng.state["log"],
        "pos": eng.pos(),
        "enemies": room["enemies"],
        "player": {
            "name": my_data["name"],
            "icon": my_data["icon"],
            "hp": eng.state["hp"],
            "max": my_data["hp"],
            "is_dead": eng.state["is_dead"] # הדגל החשוב לממשק
        }
    })

# ==========================================
# INTERFACE (UI)
# ==========================================
UI = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>PARASITE</title>
<style>
    body { background: #050a00; color: #aaddaa; margin:0; font-family: monospace; display: flex; flex-direction: column; height: 100vh;}
    
    /* Top Bar */
    .status-bar { 
        background: #111; padding: 15px; border-bottom: 2px solid #00aa00; 
        display: flex; justify-content: space-between; align-items: center;
    }
    .big-icon { font-size: 30px; margin-left: 10px; }
    
    /* Screen Styles */
    .main-screen { flex: 1; display: flex; flex-direction: column; padding: 10px; overflow: hidden; }
    .normal-mode { background: radial-gradient(circle, #0a1100 0%, #000 100%); }
    .ghost-mode { background: #300; border: 5px solid red; animation: pulse-red 1s infinite alternate; }
    
    /* Enemies */
    .scene { 
        flex: 1; display: flex; gap: 15px; justify-content: center; align-items: center; 
        flex-wrap: wrap; overflow-y: auto; padding: 20px;
    }
    
    .enemy-card { 
        width: 120px; height: 160px; background: #222; border: 2px solid #444; border-radius: 8px;
        display: flex; flex-direction: column; align-items: center; justify-content: space-around; padding: 10px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.5);
    }
    .enemy-icon { font-size: 40px; }
    
    .btn-action { 
        width: 100%; padding: 8px; border: none; font-weight: bold; cursor: pointer; border-radius: 4px; font-family: inherit;
    }
    .atk { background: #822; color: white; }
    .inf { background: #4f4; color: black; animation: glow 0.5s infinite; }

    /* Controls */
    .control-deck { 
        background: #111; height: 150px; display: grid; grid-template-columns: repeat(3, 1fr); 
        gap: 10px; padding: 10px; align-items: center; justify-items: center; border-top: 1px solid #333;
    }
    .move-btn { 
        width: 60px; height: 60px; background: #223; color: white; border: 1px solid #555; border-radius: 8px; font-size: 24px; cursor: pointer;
    }
    .move-btn:disabled { background: #333; color: #555; border-color: #333; cursor: not-allowed; }
    
    .btn-up { grid-column: 2; grid-row: 1; }
    .btn-down { grid-column: 2; grid-row: 2; }
    .btn-left { grid-column: 1; grid-row: 2; }
    .btn-right { grid-column: 3; grid-row: 2; }

    /* LOG */
    .log-box { 
        height: 100px; overflow-y: auto; background: rgba(0,0,0,0.5); padding: 10px; 
        border-top: 1px dashed #333; color: #aaa; font-size: 13px;
    }
    
    @keyframes pulse-red { from{box-shadow: inset 0 0 20px #500;} to{box-shadow: inset 0 0 50px #f00;} }
    @keyframes glow { from{box-shadow: 0 0 5px #4f4;} to{box-shadow: 0 0 15px #afa;} }

</style>
</head>
<body>

<!-- HEAD -->
<div class="status-bar" id="header-ui">
    <div style="display:flex; align-items:center;">
        <span class="big-icon" id="p-icon">🦠</span>
        <div>
            <div id="p-name" style="font-weight:bold; font-size:1.1rem">טוען...</div>
            <div style="font-size:0.8rem">חדר: <span id="loc">0,0</span></div>
        </div>
    </div>
    <div style="font-size:1.5rem; font-weight:bold;">
        ❤️ <span id="p-hp">--</span>
    </div>
</div>

<!-- SCENE -->
<div class="main-screen normal-mode" id="game-screen">
    <div class="scene" id="scene-area">
        <div style="color:#666">אין גופות בסביבה... עבור חדר.</div>
    </div>
    
    <div class="log-box" id="log-target">
        מערכת אותחלה.
    </div>
</div>

<!-- CONTROLS -->
<div class="control-deck">
    <button class="move-btn btn-up" onclick="send('move', [0,1])">⬆️</button>
    <button class="move-btn btn-left" onclick="send('move', [-1,0])">⬅️</button>
    <button class="move-btn btn-down" onclick="send('move', [0,-1])">⬇️</button>
    <button class="move-btn btn-right" onclick="send('move', [1,0])">➡️</button>
</div>

<script>
    const API = "{{ api }}";
    
    window.onload = () => send('init');

    async function send(a, v=null) {
        try {
            let r = await fetch(API, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({a, v})});
            let d = await r.json();
            
            // 1. UPDATE PLAYER
            document.getElementById('p-icon').innerText = d.player.icon;
            document.getElementById('p-name').innerText = d.player.name;
            document.getElementById('p-hp').innerText = d.player.hp + "/" + d.player.max;
            document.getElementById('loc').innerText = d.pos;
            
            // 2. CHECK DEAD STATE
            let screen = document.getElementById('game-screen');
            let btns = document.querySelectorAll('.move-btn');
            
            if (d.player.is_dead) {
                // מצב טפיל!
                screen.className = "main-screen ghost-mode";
                document.getElementById('p-name').innerText = "טפיל חשוף (סכנה!)";
                document.getElementById('p-icon').innerText = "👻";
                // נועלים תזוזה
                btns.forEach(b => b.disabled = true);
            } else {
                // מצב רגיל
                screen.className = "main-screen normal-mode";
                btns.forEach(b => b.disabled = false);
            }

            // 3. RENDER ENEMIES
            let scene = document.getElementById('scene-area');
            scene.innerHTML = "";
            
            if(d.enemies.length === 0) {
                scene.innerHTML = "<div style='opacity:0.5; text-align:center;'>החדר ריק...<br>השתמש בחצים למטה כדי לעבור חדר</div>";
            } else {
                d.enemies.forEach((en, index) => {
                    let btnHTML = "";
                    if(d.player.is_dead) {
                        btnHTML = `<button class="btn-action inf" onclick="send('infect', ${index})">🧬 השתלטות!</button>`;
                    } else {
                        btnHTML = `<button class="btn-action atk" onclick="send('attack', ${index})">🗡️ תקוף</button>`;
                    }
                    
                    let card = document.createElement("div");
                    card.className = "enemy-card";
                    card.innerHTML = `
                        <div class="enemy-icon">${en.icon}</div>
                        <div style="font-weight:bold">${en.name}</div>
                        <div style="color:#ff6666">${en.hp}/${en.max} ❤️</div>
                        ${btnHTML}
                    `;
                    scene.appendChild(card);
                });
            }

            // 4. LOGS
            let lb = document.getElementById('log-target');
            lb.innerHTML = "";
            d.log.reverse().forEach(l => {
                lb.innerHTML += `<div>${l.text}</div>`;
            });

        } catch(e) { console.error(e); }
    }
</script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(port=5006, debug=True)
