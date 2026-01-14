import random
import uuid
import math
from flask import Flask, render_template_string, request, jsonify, session, url_for

app = Flask(__name__)
# מפתח חדש לאיפוס
app.secret_key = 'arena_hunter_ai_v10'

# ==========================================
# 🧬 מאגר היצורים המלא
# ==========================================
HOSTS = {
    # חלשים
    "blob":    {"name": "עיסה ירוקה", "icon": "🦠", "hp": 20, "atk": 3},
    "fly":     {"name": "זבוב ענק", "icon": "🪰", "hp": 15, "atk": 2},
    "chicken": {"name": "תרנגול זועם", "icon": "🐓", "hp": 25, "atk": 5},
    
    # בינוניים
    "rat":     {"name": "עכברוש", "icon": "🐀", "hp": 40, "atk": 8},
    "wolf":    {"name": "זאב בלהות", "icon": "🐺", "hp": 70, "atk": 15},
    "guard":   {"name": "שומר ראש", "icon": "👮", "hp": 90, "atk": 18},
    "alien":   {"name": "חייזר אפור", "icon": "👽", "hp": 60, "atk": 20},

    # חזקים
    "bear":    {"name": "דוב גריזלי", "icon": "🐻", "hp": 150, "atk": 25},
    "mech":    {"name": "רובוט קרב", "icon": "🤖", "hp": 130, "atk": 30},
    "tank":    {"name": "טנק חי", "icon": "🚜", "hp": 250, "atk": 15},

    # בוסים
    "dragon":  {"name": "דרקון שחור", "icon": "🐲", "hp": 300, "atk": 50},
    "cthulhu": {"name": "אל הים", "icon": "🦑", "hp": 400, "atk": 55},
    "demon":   {"name": "שטן", "icon": "😈", "hp": 280, "atk": 65}
}

