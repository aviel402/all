import random
import uuid
import time
from flask import Flask, render_template_string, request, jsonify, session

app = Flask(__name__)
app.secret_key = "cyber_syndicate_omega_key"

# --- 🧠 LORE & DATA ---

ZONE_TEMPLATES = [
    {"name": "שכונות העוני", "base_def": 20, "base_inc": 100, "desc": "מקור טוב לגיוס אנשים זולים."},
    {"name": "הנמל הישן", "base_def": 50, "base_inc": 250, "desc": "נתיב הברחות ראשי."},
    {"name": "רובע הברים", "base_def": 40, "base_inc": 350, "desc": "מזומנים זורמים כמו אלכוהול."},
    {"name": "מחסני הרכבת", "base_def": 80, "base_inc": 200, "desc": "מקום אסטרטגי לאחסון נשק."},
    {"name": "אזור התעשייה", "base_def": 120, "base_inc": 450, "desc": "מפעלים לייצור סמים סינתטיים."},
    {"name": "הקזינו הגדול", "base_def": 250, "base_inc": 900, "desc": "היהלום שבכתר."},
    {"name": "בניין העירייה", "base_def": 300, "base_inc": 600, "desc": "שליטה פוליטית וכוח מוחלט."},
    {"name": "הכספת הבנקאית", "base_def": 400, "base_inc": 1200, "desc": "המבצר הכלכלי של העיר."}
]

# --- 🎮 GAME ENGINE ---

def new_game_state():
    """Create a pristine game state."""
    zones = []
    for i, t in enumerate(ZONE_TEMPLATES):
        # אזור ראשון של השחקן
        owner = "player" if i == 0 else "enemy"
        soldiers = 10 if owner == "player" else int(t["base_def"] * 0.5)
        
        zones.append({
            "id": i,
            "name": t["name"],
            "desc": t["desc"],
            "income": t["base_inc"],
            "max_hp": t["base_def"], # בריאות הביצורים
            "hp": t["base_def"] if owner == "enemy" else 50,
            "owner": owner,
            "soldiers": soldiers,
            "level": 1,
            "spied": False # האם השחקן יודע מה הולך שם
        })

    return {
        "turn": 1,
        "cash": 800,
        "manpower": 20,  # מאגר חיילים פנויים (במפקדה)
        "heat": 0,       # רמת תשומת לב משטרתית (0-100)
        "reputation": 0,
        "tech": {"atk": 1.0, "def": 1.0}, # שדרוגים טכנולוגיים
        "zones": zones,
        "log": [{"turn": 1, "msg": "המערכת אותחלה. העיר מחכה לבוס חדש."}],
        "game_over": False
    }

def get_state():
    if 'game_id' not in session or 'game_data' not in session:
        session['game_id'] = str(uuid.uuid4())
        session['game_data'] = new_game_state()
    return session['game_data']

def save_state(state):
    session['game_data'] = state

# --- ROUTES ---

@app.route('/')
def index():
    return render_template_string(HTML_UI)

@app.route('/api/data')
def api_data():
    """Sends current game state to JS."""
    return jsonify(get_state())

@app.route('/api/recruit', methods=['POST'])
def api_recruit():
    state = get_state()
    if state['game_over']: return jsonify({"error": "Game Over"})
    
    amount = int(request.json.get('amount', 1))
    cost = amount * 50
    
    if state['cash'] >= cost:
        state['cash'] -= cost
        state['manpower'] += amount
        log(state, f"גויסו {amount} חיילים למפקדה (עלות: {cost}$)")
    else:
        return jsonify({"error": "אין מספיק כסף"})
    
    save_state(state)
    return jsonify(state)

@app.route('/api/upgrade_tech', methods=['POST'])
def api_upgrade_tech():
    state = get_state()
    type_ = request.json.get('type') # 'atk' or 'def'
    cost = int(state['tech'][type_] * 1000)
    
    if state['cash'] >= cost:
        state['cash'] -= cost
        state['tech'][type_] = round(state['tech'][type_] + 0.2, 1)
        name = "נשק מתקדם" if type_ == 'atk' else "שריון גוף"
        log(state, f"שדרוג {name} נרכש! רמה נוכחית: {state['tech'][type_]}")
    else:
        return jsonify({"error": "אין מספיק כסף"})

    save_state(state)
    return jsonify(state)

