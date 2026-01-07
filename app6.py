import random
import uuid
import json
from flask import Flask, render_template_string, request, jsonify, session, url_for

# ==========================================
# ⚙️ מסד נתונים עשיר (NPC, אויבים, אירועים)
# ==========================================

# אירועים רנדומליים בחדר
EVENTS = [
    {"msg": "💀 מצאת גופה של הרפתקן. לקחת את הזהב שלו.", "type": "gold", "val": 40},
    {"msg": "✨ מעיין קסום! שתית ממנו והבראת.", "type": "heal", "val": 30},
    {"msg": "🤮 אוויר רעיל ממלא את החדר. נחנקת קצת.", "type": "dmg", "val": 10},
    {"msg": "🎒 מצאת תיק נטוש עם אספקה.", "type": "item", "val": "מנת קרב"},
    {"msg": "🧘 פינה שקטה. נחת וצברת כוח.", "type": "stamina", "val": 40}
]

# דמויות שאפשר לדבר איתן (NPC)
NPCS = [
    {"name": "סוחר זקן", "icon": "👳‍♂️", "lines": ["הכל למכירה, חבר.", "אל תלך לשם... המפלצות רעבות."]},
    {"name": "מכשפה", "icon": "🧙‍♀️", "lines": ["אני מריחה את הפחד שלך.", "רוצה שיקוי? זה יעלה לך בנשמתך."]},
    {"name": "רובוט שבור", "icon": "🤖", "lines": ["שגיאה 404... אנושיות לא נמצאה.", "ביפ. בופ. השמדה עצמית."]},
    {"name": "ילד מסתורי", "icon": "👶", "lines": ["ראית את אמא שלי?", "המלך הגדול רואה הכל."]}
]

# אויבים
ENEMIES = [
    {"name": "אורק לוחם", "icon": "👹", "hp": 30, "atk": 8, "xp": 20, "gold": 15},
    {"name": "עכביש ענק", "icon": "🕷️", "hp": 15, "atk": 5, "xp": 10, "gold": 5},
    {"name": "רוח רפאים", "icon": "👻", "hp": 40, "atk": 12, "xp": 35, "gold": 50},
    {"name": "דרקון גור", "icon": "🐲", "hp": 80, "atk": 18, "xp": 100, "gold": 200}
]

# ==========================================
# 🧠 המנוע
# ==========================================

app = Flask(__name__)
# שיניתי מפתח כדי לאלץ איפוס של עוגיות ישנות אצל כל המשתמשים
app.secret_key = 'rpg_final_fix_v2026' 

class Generator:
    def create_room(self, x, y):
        # חדר 0,0 תמיד בטוח
        if x==0 and y==0: 
            return {"name": "בסיס הבית", "type": "base", "icon": "🏠", "enemy": None, "npc": None, "items": [], "event": None}
            
        biome = random.choice(["יער", "מערה", "צינוק", "טירה", "ביוב"])
        icon = random.choice(["🌲", "🗻", "🏯", "🕳️"])
        
        # בניית חדר
        room = {
            "name": f"{biome} ({x},{y})",
            "type": "normal",
            "icon": icon,
            "enemy": None,
            "npc": None,
            "items": [],
            "event": None
        }

        # מה יש בחדר? (Priority system)
        roll = random.random()
        
        if roll < 0.15: # אירוע מיוחד
            room["event"] = random.choice(EVENTS)
            room["icon"] = "⚠️"
        elif roll < 0.35: # NPC
            base = random.choice(NPCS)
            room["npc"] = base.copy()
            room["icon"] = "💬"
        elif roll < 0.70: # אויב
            base = random.choice(ENEMIES)
            room["enemy"] = base.copy()
            room["icon"] = "💀"
        else: # חדר רגיל עם חפצים
            if random.random() < 0.5:
                room["items"].append(random.choice(["תפוח", "שיקוי", "יהלום", "מפתח"]))

        return room

