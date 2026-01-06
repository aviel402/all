from flask import Flask, render_template_string, request, jsonify, session, url_for
import json
import uuid
import random

app = Flask(__name__)
app.secret_key = 'million_dollar_game_v1'

# --- 🌍 הגדרות משחק והרחבת תוכן ---

# אפקטים של חפצים (שימוש)
ITEM_EFFECTS = {
    "תחבושת": {"type": "heal", "val": 30, "msg": "חבשת את הפצעים. מרגיש הרבה יותר טוב."},
    "שיקוי אנרגיה": {"type": "stamina", "val": 50, "msg": "זרם של כוח עובר בגוף שלך!"},
    "מנת קרב": {"type": "heal", "val": 15, "msg": "לא טעים, אבל משביע."},
    "מטבע עתיק": {"type": "gold", "val": 100, "msg": "מכרת את המטבע לסוחר דמיוני תמורת זהב."},
    "סוללה": {"type": "recharge", "val": 20, "msg": "טענת את החליפה."},
    "יהלום": {"type": "gold", "val": 500, "msg": "אוצר אמיתי!"}
}

BIOMES = {
    "מסדרון": "⬛", "מעבדה": "🔬", "נשקייה": "🛡️", 
    "מגורים": "🛌", "כספת": "💰", "גן בוטני": "🌿"
}

ENEMIES = [
    {"name": "קיבורג משובש", "icon": "🦾", "hp": 30, "atk": 8, "gold": 20},
    {"name": "עכברוש מוטנטי", "icon": "🐀", "hp": 15, "atk": 4, "gold": 5},
    {"name": "שומר רפאים", "icon": "👻", "hp": 40, "atk": 12, "gold": 50},
    {"name": "בוט ניקיון", "icon": "🧹", "hp": 10, "atk": 2, "gold": 2}
]

# --- 🧠 מנוע לוגי משודרג ---
class WorldGenerator:
    def generate(self, x, y):
        # לא בחדר 0,0
        if x == 0 and y == 0:
            return {"name": "לובי ראשי", "type": "התחלה", "enemy": None, "items": [], "gold": 0}

        b_type = random.choice(list(BIOMES.keys()))
        enemy = None
        # 40% סיכוי לאויב
        if random.random() < 0.4:
            base = random.choice(ENEMIES)
            enemy = base.copy()
        
        # 50% סיכוי לחפצים
        loot = []
        if random.random() < 0.5:
            loot.append(random.choice(list(ITEM_EFFECTS.keys())))
        
        # זהב על הרצפה
        gold = random.randint(5, 50) if random.random() < 0.3 else 0

        return {
            "name": f"{b_type} ({x},{y})",
            "type": b_type,
            "enemy": enemy,
            "items": loot,
            "gold": gold
        }

