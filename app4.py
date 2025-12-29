import random
from flask import Flask, render_template_string, redirect

app = Flask(__name__)
app.secret_key = "thug_life_secret"

# --- הגדרת המפה והמשחק ---

ZONES_DATA = [
    {"id": 0, "name": "השיכונים (בסיס)", "defense": 0, "income": 100, "owner": "player", "diff": 0},
    {"id": 1, "name": "רובע השוק", "defense": 30, "income": 150, "owner": "neutral", "diff": 1},
    {"id": 2, "name": "אזור התעשייה", "defense": 50, "income": 200, "owner": "enemy", "diff": 1},
    {"id": 3, "name": "נמל ישן", "defense": 80, "income": 250, "owner": "enemy", "diff": 2},
    {"id": 4, "name": "מרכז העיר", "defense": 120, "income": 400, "owner": "enemy", "diff": 2},
    {"id": 5, "name": "פארק הירקון", "defense": 60, "income": 150, "owner": "neutral", "diff": 1},
    {"id": 6, "name": "הקזינו", "defense": 200, "income": 800, "owner": "boss", "diff": 3},
    {"id": 7, "name": "שכונת היוקרה", "defense": 150, "income": 500, "owner": "enemy", "diff": 2},
    {"id": 8, "name": "תחנת הרכבת", "defense": 100, "income": 300, "owner": "enemy", "diff": 2},
]

class Game:
    def __init__(self):
        self.reset()

    def reset(self):
        self.turn = 1
        self.money = 500      # כסף התחלתי
        self.soldiers = 10    # חיילים התחלתיים
        self.influence = 10   # רמת כבוד/השפעה
        # מעתיקים את הנתונים כדי לא לדרוס את המקוריים
        self.zones = [z.copy() for z in ZONES_DATA]
        self.log = ["הקמת את הכנופיה. השכונה שלך בטוחה, אבל העיר מחכה."]
        self.game_over = False
        self.victory = False

    def next_turn(self):
        if self.game_over: return
        self.turn += 1
        
        # איסוף הכנסות מהשטחים שלך
        income = 0
        for z in self.zones:
            if z["owner"] == "player":
                income += z["income"]
        
        self.money += income
        self.log.insert(0, f"📆 יום חדש (תור {self.turn}). הכנסה מהשטחים: {income}$")

        # אויבים מתחזקים! (כל תור הם מוסיפים הגנות)
        for z in self.zones:
            if z["owner"] != "player":
                growth = random.randint(5, 15)
                z["defense"] += growth
        
        # אירוע רנדומלי
        if random.random() < 0.2:
            self.random_event()

    def random_event(self):
        events = [
            ("פשיטה משטרתית!", "המשטרה פשטה על המחסנים. איבדת 200$.", lambda: self.deduct_money(200)),
            ("משלוח נשק הגיע", "מצאת ארגזים נטושים. +5 חיילים.", lambda: self.add_soldiers(5)),
            ("עריק מהאויב", "חייל ערק לצד שלך וסיפר סודות. +50 כבוד.", lambda: self.add_inf(50)),
        ]
        ev = random.choice(events)
        ev[2]() # הפעלת הפונקציה
        self.log.insert(0, f"🔔 {ev[0]} {ev[1]}")

    def deduct_money(self, amount):
        self.money = max(0, self.money - amount)
    
    def add_soldiers(self, amount):
        self.soldiers += amount

    def add_inf(self, amount):
        self.influence += amount

    def check_win_condition(self):
        owned = sum(1 for z in self.zones if z["owner"] == "player")
        if owned == len(self.zones):
            self.victory = True
            self.log.insert(0, "👑👑👑 הניצחון שלך! כל העיר תחת שליטתך. 👑👑👑")

gameState = Game()

# --- CSS & HTML UI ---
# שים לב: נוספו /game4/ בקישורים

