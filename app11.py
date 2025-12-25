import random
import uuid
from flask import Flask, render_template_string, request, jsonify, redirect

app = Flask(__name__)
app.secret_key = "manager_pro_league"

# --- מחולל נתונים (שמות ישראלים) ---
FIRST_NAMES = ["ערן", "מנור", "אוסקר", "מונס", "דיא", "דניאל", "עומר", "שרן", "בירם", "דולב", "יוגב", "ליאור"]
LAST_NAMES = ["זהבי", "סולומון", "גלוך", "דבור", "סבע", "פרץ", "אצילי", "ייני", "כיאל", "חזיזה", "אוחיון", "כהן"]
TEAMS_NAMES = ["מכבי תל אביב", "מכבי חיפה", "הפועל באר שבע", "בית\"ר ירושלים", "הפועל תל אביב", "מכבי נתניה", "מ.ס אשדוד", "בני סכנין"]

# --- מחלקות משחק ---

class Player:
    def __init__(self):
        self.id = str(uuid.uuid4())
        self.name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        self.pos = random.choice(["GK", "DEF", "DEF", "MID", "MID", "MID", "FWD", "FWD"])
        
        # יכולות שחקן
        base_stats = random.randint(50, 90)
        self.att = base_stats + random.randint(-10, 10)
        self.deny = base_stats + random.randint(-10, 10) # הגנה
        self.value = int((self.att + self.deny) * 1000)
        
    def to_dict(self):
        return self.__dict__

class Team:
    def __init__(self, name, is_ai=True):
        self.id = str(uuid.uuid4())
        self.name = name
        self.is_ai = is_ai
        self.points = 0
        self.games_played = 0
        self.wins = 0
        self.draws = 0
        self.losses = 0
        self.goals_for = 0
        self.goals_against = 0
        self.budget = 10000000 # 10 מיליון
        
        # יצירת סגל של 11 שחקנים
        self.squad = [Player() for _ in range(11)]
        
        # טקטיקה
        self.formation = "4-4-2" # ברירת מחדל

    def get_power(self):
        # חישוב כוח קבוצתי לפי ממוצע שחקנים
        avg_att = sum(p.att for p in self.squad) / len(self.squad)
        avg_def = sum(p.deny for p in self.squad) / len(self.squad)
        
        # בונוס טקטי
        if self.formation == "4-3-3": avg_att *= 1.1
        if self.formation == "5-4-1": avg_def *= 1.1
        
        return int(avg_att), int(avg_def)

# --- מנוע הליגה (Global State) ---
class League:
    def __init__(self):
        self.teams = [Team(name) for name in TEAMS_NAMES]
        self.my_team_id = self.teams[0].id # השחקן הוא הקבוצה הראשונה
        self.teams[0].is_ai = False
        self.week = 1
        self.history = [] # לוג משחקים
        self.market = [Player() for _ in range(6)] # שוק ההעברות

    def get_team(self, tid):
        return next((t for t in self.teams if t.id == tid), None)

    def play_week(self):
        # מגריל משחקים בין הקבוצות
        random.shuffle(self.teams)
        matches = []
        
        # זוגות זוגות
        for i in range(0, len(self.teams), 2):
            team_a = self.teams[i]
            team_b = self.teams[i+1]
            result = self.simulate_match(team_a, team_b)
            matches.append(result)
            
        self.week += 1
        # רענון שוק ההעברות (שחקן יוצא, שחקן נכנס)
        self.market.pop(0)
        self.market.append(Player())
        return matches

    def simulate_match(self, t1, t2):
        p1_att, p1_def = t1.get_power()
        p2_att, p2_def = t2.get_power()
        
        # חישוב שערים (בסיס אקראי + פער כוחות)
        score1 = int(random.randint(0, 4) * (p1_att / p2_def))
        score2 = int(random.randint(0, 4) * (p2_att / p1_def))
        
        # עדכון טבלה
        t1.games_played += 1; t2.games_played += 1
        t1.goals_for += score1; t1.goals_against += score2
        t2.goals_for += score2; t2.goals_against += score1
        
        if score1 > score2:
            t1.points += 3; t1.wins += 1; t2.losses += 1
        elif score2 > score1:
            t2.points += 3; t2.wins += 1; t1.losses += 1
        else:
            t1.points += 1; t2.points += 1
            t1.draws += 1; t2.draws += 1
            
        return {"t1": t1.name, "s1": score1, "t2": t2.name, "s2": score2}

