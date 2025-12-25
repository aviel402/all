import json
import uuid
import time
import math
import random
from flask import Flask, render_template_string, request, jsonify, make_response, redirect

app = Flask(__name__)
app.secret_key = "iron_and_dust_key"

DB_FILE = "iron_dust.json"
MAP_SIZE = 10 # גודל מפה 10x10

# --- נתונים קבועים ---
BUILDINGS = {
    "mine": {"name": "מכרה ברזל", "cost": {"iron": 0, "fuel": 50}, "prod": 5, "desc": "מייצר ברזל (+5/דקה)"},
    "refinery": {"name": "זיקוק דלק", "cost": {"iron": 100, "fuel": 0}, "prod": 5, "desc": "מייצר דלק (+5/דקה)"},
    "barracks": {"name": "קסרקטין", "cost": {"iron": 200, "fuel": 100}, "prod": 0, "desc": "מאפשר גיוס חיילים"},
    "wall": {"name": "חומת מגן", "cost": {"iron": 500, "fuel": 0}, "prod": 0, "desc": "מגן על הבסיס (+100 הגנה)"},
}

# --- דאטהבייס ---
def get_empty_map():
    # מייצר מפה ריקה
    grid = {}
    for y in range(MAP_SIZE):
        for x in range(MAP_SIZE):
            key = f"{x},{y}"
            grid[key] = {
                "x": x, "y": y,
                "owner": None,      # מזהה השחקן
                "building": None,   # סוג בניין
                "level": 0,
                "soldiers": 0       # חיילים המגנים על המשבצת
            }
    return grid

def load_db():
    default_db = {
        "players": {},
        "map": get_empty_map(),
        "events": [], # פעולות עתידיות (בנייה, תזוזת כוחות)
        "last_tick": time.time()
    }
    
    if not os_path_exists(DB_FILE): return default_db
    try:
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # אם אין מפה (גרסה ישנה), צור אותה
            if "map" not in data: data["map"] = get_empty_map()
            return data
    except: return default_db

def save_db(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)

def os_path_exists(path):
    import os
    return os.path.exists(path)

# --- מנוע הזמן (The Logic Engine) ---
def update_world(db):
    current_time = time.time()
    time_delta = current_time - db['last_tick']
    
    # 1. חישוב ייצור משאבים (לפי זמן שעבר)
    if time_delta > 0:
        minutes_passed = time_delta / 60
        
        for pid, p in db['players'].items():
            # בסיס מקבל הכנסה בסיסית
            p['res']['iron'] += 10 * minutes_passed
            p['res']['fuel'] += 10 * minutes_passed
            
            # בדיקת מבנים שהשחקן מחזיק
            for cell in db['map'].values():
                if cell['owner'] == pid and cell['building']:
                    b_type = cell['building']
                    if b_type == 'mine':
                        p['res']['iron'] += 5 * minutes_passed
                    elif b_type == 'refinery':
                        p['res']['fuel'] += 5 * minutes_passed
    
    # 2. הרצת אירועים (בנייה/תקיפה)
    # אנו ממיינים את האירועים לפי זמן הביצוע ומבצעים אותם לפי הסדר
    pending_events = [e for e in db['events'] if e['time'] <= current_time]
    future_events = [e for e in db['events'] if e['time'] > current_time]
    
    pending_events.sort(key=lambda x: x['time'])
    
    for event in pending_events:
        process_event(db, event)
    
    db['events'] = future_events
    db['last_tick'] = current_time
    save_db(db)

