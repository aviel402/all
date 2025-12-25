import time
import random
import json
import os
import uuid
from flask import Flask, render_template_string, redirect, url_for

app = Flask(__name__)
app.secret_key = "persistent_world_secret"

DB_FILE = "colony_data.json"

# --- נתונים ומחלקות ---

NAMES = ["אריק", "שרה", "דן", "מיה", "נועה", "תומר", "ג'ק", "אנה", "רועי", "ליאת", "סבסטיאן", "קלרה"]
JOBS = ["חקלאי", "שומר", "רופא", "מהנדס", "בטלן"]

class Colony:
    def __init__(self):
        self.load()

    def create_new(self):
        self.last_update = time.time()
        self.resources = {"food": 100, "wood": 50, "meds": 10}
        self.policy = "neutral" # strict, neutral, relaxed
        self.logs = ["המושבה הוקמה. הדמויות מתחילות לחיות."]
        
        self.villagers = []
        for _ in range(5): # מתחילים עם 5 אנשים
            self.villagers.append(self.generate_villager())

    def generate_villager(self):
        return {
            "id": str(uuid.uuid4()),
            "name": random.choice(NAMES),
            "job": random.choice(JOBS),
            "hp": 100,
            "hunger": 0, # 0 = שבע, 100 = גווע
            "happiness": 80,
            "status": "idle", # working, sleeping, rebelling, sick
            "alive": True
        }

    def simulate_offline_time(self):
        """הפונקציה הגאונית: מחשבת מה קרה כשלא היית"""
        current_time = time.time()
        seconds_passed = current_time - self.last_update
        
        # כדי לא להעמיס, אנחנו מחלקים את הזמן ל"מחזורים" של דקה משחק
        # כל דקה במציאות = שעה במשחק (לדוגמה)
        ticks = int(seconds_passed / 10) # כל 10 שניות בזמן אמת הן "תור"
        
        if ticks > 0:
            events_count = 0
            for _ in range(min(ticks, 500)): # מגבלה כדי שהשרת לא ייתקע אם חזרת אחרי שנה
                self.game_tick(silent=True)
                events_count += 1
            
            if events_count > 0:
                self.add_log(f"⏰ חזרת! עברו {events_count} מחזורי זמן כשלא היית.")
            
            self.last_update = current_time
            self.save()

    def game_tick(self, silent=False):
        """לוגיקה של מחזור חיים אחד"""
        
        # 1. הפקת משאבים (מי שעובד)
        for v in self.villagers:
            if not v["alive"]: continue
            
            # רעב עולה
            v["hunger"] += random.randint(1, 3)
            
            # עבודה (תלויה באושר ורעב)
            if v["hunger"] < 80 and v["happiness"] > 20:
                if v["job"] == "חקלאי":
                    self.resources["food"] += 0.5
                    v["status"] = "קוצר חיטה"
                elif v["job"] == "שומר":
                    v["status"] = "שומר בשער"
                elif v["job"] == "רופא":
                    v["status"] = "מטפל בחולים"
                elif v["job"] == "בטלן":
                    self.resources["food"] -= 0.1 # בטלנים גונבים אוכל
                    v["status"] = "מביט בשמיים"
            else:
                v["status"] = "עייף וממורמר"

        # 2. צריכה קולקטיבית
        alive_count = sum(1 for v in self.villagers if v['alive'])
        if alive_count == 0: return

        # אוכלים
        food_needed = alive_count * 2
        if self.resources["food"] >= food_needed:
            self.resources["food"] -= food_needed
            # איפוס רעב למי שחי
            for v in self.villagers: 
                if v['alive']: v["hunger"] = max(0, v["hunger"] - 10)
        else:
            if not silent: self.add_log("⚠️ האוכל נגמר! האנשים רעבים.")
            # מי שרעב - מאבד חיים
            for v in self.villagers:
                if v['alive']: v["hp"] -= 5

        # 3. אירועים אקראיים ומוות
        for v in self.villagers:
            if not v["alive"]: continue

            # מוות מרעב
            if v["hunger"] >= 100: v["hp"] -= 10
            
            # בדיקת חיים
            if v["hp"] <= 0:
                v["alive"] = False
                if not silent: self.add_log(f"💀 {v['name']} ({v['job']}) מת מקשיים.")
                continue

            # החלטות עצמאיות
            decision = random.random()
            if decision < 0.05: # 5% סיכוי לאירוע אישי
                if v["happiness"] < 30:
                    v["job"] = "מורד"
                    if not silent: self.add_log(f"🔥 {v['name']} התחיל למרוד במערכת!")
                elif self.policy == "relaxed" and random.random() < 0.3:
                    self.resources["food"] -= 5
                    if not silent: self.add_log(f"{v['name']} חגג וזלל יותר מדי אוכל.")

    def add_log(self, text):
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.logs.insert(0, f"[{timestamp}] {text}")
        self.logs = self.logs[:20] # לשמור רק אחרונים

    def save(self):
        data = {
            "last_update": self.last_update,
            "resources": self.resources,
            "villagers": self.villagers,
            "policy": self.policy,
            "logs": self.logs
        }
        with open(DB_FILE, "w", encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)

    def load(self):
        if os.path.exists(DB_FILE):
            try:
                with open(DB_FILE, "r", encoding='utf-8') as f:
                    data = json.load(f)
                    self.last_update = data["last_update"]
                    self.resources = data["resources"]
                    self.villagers = data["villagers"]
                    self.policy = data.get("policy", "neutral")
                    self.logs = data.get("logs", [])
            except:
                self.create_new()
        else:
            self.create_new()

colony = Colony()

# --- ממשק WEB ---