class GameEngine:
    def __init__(self, state=None):
        if not state:
            self.state = {
                "x": 0, "y": 0,
                # --- מדדים ---
                "hp": 100, "max_hp": 100,
                "stamina": 100, "max_stamina": 100,
                "xp": 0, "level": 1,
                "gold": 0,
                # -------------
                "inv": [],
                "map": {},
                "visited": ["0,0"],
                "log": [{"text": "ברוך הבא למשחק האולטימטיבי. המטרה: לשרוד ולצבור כוח.", "type": "system"}]
            }
            # חדר ראשון
            self.gen = WorldGenerator()
            self.state["map"]["0,0"] = self.gen.generate(0,0)
        else:
            self.state = state
            self.gen = WorldGenerator()

    def get_pos(self): return f"{self.state['x']},{self.state['y']}"

    # -- תנועה ושיפור הניווט --
    def move(self, dx, dy):
        # עלות אנרגיה לצעד
        if self.state["stamina"] < 5:
            self.log("⚠️ אתה עייף מדי! לחץ על 'נוח' כדי למלא אנרגיה.", "warning")
            return
        
        self.state["stamina"] -= 5
        self.state["x"] += dx
        self.state["y"] += dy
        k = self.get_pos()
        
        new_discovery = False
        if k not in self.state["map"]:
            self.state["map"][k] = self.gen.generate(self.state["x"], self.state["y"])
            new_discovery = True
        
        if k not in self.state["visited"]:
            self.state["visited"].append(k)
        
        room = self.state["map"][k]
        
        # הודעה חכמה
        if new_discovery:
            self.log(f"✨ צעדת לתוך {room['name']} הלא נודע...", "system")
        else:
            self.log(f"חזרת ל-{room['name']}.", "game")
        
        # הצגת מצב החדר
        if room["enemy"]:
            e = room["enemy"]
            self.log(f"👹 {e['name']} (Lvl {self.state['level']}) אורב לך כאן!", "danger")
        if room["items"]:
            self.log(f"🔎 ראית: {', '.join(room['items'])}", "success")

    # -- קרב וחישוב נזק --
    def attack(self):
        k = self.get_pos()
        room = self.state["map"][k]
        
        if not room["enemy"]:
            self.log("אין במי להילחם. בזבזת אנרגיה.", "game")
            self.state["stamina"] -= 2
            return
        
        if self.state["stamina"] < 10:
            self.log("😓 אין לך כוח להניף את הנשק! (נוח)", "warning")
            return

        enemy = room["enemy"]
        
        # חישוב נזק לפי רמה
        dmg = random.randint(10, 20) + (self.state["level"] * 5)
        enemy["hp"] -= dmg
        self.state["stamina"] -= 10
        self.log(f"⚔️ תקפת בעוצמה! גרמת {dmg} נזק.", "game")

        if enemy["hp"] <= 0:
            # ניצחון
            gain_gold = enemy["gold"] + random.randint(1,10)
            gain_xp = 20
            self.state["gold"] += gain_gold
            self.state["xp"] += gain_xp
            self.log(f"💀 ניצחון! {enemy['name']} הובס. זכית ב-{gain_gold} זהב.", "success")
            room["enemy"] = None
            self.check_levelup()
        else:
            # אויב תוקף חזרה
            e_dmg = max(1, enemy["atk"] - random.randint(0, 2))
            self.state["hp"] -= e_dmg
            self.log(f"💢 האויב מגיב! חטפת {e_dmg} נזק.", "danger")

    def rest(self):
        # מילוי אנרגיה ומעט חיים
        self.state["stamina"] = min(self.state["stamina"] + 30, self.state["max_stamina"])
        self.state["hp"] = min(self.state["hp"] + 5, self.state["max_hp"])
        self.log("💤 עצרת למנוחה קצרה. מרגיש רענן.", "info")

    def take(self):
        k = self.get_pos()
        room = self.state["map"][k]
        
        items_taken = []
        if room["items"]:
            for item in room["items"]:
                self.state["inv"].append(item)
                items_taken.append(item)
            room["items"] = [] # מרוקן חדר
        
        if room["gold"] > 0:
            g = room["gold"]
            self.state["gold"] += g
            room["gold"] = 0
            items_taken.append(f"{g} זהב")

        if items_taken:
            self.log(f"אספת: {', '.join(items_taken)}", "success")
        else:
            self.log("לא מצאת שום דבר בעל ערך.", "warning")

    # -- שימוש בחפצים מהתפריט --
    def use_item(self, item_name):
        if item_name not in self.state["inv"]:
            self.log("אין לך את החפץ הזה.", "warning")
            return

        # בדיקת אפקט
        effect = ITEM_EFFECTS.get(item_name)
        if effect:
            # ביצוע אפקט
            if effect["type"] == "heal":
                self.state["hp"] = min(self.state["hp"] + effect["val"], self.state["max_hp"])
            elif effect["type"] == "stamina":
                self.state["stamina"] = min(self.state["stamina"] + effect["val"], self.state["max_stamina"])
            elif effect["type"] == "gold":
                self.state["gold"] += effect["val"]
            elif effect["type"] == "recharge":
                 self.state["stamina"] = self.state["max_stamina"]
            
            # הסרה מהתיק ודיווח
            self.state["inv"].remove(item_name)
            self.log(f"✨ {effect['msg']}", "success")
        else:
            self.log("לא ניתן להשתמש בזה כאן.", "info")

    def check_levelup(self):
        threshold = self.state["level"] * 50
        if self.state["xp"] >= threshold:
            self.state["level"] += 1
            self.state["max_hp"] += 20
            self.state["hp"] = self.state["max_hp"]
            self.state["max_stamina"] += 10
            self.log(f"🆙 עלית רמה! אתה כעת רמה {self.state['level']}!", "success")

    def log(self, t, type):
        self.state["log"].append({"text": t, "type": type})

    def render_map_html(self):
        cx, cy = self.state["x"], self.state["y"]
        r = 2 
        html = "<div class='map-grid'>"
        for dy in range(r, -r - 1, -1):
            html += "<div class='map-row'>"
            for dx in range(-r, r + 1):
                tx, ty = cx + dx, cy + dy
                k = self.get_key(tx, ty)
                content = "⚫" # Fog
                cls = "fog"
                
                if dx == 0 and dy == 0:
                    content = "👤" # Player
                    cls = "player"
                elif k in self.state["visited"]:
                    room = self.state["map"][k]
                    if room["enemy"]:
                        content = "💀"
                        cls = "enemy-cell"
                    elif room["type"] in BIOMES:
                        content = BIOMES[room["type"]]
                        cls = "known"
                
                html += f"<span class='cell {cls}'>{content}</span>"
            html += "</div>"
        html += "</div>"
        return html
        
    def get_key(self, x, y): return f"{x},{y}"