def process_event(db, ev):
    # ביצוע הפעולה שהסתיימה
    target_key = ev['target']
    cell = db['map'].get(target_key)
    
    if ev['type'] == 'build':
        # סיום בנייה
        if cell['owner'] == ev['player_id']:
            cell['building'] = ev['building']
            add_notif(db, ev['player_id'], f"✅ הבנייה של {BUILDINGS[ev['building']]['name']} הסתיימה ב-{target_key}.")

    elif ev['type'] == 'move':
        # הגעת כוחות
        attacker_id = ev['player_id']
        army_size = ev['amount']
        
        if cell['owner'] == attacker_id:
            # הגעה לטריטוריה שלי (תגבור)
            cell['soldiers'] += army_size
            add_notif(db, attacker_id, f"🛡️ תגבורת של {army_size} חיילים הגיעה ל-{target_key}.")
        
        elif cell['owner'] is None:
            # כיבוש שטח נטוש
            cell['owner'] = attacker_id
            cell['soldiers'] = army_size
            add_notif(db, attacker_id, f"🏳️ כבשת אזור נטוש ב-{target_key}.")
            
        else:
            # --- מלחמה! ---
            defender_id = cell['owner']
            def_force = cell['soldiers']
            
            # בונוס הגנה אם יש חומה
            if cell['building'] == 'wall': def_force += 50
            
            # חישוב קרב פשוט (מי שנשאר לו יותר)
            # הטיה רנדומלית קטנה לקרב
            att_power = army_size * random.uniform(0.9, 1.1)
            def_power = def_force * random.uniform(0.9, 1.3) # יתרון למגן
            
            if att_power > def_power:
                # התוקף ניצח
                survivors = int(army_size * 0.7) # מאבדים חיילים בקרב
                cell['owner'] = attacker_id
                cell['soldiers'] = max(1, survivors)
                cell['building'] = None # הרס המבנה בכיבוש
                
                add_notif(db, attacker_id, f"⚔️ ניצחון! כבשת את {target_key} מידי האויב. שרדו {cell['soldiers']} חיילים.")
                add_notif(db, defender_id, f"🆘 האזור {target_key} נפל בקרב! האויב כבש אותו.")
            else:
                # המגן ניצח
                cell['soldiers'] = max(1, int(cell['soldiers'] * 0.8)) # המגן שורד אבל נפגע
                add_notif(db, attacker_id, f"💀 המתקפה על {target_key} נכשלה. כל הצבא אבד.")
                add_notif(db, defender_id, f"🛡️ מתקפה על {target_key} נהדפה בהצלחה.")

def add_notif(db, uid, msg):
    if uid in db['players']:
        # הוסף להתחלה (רק 10 הודעות אחרונות)
        db['players'][uid]['notifs'].insert(0, f"{time.strftime('%H:%M')} {msg}")
        db['players'][uid]['notifs'] = db['players'][uid]['notifs'][:10]

# --- שרת WEB ---

@app.route('/')
def home():
    uid = request.cookies.get('user_id')
    db = load_db()
    
    if not uid or uid not in db['players']:
        return render_template_string(LOGIN_HTML)
    
    # תמיד מעדכנים עולם לפני שמציגים למשתמש
    update_world(db)
    
    return render_template_string(GAME_HTML)

@app.route('/login', methods=['POST'])
def login():
    name = request.form.get('name')
    if not name: return "error", 400
    
    db = load_db()
    uid = str(uuid.uuid4())
    
    # חיפוש משבצת התחלה פנויה (רנדומלית)
    free_cells = [k for k,v in db['map'].items() if v['owner'] is None]
    if not free_cells: return "המפה מלאה! חכה לעולם חדש.", 200
    
    start_pos_key = random.choice(free_cells)
    
    db['players'][uid] = {
        "id": uid, "name": name,
        "res": {"iron": 200, "fuel": 200},
        "notifs": ["ברוך הבא למפקדה. העולם אכזרי בחוץ."],
        "color": random_color()
    }
    
    # הקצאת שטח התחלה
    db['map'][start_pos_key]['owner'] = uid
    db['map'][start_pos_key]['soldiers'] = 10
    
    save_db(db)
    resp = make_response(redirect('/'))
    resp.set_cookie('user_id', uid, max_age=60*60*24*30)
    return resp

def random_color():
    return "#{:06x}".format(random.randint(0, 0xFFFFFF))

# API למשיכת נתונים למפה
@app.route('/api/state')
def get_state():
    uid = request.cookies.get('user_id')
    db = load_db()
    update_world(db) # חישוב זמן
    
    if uid not in db['players']: return jsonify({"reload": True})
    
    # מסננים מידע רגיש (כמות חיילים של אחרים)
    public_map = {}
    for k, cell in db['map'].items():
        cell_view = cell.copy()
        if cell['owner'] != uid:
            cell_view['soldiers'] = '???' # ערפל קרב
        public_map[k] = cell_view
        
    return jsonify({
        "me": db['players'][uid],
        "map": public_map,
        "players_names": {pid: p['name'] for pid, p in db['players'].items()} # מילון שמות
    })