STYLE = """
<style>
    body { background-color: #121212; color: #eee; font-family: 'Courier New', monospace; direction: rtl; text-align: center; }
    .dashboard { max-width: 900px; margin: 0 auto; display: grid; grid-template-columns: 1fr 3fr; gap: 20px; padding: 20px; }
    
    /* Stats Panel */
    .sidebar { background: #1e1e1e; padding: 20px; border-radius: 10px; border: 1px solid #333; height: fit-content; }
    .stat { font-size: 18px; margin: 15px 0; display: flex; justify-content: space-between; }
    .stat-val { font-weight: bold; color: #00e676; }
    
    .actions button { width: 100%; padding: 12px; margin-top: 10px; border: none; background: #2979ff; color: white; cursor: pointer; font-weight: bold; border-radius: 5px; }
    .actions button:hover { background: #1565c0; }
    .end-turn { background: #ff3d00 !important; }

    /* Map Grid */
    .city-map { display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; }
    
    .zone-card { 
        background: #263238; border: 2px solid #37474f; border-radius: 8px; 
        padding: 15px; position: relative; transition: 0.2s;
    }
    .zone-card:hover { transform: scale(1.02); z-index: 10; border-color: #aaa; }
    
    /* Zone Colors based on ownership */
    .owner-player { border-color: #00e676; background: #1b5e20; }
    .owner-enemy { border-color: #d50000; }
    .owner-boss { border-color: #aa00ff; border-width: 3px; box-shadow: 0 0 10px #aa00ff; }
    
    .zone-header { font-weight: bold; margin-bottom: 5px; font-size: 1.1em; }
    .zone-info { font-size: 0.9em; color: #b0bec5; }
    
    .btn-attack { background: #d50000; color: white; border: none; padding: 5px 10px; cursor: pointer; margin-top: 10px; border-radius: 4px; width: 100%; }
    
    /* Log */
    .log-box { grid-column: 1 / -1; background: #000; color: #00e676; border: 1px solid #333; height: 100px; overflow-y: scroll; padding: 10px; text-align: right; font-size: 14px; }
    .overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.85); display: flex; align-items: center; justify-content: center; z-index: 999; flex-direction: column; }
    .overlay h1 { font-size: 3em; color: gold; }
    a.restart { padding: 15px 30px; background: white; color: black; text-decoration: none; font-weight: bold; border-radius: 5px; margin-top: 20px; }
    
    /* Back Button */
    .back-btn { display: inline-block; margin-top: 15px; color: #777; font-size: 12px; text-decoration:none; }
</style>
"""

