import random
import uuid
import math
from flask import Flask, render_template_string, request, jsonify, session, url_for

app = Flask(__name__)
app.secret_key = 'arena_royale_ultimate_v2'

# ==========================================
# 🧬 נתונים
# ==========================================
# ==========================================
# 🧬 מאגר גופים מורחב (האוסף המלא)
# ==========================================
HOSTS = {
    # --- דרגה 1: חלשים (אוכל לבוטים) ---
    "blob":    {"name": "עיסה ירוקה", "icon": "🦠", "hp": 15, "atk": 2},
    "fly":     {"name": "זבוב ענק", "icon": "🪰", "hp": 10, "atk": 1},
    "chicken": {"name": "תרנגול זועם", "icon": "🐓", "hp": 20, "atk": 5},
    "rat":     {"name": "עכברוש", "icon": "🐀", "hp": 25, "atk": 4},

    # --- דרגה 2: בינוניים (לוחמים טובים) ---
    "wolf":    {"name": "זאב בלהות", "icon": "🐺", "hp": 50, "atk": 10},
    "zombie":  {"name": "זומבי", "icon": "🧟", "hp": 60, "atk": 8},
    "alien":   {"name": "חייזר אפור", "icon": "👽", "hp": 45, "atk": 15},
    "ghost":   {"name": "רוח רפאים", "icon": "👻", "hp": 40, "atk": 12},
    "guard":   {"name": "שומר ראש", "icon": "👮", "hp": 70, "atk": 14},

    # --- דרגה 3: חזקים (מסוכנים מאוד) ---
    "mech":    {"name": "רובוט קרב", "icon": "🤖", "hp": 100, "atk": 20},
    "bear":    {"name": "דוב משוריין", "icon": "🐻", "hp": 120, "atk": 22},
    "vampire": {"name": "ערפד עתיק", "icon": "🧛", "hp": 90, "atk": 30},
    "tank":    {"name": "טנק חי", "icon": "🚜", "hp": 200, "atk": 10},

    # --- דרגה 4: אגדיים (בוסים) ---
    "dragon":  {"name": "דרקון שחור", "icon": "🐲", "hp": 250, "atk": 45},
    "cthulhu": {"name": "אל הים (בוס)", "icon": "🦑", "hp": 300, "atk": 50},
    "devil":   {"name": "שטן", "icon": "😈", "hp": 220, "atk": 60}
}
# בוטים יריבים
BOT_NAMES = [
    {"name": "סובייקט אלפא", "color": "#f55"},
    {"name": "סובייקט בטא", "color": "#55f"},
    {"name": "סובייקט גמא", "color": "#fa5"}
]

