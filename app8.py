import random
import uuid
from flask import Flask, render_template_string, request, jsonify, session, url_for

app = Flask(__name__)
app.secret_key = 'parasite_game_v1'

# ==========================================
# 🧬 מאגר גופים (Hosts)
# ==========================================
# לכל גוף יש יכולות שונות. המטרה: להחליף גופים בהתאם למכשול.
HOSTS_DB = {
    "blob": {"name": "עיסה ירוקה", "icon": "🦠", "max_hp": 10, "atk": 1, "desc": "צורת הבסיס. חלש מאוד."},
    "rat": {"name": "עכברוש", "icon": "🐀", "max_hp": 15, "atk": 2, "desc": "מהיר, יכול לעבור בתעלות."},
    "guard": {"name": "שומר אנושי", "icon": "👮", "max_hp": 50, "atk": 10, "desc": "יכול להשתמש בנשק חם."},
    "beast": {"name": "מפלצת ביוב", "icon": "👹", "max_hp": 100, "atk": 20, "desc": "חזק בטירוף, אבל איטי."},
    "robot": {"name": "רובוט סיור", "icon": "🤖", "max_hp": 40, "atk": 8, "desc": "חסין לרעל, לא נושם."},
    "boss": {"name": "המפקד העליון", "icon": "😎", "max_hp": 200, "atk": 30, "desc": "המטרה הסופית."}
}

