import json
import uuid
import time
import random
import datetime
from flask import Flask, request, render_template_string, jsonify, make_response

app = Flask(__name__)
app.secret_key = "chrono_master_key"

DB_FILE = "chrono_db.json"

# --- ניהול דאטהבייס ---
def load_db():
    default_db = {
        "users": {},
        "daily_data": {
            "date": "",
            "seed": 0,
            "leaderboard": [] # list of {name, time}
        }
    }
    if not os_path_exists(DB_FILE): return default_db
    try:
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except: return default_db

def save_db(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)

def os_path_exists(path):
    import os
    return os.path.exists(path)

def get_today_str():
    return datetime.datetime.now().strftime("%Y-%m-%d")

# --- לוגיקת אתגר יומי ---
def check_daily_reset(db):
    today = get_today_str()
    # אם התאריך השתנה מאז הפעם האחרונה שנשמר
    if db['daily_data']['date'] != today:
        print(f"🔄 מתחיל יום חדש: {today}")
        db['daily_data'] = {
            "date": today,
            "seed": random.randint(1000, 999999), # המפתח לאתגר הזהה לכולם
            "leaderboard": []
        }
        # איפוס סטטוס "שיחק היום" למשתמשים
        for uid in db['users']:
            db['users'][uid]['played_today'] = False
        save_db(db)

# --- Routes ---

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/api/init')
def init_game():
    db = load_db()
    check_daily_reset(db)
    
    uid = request.cookies.get('user_id')
    user = None
    
    if uid and uid in db['users']:
        user = db['users'][uid]
    
    # יצירת הלוח הזהה לכולם על סמך ה-Seed היומי
    seed = db['daily_data']['seed']
    # משתמשים ב-Random של פייתון עם הסיד כדי לקבל את אותו סדר תמיד
    rng = random.Random(seed)
    numbers = list(range(1, 26)) # מספרים 1 עד 25
    rng.shuffle(numbers)
    
    leaderboard = sorted(db['daily_data']['leaderboard'], key=lambda x: x['time'])[:10]
    
    return jsonify({
        "grid": numbers,
        "date": db['daily_data']['date'],
        "user": user,
        "leaderboard": leaderboard
    })

@app.route('/api/register', methods=['POST'])
def register():
    name = request.json.get('name')
    if not name: return jsonify({"error": "חובה להזין שם"}), 400
    
    db = load_db()
    uid = str(uuid.uuid4())
    
    db['users'][uid] = {
        "name": name,
        "best_all_time": None,
        "games_played": 0,
        "played_today": False
    }
    save_db(db)
    
    resp = make_response(jsonify({"success": True}))
    resp.set_cookie('user_id', uid, max_age=60*60*24*365)
    return resp

@app.route('/api/submit', methods=['POST'])
def submit():
    uid = request.cookies.get('user_id')
    finish_time = request.json.get('time') # זמן בשניות (למשל 12.45)
    
    if not finish_time: return jsonify({"error": "שגיאה בנתונים"})
    
    db = load_db()
    check_daily_reset(db) # ליתר ביטחון
    
    if uid not in db['users']: return jsonify({"error": "משתמש לא רשום"})
    
    user = db['users'][uid]
    
    # מניעת רמאות בסיסית (אי אפשר להגיש פעמיים ביום)
    if user.get('played_today'):
        return jsonify({"error": "כבר שיחקת היום! נתראה מחר."})
    
    # עדכון סטטיסטיקות
    user['played_today'] = True
    user['games_played'] += 1
    
    # שיא אישי
    if user['best_all_time'] is None or finish_time < user['best_all_time']:
        user['best_all_time'] = finish_time
    
    # הוספה ללוח המובילים היומי
    entry = {
        "name": user['name'],
        "time": finish_time,
        "rank": 0 # יחושב בהמשך
    }
    db['daily_data']['leaderboard'].append(entry)
    
    save_db(db)
    
    return jsonify({"success": True, "time": finish_time})

# --- ממשק HTML/JS/CSS ---

HTML = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
<title>ChronoDaily</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Rubik:wght@400;700;900&display=swap');

body {
    background-color: #121214; color: white; font-family: 'Rubik', sans-serif;
    margin: 0; padding: 10px; display: flex; flex-direction: column; align-items: center; min-height: 100vh;
    overflow-x: hidden;
}