# ==========================================
# ⚙️ מנוע הטורניר
# ==========================================
class Engine:
    def __init__(self, state=None):
        if not state or "rivals" not in state:
            self.state = {
                "x": 0, "y": 0,
                # נתוני השחקן
                "host": "blob",
                "hp": 15, "max_hp": 15,
                "is_dead": False,
                # עולם ובוטים
                "map_size": 4, # גבולות המפה (מ- -4 עד 4)
                "rivals": [], 
                "map_content": {}, # מה יש בכל חדר (מפלצות ניטרליות)
                "visited": ["0,0"],
                "log": [{"text": "ברוך הבא לזירה. חסל את היריבים כדי לנצח.", "type": "sys"}]
            }
            # אתחול המשחק
            self.init_world()
        else:
            self.state = state

    def log(self, t, type="game"): 
        self.state["log"].append({"text": t, "type": type})
        if len(self.state["log"]) > 40: self.state["log"].pop(0)

    def init_world(self):
        # 1. יצירת בוטים במיקומים רנדומליים
        for b in BOT_NAMES:
            bot = {
                "name": b["name"],
                "color": b["color"],
                "host": "blob", # כולם מתחילים כטפיל
                "hp": 15, "max_hp": 15,
                "x": random.randint(-4, 4),
                "y": random.randint(-4, 4),
                "dead": False
            }
            self.state["rivals"].append(bot)
        
        # 2. פיזור גופות (מפלצות) ברחבי המפה להשתלטות
        for x in range(-4, 5):
            for y in range(-4, 5):
                if x==0 and y==0: continue
                # 60% סיכוי למפלצת בחדר
                if random.random() < 0.6:
                    
                    # כאן המערכת מחליטה איזה "סוג" אויב ליצור
                    rng = random.random()
                    
                    if rng < 0.5:   # 50% סיכוי לאויב חלש
                        tier = random.choice(["rat", "fly", "chicken"])
                        
                    elif rng < 0.8: # 30% סיכוי לאויב בינוני
                        tier = random.choice(["wolf", "zombie", "alien", "ghost", "guard"])
                        
                    elif rng < 0.95: # 15% סיכוי לאויב חזק
                        tier = random.choice(["mech", "bear", "vampire", "tank"])
                        
                    else:           # 5% סיכוי לבוס נדיר!
                        tier = random.choice(["dragon", "cthulhu", "devil"])
                    
                    # יצירת המפלצת בפועל
                    self.state["map_content"][f"{x},{y}"] = {
                        "type": tier,
                        "hp": HOSTS[tier]["hp"]
                    }
    def pos(self): return f"{self.state['x']},{self.state['y']}"

    # --- תנועת בוטים (AI) ---
    def process_bots(self):
        px, py = self.state["x"], self.state["y"]
        
        for bot in self.state["rivals"]:
            if bot["dead"]: continue
            
            # 1. החלטה: האם לזוז או להילחם?
            # אם הבוט באותו חדר איתי - הוא יתקוף אותי!
            if bot["x"] == px and bot["y"] == py:
                self.bot_attack_player(bot)
                continue
            
            # אם הוא לבד, הוא זז רנדומלית ומחפש גופות
            dx = random.choice([-1, 0, 1])
            dy = random.choice([-1, 0, 1])
            # גבולות מפה
            bot["x"] = max(-4, min(4, bot["x"] + dx))
            bot["y"] = max(-4, min(4, bot["y"] + dy))
            
            # אינטראקציה של בוט עם החדר שלו
            b_key = f"{bot['x']},{bot['y']}"
            room_mon = self.state["map_content"].get(b_key)
            
            if room_mon:
                # הבוט "נלחם" במפלצת אוטומטית ואולי משתדרג
                bot_str = HOSTS[bot["host"]]["atk"]
                mon_str = HOSTS[room_mon["type"]]["atk"]
                
                if bot_str > mon_str or random.random() < 0.3:
                    # הבוט ניצח ושדרג גוף!
                    if room_mon["type"] != "rat": # שדרוג רק אם זה שווה
                        bot["host"] = room_mon["type"]
                        bot["max_hp"] = HOSTS[room_mon["type"]]["hp"]
                        bot["hp"] = bot["max_hp"]
                        # מוחק את המפלצת מהמפה
                        del self.state["map_content"][b_key]
                        self.log(f"⚠️ {bot['name']} השתלט על {HOSTS[bot['host']]['name']}!", "warning")

    def bot_attack_player(self, bot):
        # חישוב נזק
        bot_dmg = HOSTS[bot["host"]]["atk"]
        self.state["hp"] -= bot_dmg
        self.log(f"⚔️ {bot['name']} נמצא איתך בחדר ותוקף! (-{bot_dmg} חיים)", "danger")
        
        if self.state["hp"] <= 0:
            self.state["hp"] = 0
            self.state["is_dead"] = True
            self.log(f"💀 נהרגת ע'י {bot['name']}! מהר, מצא גוף אחר!", "critical")

    # --- פעולות שחקן ---
    
    def move(self, dx, dy):
        if self.state["is_dead"]: return # מתים לא זזים
        
        self.state["x"] = max(-4, min(4, self.state["x"] + dx))
        self.state["y"] = max(-4, min(4, self.state["y"] + dy))
        
        pos = self.pos()
        if pos not in self.state["visited"]: self.state["visited"].append(pos)
        
        # תור הבוטים קורה כשאתה זז
        self.process_bots()
        
        # בדיקה מי בחדר איתי
        self.check_room()

    def check_room(self):
        pos = self.pos()
        
        # האם יש בוטים?
        rivals_here = [b for b in self.state["rivals"] if f"{b['x']},{b['y']}" == pos and not b["dead"]]
        for r in rivals_here:
            self.log(f"👀 היתקלות! {r['name']} ({HOSTS[r['host']]['name']}) נמצא כאן.", "warning")
            
        # האם יש מפלצת ניטרלית?
        mon = self.state["map_content"].get(pos)
        if mon:
            m_name = HOSTS[mon['type']]['name']
            self.log(f"בחדר נמצא {m_name} פראי.", "game")

    def attack_target(self, target_type, index):
        # target_type: 'bot' or 'monster'
        pos = self.pos()
        my_dmg = HOSTS[self.state["host"]]["atk"] + random.randint(0, 5)
        
        if target_type == "monster":
            mon = self.state["map_content"].get(pos)
            if mon:
                mon["hp"] -= my_dmg
                self.log(f"תקפת את המפלצת ({my_dmg} נזק).", "success")
                if mon["hp"] <= 0:
                    self.log("הרגת את המפלצת!", "success")
                    # במכניקה הזו לא הורגים לגמרי, היא הופכת לגופה שאפשר להשתלט עליה
                    # אבל בשביל הפשטות נניח שרק "הורגים" ואז אפשר לעשות Infect בנפרד
                    
        elif target_type == "bot":
            # למצוא את הבוט הנכון בחדר
            rivals_here = [b for b in self.state["rivals"] if f"{b['x']},{b['y']}" == pos and not b["dead"]]
            if index < len(rivals_here):
                bot = rivals_here[index]
                bot["hp"] -= my_dmg
                self.log(f"תקפת את {bot['name']}! ({my_dmg} נזק)", "success")
                
                if bot["hp"] <= 0:
                    self.log(f"💀 חיסלת את {bot['name']}! הוא מחוץ למשחק.", "gold")
                    bot["dead"] = True
                    bot["host"] = "blob" # חוזר להיות סליים מת

        self.process_bots() # תגובה של הבוטים האחרים

    def infect(self, target_type, index):
        if not self.state["is_dead"]:
            self.log("אי אפשר להשתלט כשאתה חי.", "sys")
            return

        pos = self.pos()
        new_host_type = None
        new_hp = 0
        
        if target_type == "monster":
            mon = self.state["map_content"].get(pos)
            if mon:
                new_host_type = mon["type"]
                new_hp = HOSTS[new_host_type]["hp"] # מקבלים חיים מלאים של הסוג
                del self.state["map_content"][pos] # המפלצת נעלמת (הופכת להיות השחקן)

        elif target_type == "bot":
            rivals_here = [b for b in self.state["rivals"] if f"{b['x']},{b['y']}" == pos and not b["dead"]]
            # אי אפשר להשתלט על בוט חי... צריך שהוא ימות קודם?
            # במשחק הזה נאפשר "גניבת גוף" אם הבוט בחדר, אבל זה יהפוך אותו ל"מת"
            if index < len(rivals_here):
                bot = rivals_here[index]
                new_host_type = bot["host"]
                new_hp = bot["hp"]
                
                # הבוט מאבד את הגוף ונהיה מת
                bot["dead"] = True
                bot["hp"] = 0
                self.log(f"גנבת ל-{bot['name']} את הגוף!", "gold")

        if new_host_type:
            self.state["host"] = new_host_type
            self.state["hp"] = new_hp
            self.state["max_hp"] = HOSTS[new_host_type]["hp"]
            self.state["is_dead"] = False
            self.log(f"🧬 נולדת מחדש בתור {HOSTS[new_host_type]['name']}!", "success")
        
        self.process_bots()

    def get_view(self):
        # בניית המפה ותמונת מצב
        pos = self.pos()
        room_mon = self.state["map_content"].get(pos)
        
        # בוטים בחדר הנוכחי
        local_bots = []
        for i, b in enumerate(self.state["rivals"]):
            if f"{b['x']},{b['y']}" == pos and not b["dead"]:
                local_data = HOSTS[b["host"]].copy()
                local_data["bot_name"] = b["name"]
                local_data["hp"] = b["hp"]
                local_data["orig_idx"] = i # לשמור מזהה
                local_bots.append(local_data)
        
        # מפלצת בחדר
        monster = None
        if room_mon:
            monster = HOSTS[room_mon["type"]].copy()
            monster["hp"] = room_mon["hp"]

        # בניית רדאר מפה
        grid = []
        cx, cy = self.state["x"], self.state["y"]
        for dy in range(1, -2, -1):
            row = []
            for dx in range(-1, 2):
                tx, ty = cx+dx, cy+dy
                k = f"{tx},{ty}"
                cell = {"icon":"⬛", "cls":"fog"}
                
                if dx==0 and dy==0: 
                    cell = {"icon": HOSTS[self.state['host']]['icon'], "cls":"player"}
                else:
                    # האם יש שם בוט?
                    for b in self.state["rivals"]:
                        if not b["dead"] and b["x"]==tx and b["y"]==ty:
                            cell = {"icon": "🤖", "cls":"danger"}
                row.append(cell)
            grid.append(row)

        return {
            "player": self.state,
            "player_meta": HOSTS[self.state["host"]],
            "map": grid,
            "log": self.state["log"],
            "targets": {
                "monster": monster,
                "bots": local_bots
            },
            "rivals_stat": self.state["rivals"], # ללידרבורד
            "all_hosts": HOSTS # למקרא
        }

