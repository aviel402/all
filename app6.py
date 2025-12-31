from flask import Flask, request, jsonify, render_template_string
import random, time, uuid

# --- שינוי שם האפליקציה ל-app6 ---
app6 = Flask(__name__)

# --- נתונים ומשתנים ---
BOARD_W, BOARD_H = 800, 600

# משתנה המצב (State) ששומר את כל המשחק
game_state = {
    'players': {},   
    'coins': []      
}

# פונקציה ליצירת מטבע חדש
def spawn_coin():
    game_state['coins'].append({
        'id': str(uuid.uuid4()),
        'x': random.randint(20, BOARD_W - 20),
        'y': random.randint(20, BOARD_H - 20),
        'val': 10
    })

# יצירת 15 מטבעות התחלתיים
for _ in range(15): spawn_coin()

# --- ממשק המשחק (HTML/JS) ---
HTML_GAME = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>Super Game 6</title>
    <style>
        body { background-color: #121212; color: white; font-family: 'Segoe UI', sans-serif; overflow: hidden; display: flex; flex-direction: column; align-items: center; }
        #gameCanvas { background: #1a1a1a; border: 2px solid #00ff88; box-shadow: 0 0 25px rgba(0, 255, 136, 0.3); border-radius: 8px; margin-top: 10px; }
        #ui { position: absolute; top: 10px; width: 800px; display: flex; justify-content: space-between; pointer-events: none; }
        .score-board { background: rgba(0,0,0,0.6); padding: 10px; border-radius: 8px; font-weight: bold; font-size: 18px; color: #00ff88; pointer-events: auto; border: 1px solid #00ff88; }
        input { pointer-events: auto; padding: 5px; background: #333; border: 1px solid #555; color: white; border-radius: 4px; }
        button { pointer-events: auto; cursor: pointer; background: #00ff88; color:black; border: none; padding: 5px 15px; border-radius: 4px; font-weight: bold; transition: 0.2s;}
        button:hover { background: #00cc6a; transform: scale(1.05); }
    </style>
</head>
<body>
    <div id="ui">
        <div>
            שם: <input id="pName" value="שחקן6" style="width:80px;">
            <select id="pEmoji" style="background:#333;color:white;border:none;">
                <option>👽</option><option>🤠</option><option>👻</option><option>🤖</option><option>🐵</option><option>😈</option>
            </select>
            <button onclick="joinGame()">כנס למשחק</button>
        </div>
        <div class="score-board">💰 נקודות: <span id="myScore">0</span> | מלך השרת: <span id="topPlayer"></span></div>
    </div>
    
    <canvas id="gameCanvas" width="800" height="600"></canvas>

<script>
    const canvas = document.getElementById('gameCanvas');
    const ctx = canvas.getContext('2d');
    let myId = localStorage.getItem('pid') || 'user_' + Math.floor(Math.random()*9999);
    localStorage.setItem('pid', myId);

    let myPos = { x: 400, y: 300 };
    let speed = 6; // מהירות 6 כמובן :)
    let keys = {};
    let gameState = { players: {}, coins: [] };
    let joined = false;

    window.addEventListener('keydown', e => keys[e.key] = true);
    window.addEventListener('keyup', e => keys[e.key] = false);

    function joinGame() {
        joined = true;
        document.querySelector('button').disabled = true;
        document.querySelector('button').innerText = "משחק פעיל...";
    }

    function gameLoop() {
        if(joined) {
            if((keys['ArrowUp'] || keys['w']) && myPos.y > 0) myPos.y -= speed;
            if((keys['ArrowDown'] || keys['s']) && myPos.y < 600) myPos.y += speed;
            if((keys['ArrowLeft'] || keys['a']) && myPos.x > 0) myPos.x -= speed;
            if((keys['ArrowRight'] || keys['d']) && myPos.x < 800) myPos.x += speed;
        }

        // שליחת מידע לשרת
        fetch('/update', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                id: myId, x: myPos.x, y: myPos.y,
                name: document.getElementById('pName').value,
                emoji: document.getElementById('pEmoji').value,
                active: joined
            })
        }).then(r => r.json()).then(data => {
            gameState = data;
            if (gameState.players[myId]) {
                document.getElementById('myScore').innerText = gameState.players[myId].score;
            }
        });

        draw();
        requestAnimationFrame(gameLoop);
    }

    function draw() {
        // רקע שחור מגניב
        ctx.fillStyle = '#0f0f0f';
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        // קווים ברקע
        ctx.strokeStyle = '#1f1f1f';
        ctx.beginPath();
        for(let i=0; i<800; i+=50) { ctx.moveTo(i,0); ctx.lineTo(i,600); }
        for(let j=0; j<600; j+=50) { ctx.moveTo(0,j); ctx.lineTo(800,j); }
        ctx.stroke();

        // ציור המטבעות
        gameState.coins.forEach(c => {
            ctx.shadowBlur = 10;
            ctx.shadowColor = "yellow";
            ctx.font = "24px Arial";
            ctx.fillText("🪙", c.x - 12, c.y + 10);
            ctx.shadowBlur = 0;
        });

        let maxScore = -1; let leader = "אף אחד";

        // ציור השחקנים
        for (let pid in gameState.players) {
            const p = gameState.players[pid];
            if(p.score > maxScore) { maxScore = p.score; leader = p.name; }
            
            // עיגול רקע לשחקן
            ctx.fillStyle = (pid === myId) ? "rgba(0, 255, 136, 0.2)" : "rgba(255, 255, 255, 0.1)";
            ctx.beginPath(); ctx.arc(p.x, p.y - 5, 25, 0, Math.PI*2); ctx.fill();

            // האימוג'י
            ctx.font = "34px Arial";
            ctx.textAlign = "center";
            ctx.fillText(p.emoji, p.x, p.y + 8);
            
            // שם וניקוד
            ctx.fillStyle = "#bbb";
            ctx.font = "12px sans-serif";
            ctx.fillText(p.name + " (" + p.score + ")", p.x, p.y - 35);
        }
        document.getElementById('topPlayer').innerText = leader + " (" + maxScore + ")";
    }

    gameLoop();
</script>
</body>
</html>
"""

# --- הנתיבים (Routes) הוגדרו תחת app6 ---

@app6.route('/')
def home():
    return render_template_string(HTML_GAME)

@app6.route('/update', methods=['POST'])
def update_game():
    data = request.json
    uid = data['id']
    
    # עדכון שחקן
    if data['active']:
        current_score = game_state['players'].get(uid, {}).get('score', 0)
        game_state['players'][uid] = {
            'x': data['x'],
            'y': data['y'],
            'name': data['name'],
            'emoji': data['emoji'],
            'score': current_score,
            'last_seen': time.time()
        }

    # מחיקת שחקנים לא פעילים (יותר מ-6 שניות...)
    now = time.time()
    for pid in list(game_state['players'].keys()):
        if now - game_state['players'][pid]['last_seen'] > 6:
            del game_state['players'][pid]

    # בדיקת איסוף מטבעות
    player = game_state['players'].get(uid)
    if player:
        for coin in game_state['coins'][:]:
            # בדיקת מרחק פשוטה
            if abs(player['x'] - coin['x']) < 35 and abs(player['y'] - coin['y']) < 35:
                player['score'] += coin['val']
                game_state['coins'].remove(coin)
                spawn_coin() # יצירת מטבע חדש

    return jsonify(game_state)

if __name__ == '__main__':
    # הרצה עם app6
    app6.run(host='0.0.0.0', port=5000, threaded=True, debug=True)