class Engine:
    def __init__(self, state=None):
        # מנגנון תיקון עצמי: אם המידע פגום, מפרמט משחק
        if not state or "stats" not in state or "map" not in state:
            self.reset_state()
        else:
            self.state = state
        self.gen = Generator()

    def reset_state(self):
        self.state = {
            "x": 0, "y": 0,
            "stats": {"hp": 100, "max_hp": 100, "st": 100, "xp": 0, "lvl": 1, "gold": 0},
            "inv": [],
            "map": {},
            "visited": ["0,0"],
            "log": [{"text": "המשחק אותחל בהצלחה. בהצלחה!", "type": "sys"}]
        }
        self.state["map"]["0,0"] = self.gen.create_room(0,0)

    def key(self): return f"{self.state['x']},{self.state['y']}"
    
    def log(self, txt, t="game"): 
        self.state["log"].append({"text": txt, "type": t})

    # -- פעולות --
    def move(self, dx, dy):
        s = self.state["stats"]
        if s["st"] <= 0:
            self.log("חסרה לך אנרגיה! נוח (R).", "danger")
            return
        
        self.state["x"] += dx
        self.state["y"] += dy
        s["st"] -= 2
        
        k = self.key()
        if k not in self.state["map"]:
            self.state["map"][k] = self.gen.create_room(self.state['x'], self.state['y'])
        
        if k not in self.state["visited"]: self.state["visited"].append(k)
        
        r = self.state["map"][k]
        
        # טיפול אוטומטי באירועים
        if r["event"]:
            ev = r["event"]
            self.log(ev["msg"], "sys")
            if ev["type"] == "heal": s["hp"] = min(s["hp"]+ev["val"], s["max_hp"])
            if ev["type"] == "dmg": s["hp"] -= ev["val"]
            if ev["type"] == "gold": s["gold"] += ev["val"]
            r["event"] = None # אירוע חד פעמי
            
        self.log(f"זזת ל-{r['name']}", "game")

    def attack(self):
        r = self.state["map"][self.key()]
        if not r["enemy"]:
            self.log("אין במי לתקוף.", "sys")
            return
        
        e = r["enemy"]
        dmg = random.randint(10, 20) + self.state["stats"]["lvl"]*2
        e["hp"] -= dmg
        self.log(f"💥 תקפת את {e['name']} ({dmg} נזק)", "game")
        
        if e["hp"] <= 0:
            self.log(f"🎉 ניצחת! קיבלת {e['gold']} זהב.", "success")
            self.state["stats"]["gold"] += e["gold"]
            self.state["stats"]["xp"] += e["xp"]
            self.check_lvl()
            r["enemy"] = None
            r["icon"] = "✔️"
        else:
            p_dmg = max(1, e["atk"] - random.randint(0,2))
            self.state["stats"]["hp"] -= p_dmg
            self.log(f"האויב תקף חזרה! -{p_dmg} חיים", "danger")

    def talk(self):
        r = self.state["map"][self.key()]
        if r["npc"]:
            line = random.choice(r["npc"]["lines"])
            self.log(f"🗨️ {r['npc']['name']}: {line}", "sys")
        else:
            self.log("אין פה אף אחד.", "game")
            
    def take(self):
        r = self.state["map"][self.key()]
        if r["items"]:
            for i in r["items"]: self.state["inv"].append(i)
            self.log(f"אספת: {', '.join(r['items'])}", "success")
            r["items"] = []
        else:
            self.log("אין כאן כלום לאסוף.", "game")
            
    def rest(self):
        s = self.state["stats"]
        s["hp"] = min(s["hp"] + 10, s["max_hp"])
        s["st"] = 100
        self.log("💤 נחת והתמלאת אנרגיה.", "sys")
        
    def check_lvl(self):
        s = self.state["stats"]
        if s["xp"] >= s["lvl"] * 50:
            s["lvl"] += 1
            s["max_hp"] += 20
            s["hp"] = s["max_hp"]
            self.log(f"⭐ עלית לרמה {s['lvl']}!", "success")

    def render_map(self):
        cx, cy = self.state["x"], self.state["y"]
        r = 2
        html = "<div class='grid'>"
        for dy in range(r, -r-1, -1):
            html += "<div class='row'>"
            for dx in range(-r, r+1):
                k = f"{cx+dx},{cy+dy}"
                content = "<span class='fog'>☁️</span>"
                
                if dx==0 and dy==0: 
                    content = "<span class='player'>🧑‍🚀</span>"
                elif k in self.state["visited"]:
                    room = self.state["map"][k]
                    # אייקון לפי תוכן החדר
                    ic = room["icon"]
                    bg_class = "room-base"
                    if room["enemy"]: 
                        ic = "👹"
                        bg_class = "room-enemy"
                    if room["npc"]:
                        ic = "🙂"
                        bg_class = "room-npc"
                        
                    content = f"<span class='room {bg_class}'>{ic}</span>"
                html += f"<div class='cell'>{content}</div>"
            html += "</div>"
        html += "</div>"
        return html