game = League()

# --- ROUTES ---

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/data')
def get_data():
    my_team = game.get_team(game.my_team_id)
    # מיון טבלה לפי נקודות ואז הפרש שערים
    table = sorted(game.teams, key=lambda t: (t.points, t.goals_for - t.goals_against), reverse=True)
    
    return jsonify({
        "my_team": {
            "name": my_team.name,
            "budget": my_team.budget,
            "formation": my_team.formation,
            "squad": [p.to_dict() for p in my_team.squad]
        },
        "table": [{
            "pos": i+1, "name": t.name, "pts": t.points, 
            "p": t.games_played, "gd": t.goals_for - t.goals_against
        } for i, t in enumerate(table)],
        "market": [p.to_dict() for p in game.market],
        "week": game.week
    })

@app.route('/api/play', methods=['POST'])
def play_week():
    results = game.play_week()
    return jsonify(results)

@app.route('/api/formation', methods=['POST'])
def set_formation():
    form = request.json.get('formation')
    team = game.get_team(game.my_team_id)
    team.formation = form
    return jsonify({"status": "ok"})

@app.route('/api/transfer', methods=['POST'])
def transfer():
    action = request.json.get('action') # buy / sell
    pid = request.json.get('player_id')
    my_team = game.get_team(game.my_team_id)
    
    if action == 'buy':
        target = next((p for p in game.market if p.id == pid), None)
        if target and my_team.budget >= target.value:
            if len(my_team.squad) >= 15: return jsonify({"err": "הסגל מלא (15)"})
            my_team.budget -= target.value
            my_team.squad.append(target)
            game.market.remove(target)
            game.market.append(Player()) # מילוי השוק
            return jsonify({"msg": "קנית את השחקן בהצלחה!"})
        return jsonify({"err": "אין כסף או שחקן לא קיים"})

    if action == 'sell':
        # כשמוכרים מקבלים רק 80% מערך השחקן
        target = next((p for p in my_team.squad if p.id == pid), None)
        if target and len(my_team.squad) > 11: # חייב להשאיר מינימום שחקנים
            my_team.budget += int(target.value * 0.8)
            my_team.squad.remove(target)
            return jsonify({"msg": "מכרת את השחקן."})
        return jsonify({"err": "אי אפשר למכור (מינימום 11 שחקנים)"})

    return jsonify({"err": "פעולה לא חוקית"})