# ==========================================
# שרת
# ==========================================
@app.route("/")
def index():
    if "uid" not in session: session["uid"] = str(uuid.uuid4())
    api = url_for("update")
    return render_template_string(UI, api=api)

@app.route("/update", methods=["POST"])
def update():
    try: eng = Engine(session.get("arena_save"))
    except: eng = Engine(None)
    
    d = request.json or {}
    act = d.get("a")
    val = d.get("v") # [type, index]
    
    if act == "reset": eng = Engine(None)
    elif act == "move": eng.move(*val)
    elif act == "attack": eng.attack_target(*val) # val = ["bot", 0]
    elif act == "infect": eng.infect(*val)

    session["arena_save"] = eng.state
    return jsonify(eng.get_view())

# ==========================================
# CLIENT (CSS Grid Layout)
# ==========================================
UI = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ARENA: PARASITE</title>
<style>
    body { background: #1a1a1a; color: #eee; margin:0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; display:flex; height:100vh; overflow:hidden;}
    
    /* LEFT SIDEBAR (Leaderboard) */
    .sidebar { width: 220px; background: #222; padding:10px; border-left: 2px solid #444; display:flex; flex-direction:column;}
    .leader-row { background:#333; padding:8px; margin-bottom:5px; border-radius:4px; font-size:12px; display:flex; justify-content:space-between; align-items:center;}
    .l-icon { font-size:20px; margin-left:5px;}
    .dead-row { opacity: 0.5; text-decoration: line-through; }

    /* MAIN */
    .main { flex:1; display:flex; flex-direction:column; background: radial-gradient(circle, #252525, #111); position:relative;}
    .screen-red { box-shadow: inset 0 0 100px red; } /* מסך מוות */

    /* HEADER */
    .header { padding: 15px; display:flex; justify-content:space-between; background:rgba(0,0,0,0.5); align-items:center;}
    .hp-bar-bg { width:150px; height:15px; background:#444; border-radius:10px; overflow:hidden;}
    .hp-bar-fill { height:100%; width:100%; background:#0f0; transition:0.3s;}

    /* BATTLE AREA */
    .arena-view { flex:1; padding:20px; display:flex; gap:15px; justify-content:center; align-items:center; flex-wrap:wrap; overflow-y:auto;}
    
    .target-card { 
        width: 110px; height: 150px; background: #333; border: 2px solid #555; border-radius: 8px;
        display:flex; flex-direction:column; align-items:center; justify-content:space-around;
        position:relative; animation: float 3s infinite ease-in-out;
    }
    .bot-card { border-color: #f55; background: #311; }
    .icon-large { font-size:45px; }
    
    .btn-act { border:none; color:white; padding:5px 10px; border-radius:4px; cursor:pointer; width:90%; font-weight:bold;}
    .atk { background: #b33; } .inf { background: #4b4; animation: pulse 1s infinite;}

    /* CONTROLS & LOG */
    .bottom { height: 180px; background: #222; border-top: 1px solid #555; display: grid; grid-template-columns: 2fr 1fr; }
    .log-box { overflow-y:auto; padding:10px; font-size:13px; font-family: monospace; border-left:1px solid #444;}
    .msg { margin-bottom:2px; } .sys { color:#aaa; } .danger { color:#f88; } .gold { color:gold;}

    .controls { display:flex; align-items:center; justify-content:space-around; }
    
    /* RADAR */
    .radar { display:grid; grid-template-rows:repeat(3,1fr); gap:2px; width:90px; height:90px; background:#000; border:1px solid #0f0; padding:2px;}
    .r-row { display:grid; grid-template-columns:repeat(3,1fr); gap:2px; }
    .r-cell { background:#111; display:flex; align-items:center; justify-content:center; font-size:16px;}
    .player { background: #004400; box-shadow:0 0 5px #0f0; }
    .danger-zone { background: #440000; }

    /* JOYSTICK */
    .d-pad { display:grid; grid-template-columns:repeat(3,1fr); gap:3px; direction:ltr; }
    .mov-btn { width:45px; height:45px; background:#444; border:none; color:white; border-radius:5px; font-size:20px; cursor:pointer;}
    .mov-btn:active { background:#666; }
    .u{grid-column:2; grid-row:1} .l{grid-column:1; grid-row:2} .r{grid-column:3; grid-row:2} .d{grid-column:2; grid-row:2}

    @keyframes float { 0%,100% {transform:translateY(0);} 50%{transform:translateY(-5px);} }
    @keyframes pulse { 50%{opacity:0.6;} }
</style>
</head>
<body id="body">

<!-- Sidebar: Rivals Status -->
<div class="sidebar">
    <div style="text-align:center; font-weight:bold; margin-bottom:10px; color:#aaa">מתחרים בזירה</div>
    <div id="leaderboard"></div>
    <div style="margin-top:auto; font-size:11px; color:#555; text-align:center;">היה השורד האחרון<br>או החזק ביותר.</div>
</div>

<div class="main">
    <div class="header">
        <div style="display:flex; gap:10px; align-items:center;">
            <div style="font-size:30px;" id="p-icon">🦠</div>
            <div>
                <div id="p-name" style="font-weight:bold">אני</div>
                <div class="hp-bar-bg"><div class="hp-bar-fill" id="hp-bar"></div></div>
                <small id="hp-txt">15/15</small>
            </div>
        </div>
        <div>קורדינאטות: <span id="pos-txt">0,0</span></div>
    </div>

    <!-- Arena View -->
    <div class="arena-view" id="stage">
        <!-- Enemies appear here -->
    </div>

    <div class="bottom">
        <div class="log-box" id="logs"></div>
        <div class="controls">
            <!-- MiniMap -->
            <div class="radar" id="radar"></div>
            
            <!-- Move -->
            <div class="d-pad" id="dpad">
                <button class="mov-btn u" onclick="s('move',[0,1])">⬆</button>
                <button class="mov-btn l" onclick="s('move',[-1,0])">⬅</button>
                <button class="mov-btn r" onclick="s('move',[1,0])">➡</button>
                <button class="mov-btn d" onclick="s('move',[0,-1])">⬇</button>
            </div>
        </div>
    </div>
</div>

<script>
const API = "{{ api }}";
window.onload = ()=> s('init');

async function s(act, val=null){
    let res = await fetch(API, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({a:act, v:val})});
    let d = await res.json();
    
    // 1. Player UI
    document.getElementById("p-icon").innerText = d.player.icon;
    document.getElementById("p-name").innerText = d.player.dead ? "גוסס (רוח)" : d.player_meta.name;
    document.getElementById("pos-txt").innerText = d.pos;
    
    let hp_pct = (d.player.hp / d.player.max)*100;
    document.getElementById("hp-bar").style.width = hp_pct + "%";
    document.getElementById("hp-txt").innerText = d.player.hp + "/" + d.player.max;
    
    if(d.player.dead) document.getElementById("body").classList.add("screen-red");
    else document.getElementById("body").classList.remove("screen-red");

    // 2. Map Render
    let rh = "";
    d.map.forEach(row=>{
        rh+="<div class='r-row'>";
        row.forEach(c=>{
            rh+=`<div class='r-cell ${c.cls}'>${c.icon}</div>`;
        });
        rh+="</div>";
    });
    document.getElementById("radar").innerHTML = rh;

    // 3. Stage Render (Monsters + Bots)
    let sh = "";
    
    // Monster
    if(d.targets.monster){
        let m = d.targets.monster;
        // כפתור: אם אני מת, הכפתור הוא 'השתלטות'. אם חי, 'התקפה'.
        let btn = d.player.dead ? 
            `<button class='btn-act inf' onclick="s('infect',['monster',0])">🧬 עבור גוף</button>` :
            `<button class='btn-act atk' onclick="s('attack',['monster',0])">⚔️ צוד</button>`;
            
        sh += `<div class="target-card">
            <div class="icon-large">${m.icon}</div>
            <strong>${m.name}</strong>
            <small style="color:#f55">${m.hp} HP</small>
            ${btn}
        </div>`;
    }
    
    // Bots
    d.targets.bots.forEach((b, i)=>{
        let btn = d.player.dead ? 
            `<button class='btn-act inf' onclick="s('infect',['bot',${i}])">🧬 גנוב גוף!</button>` :
            `<button class='btn-act atk' onclick="s('attack',['bot',${i}])">⚔️ הילחם!</button>`;
            
        sh += `<div class="target-card bot-card">
            <div style="position:absolute; top:2px; right:5px; font-size:10px; color:#fff">${b.bot_name}</div>
            <div class="icon-large">${b.icon}</div>
            <strong>${b.name}</strong>
            <small style="color:#fff">${b.hp} HP</small>
            ${btn}
        </div>`;
    });
    
    if(sh == "") sh = "<div style='color:#555'>השטח פנוי. תמשיך לזוז.</div>";
    document.getElementById("stage").innerHTML = sh;

    // 4. Logs
    let lb = document.getElementById("logs");
    lb.innerHTML="";
    d.log.slice().reverse().forEach(l => {
        lb.innerHTML += `<div class="msg ${l.type}">${l.text}</div>`;
    });

    // 5. Leaderboard
    let lh = "";
    d.rivals_stat.forEach(r => {
        let deadCls = r.dead ? "dead-row" : "";
        let hostIcon = d.all_hosts[r.host].icon;
        lh += `<div class="leader-row ${deadCls}" style="border-right:3px solid ${r.color}">
            <span>${r.name}</span>
            <div style="display:flex; align-items:center">${r.hp} <span class="l-icon">${hostIcon}</span></div>
        </div>`;
    });
    document.getElementById("leaderboard").innerHTML = lh;
}
</script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(port=5006, debug=True)