@app.route('/api/action', methods=['POST'])
def action():
    uid = request.cookies.get('user_id')
    data = request.json
    act = data.get('act')
    target_xy = data.get('target') # "3,4"
    
    db = load_db()
    me = db['players'][uid]
    update_world(db) # לוודא שיש משאבים עדכניים
    
    msg = ""
    
    if act == "recruit":
        amount = 10
        cost = 50 # ברזל
        if me['res']['iron'] >= cost:
            me['res']['iron'] -= cost
            # החיילים נוצרים בבירה (איפה שהם נמצאים זה לא מומש פה למען הפשטות, אז נוסיף לטריטוריה הראשונה שמצוא)
            # לטובת המשחק, נניח שאפשר לגייס בכל טריטוריה שבשליטתנו
            my_tiles = [k for k,v in db['map'].items() if v['owner'] == uid]
            if my_tiles:
                target_tile = my_tiles[0] # גיוס לטריטוריה הראשונה (בסיס)
                db['map'][target_tile]['soldiers'] += amount
                msg = f"גייסת {amount} חיילים בבסיס {target_tile}"
            else:
                msg = "אין לך טריטוריה! גיים אובר."
        else:
            msg = "אין מספיק ברזל."

    elif act == "build":
        # בניית מבנה
        b_type = data.get('type')
        tile = db['map'].get(target_xy)
        
        if tile and tile['owner'] == uid:
            cost = BUILDINGS[b_type]['cost']
            if me['res']['iron'] >= cost['iron'] and me['res']['fuel'] >= cost['fuel']:
                # תשלום
                me['res']['iron'] -= cost['iron']
                me['res']['fuel'] -= cost['fuel']
                
                # יצירת אירוע בנייה (לוקח 30 שניות בדמו הזה)
                finish_time = time.time() + 30 
                db['events'].append({
                    "time": finish_time,
                    "type": "build",
                    "player_id": uid,
                    "target": target_xy,
                    "building": b_type
                })
                msg = f"הבנייה של {BUILDINGS[b_type]['name']} החלה! (30 שניות)"
            else:
                msg = "אין מספיק משאבים."
        else:
            msg = "אינך יכול לבנות בשטח שאינו שלך."

    elif act == "move":
        # הזזת כוחות / תקיפה
        amount = int(data.get('amount', 0))
        from_xy = data.get('origin')
        
        source = db['map'].get(from_xy)
        dest = db['map'].get(target_xy)
        
        if source and dest and source['owner'] == uid:
            if source['soldiers'] >= amount and amount > 0:
                # חישוב מרחק וזמן
                sx, sy = source['x'], source['y']
                dx, dy = dest['x'], dest['y']
                distance = math.sqrt((dx-sx)**2 + (dy-sy)**2)
                travel_time = distance * 10 # 10 שניות לכל משבצת מרחק
                
                # עלות דלק למסע
                fuel_cost = int(distance * 2)
                if me['res']['fuel'] >= fuel_cost:
                    me['res']['fuel'] -= fuel_cost
                    source['soldiers'] -= amount
                    
                    finish_time = time.time() + travel_time
                    db['events'].append({
                        "time": finish_time,
                        "type": "move",
                        "player_id": uid,
                        "target": target_xy,
                        "amount": amount
                    })
                    msg = f"הכוח יצא לדרך! זמן הגעה משוער: {int(travel_time)} שניות."
                else:
                    msg = f"אין מספיק דלק למסע ({fuel_cost})."
            else:
                msg = "אין מספיק חיילים במשבצת המקור."
    
    save_db(db)
    return jsonify({"msg": msg})

# --- CSS & JS Frontend ---

