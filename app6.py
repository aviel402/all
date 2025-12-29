import json
import uuid
import time
import random
import threading
import os
from flask import Flask, request, render_template_string, jsonify, make_response, redirect

app = Flask(__name__)
app.secret_key = "stock_market_crash"

# --- הקבוע לנתיב בסיס ---
GAME_PATH = "/game9"

DB_FILE = "market_db.json"

# --- נתוני פתיחה ---
STOCKS = {
    "CRYPTO": {"name": "💎 ביט-קוין", "price": 1000, "volatility": 0.15, "trend": 0},
    "GOLD":   {"name": "🌕 זהב", "price": 500, "volatility": 0.05, "trend": 0},
    "OIL":    {"name": "🛢️ נפט", "price": 200, "volatility": 0.08, "trend": 0},
    "TECH":   {"name": "📱 טק-קורפ", "price": 150, "volatility": 0.12, "trend": 0}
}

market_state = {k: v.copy() for k, v in STOCKS.items()}
player_transactions = {k: 0 for k in STOCKS.keys()} 
last_tick = time.time()

# --- דאטהבייס ---
def load_db():
    if not os.path.exists(DB_FILE):
        return {"players": {}}
    try:
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {"players": {}}

def save_db(data):
    try:
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
    except: pass

def update_market():
    global last_tick
    if time.time() - last_tick > 3:
        for symbol, data in market_state.items():
            net_volume = player_transactions[symbol] 
            demand_impact = net_volume * 0.005
            
            vol = data['volatility']
            random_fluctuation = random.uniform(-vol, vol)
            
            change_percent = random_fluctuation + demand_impact
            new_price = data['price'] * (1 + change_percent)
            data['price'] = max(1, round(new_price, 2))
            data['trend'] = change_percent 
            
            player_transactions[symbol] = 0
        last_tick = time.time()

# --- HTML ---