@app.route('/api/bribe', methods=['POST'])
def api_bribe():
    state = get_state()
    if state['heat'] <= 0: return jsonify({"error": "אין לחץ משטרתי"})
    
    cost = state['heat'] * 20
    if state['cash'] >= cost:
        state['cash'] -= cost
        state['heat'] = max(0, state['heat'] - 20)
        log(state, f"שיחדת את המפכ\"ל. המשטרה נרגעה. עלות: {cost}$")
    else:
        return jsonify({"error": "שוחד יקר מדי"})
        
    save_state(state)
    return jsonify(state)

@app.route('/api/spy', methods=['POST'])
def api_spy():
    state = get_state()
    z_id = request.json.get('id')
    zone = state['zones'][z_id]
    
    if state['cash'] >= 200:
        state['cash'] -= 200
        zone['spied'] = True
        log(state, f"המרגלים חזרו עם מידע על {zone['name']}.")
    else:
        return jsonify({"error": "אין מספיק כסף לריגול"})

    save_state(state)
    return jsonify(state)

@app.route('/api/attack', methods=['POST'])
def api_attack():
    state = get_state()
    z_id = request.json.get('id')
    soldiers_to_send = int(request.json.get('soldiers', 0))
    
    zone = state['zones'][z_id]
    
    if soldiers_to_send > state['manpower']:
        return jsonify({"error": "אין מספיק חיילים במפקדה"})
    
    state['manpower'] -= soldiers_to_send
    
    # חישוב קרב
    combat_log = []
    combat_log.append(f"⚔️ תקיפה על {zone['name']}!")
    
    player_power = soldiers_to_send * state['tech']['atk'] * random.uniform(0.9, 1.2)
    
    # חישוב הגנת האויב (חיילים + ביצורים)
    enemy_power = (zone['soldiers'] * 1.0) + (zone['hp'] * 0.5)
    
    victory = False
    
    if player_power > enemy_power:
        victory = True
        losses = int(zone['soldiers'] * 0.4) # שחקן מאבד פחות כי ניצח
        remaining_attackers = max(1, int(soldiers_to_send - losses))
        
        zone['owner'] = 'player'
        zone['soldiers'] = remaining_attackers
        zone['hp'] = int(zone['max_hp'] * 0.5) # ביצורים נפגעו בקרב
        state['heat'] += 10 # תקיפה מעלה חום
        state['reputation'] += 20
        
        combat_log.append(f"💥 ניצחון מוחץ! כוחות האויב הושמדו.")
        combat_log.append(f"🩸 אבידות: {soldiers_to_send - remaining_attackers} חיילים.")
        log(state, f"כיבוש {zone['name']} הושלם בהצלחה.")
    else:
        losses = soldiers_to_send # כולם מתו
        combat_log.append(f"💀 כישלון! הכוח נפל למארב.")
        combat_log.append(f"האויב שמר על השטח.")
        state['heat'] += 5
        log(state, f"מתקפה על {zone['name']} נכשלה. כל הכוח אבד.")
        
    save_state(state)
    return jsonify({"state": state, "combat_log": combat_log, "victory": victory})