/* UI COMPONENTS */
.header { width: 100%; max-width: 500px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.logo { font-size: 24px; font-weight: 900; background: linear-gradient(45deg, #00f260, #0575e6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.timer { font-size: 32px; font-weight: bold; font-variant-numeric: tabular-nums; color: #fff; }

.container { max-width: 500px; width: 100%; }

/* GAME GRID */
.grid {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 8px;
    margin-bottom: 20px;
    perspective: 1000px;
}

.cell {
    background: #1e1e24;
    aspect-ratio: 1;
    border-radius: 8px;
    display: flex; justify-content: center; align-items: center;
    font-size: 20px; font-weight: bold; cursor: pointer;
    box-shadow: 0 4px 0 #111;
    transition: transform 0.1s, background 0.2s;
    user-select: none;
}
.cell:active { transform: translateY(4px); box-shadow: none; }
.cell.correct { background: #00e676; color: black; opacity: 0; transform: scale(0.5); pointer-events: none; }
.cell.wrong { animation: shake 0.3s; background: #ff1744; }

@keyframes shake { 0%{transform: translateX(0)} 25%{transform: translateX(5px)} 75%{transform: translateX(-5px)} 100%{transform: translateX(0)} }

/* LOGIN & LEADERBOARD */
.card { background: #202024; padding: 20px; border-radius: 16px; text-align: center; margin-bottom: 15px; border: 1px solid #333; }
input { background: #121214; border: 1px solid #444; color: white; padding: 12px; font-size: 18px; border-radius: 8px; width: 80%; text-align: center; }
button { margin-top: 15px; background: #007bff; color: white; padding: 12px 30px; border: none; border-radius: 8px; font-size: 18px; font-weight: bold; cursor: pointer; }

.rank-row { display: flex; justify-content: space-between; padding: 10px; border-bottom: 1px solid #333; }
.rank-row:nth-child(1) { color: gold; font-weight: 900; }
.rank-row:nth-child(2) { color: silver; font-weight: bold; }
.rank-row:nth-child(3) { color: #cd7f32; font-weight: bold; }

.overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.9); z-index: 100; display: none; justify-content: center; align-items: center; flex-direction: column; }
.big-score { font-size: 60px; font-weight: 900; color: #00e676; margin: 10px; }

</style>
</head>
<body>

    <div class="header">
        <div class="logo">ChronoDaily</div>
        <div class="timer" id="timer">0.000</div>
    </div>

    <!-- מסך הרשמה -->
    <div id="login-screen" class="container">
        <div class="card">
            <h2>מוכן לאתגר היומי?</h2>
            <p>לחץ על המספרים 1-25 לפי הסדר.</p>
            <p style="color: #888">כל העולם מקבל את אותו לוח.</p>
            <br>
            <input id="username" placeholder="הכנס שם משתמש">
            <button onclick="register()">התחל משחק</button>
        </div>
    </div>

    <!-- לוח המשחק -->
    <div id="game-screen" class="container" style="display:none">
        <div class="card" id="start-msg">
            <h3>המשימה: 1 עד 25</h3>
            <p>הזמן יתחיל בלחיצה הראשונה על "1".</p>
        </div>
        <div class="grid" id="grid"></div>
    </div>

    <!-- תוצאות ודירוג -->
    <div id="leaderboard-screen" class="container" style="display:none">
        <div class="card" id="result-card" style="display:none; border-color: #00e676;">
            <h3>הזמן שלך היום</h3>
            <div class="big-score" id="final-time-display"></div>
            <div>ניסיון אחד. אין חרטות.</div>
        </div>

        <div class="card">
            <h3>🏆 המובילים היום (<span id="today-date"></span>)</h3>
            <div id="ranks-list"></div>
        </div>
        
        <div style="text-align: center; color: #666; margin-top: 20px;">
            האתגר הבא בעוד: <span id="countdown"></span>
        </div>
    </div>

<script>
let currentNumber = 1;
let startTime = null;
let timerInterval;
let gameActive = false;
let myUser = null;

// טעינה ראשונית
fetch('/api/init').then(r=>r.json()).then(data => {
    document.getElementById('today-date').innerText = data.date;
    
    // בניה הלוח
    const grid = document.getElementById('grid');
    grid.innerHTML = '';
    data.grid.forEach(num => {
        let div = document.createElement('div');
        div.className = 'cell';
        div.innerText = num;
        div.dataset.val = num;
        div.onmousedown = (e) => cellClick(e, num, div); // שימוש ב-mousedown לתגובה מהירה יותר
        div.ontouchstart = (e) => { e.preventDefault(); cellClick(e, num, div); }; // מניעת דיליי בטלפון
        grid.appendChild(div);
    });

    renderLeaderboard(data.leaderboard);
    startCountdown();

    if (data.user) {
        myUser = data.user;
        document.getElementById('login-screen').style.display = 'none';
        
        if (data.user.played_today) {
            // אם כבר שיחק, הראה ישר תוצאות
            document.getElementById('leaderboard-screen').style.display = 'block';
        } else {
            // אם טרם שיחק, אפשר להתחיל
            document.getElementById('game-screen').style.display = 'block';
        }
    }
});

function register() {
    let name = document.getElementById('username').value;
    if(!name) return alert("חובה שם");
    
    fetch('/api/register', {
        method: 'POST', headers: {'Content-Type':'application/json'},
        body: JSON.stringify({name: name})
    }).then(r=>r.json()).then(d => {
        if(d.success) {
            document.getElementById('login-screen').style.display = 'none';
            document.getElementById('game-screen').style.display = 'block';
        }
    });
}

function cellClick(e, num, div) {
    if (!myUser || myUser.played_today) return;
    
    // התחלת שעון בלחיצה על 1
    if (num === 1 && !gameActive) {
        gameActive = true;
        startTime = performance.now();
        timerInterval = requestAnimationFrame(updateTimer);
        document.getElementById('start-msg').style.opacity = '0';
    }

    if (!gameActive) return;

    if (num === currentNumber) {
        // לחיצה נכונה
        div.classList.add('correct');
        currentNumber++;
        
        if (currentNumber > 25) {
            endGame();
        }
    } else {
        // לחיצה שגויה (אופציונלי: להוסיף עונש זמן)
        div.classList.add('wrong');
        setTimeout(() => div.classList.remove('wrong'), 300);
    }
}

function updateTimer() {
    if(!gameActive) return;
    let now = performance.now();
    let diff = (now - startTime) / 1000;
    document.getElementById('timer').innerText = diff.toFixed(3);
    timerInterval = requestAnimationFrame(updateTimer);
}

function endGame() {
    gameActive = false;
    cancelAnimationFrame(timerInterval);
    let finalTime = ((performance.now() - startTime) / 1000).toFixed(3);
    
    document.getElementById('game-screen').style.display = 'none';
    document.getElementById('leaderboard-screen').style.display = 'block';
    document.getElementById('result-card').style.display = 'block';
    document.getElementById('final-time-display').innerText = finalTime + "s";

    // שליחה לשרת
    fetch('/api/submit', {
        method: 'POST', headers: {'Content-Type':'application/json'},
        body: JSON.stringify({time: parseFloat(finalTime)})
    }).then(r=>r.json()).then(d=>{
        if(d.error) alert(d.error);
        else location.reload(); // רענון כדי לראות את עצמך בטבלה
    });
}

function renderLeaderboard(list) {
    let html = "";
    if (list.length === 0) html = "<div style='padding:20px'>עדיין אין תוצאות היום. היה הראשון!</div>";
    
    list.forEach((entry, i) => {
        let medal = "";
        if(i===0) medal = "🥇";
        if(i===1) medal = "🥈";
        if(i===2) medal = "🥉";
        
        html += `
        <div class="rank-row">
            <div>${medal} ${i+1}. ${entry.name}</div>
            <div>${entry.time.toFixed(3)}s</div>
        </div>`;
    });
    document.getElementById('ranks-list').innerHTML = html;
}

function startCountdown() {
    setInterval(() => {
        let now = new Date();
        let tomorrow = new Date(now);
        tomorrow.setDate(now.getDate() + 1);
        tomorrow.setHours(0,0,0,0);
        
        let diff = tomorrow - now;
        let hours = Math.floor(diff / (1000 * 60 * 60));
        let minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
        let seconds = Math.floor((diff % (1000 * 60)) / 1000);
        
        document.getElementById('countdown').innerText = 
            `${hours}:${minutes.toString().padStart(2,'0')}:${seconds.toString().padStart(2,'0')}`;
    }, 1000);
}

</script>
</body>
</html>
"""

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
