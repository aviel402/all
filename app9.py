import time
import random
import json
import uuid
import datetime
from flask import Flask, request, render_template_string, jsonify, make_response

app = Flask(__name__)
app.secret_key = "aether_guilds_key"

DB_FILE = "mmorpg_data.json"

# --- הגדרת המקצועות ---
CLASSES = {
    "guardian": {
        "name": "🛡️ שומר", "hp": 300, "dmg": 5, 
        "skill": "שאגה (מושך אש מהבוס)", "role": "tank", "cd": 5
    },
    "mage": {
        "name": "🔥 מכשף", "hp": 100, "dmg": 40, 
        "skill": "כדור אש (נזק כבד)", "role": "dps", "cd": 4
    },
    "druid": {
        "name": "🌿 דרואיד", "hp": 150, "dmg": 8, 
        "skill": "ריפוי קבוצתי (מרפא את כולם)", "role": "healer", "cd": 6
    }
}

# --- דאטהבייס ומנוע משחק ---

def load_db():
    if not os_path_exists(DB_FILE):
        return init_world()
    try:
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except: return init_world()

def init_world():
    return {
        "players": {},
        "boss": spawn_boss(1),
        "chat": [],
        "last_boss_attack": time.time()
    }

def save_db(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)

def os_path_exists(path):
    import os
    return os.path.exists(path)

def spawn_boss(level):
    names = ["דרקון האפר", "גולם בזלת", "מלך השלדים", "שד הלהבות"]
    return {
        "name": random.choice(names),
        "level": level,
        "max_hp": 1000 + (level * 500),
        "hp": 1000 + (level * 500),
        "dmg": 20 + (level * 5),
        "target": None, # על מי הבוס כועס עכשיו
        "status": "alive"
    }

def add_log(db, text, type="info"):
    msg = {"time": datetime.datetime.now().strftime("%H:%M:%S"), "text": text, "type": type}
    db['chat'].insert(0, msg)
    db['chat'] = db['chat'][:30]

# --- שרת WEB ---

@app.route('/')
def home():
    uid = request.cookies.get('player_id')
    db = load_db()
    if uid and uid in db['players']:
        return render_template_string(GAME_HTML)
    return render_template_string(LOGIN_HTML)

@app.route('/login', methods=['POST'])
def login():
    name = request.form.get('name')
    role = request.form.get('role')
    
    if not name or role not in CLASSES: return "Invalid Data", 400
    
    db = load_db()
    uid = str(uuid.uuid4())
    
    base_stats = CLASSES[role]
    db['players'][uid] = {
        "id": uid, "name": name, "role": role,
        "lvl": 1, "xp": 0,
        "hp": base_stats['hp'], "max_hp": base_stats['hp'],
        "dead_until": 0, "last_action": 0
    }
    
    add_log(db, f"✨ הגיבור {name} ({base_stats['name']}) הצטרף לגילדה.", "join")
    save_db(db)
    
    resp = make_response(jsonify({"status": "ok"}))
    resp.set_cookie('player_id', uid)
    return resp

# --- לוגיקת משחק בזמן אמת ---