@app.route('/api/next_turn', methods=['POST'])
def api_next_turn():
    state = get_state()
    state['turn'] += 1
    
    # 1. הכנסות
    income = 0
    player_zones = [z for z in state['zones'] if z['owner'] == 'player']
    
    for z in player_zones:
        income += z['income'] * (z['level'] * 1.0) # הכנסה לפי רמה
        # שיקום איטי של ביצורים
        z['hp'] = min(z['max_hp'], z['hp'] + 10)
    
    # חישוב הפסדים עקב "חום" (המשטרה מחרימה כסף)
    police_fine = 0
    if state['heat'] > 50:
        police_fine = int(income * (state['heat'] / 200))
        log(state, f"🚨 פשיטה משטרתית! הוחרמו {police_fine}$ מהרווחים.")
    
    actual_income = max(0, int(income - police_fine))
    state['cash'] += actual_income
    
    log(state, f"📆 תור {state['turn']}: רווח נקי {actual_income}$")
    
    # 2. האויב מתחזק ומגיב
    enemy_zones = [z for z in state['zones'] if z['owner'] == 'enemy']
    
    # גדילה טבעית של האויב
    for z in enemy_zones:
        z['soldiers'] += random.randint(2, 5)
        # סיכוי קטן שזון שהרגנו בו מרגלים יחזור להיות נסתר
        if z['spied'] and random.random() < 0.2:
            z['spied'] = False
    
    # התקפת נגד! (Counter Attack)
    # האויב יתקוף אם יש לו מספיק כוח ויש שטח שחקן חלש
    if len(player_zones) > 0 and random.random() < 0.3:
        target = min(player_zones, key=lambda x: x['soldiers']) # תוקף את החלש ביותר
        attacker = max(enemy_zones, key=lambda x: x['soldiers']) if enemy_zones else None
        
        if attacker and attacker['soldiers'] > target['soldiers'] + 20:
            attack_force = int(attacker['soldiers'] * 0.6)
            
            log(state, f"⚠️ התראת חירום! האויב תוקף את {target['name']} עם {attack_force} חיילים!")
            
            def_power = target['soldiers'] * state['tech']['def'] + (target['hp'] / 5)
            att_power = attack_force * 1.0 
            
            if att_power > def_power:
                target['owner'] = 'enemy'
                target['soldiers'] = int(attack_force * 0.7)
                log(state, f"❌ איבדת שליטה ב{target['name']}! האויב כבש אותו מחדש.")
            else:
                losses = int(target['soldiers'] * 0.2)
                target['soldiers'] -= losses
                log(state, f"🛡️ ההגנה הצליחה! הדפת את המתקפה על {target['name']}.")

    # אירועים רנדומליים
    roll_event(state)

    save_state(state)
    return jsonify(state)

@app.route('/api/restart')
def api_restart():
    session.clear()
    return jsonify(get_state())

# --- UTIL ---
def log(state, msg):
    state['log'].insert(0, {"turn": state['turn'], "msg": msg})
    if len(state['log']) > 50: state['log'].pop()

def roll_event(state):
    chance = random.random()
    if chance < 0.05:
        bonus = 300
        state['cash'] += bonus
        log(state, f"🍀 משאית משוריינת נשדדה בהצלחה! +{bonus}$")
    elif chance > 0.95:
        # אסון
        loss = int(state['manpower'] * 0.2)
        state['manpower'] -= loss
        log(state, f"🤧 שפעת קטלנית במפקדה. {loss} חיילים חלו/מתו.")

# --- HTML/JS APP ---

