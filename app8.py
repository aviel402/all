import random
import uuid
from flask import Flask, render_template_string, request, jsonify, session, url_for

app = Flask(__name__)
app.secret_key = 'parasite_royale_final_v12'

# ==========================================
# 🧬 מאגר גופים
# ==========================================
HOSTS = {
    # חלשים (דרגה 1)
    "blob":    {"name": "עיסה ירוקה", "icon": "🦠", "hp": 20, "atk": 2},
    "rat":     {"name": "עכברוש", "icon": "🐀", "hp": 30, "atk": 5},
    "drone":   {"name": "רחפן ריגול", "icon": "🛸", "hp": 25, "atk": 4},
    
    # לוחמים (דרגה 2)
    "wolf":    {"name": "זאב", "icon": "🐺", "hp": 60, "atk": 12},
    "soldier": {"name": "חייל עוין", "icon": "👮", "hp": 80, "atk": 15},
    "alien":   {"name": "חייזר לוחם", "icon": "👽", "hp": 70, "atk": 18},

    # חזקים (דרגה 3)
    "robot":   {"name": "רובוט משוריין", "icon": "🤖", "hp": 150, "atk": 20},
    "beast":   {"name": "מפלצת ביוב", "icon": "👹", "hp": 180, "atk": 25},
    "dragon":  {"name": "דרקון זירה", "icon": "🐲", "hp": 300, "atk": 45}
}