# ==========================================
# ⚙️ מנוע חכם (Smart Engine)
# ==========================================
class Engine:
    def __init__(self, state=None):
        if not state or "rivals" not in state:
            self.state = {
                "x": 0, "y": 0,
                # נתוני שחקן
                "host": "blob",
                "hp": 20, "max_hp": 20,
                "is_dead": False,
                # עולם ובוטים
                "map_bound": 10, # גבולות עולם (-10 עד 10)
                "rivals": [], 
                "map_content": {}, # מפלצות ניטרליות
                "visited": ["0,0"],
                "log": [{"text": "הישרדות: תזוזה בחיצים. אויבים ירדפו אחריך.", "type": "sys"}]
            }
            self.init_world()
        else:
            self.state = state

    def log(self, t, type="game"): 
        self.state["log"].append({"text": t, "type": type})
        if len(self.state["log"]) > 40: self.state["log"].pop(0)

    def init_world(self):
        # יצירת 5 בוטים יריבים
        colors = ["#f55", "#55f", "#fa5", "#f0f", "#0ff"]
        for i in range(5):
            bot = {
                "name": f"יריב #{i+1}",
                "color": colors[i],
                "host": "rat", # מתחילים קצת יותר חזקים
                "hp": 40, "max_hp": 40,
                "x": random.randint(-5, 5),
                "y": random.randint(-5, 5),
                "dead": False
            }
            self.state["rivals"].append(bot)
        
        # יצירת מפלצות במפה
        for x in range(-10, 11):
            for y in range(-10, 11):
                if x==0 and y==0: continue
                # 60% סיכוי למפלצת
                if random.random() < 0.6:
                    self.spawn_monster_at(x, y)

    def spawn_monster_at(self, x, y):
        rng = random.random()
        tier = "fly"
        if rng < 0.4: tier = random.choice(["fly", "chicken", "rat"])
        elif rng < 0.7: tier = random.choice(["wolf", "guard", "alien"])
        elif rng < 0.9: tier = random.choice(["bear", "mech", "tank"])
        else: tier = random.choice(["dragon", "cthulhu", "demon"])
        
        self.state["map_content"][f"{x},{y}"] = {
            "type": tier,
            "hp": HOSTS[tier]["hp"]
        }

    def pos(self): return f"{self.state['x']},{self.state['y']}"

    # --- מנגנון רדיפה (Hunting Logic) ---
    def process_ai(self):
        px, py = self.state["x"], self.state["y"]
        
        # 1. בוטים
        for bot in self.state["rivals"]:
            if bot["dead"]: continue
            
            # אם הבוט נמצא באותו חדר איתך - הוא תוקף מיד
            if bot["x"] == px and bot["y"] == py:
                # הבוט לא יכול לתקוף רוח רפאים
                if not self.state["is_dead"]:
                    dmg = HOSTS[bot["host"]]["atk"]
                    self.state["hp"] -= dmg
                    self.log(f"⚔️ {bot['name']} תקף אותך! (-{dmg})", "danger")
                    if self.state["hp"] <= 0: self.die()
                continue # הבוט עסוק בלתקוף, לא זז

            # אם הבוט קרוב (מרחק 4) - הוא מתקרב אליך! (Hunt Mode)
            dist_x = px - bot["x"]
            dist_y = py - bot["y"]
            
            if abs(dist_x) <= 4 and abs(dist_y) <= 4:
                # זז משבצת אחת לכיוון השחקן
                dx = 1 if dist_x > 0 else (-1 if dist_x < 0 else 0)
                dy = 1 if dist_y > 0 else (-1 if dist_y < 0 else 0)
                bot["x"] += dx
                bot["y"] += dy
                
                # אם בטעות הוא נכנס לחדר עם השחקן עכשיו
                if bot["x"] == px and bot["y"] == py:
                    self.log(f"👀 {bot['name']} רדף אחריך ונכנס לחדר שלך!", "warning")
            else:
                # זז רנדומלית
                bot["x"] += random.choice([-1, 0, 1])
                bot["y"] += random.choice([-1, 0, 1])

            # הבוט נלחם במפלצות בחדר שלו (בצורה מופשטת)
            b_key = f"{bot['x']},{bot['y']}"
            if b_key in self.state["map_content"]:
                # אם הבוט חזק מהמפלצת, הוא מנצח וגונב את הגוף
                mon = self.state["map_content"][b_key]
                bot_str = HOSTS[bot["host"]]["atk"]
                mon_str = HOSTS[mon["type"]]["atk"]
                if bot_str > mon_str or random.random() < 0.2:
                    # שדרוג בוט
                    if HOSTS[mon["type"]]["hp"] > bot["max_hp"]:
                        bot["host"] = mon["type"]
                        bot["max_hp"] = HOSTS[mon["type"]]["hp"]
                        bot["hp"] = bot["max_hp"]
                        self.log(f"⚠️ {bot['name']} השתדרג ל-{HOSTS[mon['type']]['name']}!", "gold")
                        del self.state["map_content"][b_key] # מפלצת נעלמה

        # 2. מפלצות ניטרליות בחדר שלך (תוקפות!)
        current_room_monster = self.state["map_content"].get(self.pos())
        if current_room_monster and not self.state["is_dead"]:
            m_data = HOSTS[current_room_monster["type"]]
            # 80% סיכוי לתקיפה
            if random.random() < 0.8:
                dmg = m_data["atk"]
                self.state["hp"] -= dmg
                self.log(f"🩸 {m_data['name']} פראי תקף אותך! (-{dmg})", "danger")
                if self.state["hp"] <= 0: self.die()

    def die(self):
        self.state["hp"] = 0
        self.state["is_dead"] = True
        self.log("☠️ הגוף שלך מת! הפכת לטפיל רוחני. תפוס גוף חדש מיד!", "critical")

    # --- פעולות שחקן ---
    
    def move(self, dx, dy):
        if self.state["is_dead"]:
            self.log("רוח לא יכולה לעזוב את החדר. תשתלט על מישהו!", "warning")
            return

        # בדיקה אם אפשר לברוח (אם יש מפלצת חזקה, אולי נכשלים בבריחה?)
        # נעשה את זה פשוט בינתיים
        
        self.state["x"] = max(-10, min(10, self.state["x"] + dx))
        self.state["y"] = max(-10, min(10, self.state["y"] + dy))
        
        pos = self.pos()
        if pos not in self.state["visited"]: self.state["visited"].append(pos)
        
        self.process_ai() # תור העולם

    def attack_target(self, type, index):
        if self.state["is_dead"]: return 

        pos = self.pos()
        my_stats = HOSTS[self.state["host"]]
        damage = my_stats["atk"] + random.randint(-2, 2)
        
        killed_something = False

        if type == "monster":
            mon = self.state["map_content"].get(pos)
            if mon:
                mon["hp"] -= damage
                self.log(f"תקפת את המפלצת (-{damage})", "success")
                if mon["hp"] <= 0:
                    self.log("הרגת אותה! עכשיו אפשר לקחת את הגוף (Infect).", "success")
                    killed_something = True # לא מוחקים אותה, משאירים עם 0 חיים להשתלטות

        elif type == "bot":
            rivals = [b for b in self.state["rivals"] if f"{b['x']},{b['y']}" == pos and not b["dead"]]
            if index < len(rivals):
                bot = rivals[index]
                bot["hp"] -= damage
                self.log(f"פגעת ב-{bot['name']} (-{damage})", "success")
                if bot["hp"] <= 0:
                    bot["dead"] = True
                    # הופך למפלצת "גופה" שאפשר להשתלט עליה
                    self.state["map_content"][pos] = {"type": bot["host"], "hp": 0}
                    self.log(f"חיסלת את {bot['name']}! הגופה שלו זמינה.", "gold")
        
        if not killed_something:
            self.process_ai() # העולם מגיב (תקיפה חזרה)

    def infect(self, type, index):
        if not self.state["is_dead"]:
            self.log("חייבים להיות מתים כדי להשתלט.", "sys")
            return

        pos = self.pos()
        target_type = None
        
        # אפשר להשתלט על מפלצת בחדר (גם אם היא חיה או מתה במשחק הזה, הופכים לטפיל פנימי)
        # אבל כדי שיהיה מעניין - נאפשר רק אם HP שלה נמוך? לא, נאפשר תמיד למען הכיף.
        if type == "monster":
            mon = self.state["map_content"].get(pos)
            if mon:
                target_type = mon["type"]
                # המפלצת נעלמת כי אני זה היא
                del self.state["map_content"][pos]

        # או על בוט (אם הוא חי - זה השתלטות עוינת והוא מת)
        elif type == "bot":
            rivals = [b for b in self.state["rivals"] if f"{b['x']},{b['y']}" == pos and not b["dead"]]
            if index < len(rivals):
                bot = rivals[index]
                target_type = bot["host"]
                bot["dead"] = True # הוא מת
        
        if target_type:
            self.state["host"] = target_type
            self.state["max_hp"] = HOSTS[target_type]["hp"]
            self.state["hp"] = self.state["max_hp"]
            self.state["is_dead"] = False
            self.log(f"🧬 נכנסת לגוף של {HOSTS[target_type]['name']}!", "success")
            self.process_ai() # העולם ממשיך לזוז

    def get_ui(self):
        # מיפוי שדה ראייה 5x5
        cx, cy = self.state["x"], self.state["y"]
        grid = []
        radius = 2 # רדיוס 2 נותן גריד 5x5
        
        for dy in range(radius, -radius-1, -1):
            row = []
            for dx in range(-radius, radius+1):
                tx, ty = cx + dx, cy + dy
                k = f"{tx},{ty}"
                cell = {"icon":"⚫", "cls":"fog"}
                
                # בדיקה מה יש במשבצת הזו
                content = self.state["map_content"].get(k)
                bots_here = [b for b in self.state["rivals"] if b["x"]==tx and b["y"]==ty and not b["dead"]]
                
                # עדיפויות לאייקונים
                if dx==0 and dy==0: 
                    cell = {"icon": HOSTS[self.state['host']]['icon'], "cls":"player"}
                elif k in self.state["visited"] or (abs(dx)<=1 and abs(dy)<=1): # רואים גם 1 מסביב בלי לבקר
                    if bots_here:
                        cell = {"icon": "👿", "cls":"danger"}
                    elif content:
                        cell = {"icon": HOSTS[content["type"]]["icon"], "cls":"room-monster"}
                    else:
                        cell = {"icon": "⬜", "cls":"empty"}
                        
                row.append(cell)
            grid.append(row)

        # נתונים על החדר הנוכחי
        pos = self.pos()
        local_mon = self.state["map_content"].get(pos)
        local_bots = [b for b in self.state["rivals"] if f"{b['x']},{b['y']}" == pos and not b["dead"]]
        
        # המרה למידע מלא לתצוגה
        if local_mon: 
            local_mon["data"] = HOSTS[local_mon["type"]]
        
        final_bots = []
        for b in local_bots:
            dat = b.copy()
            dat["meta"] = HOSTS[b["host"]]
            final_bots.append(dat)

        return {
            "me": {
                "stats": HOSTS[self.state["host"]],
                "hp": self.state["hp"],
                "max": self.state["max_hp"],
                "dead": self.state["is_dead"]
            },
            "room": {
                "monster": local_mon,
                "bots": final_bots
            },
            "map": grid,
            "log": self.state["log"]
        }