@app.route('/api/gamestate')
def gamestate():
    uid = request.cookies.get('player_id')
    db = load_db()
    
    if not uid or uid not in db['players']: return jsonify({"error": "relogin"})
    me = db['players'][uid]
    boss = db['boss']
    
    current_time = time.time()
    
    # 1. התחדשות ובוס AI
    if boss['status'] == "alive":
        # הבוס תוקף כל 3 שניות
        if current_time - db['last_boss_attack'] > 3:
            living_players = [p for p in db['players'].values() if p['hp'] > 0]
            if living_players:
                # אם יש לבוס מטרה ספציפית (טאונט), תקוף אותה. אחרת רנדומלי
                target_id = boss['target']
                victim = next((p for p in living_players if p['id'] == target_id), None)
                
                if not victim: # אם המטרה מתה או לא קיימת, בחר רנדומלי
                    victim = random.choice(living_players)
                    boss['target'] = victim['id']
                
                dmg = boss['dmg'] + random.randint(-5, 5)
                victim['hp'] -= dmg
                db['last_boss_attack'] = current_time
                
                add_log(db, f"👿 {boss['name']} תקף את {victim['name']} ב-{dmg} נזק!", "boss_atk")
                
                if victim['hp'] <= 0:
                    victim['hp'] = 0
                    victim['dead_until'] = current_time + 10 # החייאה אחרי 10 שניות
                    boss['target'] = None # הבוס מחפש קורבן חדש
                    add_log(db, f"💀 {victim['name']} נפל בקרב!", "death")
                
                save_db(db) # שומרים את השינוי כי הבוס פעל אוטונומית

    # 2. החייאת שחקנים מתים
    if me['hp'] <= 0 and current_time > me['dead_until']:
        me['hp'] = int(me['max_hp'] * 0.5)
        save_db(db)

    # 3. בוס Respawn
    if boss['status'] == "dead" and current_time > db['boss_respawn_time']:
        db['boss'] = spawn_boss(boss['level'] + 1)
        add_log(db, f"⚠️ בוס חדש הופיע: {db['boss']['name']} (רמה {db['boss']['level']})", "boss_spawn")
        save_db(db)

    # בניית המידע לתצוגה
    other_players = [p for pid, p in db['players'].items() if pid != uid and (current_time - p.get('last_seen', 0) < 60)]
    
    # עדכון שנראינו לאחרונה (Heartbeat)
    db['players'][uid]['last_seen'] = current_time
    save_db(db) # שמירה לייט ללא כתיבה מסיבית אם אין שינוי משמעותי? כאן נשמור תמיד לשם פשטות.

    return jsonify({
        "me": me,
        "boss": boss,
        "team": other_players,
        "chat": db['chat'],
        "classes": CLASSES
    })

@app.route('/api/action', methods=['POST'])
def action():
    uid = request.cookies.get('player_id')
    act_type = request.json.get('type') # attack, skill
    db = load_db()
    
    me = db['players'][uid]
    boss = db['boss']
    cls = CLASSES[me['role']]
    
    if me['hp'] <= 0: return jsonify({"msg": "אתה מת! חכה להחייאה"})
    if boss['status'] != 'alive': return jsonify({"msg": "הבוס מת"})
    
    current_time = time.time()
    
    # התקפה רגילה
    if act_type == 'attack':
        boss['hp'] -= cls['dmg']
        msg = f"פגעת בבוס ({cls['dmg']})"
    
    # יכולת מיוחדת (Cooldown)
    elif act_type == 'skill':
        if current_time - me['last_action'] < cls['cd']:
            return jsonify({"msg": "היכולת בטעינה!"})
        
        me['last_action'] = current_time
        
        if me['role'] == 'guardian':
            boss['target'] = uid # Taunt
            boss['hp'] -= cls['dmg'] * 2
            add_log(db, f"🛡️ {me['name']} שאג ומשך את הבוס אליו!", "skill")
            
        elif me['role'] == 'mage':
            dmg = cls['dmg'] * 3
            boss['hp'] -= dmg
            add_log(db, f"🔥 {me['name']} הטיל כדור אש! {dmg} נזק.", "skill")
            
        elif me['role'] == 'druid':
            # ריפוי כל הקבוצה
            heal = 40 + (me['lvl'] * 5)
            for p in db['players'].values():
                if p['hp'] > 0:
                    p['hp'] = min(p['max_hp'], p['hp'] + heal)
            add_log(db, f"🌿 {me['name']} ריפא את כל הקבוצה ב-{heal} חיים.", "heal")

    # בדיקה אם הבוס מת
    if boss['hp'] <= 0:
        boss['hp'] = 0
        boss['status'] = "dead"
        db['boss_respawn_time'] = current_time + 10
        # חלוקת XP לכולם
        xp_gain = 50 * boss['level']
        for p in db['players'].values():
            p['xp'] += xp_gain
            if p['xp'] >= p['lvl'] * 100:
                p['lvl'] += 1
                p['xp'] = 0
                p['max_hp'] += 50
                p['hp'] = p['max_hp']
        add_log(db, f"🏆 הבוס חוסל! כולם קיבלו {xp_gain} ניסיון.", "win")

    save_db(db)
    return jsonify({"success": True})

# --- Frontend HTML ---