class Engine:
    def __init__(self, state=None):
        if not state or "rivals" not in state:
            self.state = {
                "x": 0, "y": 0,
                # סטטוס שחקן
                "host": "blob",
                "hp": 20, "max_hp": 20,
                "is_dead": False,
                # נתוני זירה
                "map_size": 5, # רדיוס 5 = מפה 10x10 (-5 עד 5)
                "rivals": [], 
                "map_content": {}, # מפלצות וגופות בחדרים
                "visited": ["0,0"],
                "log": [{"text": "ברוך הבא לזירה 10x10. השמד את כל המתחרים.", "type": "sys"}]
            }
            self.init_arena()
        else:
            self.state = state

    def log(self, t, type="game"): 
        self.state["log"].append({"text": t, "type": type})
        if len(self.state["log"]) > 40: self.state["log"].pop(0)

    def init_arena(self):
        # יצירת 4 בוטים יריבים מפוזרים
        names = ["נמסיס", "אלפא", "אומגה", "צללית"]
        for n in names:
            bot = {
                "name": n,
                "host": "rat", # כולם מתחילים חלשים
                "hp": 30, "max_hp": 30,
                "x": random.randint(-4, 4),
                "y": random.randint(-4, 4),
                "dead": False
            }
            self.state["rivals"].append(bot)
        
        # מילוי הזירה במפלצות
        for x in range(-5, 6):
            for y in range(-5, 6):
                if x==0 and y==0: continue # התחלה נקייה
                
                # 70% סיכוי למשהו בחדר
                if random.random() < 0.7:
                    rng = random.random()
                    tier = "rat"
                    if rng < 0.5: tier = random.choice(["rat", "drone"])
                    elif rng < 0.8: tier = random.choice(["wolf", "soldier", "alien"])
                    elif rng < 0.95: tier = random.choice(["robot", "beast"])
                    else: tier = "dragon" # נדיר מאוד
                    
                    self.state["map_content"][f"{x},{y}"] = {
                        "type": tier,
                        "hp": HOSTS[tier]["hp"],
                        "alive": True # האם המפלצת חיה או גופה
                    }

    def pos(self): return f"{self.state['x']},{self.state['y']}"

    # === מערכת AI משופרת (בוטים ומפלצות) ===
    def process_ai(self):
        px, py = self.state["x"], self.state["y"]
        pos_key = self.pos()

        # 1. תור הבוטים
        for bot in self.state["rivals"]:
            if bot["dead"]: continue
            
            # אם הבוט באותו חדר איתי
            if bot["x"] == px and bot["y"] == py:
                # הבוט לא תוקף אם הוא מת (מן הסתם) וגם לא תוקף אותך אם אתה רוח
                if not self.state["is_dead"]:
                    dmg = HOSTS[bot["host"]]["atk"]
                    self.state["hp"] -= dmg
                    self.log(f"⚠️ {bot['name']} בחדר ותוקף אותך! (-{dmg})", "danger")
            
            else:
                # לוגיקת תנועה של בוט
                # בודקים אם יש בוט אחר או מפלצת בחדר הנוכחי שלו
                bot_pos = f"{bot['x']},{bot['y']}"
                local_mon = self.state["map_content"].get(bot_pos)
                
                # אם יש מפלצת והיא חיה, הבוט נלחם בה
                if local_mon and local_mon["alive"]:
                    mon_dmg = HOSTS[local_mon["type"]]["atk"]
                    bot_dmg = HOSTS[bot["host"]]["atk"]
                    
                    # הבוט חוטף מכה
                    bot["hp"] -= mon_dmg
                    
                    # המפלצת חוטפת (סימולציה)
                    # אם הבוט חזק, הוא מנצח ומשדרג גוף
                    if bot["hp"] > 0 and (bot_dmg > mon_dmg or random.random() < 0.2):
                        # הבוט ניצח
                        local_mon["alive"] = False # מפלצת מתה
                        # שדרוג אם הגוף טוב יותר
                        if HOSTS[local_mon["type"]]["hp"] > bot["max_hp"]:
                            bot["host"] = local_mon["type"]
                            bot["max_hp"] = HOSTS[local_mon["type"]]["hp"]
                            bot["hp"] = bot["max_hp"]
                            # ההודעה מופיעה רק אם אתה קרוב
                            if abs(bot['x']-px) < 3 and abs(bot['y']-py) < 3:
                                self.log(f"שמעת צרחה... {bot['name']} שדרג גוף!", "warning")
                    
                    if bot["hp"] <= 0:
                        bot["dead"] = True # הבוט מת בקרב PvE
                        self.log(f"🎉 {bot['name']} מת איפשהו בזירה.", "gold")

                else:
                    # הבוט זז
                    # אם השחקן קרוב (טווח 3), רודף אחריו. אחרת רנדומלי.
                    dx, dy = 0, 0
                    dist = abs(bot["x"] - px) + abs(bot["y"] - py)
                    
                    if dist <= 3 and not self.state["is_dead"]: # ציד
                        dx = 1 if bot["x"] < px else (-1 if bot["x"] > px else 0)
                        dy = 1 if bot["y"] < py else (-1 if bot["y"] > py else 0)
                    else: # שוטטות
                        dx = random.choice([-1, 0, 1])
                        dy = random.choice([-1, 0, 1])
                    
                    # וידוא גבולות מפה 5+-
                    bot["x"] = max(-5, min(5, bot["x"] + dx))
                    bot["y"] = max(-5, min(5, bot["y"] + dy))

        # 2. מפלצות חיות בחדר שלי תוקפות
        my_room_mon = self.state["map_content"].get(pos_key)
        if my_room_mon and my_room_mon["alive"] and not self.state["is_dead"]:
            m_dat = HOSTS[my_room_mon["type"]]
            # תוקפות חזרה תמיד
            self.state["hp"] -= m_dat["atk"]
            self.log(f"🩸 {m_dat['name']} נשך אותך (-{m_dat['atk']})", "danger")

        # בדיקת מוות שלי בסוף התור
        if self.state["hp"] <= 0 and not self.state["is_dead"]:
            self.state["hp"] = 0
            self.state["is_dead"] = True
            self.log("☠️ מתת! הגוף נהרס. השתלט על מישהו או הפסד.", "critical")

    # === פעולות ===
    
    def move(self, dx, dy):
        if self.state["is_dead"]:
            self.log("רוחות לא יכולות לעזוב את החדר. תשתלט!", "sys")
            return

        nx = self.state["x"] + dx
        ny = self.state["y"] + dy
        
        # גבולות מפה (קירות)
        if nx < -5 or nx > 5 or ny < -5 or ny > 5:
            self.log("🚧 הגעת לקיר החיצוני של הזירה.", "sys")
            return

        self.state["x"] = nx
        self.state["y"] = ny
        
        pos = self.pos()
        if pos not in self.state["visited"]: self.state["visited"].append(pos)
        
        self.process_ai() # תור העולם

    def attack(self, target_type, idx):
        if self.state["is_dead"]: return # לא תוקפים כמתים

        pos = self.pos()
        my_stats = HOSTS[self.state["host"]]
        my_dmg = my_stats["atk"] + random.randint(0, 3)
        hit = False

        # תקיפת מפלצת
        if target_type == "monster":
            mon = self.state["map_content"].get(pos)
            if mon and mon["alive"]:
                mon["hp"] -= my_dmg
                self.log(f"פגעת במפלצת ({my_dmg}).", "success")
                if mon["hp"] <= 0:
                    mon["alive"] = False
                    mon["hp"] = 0
                    self.log("הרגת אותה! הגופה זמינה להשתלטות.", "gold")
                hit = True

        # תקיפת בוט
        elif target_type == "bot":
            # מוצאים את הבוט הספציפי ברשימה הכללית
            active_bots = [b for b in self.state["rivals"] if f"{b['x']},{b['y']}"==pos and not b["dead"]]
            if idx < len(active_bots):
                bot = active_bots[idx]
                bot["hp"] -= my_dmg
                self.log(f"תקפת את {bot['name']} (-{my_dmg})", "success")
                if bot["hp"] <= 0:
                    bot["dead"] = True
                    # משאירים גופה
                    self.state["map_content"][pos] = {"type": bot["host"], "hp": 0, "alive": False}
                    self.log(f"🏆 חיסלת את {bot['name']}!", "gold")
                hit = True

        # אם תקפנו - העולם מגיב (מי ששרד תוקף חזרה)
        if hit:
            self.process_ai()

    def infect(self, target_type, idx):
        # השתלטות - מותרת רק למתים
        if not self.state["is_dead"]:
            self.log("חייב להיות רוח כדי להשתלט.", "sys")
            return

        pos = self.pos()
        new_type = None
        
        # השתלטות על מפלצת (חיה או מתה - הטפיל נכנס פנימה)
        if target_type == "monster":
            mon = self.state["map_content"].get(pos)
            if mon:
                new_type = mon["type"]
                # מוחקים מהמפה כי היא הופכת לשחקן
                del self.state["map_content"][pos]

        # השתלטות על בוט (הופך אותו למת אם הוא לא היה, ולוקח גוף)
        elif target_type == "bot":
            active_bots = [b for b in self.state["rivals"] if f"{b['x']},{b['y']}"==pos and not b["dead"]]
            if idx < len(active_bots):
                bot = active_bots[idx]
                new_type = bot["host"]
                bot["dead"] = True
                self.log(f"הוצאת את הנשמה ל-{bot['name']} ולקחת לו את הגוף!", "gold")

        if new_type:
            self.state["host"] = new_type
            self.state["max_hp"] = HOSTS[new_type]["hp"]
            self.state["hp"] = self.state["max_hp"] # ריפוי מלא בגוף חדש
            self.state["is_dead"] = False
            self.log(f"🧬 קמת לתחייה בתור {HOSTS[new_type]['name']}!", "success")
            
            # בוטים יגיבו לשינוי בתור הבא, לא מיידית

    def get_ui(self):
        pos = self.pos()
        
        # 1. מידע מפה (רדאר 7x7 לרדיוס 3)
        grid = []
        radius = 3 
        cx, cy = self.state["x"], self.state["y"]
        
        for dy in range(radius, -radius-1, -1):
            row = []
            for dx in range(-radius, radius+1):
                tx, ty = cx + dx, cy + dy
                k = f"{tx},{ty}"
                cell = {"txt":"⬛", "cls":"fog"}
                
                # גבולות מפה
                if tx < -5 or tx > 5 or ty < -5 or ty > 5:
                    cell = {"txt":"🚫", "cls":"wall"}
                elif dx==0 and dy==0:
                    cell = {"txt": "😊", "cls":"me"} # שחקן
                elif k in self.state["visited"] or (abs(dx)<=1 and abs(dy)<=1):
                    # תוכן תא
                    cont = self.state["map_content"].get(k)
                    bots_here = [b for b in self.state["rivals"] if b["x"]==tx and b["y"]==ty and not b["dead"]]
                    
                    if bots_here: cell = {"txt":"🤖", "cls":"rival"}
                    elif cont: 
                        icon = HOSTS[cont["type"]]["icon"]
                        cls = "alive" if cont["alive"] else "dead_body"
                        cell = {"txt": icon, "cls": cls}
                    else: cell = {"txt":"⬜", "cls":"empty"}
                        
                row.append(cell)
            grid.append(row)

        # 2. אויבים בחדר
        room_mon = self.state["map_content"].get(pos)
        room_bots = [b for b in self.state["rivals"] if f"{b['x']},{b['y']}"==pos and not b["dead"]]
        
        # בדיקת ניצחון (האם כל הבוטים מתים?)
        live_bots = len([b for b in self.state["rivals"] if not b["dead"]])
        victory = (live_bots == 0)

        # עיבוד מידע ל-JS
        scene_objects = []
        
        if room_mon:
            scene_objects.append({
                "type": "monster", "idx": 0, 
                "name": HOSTS[room_mon["type"]]["name"],
                "icon": HOSTS[room_mon["type"]]["icon"],
                "hp": room_mon["hp"],
                "is_corpse": not room_mon["alive"]
            })
            
        for i, b in enumerate(room_bots):
            scene_objects.append({
                "type": "bot", "idx": i,
                "name": f"{b['name']} ({HOSTS[b['host']]['name']})",
                "icon": HOSTS[b["host"]]["icon"],
                "hp": b["hp"],
                "is_corpse": False
            })

        return {
            "map": grid,
            "log": self.state["log"],
            "scene": scene_objects,
            "player": {
                "name": HOSTS[self.state["host"]]["name"],
                "icon": HOSTS[self.state["host"]]["icon"],
                "hp": self.state["hp"], "max": self.state["max_hp"],
                "dead": self.state["is_dead"],
                "bots_left": live_bots,
                "won": victory
            }
        }

