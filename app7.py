import random
import uuid
from flask import Flask, render_template_string, request, jsonify, session, url_for

app = Flask(__name__)
app.secret_key = 'hebrew_commander_v10'

# ==========================================
# 🛰️ הגדרות התחנה והאויבים (מתורגם)
# ==========================================

SECTORS = {
    "N": {"name": "האנגר צפוני", "defense": 0, "max_def": 100},
    "S": {"name": "כור דרומי",   "defense": 20, "max_def": 100},
    "E": {"name": "מעבדות מזרח", "defense": 10, "max_def": 100},
    "W": {"name": "נשקייה מערב", "defense": 10, "max_def": 100},
    "CORE": {"name": "ליבת הפיקוד", "defense": 1000, "max_def": 1000} 
}

ALIENS = [
    {"name": "רחפן עוקץ", "dmg": 5, "speed": 1},
    {"name": "משחית כבד", "dmg": 15, "speed": 2},
    {"name": "המלכה", "dmg": 40, "speed": 1}
]

# ==========================================
# ⚙️ מנוע המשחק
# ==========================================
class Engine:
    def __init__(self, state=None):
        if not state:
            self.state = {
                "energy": 100, "max_energy": 100,
                "oxygen": 100, "max_oxygen": 100,
                "day": 1,
                "sectors": SECTORS.copy(),
                "enemies": [],
                "log": [{"text": "המערכות אותחלו בהצלחה. ממתין לפקודות, המפקד.", "type": "sys"}]
            }
        else:
            self.state = state

    def log(self, t, type="sys"): 
        self.state["log"].append({"text": t, "type": type})

    def spawn_wave(self):
        count = random.randint(1, self.state["day"] + 1)
        for _ in range(count):
            loc = random.choice(["N", "S", "E", "W"])
            base = random.choice(ALIENS)
            enemy = {
                "name": base["name"],
                "dmg": base["dmg"],
                "hp": 20 + (self.state["day"] * 5),
                "loc": loc
            }
            self.state["enemies"].append(enemy)
            sector_name = self.state["sectors"][loc]["name"]
            self.log(f"⚠️ אזהרת חדירה! {enemy['name']} זוהה ב-{sector_name}!", "danger")

    def next_turn(self):
        s = self.state
        s["energy"] = min(s["energy"] + 10, s["max_energy"]) 
        s["oxygen"] -= 2
        
        if s["oxygen"] <= 0:
            self.log("❌ אזל החמצן. התחנה אבדה.", "danger")
            return "dead"

        # אויבים תוקפים
        alive = []
        for e in s["enemies"]:
            loc = e["loc"]
            sec = s["sectors"][loc]
            
            # פריצת חדר
            if sec["defense"] <= 0 and loc != "CORE":
                self.log(f"🚨 {sec['name']} נפרץ! האויב מתקדם לליבה.", "danger")
                e["loc"] = "CORE"
                sec["defense"] = 0
            
            target = s["sectors"][e["loc"]]
            target["defense"] -= e["dmg"]
            
            # הגנות אוטומטיות יורות
            e["hp"] -= 5 
            
            if target["defense"] <= 0 and e["loc"] == "CORE":
                return "dead"
            
            if e["hp"] > 0:
                alive.append(e)
            else:
                self.log(f"🔫 מערכות אוטומטיות חיסלו את {e['name']}.", "success")

        s["enemies"] = alive
        
        # סיכוי לגל חדש
        if random.random() < 0.35 + (s["day"] * 0.05):
            self.spawn_wave()

        return "ok"

    def action_fire(self, loc):
        if self.state["energy"] >= 25:
            self.state["energy"] -= 25
            hits = 0
            survivors = []
            for e in self.state["enemies"]:
                if e["loc"] == loc:
                    e["hp"] -= 50
                    hits += 1
                    if e["hp"] > 0: survivors.append(e)
                    else: self.log(f"🚀 טיל הושגר וחיסל {e['name']}!", "success")
                else:
                    survivors.append(e)
            self.state["enemies"] = survivors
            if hits == 0: self.log(f"ירית ל{loc} אך החדר היה ריק.", "sys")
        else:
            self.log("⚡ אין מספיק חשמל לירי!", "danger")

    def action_repair(self, loc):
        if self.state["energy"] >= 15:
            self.state["energy"] -= 15
            self.state["sectors"][loc]["defense"] = self.state["sectors"][loc]["max_def"]
            nm = self.state["sectors"][loc]["name"]
            self.log(f"🔧 צוותי בינוי תיקנו את ההגנות ב-{nm}.", "info")
        else:
            self.log("⚡ אין מספיק חשמל לתיקון!", "danger")

    def action_ventilate(self):
        if self.state["energy"] >= 30:
            self.state["energy"] -= 30
            self.state["oxygen"] = min(self.state["oxygen"] + 40, 100)
            self.log("💨 החלפת מסנני חמצן בוצעה.", "success")
        else:
            self.log("⚡ אין חשמל למערכת האוורור!", "danger")

# ==========================================
# WEB
# ==========================================
@app.route("/")
def index():
    if "uid" not in session: session["uid"] = str(uuid.uuid4())
    return render_template_string(HTML, api=url_for("update"))

@app.route("/api/update", methods=["POST"])
def update():
    d = request.json
    try: eng = Engine(session.get("game_cmd"))
    except: eng