# ==========================================
# WEB LAYER
# ==========================================
@app.route("/")
def index():
    if "uid" not in session: session["uid"] = str(uuid.uuid4())
    api = url_for("game_loop")
    return render_template_string(HTML, api=api)

@app.route("/update", methods=["POST"])
def game_loop():
    try: eng = Engine(session.get("arena_pro"))
    except: eng = Engine(None)
    
    d = request.json or {}
    act = d.get("a")
    val = d.get("v")
    
    if act == "move": eng.move(*val)
    elif act == "attack": eng.attack_target(*val)
    elif act == "infect": eng.infect(*val)
    elif act == "reset": eng = Engine(None)
    
    session["arena_pro"] = eng.state
    return jsonify(eng.get_ui())

# ==========================================
# UI 
# ==========================================
HTML = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ARENA ULTIMATE</title>
<style>
    body { background: #000; color: #fff; font-family: 'Courier New', monospace; margin: 0; display:flex; height:100vh; overflow:hidden;}
    
    /* Layout: Left (Map & Log), Right (Action) */
    .container { display:flex; width:100%; height:100%; }
    
    .sidebar { width: 40%; border-left: 2px solid #333; display:flex; flex-direction:column; padding:10px; background: #080808;}
    .main-view { width: 60%; padding: 20px; display:flex; flex-direction:column; align-items:center; position:relative; 
        background: radial-gradient(circle, #151515, #000); 
    }
    
    /* RADAR 5x5 */
    .radar-box { width: 100%; aspect-ratio: 1; background: #000; border: 1px solid #444; margin-bottom: 10px; display: flex; flex-direction:column;}
    .r-row { flex:1; display:flex; }
    .r-cell { flex:1; display:flex; align-items:center; justify-content:center; font-size: 20px; border:1px solid #111;}
    .fog { background: #000; color: #222; }
    .player { background: #003300; border:1px solid lime; z-index:2;}
    .room-monster { background: #1a1a1a; color: #aaa; }
    .danger { background: #300; animation: blink 0.5s infinite; }
    .empty { background: #111; }

    /* LOG */
    .logs { flex: 1; overflow-y: auto; font-size: 12px; background: #0a0a0a; padding: 5px; border:1px solid #333;}
    .msg { margin-bottom: 2px; } .danger { color: #f55; } .success { color: #5f5; } .gold { color: gold; }

    /* CARDS */
    .cards-area { flex: 1; width: 100%; display: flex; flex-wrap: wrap; justify-content: center; gap: 10px; align-content: center; }
    
    .card { width: 120px; height: 160px; background: #222; border: 2px solid #444; border-radius: 8px; display:flex; flex-direction:column; align-items:center; padding:5px; justify-content:space-between; transition:0.2s;}
    .card:hover { transform: translateY(-5px); border-color:white;}
    .c-icon { font-size: 40px; }
    .btn { width: 100%; padding: 8px; border:none; cursor:pointer; font-weight:bold; }
    .atk { background: #822; color:white; }
    .inf { background: #282; color:white; animation: glow 1s infinite;}

    /* DEAD OVERLAY */
    .dead-fx { box-shadow: inset 0 0 100px red; }

    /* CONTROLS (D-Pad) - Floating Bottom Right for Main View? Or Keyboard only? */
    .controls-hint { position: absolute; bottom: 10px; right: 10px; color: #555; font-size: 10px; }

    /* Top Bar Me */
    .my-stats { width: 100%; background: #111; padding: 10px; border-bottom: 2px solid #555; display:flex; justify-content:space-between; align-items:center;}
    
    @keyframes blink { 50%{opacity:0.5} }
    @keyframes glow { 50%{background:#4b4} }
</style>
</head>
<body id="bd">

<div class="container">
    
    <div class="sidebar">
        <div style="text-align:center; color:#0f0; margin-bottom:5px;">R.A.D.A.R SYSTEM</div>
        <div class="radar-box" id="map-target"></div>
        <div class="logs" id="log-target"></div>
        <button onclick="s('reset')" style="background:#300; color:#f55; border:1px solid #500; margin-top:5px; cursor:pointer">איפוס מערכת (R)</button>
    </div>

    <div class="main-view">
        <div class="my-stats">
            <div style="font-size:30px;" id="p-icon">🦠</div>
            <div style="flex:1; margin:0 10px;">
                <div id="p-name" style="font-weight:bold; color: gold;">טוען...</div>
                <div style="background:#333; height:10px; width:100%"><div id="hp-bar" style="background:#f33; height:100%; width:50%"></div></div>
                <small id="hp-text">0/0</small>
            </div>
        </div>

        <div class="cards-area" id="scene">
            <!-- Cards go here -->
        </div>
        
        <div class="controls-hint">תנועה: חצים / WASD</div>
    </div>

</div>

<script>
    const API = "{{ api }}";
    
    window.onload = ()=> s('init');

    async function s(act, val=null){
        let res = await fetch(API, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({a:act, v:val})});
        let d = await res.json();
        
        // Me
        document.getElementById("p-icon").innerText = d.me.stats.icon;
        document.getElementById("p-name").innerText = d.me.dead ? "גוסס..." : d.me.stats.name;
        let pct = (d.me.hp / d.me.max) * 100;
        document.getElementById("hp-bar").style.width = pct + "%";
        document.getElementById("hp-text").innerText = d.me.hp + " / " + d.me.max;
        
        if(d.me.dead) document.getElementById("bd").classList.add("dead-fx");
        else document.getElementById("bd").classList.remove("dead-fx");

        // Map
        let mh = "";
        d.map.forEach(r => {
            mh += "<div class='r-row'>";
            r.forEach(c => mh += `<div class='r-cell ${c.cls}'>${c.icon}</div>`);
            mh += "</div>";
        });
        document.getElementById("map-target").innerHTML = mh;

        // Scene (Cards)
        let sh = "";
        
        // Monster?
        if(d.room.monster){
            let m = d.room.monster;
            let m_dat = m.data;
            // אם אני מת - הכפתור הוא 'השתלטות'
            let btn = d.me.dead ? 
                `<button class="btn inf" onclick="s('infect',['monster',0])">🧬 עבור גוף</button>` :
                `<button class="btn atk" onclick="s('attack',['monster',0])">⚔️ תקיפה</button>`;
            
            sh += createCard(m_dat.icon, m_dat.name, m.hp + " HP", btn);
        }
        
        // Bots?
        d.room.bots.forEach((b, i) => {
            let m = b.meta;
            let btn = d.me.dead ? 
                `<button class="btn inf" onclick="s('infect',['bot',${i}])">🧬 גנוב!</button>` :
                `<button class="btn atk" onclick="s('attack',['bot',${i}])">⚔️ קרב</button>`;
                
            sh += createCard("🤖", b.bot_name, `[${m.name}] ${b.hp} HP`, btn, "border-color:red;");
        });
        
        if (sh == "") sh = "<div style='color:#555'>החדר ריק... היזהר מהאויבים</div>";
        document.getElementById("scene").innerHTML = sh;

        // Logs
        let lh = "";
        d.log.slice().reverse().forEach(l => {
            lh += `<div class='msg ${l.type}'>${l.text}</div>`;
        });
        document.getElementById("log-target").innerHTML = lh;
    }

    function createCard(icon, title, sub, btn, style="") {
        return `
        <div class="card" style="${style}">
            <div class="c-icon">${icon}</div>
            <strong>${title}</strong>
            <small>${sub}</small>
            ${btn}
        </div>`;
    }

    // Keybinds
    window.addEventListener('keydown', (e) => {
        let k = e.key;
        if(k=="ArrowUp" || k=="w") s('move',[0,1]);
        if(k=="ArrowDown" || k=="s") s('move',[0,-1]);
        if(k=="ArrowLeft" || k=="a") s('move',[-1,0]);
        if(k=="ArrowRight" || k=="d") s('move',[1,0]);
        if(k=="r") s('reset');
    });
</script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(port=5006, debug=True)