# ==========================================
# SERVER
# ==========================================
@app.route("/")
def index():
    if "uid" not in session: session["uid"] = str(uuid.uuid4())
    api = url_for("update")
    return render_template_string(HTML, api=api)

@app.route("/api", methods=["POST"])
def update():
    try: eng = Engine(session.get("br_save"))
    except: eng = Engine(None)
    
    d = request.json or {}
    act = d.get("a")
    val = d.get("v")
    
    if act=="reset": eng = Engine(None)
    elif act=="move": eng.move(*val)
    elif act=="attack": eng.attack(*val)
    elif act=="infect": eng.infect(*val)
    
    session["br_save"] = eng.state
    return jsonify(eng.get_ui())

# ==========================================
# HTML UI
# ==========================================
HTML = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>PARASITE ROYALE</title>
<style>
    body { background: #111; color: #ccc; margin:0; font-family: monospace; display:flex; flex-direction:column; height:100vh; overflow:hidden;}
    
    /* Top: Info */
    .header { background: #222; padding: 10px; display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #444;}
    .stat { border:1px solid #555; padding:5px 10px; border-radius:5px; background:#000; font-size:12px;}
    .rivals-count { color: #f55; font-weight:bold; animation: pulse 2s infinite; }

    /* Main Area: Split Screen */
    .content { flex:1; display:flex; height: 100%;}
    
    /* Radar Left */
    .radar-box { width: 40%; background: #050505; display:flex; flex-direction:column; justify-content:center; align-items:center; border-left:1px solid #333; padding:10px;}
    .radar-grid { display:grid; grid-template-rows:repeat(7, 1fr); gap:1px; background:#222; width:100%; aspect-ratio:1; max-width:300px; border:2px solid #0f0;}
    .r-row { display:grid; grid-template-columns:repeat(7, 1fr); gap:1px; }
    .cell { display:flex; align-items:center; justify-content:center; font-size:16px; background:#000;}
    
    .fog { background:#000; }
    .wall { background:#330000; color:red; font-size:10px;}
    .empty { background:#111; }
    .room-monster { color:#aaa; background:#1a1a1a; }
    .me { background:#0f0; box-shadow:0 0 10px lime; z-index:2;}
    .danger { background:red; color:yellow; font-weight:bold; }
    .alive { color: white; }
    .dead_body { color: #555; text-decoration: line-through;}

    /* Scene Right */
    .scene-box { flex:1; display:flex; flex-direction:column; padding:10px; background:#151515;}
    .enemies-list { flex:1; overflow-y:auto; display:flex; flex-wrap:wrap; gap:10px; align-content: flex-start;}
    .card { width:100px; height:130px; background:#222; border:1px solid #444; border-radius:6px; padding:5px; text-align:center; display:flex; flex-direction:column; justify-content:space-between;}
    .dead-card { border-color:#555; opacity:0.7; filter: grayscale(100%); }
    .live-card { border-color:#f55; }
    
    /* Log Bottom */
    .log-container { height: 100px; background:#000; border-top:1px solid #444; padding:5px; font-size:12px; overflow-y:auto;}
    .msg { border-bottom:1px solid #111; padding:2px;} .success { color:#afa; } .critical{color:red;font-weight:bold;}

    /* Controls */
    .controls { height: 120px; background:#222; border-top:2px solid #444; display:grid; grid-template-columns: 2fr 1fr; align-items:center;}
    .d-pad { display:grid; grid-template-columns:repeat(3, 1fr); gap:5px; width:120px; direction:ltr; margin:0 auto;}
    .btn { background:#333; border:1px solid #555; color:white; border-radius:5px; height:35px; cursor:pointer; font-size:18px;}
    .btn:active{ background:#555;}
    
    .u{grid-column:2} .l{grid-column:1; grid-row:2} .d{grid-column:2; grid-row:2} .r{grid-column:3; grid-row:2}
    
    .overlay { position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.8); z-index:99; display:none; flex-direction:column; justify-content:center; align-items:center; color:gold;}

    @keyframes pulse { 50% { opacity:0.5; } }
</style>
</head>
<body id="body">

<div id="win-screen" class="overlay">
    <h1>🏆 ניצחון מוחלט! 🏆</h1>
    <h2>כל היריבים הושמדו.</h2>
    <h3>אתה שליט הזירה.</h3>
    <button onclick="s('reset')" style="padding:15px; font-size:20px; margin-top:20px; background:gold; border:none; cursor:pointer;">משחק חדש</button>
</div>

<div class="header">
    <div style="display:flex; gap:10px; align-items:center;">
        <span style="font-size:30px;" id="p-icon">🦠</span>
        <div>
            <div id="p-name" style="font-weight:bold;">טוען...</div>
            <div style="font-size:12px; color:#aaa"><span id="p-hp">0</span> HP</div>
        </div>
    </div>
    <div class="stat">בוטים נותרו: <span class="rivals-count" id="bot-count">4</span></div>
</div>

<div class="content">
    <div class="radar-box">
        <small style="color:#0f0; margin-bottom:5px;">R.A.D.A.R</small>
        <div class="radar-grid" id="map"></div>
    </div>
    <div class="scene-box">
        <div style="font-size:11px; text-align:center; color:#555; margin-bottom:5px;">סריקה חזותית:</div>
        <div class="enemies-list" id="scene"></div>
    </div>
</div>

<div class="log-container" id="log"></div>

<div class="controls">
    <button onclick="s('reset')" style="font-size:10px; height:30px; background:#400; border:none; color:#f88; width:50px; margin-right:20px;">RESET</button>
    <div class="d-pad">
        <button class="btn u" onclick="s('move',[0,1])">⬆</button>
        <button class="btn l" onclick="s('move',[-1,0])">⬅</button>
        <button class="btn d" onclick="s('move',[0,-1])">⬇</button>
        <button class="btn r" onclick="s('move',[1,0])">➡</button>
    </div>
</div>

<script>
    const API = "{{ api }}";
    
    window.onload = ()=> s('init');

    async function s(act, val=null){
        try{
            let res = await fetch(API, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({a:act, v:val})});
            let d = await res.json();
            
            // Win?
            if(d.player.won) document.getElementById("win-screen").style.display = "flex";
            else document.getElementById("win-screen").style.display = "none";

            // Header
            let p = d.player;
            document.getElementById("p-icon").innerText = p.icon;
            document.getElementById("p-name").innerText = p.dead ? "גוסס..." : p.name;
            document.getElementById("p-hp").innerText = p.hp + "/" + p.max;
            document.getElementById("bot-count").innerText = p.bots_left;
            
            if(p.dead) document.body.style.boxShadow = "inset 0 0 50px red";
            else document.body.style.boxShadow = "none";

            // Map
            let mh = "";
            d.map.forEach(row=>{
                row.forEach(c => mh+=`<div class="cell ${c.cls}">${c.txt}</div>`);
            });
            document.getElementById("map").innerHTML = mh;
            document.getElementById("map").style.gridTemplateRows = `repeat(${d.map.length}, 1fr)`;
            document.querySelectorAll(".cell").forEach(el=> el.parentElement.style.gridTemplateColumns=`repeat(${d.map[0].length}, 1fr)`);

            // Scene
            let sh = "";
            if(d.scene.length===0) sh = "<div style='width:100%; text-align:center; color:#444; margin-top:50px;'>שטח נקי.</div>";
            else {
                d.scene.forEach(obj => {
                    // Logic: Dead items only infected if player is dead. Live items attacked if player alive.
                    let btn = "";
                    let cardClass = obj.is_corpse ? "dead-card" : "live-card";
                    let hpColor = obj.is_corpse ? "#555" : "#f55";
                    
                    if (p.dead) {
                        btn = `<button style='background:#282; color:white; border:none; width:100%; cursor:pointer; border-radius:4px;' onclick="s('infect',['${obj.type}',${obj.idx}])">🧬 פלוש</button>`;
                    } else if (!obj.is_corpse) {
                        btn = `<button style='background:#822; color:white; border:none; width:100%; cursor:pointer; border-radius:4px;' onclick="s('attack',['${obj.type}',${obj.idx}])">⚔️ תקיפה</button>`;
                    } else {
                        btn = "<div style='font-size:10px; color:#555'>(גופה)</div>";
                    }

                    sh += `<div class="card ${cardClass}">
                        <div style="font-size:30px;">${obj.icon}</div>
                        <strong style="font-size:12px;">${obj.name}</strong>
                        <div style="color:${hpColor}; font-size:11px;">${obj.hp} HP</div>
                        ${btn}
                    </div>`;
                });
            }
            document.getElementById("scene").innerHTML = sh;

            // Logs
            let lh="";
            d.log.slice().reverse().forEach(l=> lh+=`<div class="msg ${l.type}">${l.text}</div>`);
            document.getElementById("log").innerHTML=lh;

        }catch(e){console.error(e);}
    }
    
    // Arrows
    window.addEventListener("keydown", e=>{
        if(e.key=="ArrowUp") s('move',[0,1]);
        if(e.key=="ArrowDown") s('move',[0,-1]);
        if(e.key=="ArrowLeft") s('move',[-1,0]);
        if(e.key=="ArrowRight") s('move',[1,0]);
    });
</script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(port=5006, debug=True)