HTML_PAGE = """
<!DOCTYPE html>
<html lang="he">
<head>
    <meta charset="UTF-8">
    <title>Underworld Wars</title>
    """ + STYLE + """
</head>
<body>

    <h1>🏙️ UNDERWORLD WARS 🔫</h1>

    {% if game.victory %}
    <div class="overlay">
        <h1>העיר שלך! 👑</h1>
        <p>ניצחת בכל הרובעים. הכנופיות האחרות נמחקו.</p>
        <a href="/game4/reset" class="restart">התחל עונה חדשה</a>
    </div>
    {% endif %}

    {% if game.money <= 0 and game.soldiers <= 0 and not game.victory %}
    <div class="overlay">
        <h1 style="color: red">החוסלת! 💀</h1>
        <p>אין לך כסף ואין חיילים. המשחק נגמר.</p>
        <a href="/game4/reset" class="restart">נסה שוב</a>
    </div>
    {% endif %}

    <div class="dashboard">
        <!-- Sidebar -->
        <div class="sidebar">
            <h3>הכנופיה שלך</h3>
            <div class="stat">💵 מזומן <span class="stat-val">{{ game.money }}$</span></div>
            <div class="stat">🔫 חיילים <span class="stat-val">{{ game.soldiers }}</span></div>
            <div class="stat">👁️ שליטה <span class="stat-val">{{ game.influence }}</span></div>
            <div class="stat">📅 יום <span class="stat-val">{{ game.turn }}</span></div>
            
            <hr>
            <div class="actions">
                <h4>פעולות:</h4>
                <a href="/game4/recruit/1"><button>גייס 1 חייל (50$)</button></a>
                <a href="/game4/recruit/15"><button>גייס 15 חיילים (450$)</button></a>
                <br><br>
                <a href="/game4/next_turn"><button class="end-turn">סיים יום (קבל הכנסה) 🌙</button></a>
                <br>
                <p style="font-size:12px; color:gray">סיום יום נותן כסף אך מחזק את האויב</p>
            </div>
            
            <a href="/" class="back-btn">יציאה לתפריט ראשי</a>
        </div>

        <!-- City Map -->
        <div class="city-map">
            {% for z in game.zones %}
            <div class="zone-card owner-{{ z.owner }}">
                <div class="zone-header">{{ z.name }}</div>
                <div class="zone-info">
                    {% if z.owner == 'player' %}
                        🛡️ בשליטתך<br>
                        💰 הכנסה: {{ z.income }}$
                    {% else %}
                        👿 אויב ({{ 'בוס' if z.owner == 'boss' else 'כנופיה' }})<br>
                        🏰 הגנה משוערת: {{ z.defense }}<br>
                        💰 פוטנציאל: {{ z.income }}$
                        
                        <form action="/game4/attack/{{ z.id }}" method="post">
                            <button class="btn-attack">⚔️ שלח חיילים לכיבוש</button>
                        </form>
                    {% endif %}
                </div>
            </div>
            {% endfor %}
        </div>

        <!-- Game Log -->
        <div class="log-box">
            {% for l in game.log %}
            <div>> {{ l }}</div>
            {% endfor %}
        </div>
    </div>

</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_PAGE, game=gameState)

@app.route('/recruit/<int:amount>')
def recruit(amount):
    cost = 50 * amount
    if amount >= 10: cost = 450 # הנחת כמות
    
    if gameState.money >= cost:
        gameState.money -= cost
        gameState.soldiers += amount
        gameState.log.insert(0, f"גייסת {amount} חיילים חדשים. עלות: {cost}$")
    else:
        gameState.log.insert(0, "❌ אין מספיק מזומן לגיוס.")
    return redirect('/game4/')

@app.route('/attack/<int:zone_id>', methods=['POST'])
def attack(zone_id):
    target = next((z for z in gameState.zones if z['id'] == zone_id), None)
    if not target or target['owner'] == 'player': return redirect('/game4/')

    if gameState.soldiers <= 0:
        gameState.log.insert(0, "❌ אין לך חיילים להתקפה!")
        return redirect('/game4/')

    # Combat Logic
    
    attack_force = gameState.soldiers
    defense_force = target['defense']
    
    # חישוב יחס קרב + רנדומליות
    att_roll = attack_force * random.uniform(0.8, 1.2)
    def_roll = defense_force * random.uniform(0.8, 1.2)

    gameState.log.insert(0, f"⚔️ הקרב על {target['name']} התחיל! שלחת {attack_force} חיילים...")

    if att_roll > def_roll:
        # ניצחון
        losses = int(defense_force * 0.3) 
        gameState.soldiers = max(1, gameState.soldiers - losses)
        
        target['owner'] = 'player'
        target['defense'] = 50 # איפוס הגנה
        
        gameState.log.insert(0, f"✅ ניצחון! כבשת את {target['name']}. איבדת {losses} חיילים. האזור שלך.")
        gameState.check_win_condition()
    else:
        # הפסד
        losses = int(gameState.soldiers * 0.6) 
        gameState.soldiers -= losses
        gameState.log.insert(0, f"💀 הפסד צורב. הכנופיה היריבה הדפה אותך. איבדת {losses} חיילים בנסיגה.")

    return redirect('/game4/')

@app.route('/next_turn')
def next_turn():
    gameState.next_turn()
    return redirect('/game4/')

@app.route('/reset')
def reset():
    gameState.reset()
    return redirect('/game4/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
