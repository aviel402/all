import json
import uuid
import time
import random
import os
from flask import Flask, request, render_template_string, redirect, jsonify, make_response

app = Flask(__name__)
app.secret_key = "factions_war_secret_key"

# --- הקבוע שיסדר את כל הבעיות ---
GAME_PATH = "/game6" 

DB_FILE = "factions_db.json"

ROLES = {
    "fighter": {"name": "🗡️ לוחם", "hp": 120, "ap_regen": 2, "desc": "תוקף שחקנים וגונב כסף"},
    "merchant": {"name": "💎 סוחר", "hp": 80, "ap_regen": 3, "desc": "מייצר כסף ומבצע עסקאות"},
    "manager": {"name": "👔 מנהל", "hp": 100, "ap_regen": 1, "desc": "גובה מיסים ושולט בתקציב העיר"},
    "spy": {"name": "🕵️ מרגל", "hp": 60, "ap_regen": 4, "desc": "בלתי נראה, גונב בשקט"}
}

# --- דאטהבייס ---
def load_db():
    if not os.path.exists(DB_FILE):
        return {"players": {}, "city_bank": 500, "logs": []}
    try:
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {"players": {}, "city_bank": 500, "logs": []}

def save_db(data):
    try:
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
    except: pass

def add_log(db, text):
    import datetime
    time_str = datetime.datetime.now().strftime("%H:%M:%S")
    db['logs'].insert(0, f"[{time_str}] {text}")
    db['logs'] = db['logs'][:50]

# --- HTML ---