# ==========================================
# SERVER ROUTES
# ==========================================

@app.route("/")
def index():
    if "uid" not in session: session["uid"] = str(uuid.uuid4())
    return render_template_string(HTML)

@app.route("/act", methods=["POST"])
def act():
    data = request.json
    # אם קרתה שגיאה בטעינת המצב הקודם, יוצרים מנוע חדש שמאפס את עצמו
    try:
        eng = Engine(session.get("game"))
    except:
        eng = Engine(None) # Force Reset

    action = data.get("a")
    val = data.get("v")

    if eng.state["stats"]["hp"] <= 0 and action != "reset":
        return jsonify({"dead": True})

    if action == "move": eng.move(*val)
    elif action == "attack": eng.attack()
    elif action == "talk": eng.talk()
    elif action == "take": eng.take()
    elif action == "rest": eng.rest()
    elif action == "reset": eng.reset_state()
    
    session["game"] = eng.state
    
    room = eng.state["map"][eng.key()]
    return jsonify({
        "log": eng.state["log"],
        "hud": eng.render_map(),
        "stats": eng.state["stats"],
        "inv": eng.state["inv"],
        "loc": room["name"]
    })

# ==========================================
# UI (HTML/CSS/JS)
# ==========================================
HTML = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>RPG v3</title>
<style>
    /* RESET & BASE */
    * { box-sizing: border-box; }
    body { background: #111; color: #ddd; font-family: 'Segoe UI', sans-serif; margin: 0; display: flex; height: 100vh; overflow: hidden; }

    /* LAYOUT */
    .container { display: flex; width: 100%; height: 100%; }
    
    .sidebar { width: 300px; background: #1a1a1a; padding: 15px; display: flex; flex-direction: column; gap: 15px; border-left: 2px solid #333; }
    
    .main { flex: 1; display: flex; flex-direction: column; position: relative; }
    
    /* MAP STYLE */
    .map-frame { background: #000; padding: 10px; border-radius: 8px; border: 1px solid #444; display: flex; justify-content: center; }
    .grid { display: flex; flex-direction: column; gap: 2px; }
    .row { display: flex; gap: 2px; }
    .cell { width: 40px; height: 40px; background: #222; display: flex; align-items: center; justify-content: center; border-radius: 4px; font-size: 20px;}
    .fog { opacity: 0.1; }
    .player { border: 2px solid #0f0; background: #002200; border-radius: 50%; width: 100%; height: 100%; display: flex; align-items: center; justify-content: center;}
    .room-base { background: #333; }
    .room-enemy { background: #500; animation: blink 1s infinite; }
    .room-npc { background: #005; }
    
    /* STATS */
    .stat-row { display: flex; justify-content: space-between; border-bottom: 1px solid #333; padding: 5px 0; }
    
    /* LOG */
    .log { flex: 1; overflow-y: auto; padding: 20px; background: #0d0d0d; display: flex; flex-direction: column; gap: 8px; }
    .msg { padding: 8px 12px; border-radius: 4px; background: #222; font-size: 0.95rem; border-right: 3px solid transparent;}
    .sys { border-color: #0ff; color: #0ff; }
    .game { border-color: #888; color: #ccc; }
    .danger { border-color: #f00; background: #300; }
    .success { border-color: #0f0; color: #bfb; }

    /* CONTROLS */
    .controls { padding: 15px; background: #1a1a1a; display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; height: 160px; border-top: 2px solid #333;}
    .btn { background: #333; color: white; border: none; border-radius: 6px; font-size: 24px; cursor: pointer; display: flex; flex-direction: column; align-items: center; justify-content: center; transition: 0.1s; }
    .btn:active { background: #555; transform: scale(0.95); }
    .btn span { font-size: 11px; margin-top: 4px; color: #aaa; font-family: sans-serif; }
    
    .btn-atk { background: #722; grid-column: span 2; }
    .btn-move { background: #235; }
    
    @keyframes blink { 50% { opacity: 0.6; } }

</style>
</head>
<body>
    <div class="container">
        
        <!-- SIDEBAR: MAP & STATS -->
        <div class="sidebar">
            <h3 style="margin:0; text-align:center; color:#ccc;">WORLD MAP</h3>
            <div class="map-frame" id="map-wrap"></div>
            
            <div style="margin-top:20px;">
                <div class="stat-row"><span style="color:#e57373">❤️ חיים</span><span id="hp">100/100</span></div>
                <div class="stat-row"><span style="color:#64b5f6">⚡ אנרגיה</span><span id="st">100</span></div>
                <div class="stat-row"><span style="color:#ffd54f">🪙 זהב</span><span id="gold">0</span></div>
                <div class="stat-row"><span style="color:#ba68c8">⭐ רמה</span><span id="lvl">1</span></div>
            </div>
            
            <div style="margin-top:auto; background:#222; padding:10px; border-radius:5px; height: 100px; overflow-y:auto;">
                <div style="font-size:12px; color:#aaa; margin-bottom:5px;">תיק:</div>
                <div id="inv-wrap" style="font-size:13px;">ריק</div>
            </div>
            <button onclick="send('reset')" style="background:#b33; color:white; border:none; padding:10px; cursor:pointer;">איפוס משחק</button>
        </div>
        
        <!-- MAIN: LOG & CONTROLS -->
        <div class="main">
            <div style="padding:10px; background:#222; text-align:center; font-weight:bold;" id="loc-name">...</div>
            <div class="log" id="log-wrap"></div>
            
            <div class="controls">
                <button class="btn btn-move" onclick="send('move',[0,1])">⬆️<span>צפון</span></button>
                <button class="btn btn-move" onclick="send('move',[0,-1])">⬇️<span>דרום</span></button>
                <button class="btn btn-move" onclick="send('move',[1,0])">➡️<span>מזרח</span></button>
                <button class="btn btn-move" onclick="send('move',[-1,0])">⬅️<span>מערב</span></button>
                
                <button class="btn btn-atk" onclick="send('attack')">⚔️<span>תקוף</span></button>
                <button class="btn" onclick="send('talk')">💬<span>דבר</span></button>
                <button class="btn" onclick="send('take')">✋<span>קח</span></button>
            </div>
        </div>
    </div>

<script>
    document.addEventListener("DOMContentLoaded", () => send("look"));

    async function send(action, val=null) {
        try {
            let res = await fetch('/act', {
                method:'POST', 
                headers:{'Content-Type':'application/json'},
                body:JSON.stringify({a: action, v: val})
            });
            let d = await res.json();
            
            if (d.dead) { alert("Game Over! starting new game."); send("reset"); return; }
            if (d.reload) location.reload();

            // Render Layout
            document.getElementById("hp").innerText = d.stats.hp + "/" + d.stats.max_hp;
            document.getElementById("st").innerText = d.stats.st;
            document.getElementById("gold").innerText = d.stats.gold;
            document.getElementById("lvl").innerText = d.stats.lvl;
            document.getElementById("loc-name").innerText = d.loc;
            document.getElementById("map-wrap").innerHTML = d.hud;
            document.getElementById("inv-wrap").innerText = d.inv.length ? d.inv.join(", ") : "ריק";

            // Logs
            let l = document.getElementById("log-wrap");
            l.innerHTML = "";
            d.log.forEach(item => {
                l.innerHTML += `<div class="msg ${item.type}">${item.text}</div>`;
            });
            l.scrollTop = l.scrollHeight;
            
        } catch(e) { console.error("Error:", e); }
    }
    
    // Keybinds
    document.onkeydown = function(e) {
        let k = e.key;
        if(k=="ArrowUp") send('move',[0,1]);
        if(k=="ArrowDown") send('move',[0,-1]);
        if(k=="ArrowLeft") send('move',[-1,0]);
        if(k=="ArrowRight") send('move',[1,0]);
        if(k==" ") send('attack');
        if(k=="e" || k=="Enter") send('take');
    };
</script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(port=5006, debug=True)