HTML = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="10"> <!-- רענון אוטומטי כל 10 שניות -->
    <title>המושבה האבודה</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { background: #222; color: #ddd; font-family: sans-serif; max-width: 800px; margin: 0 auto; padding: 10px; }
        .top-bar { display: flex; justify-content: space-between; background: #333; padding: 10px; border-radius: 8px; margin-bottom: 20px; }
        .res { font-weight: bold; color: #ffeb3b; }
        
        .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 10px; }
        
        .person-card { 
            background: #2a2a2a; border: 1px solid #444; border-radius: 8px; padding: 10px; 
            position: relative; transition: 0.3s; 
        }
        .dead { opacity: 0.5; border-color: red; filter: grayscale(1); }
        .rebel { border-color: orange; }
        
        .status-badge { font-size: 12px; background: #444; padding: 2px 5px; border-radius: 4px; position: absolute; top: 10px; left: 10px; }
        h3 { margin: 5px 0; font-size: 16px; }
        .job { font-size: 12px; color: #888; }
        
        .bar { height: 4px; background: #555; margin-top: 5px; border-radius: 2px; overflow: hidden; }
        .fill { height: 100%; transition: 0.5s; }
        .hp-fill { background: #e91e63; }
        .hap-fill { background: #03a9f4; }
        .hun-fill { background: #ff9800; }

        .logs { background: #111; padding: 10px; height: 150px; overflow-y: auto; border: 1px solid #333; margin-top: 20px; font-family: monospace; font-size: 13px; }
        
        .controls { margin-bottom: 20px; padding: 10px; background: #1a1a1a; border-radius: 8px; }
        button { background: #009688; border: none; color: white; padding: 8px 15px; border-radius: 4px; cursor: pointer; margin-left: 5px; }
        button.bad { background: #d32f2f; }
        
        .policy-btn { opacity: 0.5; }
        .active-policy { opacity: 1; border: 2px solid white; font-weight: bold; }

    </style>
</head>
<body>

    <div class="top-bar">
        <div>🥪 מזון: <span class="res">{{ game.resources.food|round|int }}</span></div>
        <div>🪵 עץ: <span class="res">{{ game.resources.wood|round|int }}</span></div>
        <div>💊 תרופות: <span class="res">{{ game.resources.meds|round|int }}</span></div>
        <div>👥 חיים: {{ alive_count }} / {{ game.villagers|length }}</div>
    </div>

    <div class="controls">
        <b>מדיניות שליט:</b>
        <a href="/policy/strict"><button class="policy-btn {{ 'active-policy' if game.policy=='strict' else '' }}">קשוחה (עבודה+ / אושר-)</button></a>
        <a href="/policy/neutral"><button class="policy-btn {{ 'active-policy' if game.policy=='neutral' else '' }}">רגילה</button></a>
        <a href="/policy/relaxed"><button class="policy-btn {{ 'active-policy' if game.policy=='relaxed' else '' }}">חופשית (אושר+ / צריכה+)</button></a>
        <span style="float:left">
            <a href="/action/scavenge"><button>שלח משלחת חיפוש</button></a>
            <a href="/reset"><button class="bad">אפס עולם</button></a>
        </span>
    </div>

    <div class="grid">
        {% for v in game.villagers %}
        <div class="person-card {{ 'dead' if not v.alive else '' }} {{ 'rebel' if v.job == 'מורד' else '' }}">
            <span class="status-badge">{{ v.status }}</span>
            <h3>{{ v.name }}</h3>
            <div class="job">{{ v.job }} {{ '💀' if not v.alive else '' }}</div>
            
            {% if v.alive %}
                <!-- Health -->
                <div class="bar" title="בריאות"><div class="fill hp-fill" style="width: {{ v.hp }}%"></div></div>
                <!-- Hunger (inversed: 0 width = 0 hunger) -->
                <div class="bar" title="רעב (מלא=גווע)"><div class="fill hun-fill" style="width: {{ v.hunger }}%"></div></div>
                <!-- Happiness -->
                <div class="bar" title="אושר"><div class="fill hap-fill" style="width: {{ v.happiness }}%"></div></div>
            {% endif %}
        </div>
        {% endfor %}
    </div>

    <div class="logs">
        {% for l in game.logs %}
            <div>{{ l }}</div>
        {% endfor %}
    </div>

</body>
</html>
"""

@app.route('/')
def index():
    # כל פעם שמישהו נכנס לאתר, אנחנו בודקים כמה זמן עבר מאז העדכון האחרון ומריצים סימולציה
    colony.simulate_offline_time()
    
    alive = sum(1 for v in colony.villagers if v['alive'])
    return render_template_string(HTML, game=colony, alive_count=alive)

@app.route('/policy/<mode>')
def set_policy(mode):
    colony.policy = mode
    colony.add_log(f"החוקים השתנו. מדיניות חדשה: {mode}")
    colony.save()
    return redirect('/')

@app.route('/action/scavenge')
def scavenge():
    # פעולה אקטיבית
    colony.simulate_offline_time()
    
    loot_food = random.randint(5, 30)
    loot_wood = random.randint(2, 10)
    
    colony.resources["food"] += loot_food
    colony.resources["wood"] += loot_wood
    
    # סיכון שמישהו ייפצע
    if random.random() < 0.3:
        victim = random.choice([v for v in colony.villagers if v['alive']])
        victim['hp'] -= 15
        colony.add_log(f"המשלחת חזרה עם ציוד, אבל {victim['name']} נפצע.")
    else:
        colony.add_log(f"המשלחת חזרה בשלום. הבאתם {loot_food} אוכל ו-{loot_wood} עץ.")
    
    colony.save()
    return redirect('/')

@app.route('/reset')
def reset():
    colony.create_new()
    colony.save()
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
