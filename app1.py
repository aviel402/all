from flask import Flask, render_template_string

app = Flask(__name__)

GAME_HTML = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>הישרדות: היום האחרון</title>
    <style>
        body {
            background-color: #121212;
            color: #e0e0e0;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            text-align: center;
            margin: 0;
            padding: 10px;
            display: flex;
            flex-direction: column;
            align-items: center;
            height: 100vh;
        }
        h1 { margin: 10px 0; color: #ff4444; font-size: 24px; text-transform: uppercase; letter-spacing: 2px; }
        
        .container {
            width: 100%;
            max-width: 400px;
            background: #1e1e1e;
            padding: 15px;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.8);
            border: 1px solid #333;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin-bottom: 15px;
        }

        .stat-box {
            background: #2a2a2a;
            padding: 8px;
            border-radius: 8px;
            text-align: left;
            position: relative;
        }
        
        .stat-label { font-size: 12px; color: #aaa; margin-bottom: 4px; display: block; }
        .stat-bar-bg { background: #444; height: 6px; border-radius: 3px; width: 100%; }
        .stat-bar { height: 100%; border-radius: 3px; transition: width 0.3s; }

        .hp-bar { background: #d32f2f; }
        .food-bar { background: #f57c00; }
        .water-bar { background: #0288d1; }
        .nrg-bar { background: #fbc02d; }

        .time-display {
            background: #000;
            color: #fff;
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 15px;
            font-weight: bold;
            border: 1px solid #444;
        }

        .log-area {
            background: #000;
            height: 120px;
            overflow-y: auto;
            border: 1px solid #333;
            padding: 10px;
            text-align: right;
            font-size: 13px;
            margin-bottom: 15px;
            color: #ccc;
            font-family: monospace;
        }
        .log-entry { margin-bottom: 6px; border-bottom: 1px solid #222; padding-bottom: 4px; }
        .log-bad { color: #ff5252; }
        .log-good { color: #69f0ae; }
        .log-info { color: #82b1ff; }

        .inventory {
            display: flex;
            justify-content: space-around;
            background: #252525;
            padding: 10px;
            border-radius: 8px;
            margin-bottom: 15px;
        }
        .item { font-size: 14px; }

        .actions { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
        button {
            padding: 12px;
            border: none;
            border-radius: 6px;
            background: #424242;
            color: white;
            font-weight: bold;
            font-size: 14px;
            cursor: pointer;
            transition: 0.2s;
        }
        button:hover { background: #616161; }
        button:disabled { opacity: 0.5; cursor: not-allowed; }
        
        .btn-scavenge { background: #5d4037; grid-column: span 2; border: 1px solid #795548; }
        .btn-rest { background: #303f9f; border: 1px solid #3f51b5; }
        .btn-eat { background: #e65100; border: 1px solid #ff9800; }
        .btn-drink { background: #01579b; border: 1px solid #039be5; }
        .btn-heal { background: #b71c1c; grid-column: span 2; border: 1px solid #d32f2f; }

        .overlay {
            position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0,0,0,0.95);
            display: none; justify-content: center; align-items: center; flex-direction: column;
            z-index: 100;
        }
        .game-over-text { color: red; font-size: 40px; font-weight: bold; }
        .restart-btn { background: white; color: black; margin-top: 20px; }

    </style>
</head>
<body>

    <h1>שורד: היום <span id="dayNum">1</span></h1>

    <div class="container">
        
        <div class="time-display" id="timeDisplay">☀️ צהריים (יום 1)</div>

        <div class="stats-grid">
            <div class="stat-box">
                <span class="stat-label">❤️ בריאות <span id="val-hp">100</span>%</span>
                <div class="stat-bar-bg"><div class="stat-bar hp-bar" id="bar-hp" style="width: 100%"></div></div>
            </div>
            <div class="stat-box">
                <span class="stat-label">⚡ אנרגיה <span id="val-nrg">100</span>%</span>
                <div class="stat-bar-bg"><div class="stat-bar nrg-bar" id="bar-nrg" style="width: 100%"></div></div>
            </div>
            <div class="stat-box">
                <span class="stat-label">🍗 רעב <span id="val-food">100</span>%</span>
                <div class="stat-bar-bg"><div class="stat-bar food-bar" id="bar-food" style="width: 100%"></div></div>
            </div>
            <div class="stat-box">
                <span class="stat-label">💧 צמא <span id="val-water">100</span>%</span>
                <div class="stat-bar-bg"><div class="stat-bar water-bar" id="bar-water" style="width: 100%"></div></div>
            </div>
        </div>

        <div class="inventory">
            <div class="item">🥫 שימורים: <span id="inv-food">1</span></div>
            <div class="item">🥤 מים: <span id="inv-water">1</span></div>
            <div class="item">💊 תחבושת: <span id="inv-med">0</span></div>
        </div>

        <div class="log-area" id="log">
            <div class="log-entry log-info">התעוררת במחסה. העולם הרוס. שרוד.</div>
        </div>

        <div class="actions">
            <button class="btn-scavenge" onclick="action('scavenge')">🔎 צא לחפש משאבים (סיכון!)</button>
            <button class="btn-eat" onclick="action('eat')">🥫 אכול</button>
            <button class="btn-drink" onclick="action('drink')">🥤 שתה</button>
            <button class="btn-rest" onclick="action('rest')">💤 לישון (סיים יום)</button>
            <button class="btn-heal" onclick="action('heal')">💊 חבוש פצעים</button>
        </div>
    </div>

    <div class="overlay" id="gameOverScreen">
        <div class="game-over-text">מוות</div>
        <p style="color:white" id="deathReason">מתת מרעב</p>
        <p style="color:#aaa">שרדת <span id="finalDays">0</span> ימים</p>
        <button class="restart-btn" onclick="location.reload()">נסה שוב</button>
    </div>

    <script>
        // Game State
        let stats = {
            hp: 100,
            food: 80,
            water: 80,
            nrg: 100
        };
        let inventory = {
            food: 1,
            water: 1,
            med: 0
        };
        let day = 1;
        let isNight = false; // מתחילים ביום

        // Update UI Function
        function updateUI() {
            // Bars Width
            document.getElementById('bar-hp').style.width = stats.hp + '%';
            document.getElementById('bar-nrg').style.width = stats.nrg + '%';
            document.getElementById('bar-food').style.width = stats.food + '%';
            document.getElementById('bar-water').style.width = stats.water + '%';

            // Text Values
            document.getElementById('val-hp').innerText = stats.hp;
            document.getElementById('val-nrg').innerText = stats.nrg;
            document.getElementById('val-food').innerText = stats.food;
            document.getElementById('val-water').innerText = stats.water;

            // Inventory
            document.getElementById('inv-food').innerText = inventory.food;
            document.getElementById('inv-water').innerText = inventory.water;
            document.getElementById('inv-med').innerText = inventory.med;

            // World Info
            document.getElementById('dayNum').innerText = day;
            const timeText = isNight ? "🌑 לילה (מסוכן בחוץ)" : "☀️ יום (בטוח יחסית)";
            document.getElementById('timeDisplay').innerText = timeText + " - יום " + day;
            document.getElementById('timeDisplay').style.background = isNight ? "#1a237e" : "#000";

            checkDeath();
        }

        function addLog(msg, type) {
            const log = document.getElementById('log');
            const entry = document.createElement('div');
            entry.className = "log-entry " + type;
            entry.innerText = "◄ " + msg;
            log.prepend(entry);
        }

        function checkDeath() {
            let reason = "";
            if (stats.hp <= 0) reason = "מתת מפציעות ואיבוד דם.";
            if (stats.food <= 0) reason = "גססת למוות מרעב.";
            if (stats.water <= 0) reason = "התייבשת למוות.";

            // מחסור חמור גורם נזק לבריאות
            if (stats.food === 0) { stats.hp -= 10; addLog("הבטן שלך נדבקת לגב... (נזק!)", "log-bad"); }
            if (stats.water === 0) { stats.hp -= 15; addLog("הגרון יבש כמו מדבר... (נזק קשה!)", "log-bad"); }

            if (stats.hp <= 0 || stats.food <= 0 || stats.water <= 0) {
                if (stats.hp <= 0) { // לוודא שמוות קורה רק ב-0 HP או מצב קיצוני
                    document.getElementById('deathReason').innerText = reason || "הטבע ניצח אותך.";
                    document.getElementById('finalDays').innerText = day;
                    document.getElementById('gameOverScreen').style.display = 'flex';
                }
            }
        }

        // --- Core Logic ---

        function action(act) {
            if (stats.hp <= 0) return;

            // עלויות בסיסיות לכל פעולה
            let hungerCost = 5;
            let waterCost = 7;
            let nrgCost = 5;

            // ---- Scavenge (חיפוש) ----
            if (act === 'scavenge') {
                if (stats.nrg < 20) {
                    addLog("אתה עייף מדי כדי לצאת! לך לישון.", "log-bad");
                    return;
                }
                
                nrgCost = 25;
                hungerCost = 10;
                waterCost = 15;
                
                let risk = isNight ? 0.7 : 0.3; // לילה הרבה יותר מסוכן (70%)
                
                addLog(isNight ? "יצאת בחשיכה..." : "יצאת לסרוק את השטח...", "log-info");

                // חישוב מציאת חפצים
                let foundSomething = false;
                let rnd = Math.random();
                
                if (rnd > 0.3) { // 70% למצוא משהו
                    let loot = Math.random();
                    if (loot < 0.4) { 
                        inventory.food++; 
                        addLog("מצאת קופסת שימורים ישנה! 🥫", "log-good"); 
                    } else if (loot < 0.7) {
                        inventory.water++;
                        addLog("מצאת בקבוק מים! 🥤", "log-good");
                    } else if (loot < 0.9) {
                        inventory.med++;
                        addLog("מצאת ערכת עזרה ראשונה! 💊", "log-good");
                    } else {
                        inventory.food++; inventory.water++;
                        addLog("מזל! מצאת תרמיל עם אוכל ומים! 🎒", "log-good");
                    }
                    foundSomething = true;
                } else {
                    addLog("חזרת בידיים ריקות.", "log-bad");
                }

                // חישוב פציעות (ריסק)
                if (Math.random() < risk) {
                    let dmg = Math.floor(Math.random() * 20) + 5;
                    stats.hp -= dmg;
                    let cause = isNight ? "להקת כלבים תקפה אותך בחושך!" : "נפלת ממהצוק ושברת רגל.";
                    addLog(cause + " (-" + dmg + " HP)", "log-bad");
                }

            }

            // ---- Eat ----
            if (act === 'eat') {
                if (inventory.food > 0) {
                    inventory.food--;
                    stats.food = Math.min(100, stats.food + 35);
                    stats.hp = Math.min(100, stats.hp + 5);
                    addLog("פתחת קופסת שעועית קרה. טעים. (+35 רעב)", "log-good");
                } else {
                    addLog("אין לך אוכל! צא לחפש.", "log-bad");
                    return;
                }
            }

            // ---- Drink ----
            if (act === 'drink') {
                if (inventory.water > 0) {
                    inventory.water--;
                    stats.water = Math.min(100, stats.water + 40);
                    stats.nrg = Math.min(100, stats.nrg + 5);
                    addLog("המים מרווים. (+40 צמא)", "log-good");
                } else {
                    addLog("אין לך מים!", "log-bad");
                    return;
                }
            }

            // ---- Rest / Sleep ----
            if (act === 'rest') {
                addLog(isNight ? "הלכת לישון עד הבוקר..." : "נחת קצת בצל עד הערב...", "log-info");
                stats.nrg = Math.min(100, stats.nrg + 50); // שינה ממלאת המון אנרגיה
                // בשינה הרעב והצמא גוברים משמעותית כי עובר זמן
                hungerCost = 15;
                waterCost = 15;
                
                // הופך יום ולילה
                isNight = !isNight;
                if (!isNight) {
                    day++; // התחיל יום חדש
                    addLog("--- התחיל יום " + day + " ---", "log-info");
                }
            }

            // ---- Heal ----
            if (act === 'heal') {
                if (inventory.med > 0) {
                    inventory.med--;
                    stats.hp = Math.min(100, stats.hp + 40);
                    addLog("חבשת את הפצעים. מרגיש יותר טוב. (+40 HP)", "log-good");
                } else {
                    addLog("אין לך ציוד רפואי! צא לחפש תחבושות.", "log-bad");
                    return;
                }
            }

            // הורדת מדדים אחרי פעולה
            stats.food = Math.max(0, stats.food - hungerCost);
            stats.water = Math.max(0, stats.water - waterCost);
            stats.nrg = Math.max(0, stats.nrg - nrgCost);

            // אזהרות קריטיות
            if (stats.food < 20) addLog("הבטן מקרקרת בטירוף...", "log-bad");
            if (stats.water < 20) addLog("סחרחורת... חייב לשתות...", "log-bad");

            updateUI();
        }

    </script>
</body>
</html>
"""

@app.route('/')
def game():
    return render_template_string(GAME_HTML)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