LOGIN_HTML = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<title>Iron & Dust - Login</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body { background: #111; color: #ddd; font-family: sans-serif; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }
.card { background: #222; padding: 30px; border: 1px solid #444; border-radius: 8px; text-align: center; }
button { padding: 10px 20px; font-size: 18px; background: #e67e22; border: none; cursor: pointer; color: white; margin-top: 10px; }
input { padding: 10px; font-size: 16px; text-align: center; background: #333; color: white; border: 1px solid #555; }
</style>
</head>
<body>
<div class="card">
    <h1>🌍 Iron & Dust</h1>
    <p>עולם אסטרטגיה בזמן אמת.</p>
    <form action="/login" method="post">
        <input type="text" name="name" placeholder="שם המפקד" required><br>
        <button>ייסד מושבה</button>
    </form>
</div>
</body>
</html>
"""

GAME_HTML = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
<title>Iron & Dust</title>
<style>
/* CSS לאווירה צבאית/פוסט-אפוקליפטית */
body { margin:0; background: #0b0c10; color: #c5c6c7; font-family: 'Segoe UI', sans-serif; overflow: hidden; }
* { box-sizing: border-box; }

/* פאנל עליון */
.hud {
    height: 60px; background: #1f2833; display: flex; align-items: center; justify-content: space-between; padding: 0 15px; border-bottom: 2px solid #45a29e;
    box-shadow: 0 0 10px rgba(0,0,0,0.8);
}
.res-box { display: flex; gap: 15px; font-size: 14px; font-weight: bold; }
.res { color: #66fcf1; } 
.notif-btn { background: #c3073f; border:none; color:white; border-radius: 50%; width: 25px; height: 25px; cursor: pointer; }

/* מפת העולם */
#map-container {
    width: 100vw; height: calc(100vh - 60px);
    overflow: scroll; /* מאפשר גלילה במפה גדולה */
    background: #000;
    position: relative;
    display: flex;
    justify-content: center;
    align-items: center;
}

#grid {
    display: grid;
    grid-template-columns: repeat(10, 60px); /* 10 עמודות */
    gap: 2px;
    padding: 20px;
}

.tile {
    width: 60px; height: 60px;
    background: #2b2e31;
    border: 1px solid #444;
    position: relative;
    cursor: pointer;
    display: flex; justify-content: center; align-items: center;
    font-size: 20px;
}
.tile:hover { border-color: #66fcf1; }
.tile.mine { border: 2px solid gold; background: #3d3d29; } /* משבצת שלי */
.tile-soldiers { position: absolute; bottom: 2px; right: 2px; font-size: 10px; color: #fff; background: rgba(0,0,0,0.6); padding: 1px 3px; border-radius: 4px; }
.tile-build { position: absolute; top: 2px; left: 2px; font-size: 12px; }

/* פאנל פעולות (Modal) */
#panel {
    position: absolute; bottom: -300px; left: 0; width: 100%; height: 300px;
    background: #151515; border-top: 2px solid #66fcf1;
    transition: bottom 0.3s; z-index: 100;
    padding: 20px;
    display: flex; flex-direction: column;
}
#panel.open { bottom: 0; }
.panel-header { display: flex; justify-content: space-between; margin-bottom: 10px; }
.btn-close { background: transparent; border: none; color: white; font-size: 20px; cursor: pointer; }

.actions { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
button { padding: 12px; background: #45a29e; border: none; color: black; font-weight: bold; cursor: pointer; }
button:active { transform: scale(0.98); }
button.atk { background: #c3073f; color: white; }

#notifications {
    position: fixed; top: 60px; right: 0; width: 300px; max-height: 200px;
    background: rgba(0,0,0,0.9); color: #0f0; padding: 10px;
    font-family: monospace; font-size: 12px;
    display: none; border: 1px solid #0f0; overflow-y: auto;
}

</style>
</head>
<body>

<div class="hud">
    <div id="username" style="color:white; font-weight:bold;">Loading...</div>
    <div class="res-box">
        <span>🔩 ברזל: <span id="res-iron" class="res">0</span></span>
        <span>⛽ דלק: <span id="res-fuel" class="res">0</span></span>
    </div>
    <button class="notif-btn" onclick="toggleNotifs()">!</button>
</div>

<div id="notifications"></div>

<div id="map-container">
    <div id="grid">
        <!-- JS ייצור את המשבצות כאן -->
    </div>
</div>

<div id="panel">
    <div class="panel-header">
        <h3 id="panel-title" style="margin:0">אזור לא ידוע</h3>
        <button class="btn-close" onclick="closePanel()">✕</button>
    </div>
    <div id="panel-content" class="actions">
        <!-- תוכן דינמי -->
    </div>
    <div id="status-msg" style="margin-top:10px; color:orange; font-size:12px;"></div>
</div>

<script>
let state = null;
let selectedTile = null; // הקואורדינטות הנבחרות כרגע "3,4"
let myId = null;

async function update() {
    let r = await fetch('/api/state');
    let d = await r.json();
    if(d.reload) window.location.reload();
    
    state = d;
    myId = d.me.id;
    
    // HUD Update
    document.getElementById('username').innerText = d.me.name;
    document.getElementById('res-iron').innerText = Math.floor(d.me.res.iron);
    document.getElementById('res-fuel').innerText = Math.floor(d.me.res.fuel);
    
    renderNotifs(d.me.notifs);
    renderMap(d.map);
    
    // אם פאנל פתוח, עדכן אותו
    if(selectedTile) updatePanelContent();
}

function renderMap(mapData) {
    const grid = document.getElementById('grid');
    grid.innerHTML = ''; // מנקה ובונה מחדש (אפשר לייעל)
    
    // מעבר על גודל מפה קבוע
    for (let y=0; y<10; y++) {
        for (let x=0; x<10; x++) {
            let key = `${x},${y}`;
            let cell = mapData[key];
            
            let div = document.createElement('div');
            div.className = 'tile';
            div.onclick = () => selectTile(key);
            
            // צבע הבעלים
            if (cell.owner) {
                if (cell.owner === myId) div.classList.add('mine');
                else {
                    div.style.background = '#3e1515'; // אויב
                    div.style.borderColor = 'red';
                }
            }
            
            // אייקון בניין
            let icon = "";
            if (cell.building === 'mine') icon = "⛏️";
            else if (cell.building === 'refinery') icon = "🛢️";
            else if (cell.building === 'barracks') icon = "🎪";
            else if (cell.building === 'wall') icon = "🧱";
            
            div.innerHTML = `<span class='tile-build'>${icon}</span>`;
            
            // חיילים (רק אם זה שלי או שאין ערפל קרב מלא)
            if (cell.soldiers !== '???') {
                div.innerHTML += `<span class='tile-soldiers'>${cell.soldiers}</span>`;
            }
            
            grid.appendChild(div);
        }
    }
}

function renderNotifs(list) {
    const el = document.getElementById('notifications');
    el.innerHTML = list.map(n => `<div>${n}</div>`).join('');
}

function toggleNotifs() {
    let el = document.getElementById('notifications');
    el.style.display = el.style.display === 'block' ? 'none' : 'block';
}

function selectTile(key) {
    selectedTile = key;
    document.getElementById('panel').classList.add('open');
    updatePanelContent();
}

function closePanel() {
    document.getElementById('panel').classList.remove('open');
    selectedTile = null;
}

function updatePanelContent() {
    if (!selectedTile) return;
    const cell = state.map[selectedTile];
    const container = document.getElementById('panel-content');
    const title = document.getElementById('panel-title');
    
    title.innerText = `קואורדינטות ${selectedTile}`;
    
    let html = "";
    
    // מצב 1: שטח שלי
    if (cell.owner === myId) {
        title.innerText += " (הבסיס שלך)";
        if (!cell.building) {
            html += `<button onclick="sendAction('build', 'mine')">בנה מכרה ברזל (50 דלק)</button>`;
            html += `<button onclick="sendAction('build', 'refinery')">בנה מזקקה (100 ברזל)</button>`;
            html += `<button onclick="sendAction('build', 'wall')">בנה חומה (500 ברזל)</button>`;
        } else {
            html += `<div style="grid-column: span 2; text-align:center">כבר בנוי: ${cell.building}</div>`;
        }
        
        // גיוס ושיגור כוחות
        html += `<button onclick="sendAction('recruit')">גייס 10 חיילים (50 ברזל)</button>`;
        html += `<button onclick="showMoveOptions()">🚀 שלח כוחות למקום אחר</button>`;
        
    } else {
        // מצב 2: אויב או נטוש
        let ownerName = cell.owner ? (state.players_names[cell.owner] || 'אויב') : 'נטוש';
        title.innerText += ` (${ownerName})`;
        
        html += `<div style="grid-column: span 2; text-align:center">כדי לכבוש, עליך לשלוח כוחות מהשטח שלך.</div>`;
        html += `<div style="color:#aaa; text-align:center">לחץ על אחד מהבסיסים שלך ואז בחר "שלח כוחות" לפה.</div>`;
    }
    
    container.innerHTML = html;
}

function showMoveOptions() {
    let dest = prompt("לאיזה קואורדינטות לשלוח? (פורמט: x,y)", "0,0");
    if(!dest) return;
    let amount = prompt("כמה חיילים לשלוח?", "10");
    
    sendAction('move', null, { amount: amount, origin: selectedTile, target: dest });
}

async function sendAction(act, type=null, extra={}) {
    let payload = { act: act, target: selectedTile };
    if (type) payload.type = type;
    if (extra.amount) { 
        payload.amount = extra.amount; 
        payload.origin = extra.origin; 
        payload.target = extra.target; // Override target for move
    }
    
    let res = await fetch('/api/action', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload)
    });
    let data = await res.json();
    document.getElementById('status-msg').innerText = data.msg;
    update();
}

// Loop
setInterval(update, 2000);
update(); // First run

</script>
</body>
</html>
"""

if __name__ == '__main__':
    # הרצת השרת בפורט 80 (נגיש כשרת ווב רגיל) או 5000
    app.run(host='0.0.0.0', port=5000, debug=True)