LOGIN_HTML = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>גילדות האתר - כניסה</title>
<style>
body { background: #1a1a2e; color: #fff; font-family: 'Segoe UI', sans-serif; text-align: center; display: flex; flex-direction: column; justify-content: center; height: 100vh; margin: 0; }
.card { background: #16213e; padding: 30px; border-radius: 15px; border: 2px solid #e94560; max-width: 400px; margin: auto; box-shadow: 0 0 20px rgba(233, 69, 96, 0.2); }
input, select, button { width: 100%; padding: 12px; margin: 10px 0; border-radius: 5px; font-size: 16px; border: none; box-sizing: border-box;}
button { background: #e94560; color: white; font-weight: bold; cursor: pointer; transition: 0.3s; }
button:hover { background: #ff2e63; }
</style>
</head>
<body>
<div class="card">
    <h1>⚔️ גילדות האתר ⚔️</h1>
    <p>העולם זקוק לגיבורים. בחרו נתיב.</p>
    <form id="loginForm">
        <input type="text" id="name" placeholder="שם הגיבור" required>
        <select id="role">
            <option value="guardian">🛡️ שומר (Tank) - המגן האנושי</option>
            <option value="mage">🔥 מכשף (DPS) - אדון האש</option>
            <option value="druid">🌿 דרואיד (Healer) - מרפא הפצעים</option>
        </select>
        <button type="submit">צא להרפתקה</button>
    </form>
</div>
<script>
document.getElementById('loginForm').onsubmit = async (e) => {
    e.preventDefault();
    let fd = new FormData();
    fd.append('name', document.getElementById('name').value);
    fd.append('role', document.getElementById('role').value);
    await fetch('/login', {method: 'POST', body: fd});
    window.location.reload();
}
</script>
</body>
</html>
"""

GAME_HTML = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Raid Battle</title>
<style>
/* Reset & Base */
body { background: #0f0f13; color: #e0e0e0; font-family: 'Segoe UI', Tahoma, sans-serif; margin: 0; padding-bottom: 20px; overflow-x: hidden; }
* { box-sizing: border-box; }

/* HUD Header */
.hud { background: #1f1f25; padding: 10px; display: flex; justify-content: space-between; align-items: center; border-bottom: 3px solid #333; position: sticky; top: 0; z-index: 100; box-shadow: 0 5px 15px rgba(0,0,0,0.5); }
.hero-stats { font-size: 14px; font-weight: bold; }
.hero-lvl { background: #ffd700; color: black; padding: 2px 6px; border-radius: 4px; }

/* Main Boss Arena */
.arena { text-align: center; padding: 20px; min-height: 250px; background: url('https://i.imgur.com/3q1Zc8s.png') no-repeat center; background-size: cover; position: relative; }
.arena::before { content:''; position:absolute; top:0; left:0; width:100%; height:100%; background: rgba(0,0,0,0.7); }
.boss-container { position: relative; z-index: 10; margin: 20px auto; max-width: 600px; }

.boss-avatar { font-size: 80px; text-shadow: 0 0 20px red; animation: float 3s infinite ease-in-out; }
.boss-name { font-size: 24px; font-weight: 900; color: #ff4757; text-transform: uppercase; text-shadow: 0 2px 0 black; margin-bottom: 5px; }
.health-bar { background: #333; height: 20px; width: 100%; border-radius: 10px; overflow: hidden; border: 2px solid #555; position: relative; }
.health-fill { background: #e84118; height: 100%; width: 100%; transition: width 0.3s; }
.health-text { position: absolute; width: 100%; text-align: center; top: -1px; font-size: 14px; font-weight: bold; color: white; text-shadow: 1px 1px 1px black; }

.taunt-marker { font-size: 12px; background: #eccc68; color: black; padding: 3px 8px; border-radius: 10px; display: inline-block; margin-bottom: 5px; border: 1px solid #ffa502; }

/* Player Actions */
.controls { position: fixed; bottom: 0; width: 100%; background: #161b22; padding: 15px; display: flex; gap: 10px; justify-content: center; border-top: 1px solid #30363d; z-index: 100; }
.btn { border: none; padding: 15px 0; border-radius: 8px; font-size: 18px; font-weight: bold; cursor: pointer; flex: 1; max-width: 200px; transition: transform 0.1s, opacity 0.3s; position: relative; overflow: hidden; }
.btn:active { transform: scale(0.95); }
.btn-atk { background: #dfe4ea; color: #2f3542; border-bottom: 4px solid #ced6e0; }
.btn-skill { background: #3742fa; color: white; border-bottom: 4px solid #232eba; }
.btn-cd { position: absolute; top:0; left:0; height:100%; width:100%; background: rgba(0,0,0,0.6); display: none; } /* Cooldown overlay */

/* Party Grid */
.party-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 10px; padding: 15px; margin-bottom: 80px; }
.player-card { background: #2f3640; padding: 10px; border-radius: 8px; text-align: center; border: 1px solid #353b48; transition: 0.3s; }
.p-role { font-size: 24px; margin-bottom: 5px; }
.p-name { font-size: 14px; font-weight: bold; color: #f1f2f6; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.p-hp-bar { height: 6px; background: #222; border-radius: 3px; margin-top: 5px; overflow: hidden; }
.p-hp-fill { height: 100%; background: #2ed573; transition: width 0.3s; }
.dead-card { opacity: 0.5; border-color: red; filter: grayscale(1); }

/* Combat Log */
.logs { background: rgba(0,0,0,0.8); color: #ccc; height: 120px; overflow-y: auto; font-family: monospace; font-size: 12px; padding: 10px; border-bottom: 2px solid #444; }
.log-row { margin-bottom: 3px; }
.log-join { color: #f6e58d; }
.log-boss_atk { color: #ff6b6b; }
.log-heal { color: #7bed9f; }
.log-win { color: gold; font-weight: bold; }

@keyframes float { 0% { transform: translateY(0px); } 50% { transform: translateY(-15px); } 100% { transform: translateY(0px); } }
.shake { animation: shake 0.5s; }
@keyframes shake { 0% { transform: translate(1px, 1px) rotate(0deg); } 10% { transform: translate(-1px, -2px) rotate(-1deg); } 20% { transform: translate(-3px, 0px) rotate(1deg); } 30% { transform: translate(3px, 2px) rotate(0deg); } 40% { transform: translate(1px, -1px) rotate(1deg); } 50% { transform: translate(-1px, 2px) rotate(-1deg); } 60% { transform: translate(-3px, 1px) rotate(0deg); } 70% { transform: translate(3px, 1px) rotate(-1deg); } 80% { transform: translate(-1px, -1px) rotate(1deg); } 90% { transform: translate(1px, 2px) rotate(0deg); } 100% { transform: translate(1px, -2px) rotate(-1deg); } }

</style>
</head>
<body>

<!-- Combat Log -->
<div class="logs" id="chatBox"></div>

<div class="hud">
    <div class="hero-stats">
        <span class="hero-lvl">Lv.<span id="myLvl">1</span></span>
        <span id="myName">Loading...</span>
    </div>
    <div style="font-size:12px; color: #a4b0be">לחץ להתקפה</div>
</div>

<div class="arena" id="arenaBg">
    <div class="boss-container">
        <div class="boss-avatar" id="bossIcon">🐲</div>
        <div id="targetBadge" style="display:none;" class="taunt-marker">TARGET 🎯</div>
        <div class="boss-name" id="bossName">Loading Boss...</div>
        <div class="health-bar">
            <div class="health-fill" id="bossHpBar"></div>
            <div class="health-text"><span id="bossHp">0</span> / <span id="bossMax">0</span></div>
        </div>
    </div>
</div>

<div class="party-grid" id="partyList">
    <!-- שחקנים אחרים יופיעו פה -->
</div>

<div class="controls">
    <button class="btn btn-atk" onclick="doAction('attack')">⚔️ התקפה</button>
    <button class="btn btn-skill" onclick="doAction('skill')" id="skillBtn">
        ✨ <span id="skillName">יכולת</span>
    </button>
</div>

<script>
// סמלים לפי תפקיד
const ICONS = {'guardian': '🛡️', 'mage': '🔥', 'druid': '🌿'};
let skillCooldown = 0;
let cdTimer = null;

async function updateState() {
    try {
        let res = await fetch('/api/gamestate');
        let data = await res.json();
        if(data.error) window.location.reload();

        renderMyStats(data.me, data.classes);
        renderBoss(data.boss, data.players, data.me.id);
        renderParty(data.me, data.team, data.boss.target);
        renderChat(data.chat);
    } catch(e) {}
    
    requestAnimationFrame(() => setTimeout(updateState, 1000));
}

function renderMyStats(me, classes) {
    document.getElementById('myName').innerText = ICONS[me.role] + ' ' + me.name;
    document.getElementById('myLvl').innerText = me.lvl;
    
    // Skill Button
    let btn = document.getElementById('skillBtn');
    let skillData = classes[me.role];
    document.getElementById('skillName').innerText = skillData.skill;
    skillCooldown = skillData.cd; // שמירה לשימוש ללחיצה
    
    if (me.hp <= 0) {
        document.body.style.filter = "grayscale(1)";
    } else {
        document.body.style.filter = "none";
    }
}

function renderBoss(boss, players, myId) {
    if (boss.status === 'dead') {
        document.getElementById('bossName').innerText = "💀 הבוס מת...";
        document.getElementById('bossIcon').innerText = "⚰️";
        document.getElementById('bossHpBar').style.width = "0%";
        document.getElementById('targetBadge').style.display = 'none';
        return;
    }

    document.getElementById('bossName').innerText = boss.name + " (Lv." + boss.level + ")";
    document.getElementById('bossIcon').innerText = "🐲"; // או גיוון לפי שם
    document.getElementById('bossHp').innerText = boss.hp;
    document.getElementById('bossMax').innerText = boss.max_hp;
    let pct = (boss.hp / boss.max_hp) * 100;
    document.getElementById('bossHpBar').style.width = pct + "%";
    
    // האם הבוס מסתכל עליי?
    let targetEl = document.getElementById('targetBadge');
    if (boss.target === myId) {
        targetEl.style.display = 'inline-block';
        targetEl.innerText = "😡 תוקף אותך!";
        targetEl.style.background = 'red';
        targetEl.style.color = 'white';
        document.getElementById('arenaBg').style.borderColor = "red";
    } else if (boss.target) {
        targetEl.style.display = 'inline-block';
        targetEl.innerText = "🎯 נעול על טרף";
        targetEl.style.background = '#eccc68';
        document.getElementById('arenaBg').style.borderColor = "transparent";
    } else {
        targetEl.style.display = 'none';
    }
}

function renderParty(me, others, bossTarget) {
    let list = document.getElementById('partyList');
    let html = ``;
    
    // אני (תמיד ראשון)
    let myHpPct = (me.hp / me.max_hp) * 100;
    html += createCardHTML(me, myHpPct, true, me.id === bossTarget);
    
    // אחרים
    others.forEach(p => {
        let pct = (p.hp / p.max_hp) * 100;
        html += createCardHTML(p, pct, false, p.id === bossTarget);
    });
    
    list.innerHTML = html;
}

function createCardHTML(p, hpPct, isMe, isTarget) {
    let hpColor = hpPct < 30 ? '#ff4757' : '#2ed573';
    let border = isTarget ? 'border: 2px solid red;' : '';
    let deadClass = p.hp <= 0 ? 'dead-card' : '';
    let youLabel = isMe ? '<small>(אתה)</small>' : '';
    
    return `
    <div class="player-card ${deadClass}" style="${border}">
        <div class="p-role">${ICONS[p.role]}</div>
        <div class="p-name">${p.name} ${youLabel}</div>
        <div class="p-hp-bar">
            <div class="p-hp-fill" style="width:${hpPct}%; background:${hpColor}"></div>
        </div>
        <div style="font-size:10px; margin-top:2px;">${p.hp}/${p.max_hp}</div>
    </div>
    `;
}

function renderChat(logs) {
    let box = document.getElementById('chatBox');
    let html = '';
    logs.forEach(l => {
        let cls = `log-${l.type}`;
        html += `<div class="log-row ${cls}"><span style="opacity:0.5">[${l.time}]</span> ${l.text}</div>`;
    });
    box.innerHTML = html;
}

async function doAction(type) {
    // אנימציית Cooldown פשוטה בכפתור
    let btn = type === 'attack' ? document.querySelector('.btn-atk') : document.querySelector('.btn-skill');
    
    if (type === 'skill') {
        btn.disabled = true;
        btn.style.opacity = 0.5;
        setTimeout(() => { btn.disabled = false; btn.style.opacity = 1; }, skillCooldown * 1000);
    }
    
    // אפקט רעידה לזירה בהתקפה
    document.getElementById('bossIcon').classList.add('shake');
    setTimeout(()=>document.getElementById('bossIcon').classList.remove('shake'), 500);

    await fetch('/api/action', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({type: type})
    });
    // רענון מיידי לתגובה מהירה
    updateState();
}

// התחל
updateState();

</script>
</body>
</html>
"""

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