# ==========================================
# 🧠 מנוע המשחק
# ==========================================
class Engine:
    def __init__(self, state=None):
        if not state:
            self.state = {
                # נתונים של הטפיל (השחקן)
                "host": "blob", # הגוף הנוכחי
                "hp": 10,
                "x": 0, "y": 0,
                "kills": 0,
                "is_dead": False, # האם הגוף הנוכחי מת?
                
                # עולם
                "map": {},
                "visited": ["0,0"],
                "log": [{"text": "התעוררת כעיסה ירוקה. מצא גוף מארח מהר!", "type": "sys"}]
            }
            # יצירת חדר ראשון עם עכברוש (כדי שיהיה על מי להשתלט)
            self.create_room(0, 0, force_type="rat")
        else:
            self.state = state

    def pos(self): return f"{self.state['x']},{self.state['y']}"
    
    def log(self, txt, t="game"): 
        # שומר רק 30 הודעות אחרונות
        self.state["log"].append({"text": txt, "type": t})
        if len(self.state["log"]) > 30: self.state["log"].pop(0)

    # יצירת חדר עם אויבים שונים (שיהפכו לגופים פוטנציאליים)
    def create_room(self, x, y, force_type=None):
        k = f"{x},{y}"
        if k in self.state["map"]: return

        enemies = []
        # בחדר רגיל יש סיכוי לגוף חדש
        if force_type:
            types = [force_type]
        else:
            # בוחרים אויבים רנדומליים, אבל לא הבוס מיד
            opts = ["rat", "rat", "guard", "robot", "beast"]
            count = random.randint(1, 2)
            types = [random.choice(opts) for _ in range(count)]

        for t in types:
            data = HOSTS_DB[t]
            enemies.append({
                "type": t,
                "name": data["name"],
                "icon": data["icon"],
                "hp": data["max_hp"],
                "max_hp": data["max_hp"],
                "atk": data["atk"]
            })

        self.state["map"][k] = {
            "enemies": enemies,
            "items": []
        }

    def move(self, dx, dy):
        # אי אפשר לזוז אם אתה "רוח רפאים" (גוף מת)
        if self.state["is_dead"]:
            self.log("הגוף שלך מושמד! אתה חייב להשתלט על גוף חדש כדי לזוז.", "danger")
            return

        self.state["x"] += dx
        self.state["y"] += dy
        k = self.pos()
        
        if k not in self.state["map"]:
            self.create_room(self.state["x"], self.state["y"])
        
        self.state["visited"].append(k)
        
        enemies = self.state["map"][k]["enemies"]
        names = [e["name"] for e in enemies]
        
        msg = f"הגעת לחדר ({self.state['x']}, {self.state['y']})."
        if names: msg += f" יש כאן: {', '.join(names)}."
        self.log(msg, "game")

    def attack(self, target_idx):
        if self.state["is_dead"]: return # אי אפשר לתקוף כרוח

        r = self.state["map"][self.pos()]
        if not r["enemies"] or target_idx >= len(r["enemies"]):
            self.log("אין את מי לתקוף.", "sys")
            return

        enemy = r["enemies"][target_idx]
        current_host = HOSTS_DB[self.state["host"]]
        
        # התקפת השחקן
        dmg = current_host["atk"] + random.randint(-2, 2)
        enemy["hp"] -= dmg
        self.log(f"תקפת את {enemy['name']} ({dmg} נזק).", "success")

        # אם האויב מת - הוא נעלם (אי אפשר להשתלט על גופה גמורה, אלא אם זה היה מנגנון אחר)
        if enemy["hp"] <= 0:
            self.log(f"הרגת את ה{enemy['name']}. הגופה שלו נהרסה ולא שימושית יותר.", "info")
            r["enemies"].pop(target_idx)
            self.state["kills"] += 1
            return

        # אויב מחזיר מלחמה
        e_dmg = enemy["atk"] + random.randint(-1, 3)
        self.state["hp"] -= e_dmg
        
        if self.state["hp"] <= 0:
            self.state["hp"] = 0
            self.state["is_dead"] = True
            self.log("🚨 הגוף המארח הושמד! אתה במצב טפיל חופשי!", "critical")
            self.log("בחר גוף חדש בחדר כדי להשתלט עליו (INFECT)!", "critical")
        else:
            self.log(f"{enemy['name']} תקף חזרה! ירדו {e_dmg} חיים.", "danger")

    # === המכניקה החדשה: השתלטות (Parasite Jump) ===
    def infect(self, target_idx):
        # אפשר להשתלט רק אם אתה "מת" (בלי גוף), או בתור מהלך מיוחד (אופציונלי)
        if not self.state["is_dead"]:
            self.log("אתה כבר בתוך גוף! (צריך שהגוף ימות כדי לעבור)", "sys")
            return

        r = self.state["map"][self.pos()]
        if not r["enemies"]:
            self.log("אין גופים בחדר! הטפיל מת מחוסר חמצן... (Game Over סופי)", "critical")
            # כאן זה באמת גיים אובר כי אין לאן לקפוץ
            return "real_death"

        # לוקחים את האויב
        target = r["enemies"][target_idx]
        
        # מעבירים את הנתונים שלו לשחקן
        self.state["host"] = target["type"]
        self.state["hp"] = target["hp"] # מקבלים את החיים שנשארו לו
        
        # מסירים אותו מרשימת האויבים (כי הוא עכשיו השחקן)
        old_name = target["name"]
        r["enemies"].pop(target_idx)
        
        self.state["is_dead"] = False
        self.log(f"🧬 השתלטות מוצלחת! אתה עכשיו {old_name}.", "bio")
        self.log(f"יכולות חדשות: {HOSTS_DB[self.state['host']]['desc']}", "info")

# ==========================================
# שרת
# ==========================================
@app.route("/")
def index():
    if "uid" not in session: session["uid"] = str(uuid.uuid4())
    api = url_for("update")
    return render_template_string(UI, api=api)