HTML = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
<title>Black Market Trader</title>
<style>
body { background: #000; color: #00ff41; font-family: 'Courier New', monospace; margin: 0; padding: 10px; font-weight: bold; }
* { box-sizing: border-box; }
.header { display: flex; justify-content: space-between; border-bottom: 1px solid #00ff41; padding-bottom: 5px; margin-bottom: 15px; }
.net-worth { font-size: 20px; color: gold; }
.market-grid { display: grid; gap: 15px; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); }
.stock-card { background: #0d1117; border: 1px solid #30363d; padding: 15px; border-radius: 5px; position: relative; transition: 0.2s; }
.stock-card.up { border-color: #00ff41; box-shadow: 0 0 10px rgba(0, 255, 65, 0.2); }
.stock-card.down { border-color: #ff0000; box-shadow: 0 0 10px rgba(255, 0, 0, 0.2); }
.stock-name { font-size: 1.2em; display: flex; justify-content: space-between; }
.stock-price { font-size: 1.5em; margin: 10px 0; }
.holding { color: #888; font-size: 0.9em; }
.controls { display: flex; gap: 5px; margin-top: 10px; }
button { flex: 1; padding: 10px; background: #000; color: #00ff41; border: 1px solid #00ff41; cursor: pointer; font-weight: bold; }
button:hover { background: #00ff41; color: black; }
button.sell { color: #ff3333; border-color: #ff3333; }
button.sell:hover { background: #ff3333; color: black; }
.leaderboard { margin-top: 30px; border: 1px solid #555; padding: 10px; }
.player-row { display: flex; justify-content: space-between; padding: 5px 0; border-bottom: 1px dashed #333; }
.dead { text-decoration: line-through; color: red; }
.dark-btn { width: 100%; margin-top: 20px; border-color: purple; color: purple; }
.dark-btn:hover { background: purple; color: white; }
#login-screen { position: fixed; top:0; left:0; width:100%; height:100%; background: #000; z-index: 100; display: flex; justify-content: center; align-items: center; flex-direction: column; }
input { padding: 10px; font-size: 18px; text-align: center; background: #111; color: white; border: 1px solid green; margin-bottom: 10px; }
@keyframes flash-green { 0%{background: #000} 50%{background: #003300} 100%{background: #000} }
@keyframes flash-red { 0%{background: #000} 50%{background: #330000} 100%{background: #000} }
.anim-up { animation: flash-green 0.5s; }
.anim-down { animation: flash-red 0.5s; }
.back-btn { display:block; text-align:center; color:#555; margin-top:30px; text-decoration:none; font-size:12px; }
</style>
</head>
<body>

<div id="login-screen">
    <h1>🏛️ הבורסה השחורה</h1>
    <input id="username" placeholder="כינוי למסחר">
    <button onclick="login()" style="width: 200px">פתח תיק השקעות</button>
</div>

<div id="game-ui" style="display:none">
    <div class="header">
        <div>💰 מזומן: <span id="my-cash">0</span>$</div>
        <div class="net-worth">שווי: <span id="my-worth">0</span>$</div>
    </div>

    <div class="market-grid" id="market-container"></div>

    <div class="leaderboard">
        <h3>🏆 הטייקונים המובילים</h3>
        <div id="ranks"></div>
    </div>

    <button class="dark-btn" onclick="openDarkWeb()">🕵️ כניסה לדארק-נט (רמאות)</button>
    <a href="/" class="back-btn">חזרה ללובי</a>
</div>

<script>
// המפתח: שימוש במשתנה בסיס
const BASE_PATH = "{{ base }}";
let lastPrices = {};

function login() {
    let name = document.getElementById('username').value;
    if(!name) return;
    
    // שליחת בקשת Login לנתיב המתוקן
    fetch(BASE_PATH + '/api/join', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({name: name})
    }).then(r=>r.json()).then(d=>{
        if(d.error) return alert(d.error);
        
        document.getElementById('login-screen').style.display = 'none';
        document.getElementById('game-ui').style.display = 'block';
        setInterval(tick, 3000); 
        tick();
    })
}

function tick() {
    // שליפת נתונים
    fetch(BASE_PATH + '/api/tick').then(r=>r.json()).then(data => {
        if(data.need_login) return window.location.reload(); // ריענון יקפיץ את הלוגין שוב
        
        if(data.me.is_bankrupt) {
            document.body.innerHTML = "<h1 style='color:red; text-align:center; margin-top:20%'>GAME OVER<br>פשטת את הרגל!</h1><center><a href='"+BASE_PATH+"/' style='color:white'>התחל מחדש</a></center>";
            return;
        }

        document.getElementById('my-cash').innerText = data.me.cash.toFixed(0);
        document.getElementById('my-worth').innerText = data.me.net_worth.toFixed(0);

        renderMarket(data.market, data.me.portfolio);
        renderRanks(data.leaderboard);
    })
}

function renderMarket(market, portfolio) {
    const container = document.getElementById('market-container');
    container.innerHTML = '';
    
    for(let sym in market) {
        let stock = market[sym];
        let oldPrice = lastPrices[sym] || stock.price;
        let changeClass = stock.price > oldPrice ? 'up' : (stock.price < oldPrice ? 'down' : '');
        let animClass = stock.price > oldPrice ? 'anim-up' : (stock.price < oldPrice ? 'anim-down' : '');
        
        lastPrices[sym] = stock.price;

        container.innerHTML += `
        <div class="stock-card ${changeClass} ${animClass}">
            <div class="stock-name">${stock.name} <span>${stock.price.toFixed(1)}$</span></div>
            <div class="holding">יש לך: ${portfolio[sym]} יח'</div>
            <div class="controls">
                <button onclick="trade('${sym}', 'buy', 1)">קנה 1</button>
                <button onclick="trade('${sym}', 'buy', 10)">10</button>
                <button class="sell" onclick="trade('${sym}', 'sell', 1)">מכור 1</button>
                <button class="sell" onclick="trade('${sym}', 'sell', 10)">10</button>
            </div>
        </div>
        `;
    }
}

function renderRanks(list) {
    let html = "";
    list.forEach(p => {
        html += `<div class="player-row ${p.dead ? 'dead' : ''}">
            <span>${p.name}</span>
            <span>${p.val.toFixed(0)}$</span>
        </div>`;
    });
    document.getElementById('ranks').innerHTML = html;
}

function trade(sym, act, amt) {
    fetch(BASE_PATH + '/api/trade', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({symbol: sym, action: act, amount: amt})
    }).then(r=>r.json()).then(d=>{
        if(d.error) alert(d.error);
        else tick(); 
    })
}

function openDarkWeb() {
    let action = prompt("ברוך הבא לרשת האפלה.\\n1. מידע פנים (500$) - לדעת מה יעלה/ירד\\n2. הרצת מניות (1000$) - לרסק מניה");
    
    if(action == '1') {
        fetch(BASE_PATH + '/api/darkweb', {
            method:'POST', headers: {'Content-Type':'application/json'},
            body: JSON.stringify({op: 'insider'})
        }).then(r=>r.json()).then(d => { if(d.msg) alert(d.msg); });
    }
    else if(action == '2') {
        let target = prompt("איזו מניה לרסק? (CRYPTO / GOLD / OIL / TECH)");
        if(target) {
            fetch(BASE_PATH + '/api/darkweb', {
                method:'POST', headers: {'Content-Type':'application/json'},
                body: JSON.stringify({op: 'crash', target: target.toUpperCase()})
            }).then(r=>r.json()).then(d => { if(d.msg) alert(d.msg); });
        }
    }
}
</script>
</body>
</html>
"""

# --- צד שרת ---

@app.route('/')
def home():
    # העברת המשתנה לתבנית HTML
    return render_template_string(HTML, base=GAME_PATH)

@app.route('/api/join', methods=['POST'])
def join():
    name = request.json.get('name')
    if not name: return jsonify({'error': 'Name needed'}), 400
    
    db = load_db()
    uid = str(uuid.uuid4())
    
    db['players'][uid] = {
        "id": uid, "name": name,
        "cash": 2000, "portfolio": {s: 0 for s in STOCKS},
        "net_worth": 2000, "is_bankrupt": False, "insider_info": None
    }
    save_db(db)
    
    resp = make_response(jsonify({'status': 'ok'}))
    # הגדרת הקוקי לנתיב השורש
    resp.set_cookie('trader_id', uid, path='/')
    return resp

@app.route('/api/tick')
def tick():
    uid = request.cookies.get('trader_id')
    db = load_db()
    
    update_market()
    
    if not uid or uid not in db['players']:
        return jsonify({"need_login": True})
        
    me = db['players'][uid]
    
    total_assets = sum(me['portfolio'][s] * market_state[s]['price'] for s in STOCKS)
    me['net_worth'] = round(me['cash'] + total_assets, 2)
    
    if me['net_worth'] <= 0 and not me['is_bankrupt']:
        me['is_bankrupt'] = True
        save_db(db)
    
    leaderboard = []
    for p in db['players'].values():
        val = p.get('net_worth', 0)
        leaderboard.append({"name": p['name'], "val": val, "dead": p.get('is_bankrupt')})
    leaderboard.sort(key=lambda x: x['val'], reverse=True)

    return jsonify({
        "market": market_state,
        "me": me,
        "leaderboard": leaderboard[:5]
    })

@app.route('/api/trade', methods=['POST'])
def trade():
    uid = request.cookies.get('trader_id')
    data = request.json
    action = data.get('action') 
    symbol = data.get('symbol')
    amount = int(data.get('amount', 0))
    
    db = load_db()
    if uid not in db['players']: return jsonify({"error":"Login error"})
    me = db['players'][uid]
    
    if me['is_bankrupt']: return jsonify({"error": "אתה פשוט רגל!"})
    if amount <= 0: return jsonify({"error": "כמות לא חוקית"})
    
    price = market_state[symbol]['price']
    cost = price * amount
    
    if action == 'buy':
        if me['cash'] >= cost:
            me['cash'] -= cost
            me['portfolio'][symbol] += amount
            player_transactions[symbol] += amount
        else:
            return jsonify({"error": "אין מספיק כסף!"})
            
    elif action == 'sell':
        if me['portfolio'][symbol] >= amount:
            me['cash'] += cost
            me['portfolio'][symbol] -= amount
            player_transactions[symbol] -= amount 
        else:
            return jsonify({"error": "אין לך מספיק מניות!"})

    save_db(db)
    return jsonify({"status": "ok"})

@app.route('/api/darkweb', methods=['POST'])
def darkweb():
    uid = request.cookies.get('trader_id')
    op = request.json.get('op') 
    db = load_db()
    if uid not in db['players']: return jsonify({"error":"Error"})
    me = db['players'][uid]
    
    if me['cash'] < 500: return jsonify({"msg": "❌ השוק השחור דורש 500$ מזומן"})
    msg = ""
    
    if op == 'insider':
        me['cash'] -= 500
        trends = []
        for sym, data in market_state.items():
            direction = "ייעלה 🟢" if data['trend'] > 0 else "יירד 🔴"
            trends.append(f"{sym}: {direction}")
        msg = "🕵️ מידע פנים:\n" + "\n".join(trends)
        
    elif op == 'crash':
        target = request.json.get('target') 
        if target in market_state:
            me['cash'] -= 1000 
            market_state[target]['price'] *= 0.7 
            msg = f"📉 הפצת שמועה זדונית על {target}. המחיר קרס!"
        
    save_db(db)
    return jsonify({"msg": msg})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