HTML_UI = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>NEON SYNDICATE WARS</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Segoe+UI:wght@300;400;700&display=swap');
        
        :root {
            --bg-dark: #050505;
            --neon-blue: #00f3ff;
            --neon-red: #ff0055;
            --neon-green: #00ff66;
            --neon-purple: #bc13fe;
            --glass: rgba(20, 20, 30, 0.7);
            --border: 1px solid rgba(255, 255, 255, 0.1);
        }

        body {
            background-color: var(--bg-dark);
            color: #eee;
            font-family: 'Segoe UI', sans-serif;
            margin: 0;
            padding: 20px;
            background-image: 
                radial-gradient(circle at 50% 50%, rgba(0, 50, 100, 0.2), transparent 70%),
                linear-gradient(0deg, transparent 98%, rgba(0, 243, 255, 0.05) 99%);
            background-size: 100% 100%, 100% 20px;
            overflow: hidden;
            height: 100vh;
            display: flex;
            gap: 20px;
        }
        
        h1, h2, h3 { margin: 0 0 10px 0; text-transform: uppercase; letter-spacing: 2px; }
        .text-blue { color: var(--neon-blue); text-shadow: 0 0 10px var(--neon-blue); }
        .text-red { color: var(--neon-red); text-shadow: 0 0 10px var(--neon-red); }
        
        button {
            background: rgba(0, 243, 255, 0.1);
            color: var(--neon-blue);
            border: 1px solid var(--neon-blue);
            padding: 10px 20px;
            cursor: pointer;
            transition: all 0.3s;
            font-weight: bold;
            font-family: inherit;
        }
        button:hover { background: var(--neon-blue); color: #000; box-shadow: 0 0 20px var(--neon-blue); }
        button:disabled { opacity: 0.3; cursor: not-allowed; }
        
        .btn-danger { color: var(--neon-red); border-color: var(--neon-red); background: rgba(255,0,85,0.1); }
        .btn-danger:hover { background: var(--neon-red); box-shadow: 0 0 20px var(--neon-red); color:white; }

        /* LAYOUT */
        .sidebar { width: 350px; display: flex; flex-direction: column; gap: 20px; }
        .main-area { flex-grow: 1; display: flex; flex-direction: column; gap: 20px; overflow: hidden; }

        /* CARDS */
        .panel {
            background: var(--glass);
            border: var(--border);
            padding: 20px;
            backdrop-filter: blur(10px);
            box-shadow: 0 4px 30px rgba(0, 0, 0, 0.5);
        }

        /* STATS GRID */
        .stats-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 20px; }
        .stat-box { background: rgba(0,0,0,0.3); padding: 10px; border-right: 2px solid #555; }
        .stat-label { font-size: 12px; color: #888; display:block; }
        .stat-val { font-size: 20px; font-weight: bold; }
        
        /* LOG */
        #log-container {
            flex-grow: 1; overflow-y: auto; font-family: monospace; font-size: 13px;
            border-top: 1px solid #333; margin-top: 10px; padding-top: 10px;
        }
        .log-entry { margin-bottom: 5px; animation: fadeIn 0.3s forwards; }
        .log-turn { color: #888; display: inline-block; width: 60px; }

        /* CITY MAP */
        #city-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 15px;
            overflow-y: auto;
            padding-right: 10px;
            flex-grow: 1;
        }
        
        .zone-card {
            background: rgba(0,0,0,0.6);
            border: 1px solid #333;
            padding: 15px;
            position: relative;
            transition: 0.2s;
            cursor: pointer;
        }
        .zone-card:hover { transform: translateY(-5px); border-color: #aaa; }
        .zone-card.owned { border-color: var(--neon-green); box-shadow: inset 0 0 10px rgba(0,255,102,0.1); }
        .zone-card.enemy { border-color: var(--neon-red); }
        
        .zone-name { font-weight: bold; font-size: 1.1em; }
        .zone-badge { position: absolute; top: 10px; left: 10px; font-size: 20px; }
        
        .bar-container { background: #333; height: 5px; margin: 10px 0; width: 100%; position:relative; }
        .bar-fill { height: 100%; transition: width 0.5s; }
        .def-fill { background: var(--neon-blue); }
        
        /* ACTIONS FOOTER */
        .actions-bar {
            display: flex; gap: 10px; margin-top: 10px; flex-wrap: wrap;
        }
        .tech-box { font-size: 12px; border: 1px solid #333; padding: 5px; flex-grow: 1; display:flex; justify-content:space-between; align-items:center; }

        /* MODAL */
        #modal-overlay {
            position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0,0,0,0.8); z-index: 100;
            display: none; align-items: center; justify-content: center;
        }
        .modal {
            width: 400px; background: #111; border: 1px solid var(--neon-purple);
            padding: 30px; text-align: center; position:relative;
            box-shadow: 0 0 50px rgba(188, 19, 254, 0.3);
        }
        .slider-container { margin: 20px 0; }

        /* Animations */
        @keyframes fadeIn { from { opacity: 0; transform: translateY(5px); } to { opacity: 1; transform: translateY(0); } }
        
        /* Scrollbar */
        ::-webkit-scrollbar { width: 5px; }
        ::-webkit-scrollbar-track { background: #111; }
        ::-webkit-scrollbar-thumb { background: #333; }
        ::-webkit-scrollbar-thumb:hover { background: var(--neon-blue); }

    </style>
</head>
<body>

    <div class="sidebar panel">
        <h2 class="text-blue">COMMAND CENTER</h2>
        
        <div class="stats-grid">
            <div class="stat-box" style="border-right-color: var(--neon-green);">
                <span class="stat-label">CASH FLOW</span>
                <div class="stat-val text-green" style="color:var(--neon-green)">$<span id="stat-cash">0</span></div>
            </div>
            <div class="stat-box" style="border-right-color: var(--neon-purple);">
                <span class="stat-label">SOLDIERS (HQ)</span>
                <div class="stat-val" style="color:var(--neon-purple)"><span id="stat-men">0</span></div>
            </div>
            <div class="stat-box" style="border-right-color: var(--neon-red);">
                <span class="stat-label">HEAT LEVEL</span>
                <div class="stat-val" style="color:var(--neon-red)"><span id="stat-heat">0</span>%</div>
            </div>
            <div class="stat-box">
                <span class="stat-label">DAY CYCLE</span>
                <div class="stat-val"><span id="stat-turn">1</span></div>
            </div>
        </div>

        <button onclick="recruit()" style="width:100%">💪 גייס כנופיה (+10 איש) - 500$</button>
        <button onclick="nextTurn()" class="btn-danger" style="width:100%; margin-top:10px;">🌙 סיים יום / אסוף רווחים</button>
        
        <h4 style="margin-top:20px;">מו"פ / שוק שחור</h4>
        <div class="tech-box">
            <span>נשק (<span id="tech-atk">1.0</span>)</span>
            <button onclick="upgradeTech('atk')" style="padding:2px 10px; font-size:10px;">שדרג</button>
        </div>
        <div class="tech-box" style="margin-top:5px;">
            <span>שריון (<span id="tech-def">1.0</span>)</span>
            <button onclick="upgradeTech('def')" style="padding:2px 10px; font-size:10px;">שדרג</button>
        </div>
        
        <button onclick="bribe()" style="width:100%; margin-top:10px; border-color:#fff; color:#fff;">💼 לשחד שוטרים (הורדת לחץ)</button>
        
        <div id="log-container"></div>
        
        <div style="margin-top:auto; text-align:center;">
             <button onclick="restartGame()" style="background:none; border:none; color:#555; font-size:10px;">RESTART SYSTEM</button>
        </div>
    </div>

    <div class="main-area">
        <div class="panel" style="height:100%; display:flex; flex-direction:column;">
            <div style="display:flex; justify-content:space-between;">
                <h3 class="text-blue">CITY SURVEILLANCE MAP</h3>
                <small style="color:#888">CLICK ZONE FOR OPTIONS</small>
            </div>
            
            <div id="city-grid">
                <!-- Zones Injected Here -->
            </div>
        </div>
    </div>

    <!-- ATTACK/INTERACT MODAL -->
    <div id="modal-overlay">
        <div class="modal">
            <h2 id="modal-title" class="text-blue">TARGET NAME</h2>
            <p id="modal-desc" style="color:#aaa">...</p>
            
            <div id="enemy-intel">
                <div style="display:flex; justify-content:space-between; margin:10px 0;">
                    <span>🏰 הגנה: <span id="m-hp">0</span></span>
                    <span>🔫 חיילים: <span id="m-sol">??</span></span>
                    <span>💰 הכנסה: <span id="m-inc">0</span></span>
                </div>
            </div>
            
            <hr style="border-color:#333; margin:15px 0;">
            
            <div id="modal-actions-enemy">
                <button onclick="doSpy()" style="margin-bottom:10px;">🕵️ שלח מרגלים (200$)</button>
                <br>
                <div class="slider-container">
                     <label>כמה חיילים לשלוח? <span id="slider-val" class="text-blue">0</span></label><br>
                     <input type="range" id="attack-slider" min="1" max="100" value="10" oninput="updateSlider()" style="width:100%">
                </div>
                <button onclick="doAttack()" class="btn-danger" style="width:100%">⚔️ בצע פשיטה!</button>
            </div>
            
            <div id="modal-actions-player" style="display:none;">
                <p style="color:var(--neon-green)">השטח הזה שלך.</p>
            </div>
            
            <button onclick="closeModal()" style="position:absolute; top:10px; right:10px; background:none; border:none; color:white;">✕</button>
        </div>
    </div>

    <script>
        let game = null;
        let selectedZone = null;

        async function refresh() {
            const res = await fetch('/api/data');
            game = await res.json();
            render();
        }

        function render() {
            if (game.game_over) {
                alert("GAME OVER!");
                return;
            }

            // Stats
            document.getElementById('stat-cash').innerText = game.cash;
            document.getElementById('stat-men').innerText = game.manpower;
            document.getElementById('stat-heat').innerText = game.heat;
            document.getElementById('stat-turn').innerText = game.turn;
            document.getElementById('tech-atk').innerText = game.tech.atk;
            document.getElementById('tech-def').innerText = game.tech.def;

            // Logs
            const logDiv = document.getElementById('log-container');
            logDiv.innerHTML = '';
            game.log.forEach(l => {
                const row = document.createElement('div');
                row.className = 'log-entry';
                row.innerHTML = `<span class="log-turn">[T${l.turn}]</span> ${l.msg}`;
                logDiv.appendChild(row);
            });

            // Zones Grid
            const grid = document.getElementById('city-grid');
            grid.innerHTML = '';
            
            game.zones.forEach(z => {
                const el = document.createElement('div');
                el.className = `zone-card ${z.owner == 'player' ? 'owned' : 'enemy'}`;
                el.onclick = () => openZone(z.id);
                
                const hpPercent = (z.hp / z.max_hp) * 100;
                const badge = z.owner == 'player' ? '🛡️' : (z.spied ? '👁️' : '🔒');
                const soldiersDisp = (z.owner == 'player' || z.spied) ? z.soldiers : '???';
                
                el.innerHTML = `
                    <div class="zone-badge">${badge}</div>
                    <div class="zone-name" style="margin-left: 30px">${z.name}</div>
                    <div style="font-size:12px; color:#888;">${z.owner == 'player' ? 'טריטוריה שלך' : 'שטח עוין'}</div>
                    
                    <div style="margin-top:10px; font-size:13px; display:flex; justify-content:space-between;">
                        <span>💰 ${z.income}</span>
                        <span>🔫 ${soldiersDisp}</span>
                    </div>
                    
                    <div class="bar-container">
                        <div class="bar-fill def-fill" style="width: ${hpPercent}%"></div>
                    </div>
                `;
                grid.appendChild(el);
            });
        }

        // --- ACTIONS ---

        async function nextTurn() {
            await fetch('/api/next_turn', {method:'POST'});
            refresh();
        }

        async function recruit() {
            const amt = prompt("כמה לגייס? (50$ לאחד)", "10");
            if(amt){
                await fetch('/api/recruit', {
                    method:'POST',
                    headers:{'Content-Type':'application/json'},
                    body: JSON.stringify({amount: amt})
                });
                refresh();
            }
        }
        
        async function upgradeTech(type) {
             await fetch('/api/upgrade_tech', {
                method:'POST',
                headers:{'Content-Type':'application/json'},
                body: JSON.stringify({type: type})
            });
            refresh();
        }

        async function bribe() {
             await fetch('/api/bribe', {method:'POST'});
             refresh();
        }

        async function restartGame() {
            await fetch('/api/restart');
            refresh();
        }

        // --- MODAL & ATTACK ---

        function openZone(zid) {
            selectedZone = game.zones[zid];
            document.getElementById('modal-overlay').style.display = 'flex';
            document.getElementById('modal-title').innerText = selectedZone.name;
            document.getElementById('modal-desc').innerText = selectedZone.desc;
            
            // Intel Logic
            document.getElementById('m-inc').innerText = selectedZone.income;
            if (selectedZone.owner == 'player' || selectedZone.spied) {
                 document.getElementById('m-hp').innerText = `${selectedZone.hp}/${selectedZone.max_hp}`;
                 document.getElementById('m-sol').innerText = selectedZone.soldiers;
            } else {
                 document.getElementById('m-hp').innerText = `???/${selectedZone.max_hp}`;
                 document.getElementById('m-sol').innerText = "???";
            }

            // Buttons Display
            const actEnemy = document.getElementById('modal-actions-enemy');
            const actPlayer = document.getElementById('modal-actions-player');
            
            if(selectedZone.owner == 'player') {
                actEnemy.style.display = 'none';
                actPlayer.style.display = 'block';
            } else {
                actEnemy.style.display = 'block';
                actPlayer.style.display = 'none';
                // Slider limit based on current manpower
                const s = document.getElementById('attack-slider');
                s.max = game.manpower;
                s.value = Math.min(game.manpower, 10);
                updateSlider();
            }
        }
        
        function closeModal() {
            document.getElementById('modal-overlay').style.display = 'none';
        }

        function updateSlider() {
            const val = document.getElementById('attack-slider').value;
            document.getElementById('slider-val').innerText = val;
        }

        async function doSpy() {
            await fetch('/api/spy', {
                method:'POST', headers:{'Content-Type':'application/json'},
                body: JSON.stringify({id: selectedZone.id})
            });
            closeModal();
            refresh();
        }

        async function doAttack() {
            const count = document.getElementById('attack-slider').value;
            closeModal();
            
            // Animation for visual effect (simulation)
            alert("מבצע התקפה... אנא המתן לדיווח.");
            
            const res = await fetch('/api/attack', {
                method:'POST', headers:{'Content-Type':'application/json'},
                body: JSON.stringify({id: selectedZone.id, soldiers: count})
            });
            const data = await res.json();
            
            // Show battle log in a simpler way or alert
            let battleText = data.combat_log.join("\n");
            alert(battleText);
            
            refresh();
        }

        // Initial Load
        refresh();

    </script>
</body>
</html>
"""

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