# --- SERVER & ROUTES ---

@app.route("/")
def index():
    if "uid" not in session: session["uid"] = str(uuid.uuid4())
    api = url_for('cmd')
    return render_template_string(HTML, api=api)

@app.route("/api/cmd", methods=["POST"])
def cmd():
    data = request.json or {}
    action = data.get("action", "") # פעולה עיקרית (move, use, attack)
    param = data.get("param", "")   # פרמטר (direction, item_name)
    
    eng = GameEngine(session.get("game"))
    
    # ניהול מוות
    if eng.state["hp"] <= 0 and action != "reset":
        return jsonify({
            "log": [{"text": "☠️ סוף המשחק. מתת. בצע ריסט.", "type": "danger"}],
            "stats": {"hp":0}, "hud": "☠️", "dead": True
        })

    # ניתוב פקודות
    if action == "move": eng.move(*param) # dx, dy
    elif action == "attack": eng.attack()
    elif action == "rest": eng.rest()
    elif action == "take": eng.take()
    elif action == "use": eng.use_item(param)
    elif action == "look": pass # רק רענון
    elif action == "reset": 
        session.clear()
        return jsonify({"reload": True})
    
    session["game"] = eng.state
    
    k = eng.get_pos()
    room = eng.state["map"][k]
    
    # בניית תפריט שימוש בחפצים ל-Frontend
    inventory_html = ""
    if not eng.state["inv"]:
        inventory_html = "<div style='color:#777; text-align:center;'>התיק ריק</div>"
    else:
        # ספירת חפצים לראות כמויות? כרגע פשוט רשימה
        for i, item in enumerate(eng.state["inv"]):
            inventory_html += f"<button class='inv-btn' onclick=\"send('use', '{item}')\">🔹 {item}</button>"

    return jsonify({
        "log": eng.state["log"],
        "hud": eng.render_map_html(),
        "loc": f"{room['name']} {k}",
        "stats": {
            "hp": eng.state["hp"], "max_hp": eng.state["max_hp"],
            "st": eng.state["stamina"], "max_st": eng.state["max_stamina"],
            "xp": eng.state["xp"], "lvl": eng.state["level"],
            "gold": eng.state["gold"]
        },
        "inv_html": inventory_html
    })


# --- עיצוב HTML/CSS משופר (LHD Layout fix for Hebrew) ---
HTML = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>LEGENDS RPG</title>
<link href="https://fonts.googleapis.com/css2?family=Rajdhani:wght@500;700&display=swap" rel="stylesheet">
<style>
    :root {
        --main-bg: #0d0015;
        --card-bg: rgba(30, 10, 50, 0.85);
        --accent: #bc13fe;
        --accent-2: #ffd700; /* Gold */
        --hp-col: #ff3333;
        -