# --- UI HTML ---

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Super Liga Manager</title>
<style>
:root { --grass: #2d6a4f; --dark: #1b4332; --light: #d8f3dc; --accent: #ffd700; }
body { margin: 0; background-color: #f0f2f5; font-family: 'Segoe UI', Tahoma, sans-serif; color: #333; padding-bottom: 60px; }

/* HEADER */
.header { background: var(--grass); color: white; padding: 15px; position: sticky; top:0; z-index:100; box-shadow: 0 2px 10px rgba(0,0,0,0.2); display: flex; justify-content: space-between; align-items: center;}
.team-title { font-weight: 900; font-size: 18px; text-transform: uppercase; }
.budget { font-family: monospace; font-size: 16px; color: var(--accent); background: rgba(0,0,0,0.3); padding: 5px 10px; border-radius: 5px; }

/* TABS */
.tabs { display: flex; background: var(--dark); padding: 5px; justify-content: space-around; }
.tab-btn { background: transparent; color: rgba(255,255,255,0.7); border: none; font-size: 16px; padding: 10px; cursor: pointer; border-bottom: 3px solid transparent; width: 100%; }
.tab-btn.active { color: white; border-bottom-color: var(--accent); font-weight: bold; }

/* CONTAINERS */
.section { padding: 15px; display: none; animation: fadeIn 0.3s; }
.section.active { display: block; }

/* CARDS & TABLES */
.card { background: white; padding: 15px; margin-bottom: 10px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border-left: 5px solid var(--grass); display: flex; justify-content: space-between; align-items: center;}
.p-info h4 { margin: 0; }
.p-stats { font-size: 12px; color: #666; margin-top: 3px; }
.p-stats b { color: var(--grass); }

.table-row { display: grid; grid-template-columns: 0.5fr 3fr 1fr 1fr 1fr; padding: 10px; border-bottom: 1px solid #ddd; background: white; font-size: 14px; text-align: center;}
.table-head { background: var(--dark); color: white; font-weight: bold; border-top-left-radius: 8px; border-top-right-radius: 8px;}
.my-rank { background: var(--light); font-weight: bold; border-left: 4px solid var(--grass); }

/* CONTROLS */
button.action-btn { background: var(--grass); color: white; border: none; padding: 8px 12px; border-radius: 4px; cursor: pointer; font-size: 14px; }
button.sell-btn { background: #e63946; }
button.buy-btn { background: #2a9d8f; }

.play-week-btn {
    position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%);
    background: linear-gradient(45deg, #1e3c72, #2a5298);
    color: white; padding: 15px 40px; border: none; border-radius: 30px;
    font-size: 18px; font-weight: bold; box-shadow: 0 5px 15px rgba(0,0,0,0.3);
    cursor: pointer; transition: transform 0.2s; z-index: 200;
}
.play-week-btn:active { transform: translateX(-50%) scale(0.95); }

/* TACTICS */
.formation-select { width: 100%; padding: 10px; margin-bottom: 15px; border-radius: 5px; font-size: 16px; }

/* MODAL RESULTS */
#modal { position: fixed; top:0; left:0; width:100%; height:100%; background: rgba(0,0,0,0.9); z-index: 300; display:none; flex-direction:column; justify-content:center; align-items:center; color:white; }
.score-board { font-size: 20px; text-align:center; background: #222; padding: 20px; border-radius: 10px; border: 2px solid var(--accent); width: 80%; }
.score-row { margin: 10px 0; border-bottom: 1px dashed #555; padding-bottom: 5px; }

@keyframes fadeIn { from { opacity:0; } to { opacity:1; } }
</style>
</head>
<body>

<div class="header">
    <div class="team-title" id="teamName">FC Loading...</div>
    <div class="budget">💰 <span id="budget">0</span></div>
</div>

<div class="tabs">
    <button class="tab-btn active" onclick="showTab('squad')">סגל</button>
    <button class="tab-btn" onclick="showTab('league')">טבלה</button>
    <button class="tab-btn" onclick="showTab('market')">העברות</button>
</div>

<!-- SQUAD TAB -->
<div id="squad" class="section active">
    <h3>הסגל שלך & טקטיקה</h3>
    <select class="formation-select" onchange="changeTactics(this.value)">
        <option value="4-4-2">מערך 4-4-2 (מאוזן)</option>
        <option value="4-3-3">מערך 4-3-3 (התקפי)</option>
        <option value="5-4-1">מערך 5-4-1 (בונקר)</option>
    </select>
    <div id="squad-list"></div>
</div>

<!-- LEAGUE TAB -->
<div id="league" class="section">
    <h3>מחזור נוכחי: <span id="weekNum">1</span></h3>
    <div class="table-row table-head">
        <div>#</div><div>קבוצה</div><div>נק'</div><div>מש'</div><div>יחס</div>
    </div>
    <div id="table-body"></div>
</div>

<!-- MARKET TAB -->
<div id="market" class="section">
    <h3>שוק ההעברות</h3>
    <p style="font-size:12px">שים לב: התקציב יורד עם כל רכישה</p>
    <div id="market-list"></div>
</div>

<button class="play-week-btn" onclick="playWeek()">⚽ שחק מחזור</button>

<!-- RESULTS MODAL -->
<div id="modal">
    <h2>תוצאות המחזור</h2>
    <div class="score-board" id="results-list"></div>
    <button onclick="document.getElementById('modal').style.display='none'" style="margin-top:20px; padding:10px 30px; background:white; border:none; font-weight:bold; cursor:pointer;">סגור</button>
</div>

<script>
function showTab(id) {
    document.querySelectorAll('.section').forEach(e => e.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(e => e.classList.remove('active'));
    document.getElementById(id).classList.add('active');
    // find button index is irrelevant, simple style toggle:
    event.target.classList.add('active');
}

function render(data) {
    // 1. Header & Basics
    document.getElementById('teamName').innerText = data.my_team.name;
    document.getElementById('budget').innerText = data.my_team.budget.toLocaleString();
    document.getElementById('weekNum').innerText = data.week;
    
    // Set active formation in select
    const formSelect = document.querySelector('.formation-select');
    formSelect.value = data.my_team.formation;

    // 2. Squad
    const squadDiv = document.getElementById('squad-list');
    squadDiv.innerHTML = data.my_team.squad.map(p => `
        <div class="card">
            <div class="p-info">
                <h4>${p.name} <span style="background:#eee; font-size:10px; padding:2px; border-radius:3px">${p.pos}</span></h4>
                <div class="p-stats">
                    ⚔️ התקפה: <b>${p.att}</b> | 🛡️ הגנה: <b>${p.deny}</b>
                </div>
                <div style="font-size:12px; color:green">שווי: ${p.value.toLocaleString()}</div>
            </div>
            <button class="action-btn sell-btn" onclick="transfer('sell', '${p.id}')">מכור</button>
        </div>
    `).join('');

    // 3. Table
    const tableDiv = document.getElementById('table-body');
    tableDiv.innerHTML = data.table.map(t => `
        <div class="table-row ${t.name === data.my_team.name ? 'my-rank' : ''}">
            <div>${t.pos}</div>
            <div style="text-align:right">${t.name}</div>
            <div style="font-weight:bold">${t.pts}</div>
            <div>${t.p}</div>
            <div dir="ltr">${t.gd > 0 ? '+'+t.gd : t.gd}</div>
        </div>
    `).join('');

    // 4. Market
    const marketDiv = document.getElementById('market-list');
    marketDiv.innerHTML = data.market.map(p => `
        <div class="card">
            <div class="p-info">
                <h4>${p.name} <span style="background:#eef; font-size:10px; padding:2px; border-radius:3px">${p.pos}</span></h4>
                <div class="p-stats">ATT: <b>${p.att}</b> | DEF: <b>${p.deny}</b></div>
                <div style="font-size:12px; font-weight:bold; color:darkblue">מחיר: ${p.value.toLocaleString()}</div>
            </div>
            <button class="action-btn buy-btn" onclick="transfer('buy', '${p.id}')">קנה</button>
        </div>
    `).join('');
}

async function loadData() {
    let r = await fetch('/api/data');
    let d = await r.json();
    render(d);
}

async function changeTactics(val) {
    await fetch('/api/formation', {
        method:'POST', headers:{'Content-Type':'application/json'},
        body:JSON.stringify({formation:val})
    });
    loadData();
}

async function transfer(action, pid) {
    if(!confirm(action === 'buy' ? "לקנות את השחקן?" : "למכור (ב-80% מערכו)?")) return;
    
    let r = await fetch('/api/transfer', {
        method:'POST', headers:{'Content-Type':'application/json'},
        body:JSON.stringify({action: action, player_id: pid})
    });
    let d = await r.json();
    if(d.err) alert(d.err);
    else {
        alert(d.msg);
        loadData();
    }
}

async function playWeek() {
    let r = await fetch('/api/play', {method:'POST'});
    let matches = await r.json();
    
    // הצגת תוצאות
    const resList = document.getElementById('results-list');
    resList.innerHTML = matches.map(m => `
        <div class="score-row">
            <span style="color:#66fcf1">${m.t1}</span> 
            <b>${m.s1} - ${m.s2}</b> 
            <span style="color:#66fcf1">${m.t2}</span>
        </div>
    `).join('');
    
    document.getElementById('modal').style.display = 'flex';
    loadData();
}

// init
loadData();

</script>
</body>
</html>
"""

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
