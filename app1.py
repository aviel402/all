from flask import Flask, render_template_string

app = Flask(__name__)

GAME_HTML = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SURVIVAL OS v2.0</title>
    <link href="https://fonts.googleapis.com/css2?family=Rubik:wght@400;700&family=Share+Tech+Mono&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #050a10;
            --panel: #0f1b29;
            --primary: #00f2ff;
            --accent: #ff0055;
            --success: #00ff9d;
            --warn: #ffae00;
            --text: #e0f7ff;
        }

        body {
            background-color: var(--bg);
            color: var(--text);
            font-family: 'Share Tech Mono', 'Rubik', monospace; /* פונט בסגנון טרמינל */
            margin: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            overflow: hidden;
        }

        .game-interface {
            width: 100%;
            max-width: 420px;
            height: 95vh;
            background: var(--panel);
            border: 2px solid var(--primary);
            box-shadow: 0 0 20px rgba(0, 242, 255, 0.2);
            border-radius: 15px;
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 15px;
            position: relative;
        }

        /* כותרת יום ושעה */
        .hud-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: rgba(0, 242, 255, 0.1);
            padding: 10px;
            border-radius: 8px;
            border: 1px solid var(--primary);
        }
        .day-counter { font-size: 20px; font-weight: bold; color: var(--primary); text-transform: uppercase; }
        .time-badge { font-size: 14px; background: var(--bg); padding: 4px 8px; border-radius: 4px; border: 1px solid #333;}

        /* סטטים (Stats) */
        .stats-container {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
        }
        
        .stat-card {
            background: #09121d;
            padding: 8px;
            border-radius: 6px;
            border-right: 3px solid #333;
        }
        
        .stat-header { display: flex; justify-content: space-between; font-size: 12px; margin-bottom: 5px; opacity: 0.8;}
        .progress-bg { height: 8px; background: #222; width: 100%; border-radius: 4px; overflow: hidden; }
        .progress-fill { height: 100%; width: 100%; transition: width 0.5s ease-out; box-shadow: 0 0 10px currentColor;}

        /* צבעים דינמיים */
        .hp-fill { background-color: var(--accent); color: var(--accent); border-right: 3px solid var(--accent); }
        .fd-fill { background-color: var(--warn); color: var(--warn); border-right: 3px solid var(--warn);}
        .wt-fill { background-color: var(--primary); color: var(--primary); border-right: 3px solid var(--primary);}
        .en-fill { background-color: var(--success); color: var(--success); border-right: 3px solid var(--success);}

        /* לוג (Terminal Log) */
        .log-terminal {
            flex-grow: 1;
            background: #000;
            border: 1px solid #333;
            font-family: 'Share Tech Mono', monospace;
            padding: 10px;
            font-size: 13px;
            overflow-y: auto;
            color: #aaa;
            box-shadow: inset 0 0 10px #000;
            display: flex;
            flex-direction: column-reverse; /* הודעות חדשות למעלה */
        }
        .msg { padding: 4px 0; border-bottom: 1px solid #111; }
        .msg-good { color: var(--success); }
        .msg-bad { color: var(--accent); }
        .msg-sys { color: var(--primary); }

        /* תיק (Inventory) */
        .inventory-box {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 8px;
            background: rgba(255,255,255,0.03);
            padding: 10px;
            border-radius: 8px;
        }
        .inv-item {
            text-align: center;
            font-size: 12px;
            background: #111;
            padding: 5px;
            border-radius: 4px;
            border: 1px solid #333;
        }
        .inv-val { font-size: 16px; font-weight: bold; display: block; color:white; }

        /* פעולות */
        .action-deck {
            display: grid;
            grid-template-columns: 1fr 1fr;
            grid-template-rows: auto auto;
            gap: 10px;
        }
        
        .btn {
            background: linear-gradient(145deg, #1a2c3d, #0f1925);
            color: var(--text);
            border: 1px solid rgba(0, 242, 255, 0.2);
            padding: 15px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            font-weight: bold;
            font-family: 'Rubik', sans-serif;
            transition: all 0.2s;
            display: flex; flex-direction: column; align-items: center;
        }
        .btn:active { transform: scale(0.95); box-shadow: none; }
        .btn:hover { border-color: var(--primary); box-shadow: 0 0 15px rgba(0,242,255,0.1); background: #162635;}
        
        .btn-main { grid-column: 1 / -1; background: linear-gradient(145deg, #2a1a1a, #200f0f); border-color: var(--accent);}
        .btn-main:hover { border-color: var(--accent); box-shadow: 0 0 15px rgba(255,0,85,0.2); }

        /* מסך מוות */
        .overlay {
            position: absolute; top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0,0,0,0.9);
            z-index: 100;
            display: none;
            justify-content: center;
            align-items: center;
            flex-direction: column;
            text-align: center;
        }
        .neon-text { color: var(--accent); text-shadow: 0 0 10px var(--accent); font-size: 40px; margin-bottom: 20px;}

    </style>
</head>
<body>

    <div class="game-interface">
        
        <!-- Header -->
        <div class="hud-header">
            <div class="day-counter">DAY <span id="dayVal">1</span></div>
            <div class="time-badge" id="timeBadge">☀️ 12:00</div>
        </div>

        <!-- Stats Bars -->
        <div class="stats-container">
            <div class="stat-card">
                <div class="stat-header"><span>❤️ בריאות</span><span id="txt-hp">100%</span></div>
                <div class="progress-bg"><div class="progress-fill hp-fill" id="bar-hp"></div></div>
            </div>
            <div class="stat-card">
                <div class="stat-header"><span>🍗 רעב</span><span id="txt-fd">100%</span></div>
                <div class="progress-bg"><div class="progress-fill fd-fill" id="bar-fd"></div></div>
            </div>
            <div class="stat-card">
                <div class="stat-header"><span>⚡ אנרגיה</span><span id="txt-en">100%</span></div>
                <div class="progress-bg"><div class="progress-fill en-fill" id="bar-en"></div></div>
            </div>
            <div class="stat-card">
                <div class="stat-header"><span>💧 מים</span><span id="txt-wt">100%</span></div>
                <div class="progress-bg"><div class="progress-fill wt-fill" id="bar-wt"></div></div>
            </div>
        </div>

        <!-- Log -->
        <div class="log-terminal" id="logBox">
            <div class="msg msg-sys">> מערכת הישרדות אותחלה...</div>
            <div class="msg">> ברוך הבא לעולם החדש.</div>
        </div>

        <!-- Inventory -->
        <div class="inventory-box">
            <div class="inv-item">🥫 שימורים<span class="inv-val" id="inv-food">2</span></div>
            <div class="inv-item">🥤 מים<span class="inv-val" id="inv-water">2</span></div>
            <div class="inv-item">💊 תרופה<span class="inv-val" id="inv-med">1</span></div>
        </div>

        <!-- Buttons -->
        <div class="action-deck">
            <button class="btn btn-main" onclick="game.scavenge()">🔭 צא לסיור (חפש ציוד)</button>
            <button class="btn" onclick="game.eat()">🥫 לאכול</button>
            <button class="btn" onclick="game.drink()">🥤 לשתות</button>
            <button class="btn" onclick="game.sleep()">💤 לישון (לילה)</button>
            <button class="btn" onclick="game.heal()">💊 לרפא</button>
        </div>

        <!-- Game Over Overlay -->
        <div class="overlay" id="endScreen">
            <div class="neon-text">SYSTEM FAILURE</div>
            <p style="color:white; margin-bottom:30px">מתת. הדרך הסתיימה.</p>
            <button class="btn" onclick="location.reload()" style="background:var(--primary); color:black; width: 200px;">🔄 נסה מחדש</button>
        </div>

    </div>

    <script>
        const game = {
            stats: { hp: 100, food: 90, water: 90, nrg: 100 },
            inv: { food: 2, water: 2, med: 1 },
            day: 1,
            isNight: false,

            // פונקציות עזר ללוגים ול-UI
            log: function(txt, cls="msg") {
                const box = document.getElementById("logBox");
                const div = document.createElement("div");
                div.className = "msg " + cls;
                div.innerText = "> " + txt;
                box.prepend(div);
            },

            updateUI: function() {
                // עדכון מספרים
                document.getElementById("txt-hp").innerText = Math.floor(this.stats.hp) + "%";
                document.getElementById("txt-fd").innerText = Math.floor(this.stats.food) + "%";
                document.getElementById("txt-en").innerText = Math.floor(this.stats.nrg) + "%";
                document.getElementById("txt-wt").innerText = Math.floor(this.stats.water) + "%";

                // עדכון רוחב הברים
                document.getElementById("bar-hp").style.width = this.stats.hp + "%";
                document.getElementById("bar-fd").style.width = this.stats.food + "%";
                document.getElementById("bar-en").style.width = this.stats.nrg + "%";
                document.getElementById("bar-wt").style.width = this.stats.water + "%";

                // עדכון מלאי
                document.getElementById("inv-food").innerText = this.inv.food;
                document.getElementById("inv-water").innerText = this.inv.water;
                document.getElementById("inv-med").innerText = this.inv.med;

                // בדיקת מוות
                if(this.stats.hp <= 0) {
                    document.getElementById("endScreen").style.display = "flex";
                }
            },

            // --- פעולות המשחק (מאוזנות להיות קלות יותר) ---

            scavenge: function() {
                if (this.stats.nrg < 10) {
                    this.log("אין לך כוח לצאת! תנוח קצת.", "msg-bad");
                    return;
                }

                this.log("יצאת לסרוק את השטח...", "msg-sys");
                
                // מחיר פעולה (נמוך יותר מפעם)
                this.stats.nrg -= 15;
                this.stats.food -= 3;
                this.stats.water -= 4;

                // חישוב מציאת חפצים (סיכוי גבוה מאוד!)
                const luck = Math.random();
                if (luck > 0.1) { // 90% הצלחה
                    const find = Math.random();
                    if (find < 0.4) {
                        this.inv.food++;
                        this.log("מצאת קופסת שימורים!", "msg-good");
                    } else if (find < 0.7) {
                        this.inv.water++;
                        this.log("מצאת מים נקיים!", "msg-good");
                    } else if (find < 0.85) {
                        this.inv.med++;
                        this.log("מדהים! מצאת תרופה.", "msg-good");
                    } else {
                        // ה"דאבל" - מציאה כפולה
                        this.inv.food++; this.inv.water++;
                        this.log("Jackpot! מצאת גם אוכל וגם מים.", "msg-good");
                    }
                } else {
                    this.log("חזרת בידיים ריקות... מוזר.", "msg");
                }

                // סיכוי קטן לפציעה
                if (Math.random() > 0.85) { // רק 15% סיכון
                    const dmg = Math.floor(Math.random() * 10) + 2;
                    this.stats.hp -= dmg;
                    this.log("נשרטת בדרך חזרה (-" + dmg + " HP)", "msg-bad");
                }

                this.checkLimits();
                this.updateUI();
            },

            eat: function() {
                if (this.inv.food > 0) {
                    this.inv.food--;
                    this.stats.food = Math.min(100, this.stats.food + 40); // ממלא הרבה
                    this.stats.hp = Math.min(100, this.stats.hp + 5);
                    this.log("אכלת לשובע. (+40)", "msg-good");
                } else {
                    this.log("התיק ריק מאוכל!", "msg-bad");
                }
                this.updateUI();
            },

            drink: function() {
                if (this.inv.water > 0) {
                    this.inv.water--;
                    this.stats.water = Math.min(100, this.stats.water + 50); // מרווה מאוד
                    this.stats.nrg = Math.min(100, this.stats.nrg + 5);
                    this.log("שתית מים קרים. (+50)", "msg-good");
                } else {
                    this.log("אין לך מים!", "msg-bad");
                }
                this.updateUI();
            },

            heal: function() {
                if (this.inv.med > 0) {
                    this.inv.med--;
                    this.stats.hp = Math.min(100, this.stats.hp + 50); // ריפוי חזק
                    this.log("השתמשת בתרופה. הבריאות משתפרת.", "msg-good");
                } else {
                    this.log("אין לך תרופות!", "msg-bad");
                }
                this.updateUI();
            },

            sleep: function() {
                this.isNight = !this.isNight;
                
                // שינה מרפאה ונותנת כוח
                this.stats.nrg = 100; // ממלא עד הסוף
                this.stats.hp = Math.min(100, this.stats.hp + 10);
                
                // עולה "קצת" ברעב וצמא (לא מעניש מדי)
                this.stats.food -= 10;
                this.stats.water -= 10;

                let timeStr = this.isNight ? "🌙 לילה" : "☀️ יום";
                
                if (!this.isNight) {
                    this.day++;
                    document.getElementById("dayVal").innerText = this.day;
                    this.log("======== בוקר יום " + this.day + " ========", "msg-sys");
                } else {
                    this.log("הלכת לישון. הלילה יורד...", "msg-sys");
                }
                
                document.getElementById("timeBadge").innerText = timeStr;
                
                this.checkLimits();
                this.updateUI();
            },

            checkLimits: function() {
                // מונע מספרים שליליים
                this.stats.food = Math.max(0, this.stats.food);
                this.stats.water = Math.max(0, this.stats.water);
                this.stats.nrg = Math.max(0, this.stats.nrg);
                
                // אם הגעת ל-0 באוכל או מים, יורד קצת HP (אבל לא מתים ישר)
                if(this.stats.food === 0) {
                    this.stats.hp -= 2;
                    this.log("אתה גווע מרעב...", "msg-bad");
                }
                if(this.stats.water === 0) {
                    this.stats.hp -= 3;
                    this.log("אתה מיובש לחלוטין...", "msg-bad");
                }
            }
        };

        // התחלה
        game.updateUI();
    </script>
</body>
</html>
"""

@app.route('/')
def game():
    return render_template_string(GAME_HTML)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