LOGIN_HTML = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Factions - התחברות</title>
<style>
body { background: #111; color: white; font-family: sans-serif; text-align: center; padding: 20px; }
input, select, button { padding: 15px; margin: 10px; width: 80%; border-radius: 8px; border: none; font-size: 18px; }
button { background: #00d4ff; color: #000; font-weight: bold; cursor: pointer; }
.card { background: #222; padding: 20px; border-radius: 15px; border: 1px solid #444; max-width: 400px; margin: 0 auto; }
</style>
</head>
<body>
<h1>FACTIONS WARS 🌍</h1>
<div class="card">
    <!-- שימוש בפרמטר base -->
    <form action="{{ base }}/login" method="post">
        <input type="text" name="username" placeholder="בחר כינוי" required>
        <h3>בחר מעמד:</h3>
        <select name="role">
            <option value="fighter">🗡️ לוחם (קרבי)</option>
            <option value="merchant">💎 סוחר (כלכלי)</option>
            <option value="manager">👔 מנהל (פוליטי)</option>
            <option value="spy">🕵️ מרגל (התגנבות)</option>
        </select>
        <button type="submit">היכנס לעולם</button>
    </form>
</div>
<a href="/" style="display:block; margin-top:20px; color:#555;">חזרה ללובי</a>
</body>
</html>
"""

GAME_HTML = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Factions Game</title>
<style>
body { margin:0; background: #0f0f13; color: #e0e0e0; font-family: 'Segoe UI', sans-serif; padding-bottom: 20px;}
.header { background: #1f1f23; padding: 15px; position: sticky; top:0; z-index:100; border-bottom: 2px solid #00d4ff; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 5px 20px rgba(0,0,0,0.5); }
.stats span { margin-left: 10px; font-weight: bold; }
.ap { color: #ffd700; } .hp { color: #ff4d4d; } .money { color: #00ff7f; }
.container { max-width: 600px; margin: 0 auto; padding: 10px; }
.logs { background: #000; height: 120px; overflow-y: scroll; padding: 10px; border-radius: 8px; border: 1px solid #333; font-size: 13px; font-family: monospace; color: #888; margin-bottom: 20px; }
.player-card { background: #25252b; margin-bottom: 10px; padding: 15px; border-radius: 10px; display: flex; justify-content: space-between; align-items: center; border: 1px solid #333; }
.player-name { font-weight: bold; font-size: 16px; color: #fff; }
.player-role { font-size: 12px; color: #aaa; }
.actions { display: flex; gap: 5px; }
button { border: none; padding: 8px 12px; border-radius: 5px; cursor: pointer; font-weight: bold; transition: 0.2s; }
.btn-atk { background: #b71c1c; color: white; }
.btn-tax { background: #1565c0; color: white; }
.btn-steal { background: #4a148c; color: white; }
.btn-self { background: #333; color: #aaa; border: 1px solid #555; width: 100%; margin-bottom: 15px; padding: 12px; }
.toast { position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%); background: #333; padding: 10px 20px; border-radius: 20px; border: 1px solid #00d4ff; display: none; z-index: 200; box-shadow: 0 0 15px rgba(0,212,255,0.4); }
.bank-info { text-align: center; color: #888; font-size: 12px; margin-top: -15px; margin-bottom: 15px; }
.back-btn { display:block; text-align:center; color:#555; text-decoration:none; margin-top:20px; }
</style>
</head>
<body>

<div class="header">
    <div style="font-weight:900; font-size:18px;">{{ me.name }}</div>
    <div class="stats">
        <span class="hp">❤️ <span id="val-hp">{{ me.hp }}</span></span>
        <span class="ap">⚡ <span id="val-ap">{{ me.ap }}</span></span>
        <span class="money">💵 <span id="val-money">{{ me.money }}</span></span>
    </div>
</div>

<div class="container">
    <div style="text-align: center; color: #aaa; font-size: 14px; margin: 10px 0;">אתה משחק בתור: <b>{{ role_name }}</b></div>
    
    {% if me.role == 'merchant' %}
        <button class="btn-self" onclick="doAction('trade')" style="background: #1b5e20; color: #fff; border: 1px solid #66bb6a;">⚖️ בצע עסקת מסחר (הכנסה)</button>
    {% endif %}
    
    <button class="btn-self" onclick="doAction('heal')">💊 קנה תרופה (20$)</button>

    <div class="logs" id="log-box">טוען נתונים...</div>
    <div class="bank-info">🏛️ קופת העיר: <span id="city-bank">0</span>$</div>
    <div id="players-list"></div>
    <a href="/" class="back-btn">יציאה ללובי</a>
</div>

<div id="toast" class="toast">הודעה</div>

<script>
const BASE_PATH = "{{ base }}"; // הפרמטר מגיע מכאן!

function update() {
    // שרשור הקבוע לנתיב ה-API
    fetch(BASE_PATH + '/api/update')
    .then(r => r.json())
    .then(data => {
        if(data.reload) window.location.reload();
        
        document.getElementById('val-hp').innerText = data.me.hp;
        document.getElementById('val-ap').innerText = data.me.ap;
        document.getElementById('val-money').innerText = data.me.money;
        document.getElementById('city-bank').innerText = data.city_bank;

        let logsHtml = "";
        data.logs.forEach(l => logsHtml += `<div>${l}</div>`);
        document.getElementById('log-box').innerHTML = logsHtml;

        let playersHtml = "";
        data.players.forEach(p => {
            let actions = "";
            let myRole = "{{ me.role }}";
            
            if (myRole === 'fighter') actions = `<button class="btn-atk" onclick="doAction('attack', '${p.id}')">תקוף</button>`;
            else if (myRole === 'manager') actions = `<button class="btn-tax" onclick="doAction('tax', '${p.id}')">החרם כסף</button>`;
            else if (myRole === 'spy') actions = `<button class="btn-steal" onclick="doAction('steal', '${p.id}')">גנוב</button>`;
            else if (myRole === 'merchant') actions = `<span style='font-size:12px; color:gray'>לקוח</span>`;

            let moneyDisplay = myRole === 'spy' ? `<div style="color:gold; font-size:11px">💰 ${p.money}</div>` : '';

            playersHtml += `
            <div class="player-card">
                <div class="player-info">
                    <div class="player-name">${p.role_icon} ${p.name}</div>
                    <div class="player-role">❤️ ${p.hp} | ${p.role}</div>
                    ${moneyDisplay}
                </div>
                <div class="actions">${actions}</div>
            </div>`;
        });
        
        if (data.players.length === 0) playersHtml = "<div style='text-align:center; padding:20px; color:#555'>העיר שקטה...</div>";
        document.getElementById('players-list').innerHTML = playersHtml;
    });
}

function doAction(act, targetId = null) {
    fetch(BASE_PATH + '/api/action', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ action: act, target_id: targetId })
    })
    .then(r => r.json())
    .then(res => {
        if(res.error) alert(res.error);
        if(res.msg) showToast(res.msg);
        update(); 
    });
}

function showToast(msg) {
    let t = document.getElementById('toast');
    t.innerText = msg;
    t.style.display = 'block';
    setTimeout(() => { t.style.display = 'none'; }, 3000);
}

setInterval(update, 2000);
update();
</script>
</body>
</html>
"""

# --- צד השרת ---

@app.route('/')
def home():
    uid = request.cookies.get('user_id')
    db = load_db()
    
    # שליחת הפרמטר base לתבנית ה-HTML
    if not uid or uid not in db['players']:
        return render_template_string(LOGIN_HTML, base=GAME_PATH)
    
    player = db['players'][uid]
    return render_template_string(GAME_HTML, me=player, role_name=ROLES[player['role']]['name'], base=GAME_PATH)

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    role = request.form.get('role')
    
    if not username or role not in ROLES:
        return "Error", 400

    db = load_db()
    uid = str(uuid.uuid4())
    
    db['players'][uid] = {
        "id": uid, "name": username, "role": role,
        "money": 100 if role != 'manager' else 1000,
        "hp": ROLES[role]['hp'], "max_hp": ROLES[role]['hp'],
        "ap": 10, "max_ap": 10, "last_seen": time.time()
    }
    
    add_log(db, f"✨ {username} הצטרף ({ROLES[role]['name']}).")
    save_db(db)
    
    # הפנייה עם הקידומת
    resp = make_response(redirect(f"{GAME_PATH}/"))
    resp.set_cookie('user_id', uid)
    return resp

@app.route('/api/update')
def api_update():
    uid = request.cookies.get('user_id')
    db = load_db()
    
    if not uid or uid not in db['players']: return jsonify({"reload": True})
    
    me = db['players'][uid]
    current_time = time.time()
    
    # regen
    if current_time - me['last_seen'] > 5:
        regen = ROLES[me['role']]['ap_regen']
        me['ap'] = min(me['max_ap'], me['ap'] + regen)
        me['last_seen'] = current_time
        save_db(db)

    visible_players = []
    for pid, p in db['players'].items():
        if pid == uid: continue
        if current_time - p['last_seen'] > 60: continue 
        if p['role'] == 'spy' and me['role'] != 'spy': continue 
        
        visible_players.append({
            "id": p['id'], "name": p['name'], "role": p['role'],
            "role_icon": ROLES[p['role']]['name'].split(' ')[0],
            "hp": p['hp'],
            "money": p['money'] if me['role'] == 'spy' else '???'
        })

    return jsonify({ "me": me, "city_bank": db['city_bank'], "players": visible_players, "logs": db['logs'] })

@app.route('/api/action', methods=['POST'])
def perform_action():
    data = request.json
    action = data.get('action')
    target_id = data.get('target_id')
    uid = request.cookies.get('user_id')
    db = load_db()
    me = db['players'].get(uid)
    target = db['players'].get(target_id)
    
    if not me: return jsonify({"error": "No User"})
    if me['ap'] < 2: return jsonify({"msg": "❌ אין מספיק אנרגיה!"})
    
    msg = ""
    # Actions logic (Shortened)
    if action == 'attack' and target:
        dmg = random.randint(10, 20)
        target['hp'] -= dmg
        me['ap'] -= 3
        msg = f"פגעת! ({dmg} נזק)"
        add_log(db, f"⚔️ {me['name']} תקף את {target['name']}.")
    elif action == 'trade':
        me['money'] += 30; db['city_bank'] += 5; me['ap'] -= 3
        msg = "הרווחת כסף!"
    elif action == 'heal':
        if me['money']>=20:
            me['money']-=20; me['hp']+=30
            msg="נרפאת."
            
    save_db(db)
    return jsonify({"msg": msg})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