@app.route("/api", methods=["POST"])
def api():
    d = request.json
    try:
        eng = Engine(session.get("game_p"))
    except:
        eng = Engine(None)

    act = d.get("a")
    val = d.get("v") # במקרה של תקיפה/הדבקה זה האינדקס של האויב

    if act == "reset": 
        eng = Engine(None)
    elif act == "move": 
        eng.move(*val)
    elif act == "attack": 
        eng.attack(val)
    elif act == "infect": 
        res = eng.infect(val)
        if res == "real_death":
            return jsonify({"game_over": True})

    session["game_p"] = eng.state
    
    # נתונים לרינדור
    room = eng.state["map"][eng.pos()]
    host_data = HOSTS_DB[eng.state["host"]]
    
    return jsonify({
        "log": eng.state["log"],
        "enemies": room["enemies"], # רשימת האויבים הנוכחית
        "player": {
            "hp": eng.state["hp"],
            "max": host_data["max_hp"],
            "name": host_data["name"],
            "icon": host_data["icon"],
            "is_dead": eng.state["is_dead"] # הנתון הקריטי לממשק
        },
        "pos": eng.pos()
    })

# ==========================================
# UI - מותאם למצב טפיל
# ==========================================
UI = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>PARASITE: ZERO</title>
<style>
    body { background: #0f1208; color: #ccffaa; font-family: monospace; margin: 0; height: 100vh; display:flex; flex-direction:column; }
    
    /* BIO UI Style */
    .bio-bar { 
        background: #1a2210; padding: 10px; border-bottom: 2px solid #5f9ea0; 
        display: flex; justify-content: space-between; align-items: center;
        box-shadow: 0 0 15px rgba(95, 158, 160, 0.3);
    }
    .bio-heart { color: #f00; font-size: 24px; animation: beat 1s infinite; display:inline-block;}
    .bio-ghost { color: #888; font-size: 24px; animation: float 2s infinite; }
    
    .screen-danger { 
        border: 4px solid red; box-shadow: inset 0 0 50px red;
    }

    .main-view { flex: 1; display: grid; grid-template-rows: 1fr 1fr; gap: 10px; padding: 10px; overflow:hidden;}
    
    /* Enemy list as visual cards */
    .scene-view { 
        border: 1px solid #344; background: #0a0e05; padding: 10px; border-radius: 8px;
        display: flex; gap: 10px; align-items: center; justify-content: center; flex-wrap: wrap; overflow-y:auto;
    }
    
    /* Enemies look different if you are dead (they become Hosts) */
    .enemy-card { 
        width: 100px; height: 120px; background: #222; border: 1px solid #555; 
        display: flex; flex-direction: column; align-items: center; justify-content: space-around;
        cursor: pointer; transition: 0.2s; position:relative;
    }
    .enemy-card:hover { transform: scale(1.05); border-color: white;}
    
    /* כפתור על האויב משתנה לפי המצב */
    .action-btn { 
        width: 100%; border: none; padding: 5px; color: white; cursor: pointer; font-weight: bold;
    }
    .btn-attack { background: #822; }
    .btn-infect { background: #282; animation: glow 0.8s infinite alternate;} /* כשמתים זה זוהר בירוק */

    /* LOG */
    .log-view { 
        border: 1px solid #344; background: #000; padding: 10px; overflow-y: auto; font-size: 14px;
        font-family: 'Courier New', Courier, monospace;
    }
    .msg { margin-bottom: 4px; }
    .msg.sys { color: #5ff; }
    .msg.critical { color: yellow; background: #500; font-weight:bold; padding: 5px; border: 1px dashed red;}
    .msg.bio { color: #0f0; }
    .msg.danger { color: #f55; }

    /* CONTROLS */
    .controls { padding: 10px; background: #111; display: flex; gap: 10px; justify-content: center; }
    .nav-btn { font-size: 24px; padding: 15px; width: 60px; background: #223; color: white; border: 1px solid #445; border-radius: 8px; cursor: pointer;}
    .nav-btn:disabled { opacity: 0.3; cursor: not-allowed; }

    @keyframes beat { 0%{transform:scale(1);} 50%{transform:scale(1.2);} 100%{transform:scale(1);} }
    @keyframes glow { from{background: #282;} to{background: #4f4;} }
</style>
</head>
<body id="bodybox">

<div class="bio-bar">
    <div>
        <span id="player-icon" style="font-size:30px">🦠</span>
        <span id="player-name" style="font-size:18px; font-weight:bold;">טפיל</span>
    </div>
    <div style="font-size:12px; color:#aaa;">חדר <span id="pos">0,0</span></div>
    <div>
        <span id="hp-text">10/10</span>
        <span id="heart-anim" class="bio-heart">❤</span>
    </div>
</div>

<div class="main-view">
    <div class="scene-view" id="scene-container">
        <!-- Enemies Render Here -->
        <div style="color:#555">אין גופים בסביבה...</div>
    </div>
    
    <div class="log-view" id="log-container"></div>
</div>

<div class="controls">
    <button class="nav-btn" onclick="act('move', [0,1])" id="btn-u">⬆️</button>
    <button class="nav-btn" onclick="act('move', [1,0])" id="btn-r">➡️</button>
    <button class="nav-btn" onclick="act('move', [0,-1])" id="btn-d">⬇️</button>
    <button class="nav-btn" onclick="act('move', [-1,0])" id="btn-l">⬅️</button>
</div>

<script>
    const API = "{{ api }}";
    
    window.onload = () => act('init');

    async function act(a, v=null) {
        let res = await fetch(API, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({a:a, v:v})});
        let d = await res.json();
        
        if(d.game_over) { alert("לא היו גופות בחדר! מתת סופית."); act('reset'); return;}

        // 1. Player Status Logic
        let p = d.player;
        document.getElementById("player-icon").innerText = p.icon;
        document.getElementById("player-name").innerText = p.name;
        document.getElementById("hp-text").innerText = p.hp + "/" + p.max;
        document.getElementById("pos").innerText = d.pos;
        
        // Critical State: אם מתים - המסך אדום והכפתורים למטה ננעלים
        let body = document.getElementById("bodybox");
        let btns = document.querySelectorAll(".nav-btn");
        let heart = document.getElementById("heart-anim");
        
        if (p.is_dead) {
            body.classList.add("screen-danger");
            heart.className = "bio-ghost"; // אייקון משתנה לרוח
            heart.innerText = "👻";
            btns.forEach(b => b.disabled = true); // אי אפשר ללכת
        } else {
            body.classList.remove("screen-danger");
            heart.className = "bio-heart";
            heart.innerText = "❤";
            btns.forEach(b => b.disabled = false);
        }

        // 2. Render Enemies (Scene)
        let sc = document.getElementById("scene-container");
        sc.innerHTML = "";
        
        if(d.enemies.length === 0) {
            sc.innerHTML = "<div style='color:#555'>החדר ריק... נוע לחדר הבא.</div>";
        } else {
            d.enemies.forEach((e, idx) => {
                let card = document.createElement("div");
                card.className = "enemy-card";
                
                // ההחלטה החשובה: אם השחקן מת - הכפתור הוא "הדבקה", אחרת "תקיפה"
                let btnHtml = "";
                if (p.is_dead) {
                    btnHtml = `<button class='action-btn btn-infect' onclick='act("infect", ${idx})'>🧬 פלוש!</button>`;
                } else {
                    btnHtml = `<button class='action-btn btn-attack' onclick='act("attack", ${idx})'>⚔️ תקוף</button>`;
                }
                
                card.innerHTML = `
                    <div style='font-size:30px; margin-top:10px;'>${e.icon}</div>
                    <div style='font-size:12px; font-weight:bold'>${e.name}</div>
                    <div style='color:#f55; font-size:11px'>${e.hp}/${e.max_hp}</div>
                    ${btnHtml}
                `;
                sc.appendChild(card);
            });
        }

        // 3. Log
        let lb = document.getElementById("log-container");
        lb.innerHTML = "";
        d.log.reverse().forEach(l => {
            lb.innerHTML += `<div class='msg ${l.type}'>${l.text}</div>`;
        });
    }
</script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(port=5006, debug=True)
