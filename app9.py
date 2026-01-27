from flask import Flask, render_template_string, jsonify, request
import random
import json

app = Flask(__name__)
app.secret_key = 'clover_master_key_v_ultimate'

# נתוני שחקן בצד שרת (לשמירת התקדמות)
PLAYER_DATA = {
    "shards": 0,
    "unlocks": ["fire", "water", "earth", "air"],
    "stats": {"wins": 0, "deaths": 0}
}

@app.route('/')
def idx():
    return render_template_string(GAME_HTML)

@app.route('/api/save', methods=['POST'])
def save():
    data = request.json
    PLAYER_DATA["shards"] += data.get("shards", 0)
    if data.get("win"): PLAYER_DATA["stats"]["wins"] += 1
    return jsonify({"status": "saved", "total_shards": PLAYER_DATA["shards"]})

# ==========================================
# קוד צד לקוח (HTML + JS ENGINE)
# ==========================================
GAME_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CLOVER: Dual Reality</title>
    <link href="https://fonts.googleapis.com/css2?family=Press+Start+2P&family=Rajdhani:wght@500;700&display=swap" rel="stylesheet">
    <style>
        :root { --ui-color: #00ffd5; --bg-dark: #050510; }
        body { margin: 0; overflow: hidden; background: #000; font-family: 'Press Start 2P', monospace; }
        
        /* מיכל המשחק */
        #game-container {
            position: relative;
            width: 100vw; height: 100vh;
            background: linear-gradient(to bottom, #0f2027, #203a43, #2c5364);
            overflow: hidden;
        }

        /* שכבה 1: עולם הפיקסלים (פריך ומפוקסל) */
        #canvas-pixel {
            position: absolute; top: 0; left: 0; width: 100%; height: 100%;
            image-rendering: pixelated; z-index: 1;
        }

        /* שכבה 2: אפקטים HD (זוהר וחלק) */
        #canvas-hd {
            position: absolute; top: 0; left: 0; width: 100%; height: 100%;
            z-index: 2; mix-blend-mode: screen; pointer-events: none;
        }

        /* שכבת UI */
        #ui-layer {
            position: absolute; top: 0; left: 0; width: 100%; height: 100%;
            z-index: 10; pointer-events: none; padding: 20px;
        }

        /* מסכי תפריט */
        .screen {
            position: absolute; top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(5, 5, 16, 0.95);
            display: flex; flex-direction: column;
            justify-content: center; align-items: center;
            z-index: 100; pointer-events: auto;
        }
        .hidden { display: none !important; }

        /* כפתורים וסטייל */
        h1 { font-size: 60px; color: transparent; -webkit-text-stroke: 2px var(--ui-color); text-shadow: 0 0 20px var(--ui-color); letter-spacing: 5px; }
        
        .char-grid { display: flex; gap: 20px; margin: 40px 0; }
        .char-card {
            width: 100px; height: 140px; border: 2px solid #555; cursor: pointer;
            display: flex; flex-direction: column; align-items: center; justify-content: center;
            transition: 0.3s; background: #222;
        }
        .char-card:hover { border-color: var(--ui-color); transform: scale(1.1); box-shadow: 0 0 15px var(--ui-color); }
        .char-color { width: 50px; height: 50px; margin-bottom: 10px; }

        /* HUD */
        .hud-bar { width: 300px; height: 20px; background: #222; border: 2px solid white; margin-bottom: 10px; position: relative; }
        .bar-fill { height: 100%; width: 100%; transition: width 0.2s cubic-bezier(0.25, 1, 0.5, 1); }
        .hp { background: #ff2a6d; box-shadow: 0 0 10px #ff2a6d; }
        .mana { background: #05d9e8; box-shadow: 0 0 10px #05d9e8; }
        
        /* Scanline Overlay for aesthetic */
        .scanlines {
            position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; z-index: 99;
            background: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.1) 50%);
            background-size: 100% 4px;
        }
    </style>
</head>
<body>

<div id="game-container">
    <canvas id="canvas-pixel"></canvas>
    <canvas id="canvas-hd"></canvas>
    <div class="scanlines"></div>
    
    <div id="ui-layer" class="hidden">
        <div class="hud-bar"><div id="bar-hp" class="bar-fill hp"></div></div>
        <div class="hud-bar"><div id="bar-en" class="bar-fill mana"></div></div>
        <div style="font-family: 'Rajdhani', sans-serif; font-size: 24px; color: #fff;">
            SHARDS: <span id="shards-count" style="color: gold;">0</span>
        </div>
        <div style="position: absolute; bottom: 20px; right: 20px; font-family: 'Rajdhani'; font-size: 14px; text-align:right;">
            MOVE: A/D | JUMP: W | CROUCH: S<br>
            CHARGE: U | ATTACK: J / K / H
        </div>
    </div>

    <!-- MAIN MENU -->
    <div id="menu-screen" class="screen">
        <h1>CLOVER</h1>
        <h3 style="color:#aaa; margin-top:-30px;">PIXEL MEETS HD</h3>
        <button onclick="toCharSelect()" style="padding:15px 40px; font-size:20px; background:var(--ui-color); border:none; cursor:pointer; font-weight:bold; margin-top:50px;">PLAY</button>
    </div>

    <!-- CHARACTER SELECT -->
    <div id="char-select" class="screen hidden">
        <h2>CHOOSE ELEMENT</h2>
        <div class="char-grid">
            <div class="char-card" onclick="startGame('FIRE')">
                <div class="char-color" style="background:#ff4500; box-shadow:0 0 10px #f40;"></div>
                <span>FIRE</span>
            </div>
            <div class="char-card" onclick="startGame('WATER')">
                <div class="char-color" style="background:#00bfff; box-shadow:0 0 10px #0bf;"></div>
                <span>WATER</span>
            </div>
            <div class="char-card" onclick="startGame('EARTH')">
                <div class="char-color" style="background:#8b4513; box-shadow:0 0 10px #a63;"></div>
                <span>EARTH</span>
            </div>
             <div class="char-card" onclick="startGame('AIR')">
                <div class="char-color" style="background:#eee; box-shadow:0 0 10px #fff;"></div>
                <span>AIR</span>
            </div>
        </div>
    </div>
</div>

<script>
/** CLOVER GAME ENGINE - Dual Rendering System **/

// קנבס כפול: אחד לפיקסלים (נמוך) אחד לאפקטים (גבוה)
const cP = document.getElementById('canvas-pixel');
const ctxP = cP.getContext('2d');
const cH = document.getElementById('canvas-hd');
const ctxH = cH.getContext('2d');

// קבועים פיזיקליים
const GRAVITY = 0.5;
const FRICTION = 0.85;
const GROUND_Y = 500; // רצפה
const TARGET_FPS = 60;

// נתוני דמויות
const WIZARDS = {
    FIRE:  { color: '#ff4500', glow: 'rgba(255,69,0,0.8)', proj: 'fireball', hp: 300, spd: 5 },
    WATER: { color: '#00bfff', glow: 'rgba(0,191,255,0.6)', proj: 'water', hp: 320, spd: 4.5 },
    EARTH: { color: '#8b4513', glow: 'rgba(139,69,19,0.5)', proj: 'rock', hp: 350, spd: 3.5 },
    AIR:   { color: '#ffffff', glow: 'rgba(255,255,255,0.7)', proj: 'wind', hp: 290, spd: 6.5 },
};

// State
let gameRunning = false;
let player;
let entities = [];
let particles = [];
let keys = {};
let camX = 0;

// שינוי גודל מסך
function resize() {
    // פיקסלים קטנים למראה רטרו
    cP.width = window.innerWidth / 2; 
    cP.height = window.innerHeight / 2;
    // HD מלא לאפקטים
    cH.width = window.innerWidth;
    cH.height = window.innerHeight;
    
    // החלקת תמונה: כבויה לפיקסלים, דלוקה ל-HD
    ctxP.imageSmoothingEnabled = false;
    ctxH.imageSmoothingEnabled = true;
}
window.onresize = resize;
resize();

// Input
window.onkeydown = e => keys[e.key.toLowerCase()] = true;
window.onkeyup = e => keys[e.key.toLowerCase()] = false;

// === CLASSES ===

class Entity {
    constructor(x, y, w, h, type, color) {
        this.x = x; this.y = y; this.w = w; this.h = h;
        this.vx = 0; this.vy = 0;
        this.color = color;
        this.type = type;
        this.grounded = false;
        this.hp = 100; this.maxHp = 100;
        this.dead = false;
    }

    physics() {
        this.vy += GRAVITY;
        this.vx *= FRICTION;
        this.x += this.vx;
        this.y += this.vy;

        // התנגשות רצפה
        if(this.y + this.h > GROUND_Y) {
            this.y = GROUND_Y - this.h;
            this.vy = 0;
            this.grounded = true;
        } else {
            this.grounded = false;
        }
    }

    draw(ctx, cam) {
        if(this.dead) return;
        // מצייר רק ריבוע בפיקסל-ארט (ה"גוף")
        // בעתיד כאן יבוא Sprite Sheet
        ctx.fillStyle = this.color;
        
        // סימולציה של אנימציית קפיצה (Squash & Stretch)
        let dh = this.h; 
        if (!this.grounded) dh += 4; // נמתח באוויר
        else if (Math.abs(this.vx) > 0.1) dh += Math.sin(Date.now()/50)*2; // רעידות בריצה
        
        ctx.fillRect(Math.floor(this.x - cam), Math.floor(this.y + (this.h-dh)), this.w, dh);
        
        // עיניים (כדי לראות לאן מסתכלים)
        ctx.fillStyle = "white";
        let eyeOffset = this.vx >= 0 ? 4 : -4;
        ctx.fillRect(Math.floor(this.x + this.w/2 + eyeOffset - cam), Math.floor(this.y + 10), 4, 4);
    }
}

class Player extends Entity {
    constructor(wizardKey) {
        let stats = WIZARDS[wizardKey];
        super(100, 300, 24, 48, 'player', stats.color);
        this.hp = stats.hp; 
        this.maxHp = stats.hp;
        this.speed = stats.spd;
        this.mana = 0;
        this.wizData = stats;
        this.cooldown = 0;
    }

    update() {
        if (this.dead) return;

        // תנועה
        if(keys['a']) this.vx -= 1;
        if(keys['d']) this.vx += 1;
        
        // הגבלת מהירות
        if(this.vx > this.speed) this.vx = this.speed;
        if(this.vx < -this.speed) this.vx = -this.speed;

        // קפיצה
        if((keys['w'] || keys[' ']) && this.grounded) {
            this.vy = -12;
            createExplosion(this.x + this.w/2, this.y + this.h, '#fff', 5, false); // אבק
        }
        
        // טעינה
        if(keys['u']) {
            this.mana = Math.min(100, this.mana + 1);
            this.vx *= 0.8; // מאט בזמן טעינה
            // אפקט טעינה
            if(Math.random() > 0.5) 
                particles.push(new Particle(this.x + Math.random()*this.w, this.y + this.h, 0, -2, this.wizData.glow, true));
        }

        // התקפה (J)
        if(this.cooldown > 0) this.cooldown--;
        if(keys['j'] && this.cooldown <= 0 && this.mana >= 10) {
            this.shoot();
        }

        this.physics();
        
        // עדכון מצלמה רכה
        let targetCam = this.x - cP.width / 3;
        camX += (targetCam - camX) * 0.1;
    }

    shoot() {
        this.mana -= 10;
        this.cooldown = 15;
        
        // Auto Aim: מחפש אויב קרוב
        let target = enemies.find(e => Math.abs(e.x - this.x) < 400 && !e.dead);
        let angle = 0;
        
        if (target) {
            angle = Math.atan2((target.y+15) - (this.y+10), (target.x+15) - this.x);
        } else {
            angle = this.vx >= 0 ? 0 : Math.PI; // אם אין אויב, יורה ישר
        }
        
        entities.push(new Projectile(this.x+12, this.y+12, angle, this.wizData));
    }
}

class Enemy extends Entity {
    constructor(x, type) {
        // בוסים ואויבים רגילים
        let w=30, h=30, c='#f0f', hp=100;
        if(type=='boss') { w=80; h=80; c='#400'; hp=1000; }
        super(x, 0, w, h, 'enemy', c);
        this.hp = hp; this.maxHp = hp;
        this.timer = 0;
    }

    update() {
        if(this.dead) return;
        this.physics();
        
        // AI בסיסי: רודף אחרי השחקן
        let dx = player.x - this.x;
        if(Math.abs(dx) < 400) {
            if(dx > 5) this.vx += 0.5;
            if(dx < -5) this.vx -= 0.5;
        }

        if(this.vx > 2) this.vx = 2;
        if(this.vx < -2) this.vx = -2;
        
        // פגיעה בשחקן
        if(collision(this, player)) {
            player.hp -= 1;
            player.vx = Math.sign(dx) * 10; // הדיפה
            this.vx = -Math.sign(dx) * 5;
            shake(10); // רעידת מסך
        }
    }
}

class Projectile {
    constructor(x, y, angle, typeData) {
        this.x = x; this.y = y;
        this.speed = 12;
        this.vx = Math.cos(angle) * this.speed;
        this.vy = Math.sin(angle) * this.speed;
        this.type = 'proj';
        this.color = typeData.color;
        this.glow = typeData.glow;
        this.life = 60;
        this.dead = false;
        this.w=10; this.h=10;
    }
    
    update() {
        this.x += this.vx;
        this.y += this.vy;
        this.life--;
        if(this.life<=0) this.dead=true;
        
        // שובל של חלקיקים (Trail)
        particles.push(new Particle(this.x, this.y, 0,0, this.color, true));
        
        // התנגשות עם אויבים
        enemies.forEach(e => {
            if(!e.dead && collision(this, e)) {
                this.dead = true;
                e.hp -= 25;
                if(e.hp <= 0) {
                    e.dead = true;
                    createExplosion(e.x+e.w/2, e.y+e.h/2, e.color, 30, true);
                    // Drop loot here
                }
                createExplosion(this.x, this.y, this.glow, 10, true);
            }
        });
    }

    draw(ctxP, ctxH, camX) {
        // בפיקסלים: נקודה קטנה
        // ב-HD: כדור זוהר ענק
        
        // HD
        let cx = (this.x - camX) * 2;
        let cy = this.y * 2;
        
        let grad = ctxH.createRadialGradient(cx, cy, 2, cx, cy, 20);
        grad.addColorStop(0, '#fff');
        grad.addColorStop(0.2, this.color);
        grad.addColorStop(1, 'rgba(0,0,0,0)');
        
        ctxH.fillStyle = grad;
        ctxH.beginPath();
        ctxH.arc(cx, cy, 20, 0, Math.PI*2);
        ctxH.fill();
    }
}

class Particle {
    constructor(x, y, vx, vy, color, isHD) {
        this.x = x; this.y = y;
        this.vx = vx; this.vy = vy;
        this.color = color;
        this.isHD = isHD;
        this.life = 1.0;
        this.decay = Math.random() * 0.05 + 0.02;
    }
    update() {
        this.x += this.vx;
        this.y += this.vy;
        this.life -= this.decay;
    }
    draw(ctxP, ctxH, camX) {
        if(this.life <= 0) return;
        
        if (this.isHD) {
            let cx = (this.x - camX) * 2;
            let cy = this.y * 2;
            ctxH.globalAlpha = this.life;
            ctxH.fillStyle = this.color;
            ctxH.beginPath();
            ctxH.arc(cx, cy, 5 * this.life, 0, Math.PI*2);
            ctxH.fill();
            ctxH.globalAlpha = 1;
        } else {
            ctxP.fillStyle = this.color;
            ctxP.fillRect(this.x - camX, this.y, 2, 2);
        }
    }
}

// === ENGINE UTILS ===

function createExplosion(x, y, color, count, hd) {
    for(let i=0; i<count; i++) {
        let ang = Math.random() * Math.PI * 2;
        let spd = Math.random() * 5;
        let p = new Particle(x, y, Math.cos(ang)*spd, Math.sin(ang)*spd, color, hd);
        particles.push(p);
    }
}

function collision(a, b) {
    return (a.x < b.x + b.w && a.x + a.w > b.x &&
            a.y < b.y + b.h && a.y + a.h > b.y);
}

let shakeAmt = 0;
function shake(amt) { shakeAmt = amt; }

// === GAME LOOP ===

function loop() {
    if(!gameRunning) return;

    // Logic
    player.update();
    entities = entities.filter(e => !e.dead); // Clean up
    entities.forEach(e => e.update()); // Only projectiles update here
    enemies.forEach(e => e.update());
    
    // ניהול רשימות
    projectiles.forEach(p => p.update());
    projectiles = projectiles.filter(p => !p.dead);
    
    particles.forEach(p => p.update());
    particles = particles.filter(p => p.life > 0);

    // Render Clean
    ctxP.clearRect(0,0,cP.width, cP.height);
    ctxH.clearRect(0,0,cH.width, cH.height);
    
    // Screen Shake
    let sx = (Math.random()-0.5) * shakeAmt;
    let sy = (Math.random()-0.5) * shakeAmt;
    if(shakeAmt>0) shakeAmt *= 0.9;
    if(shakeAmt<0.5) shakeAmt=0;
    
    // 1. Render World (Pixels)
    ctxP.fillStyle = '#333'; // Floor
    ctxP.fillRect(0 - camX, GROUND_Y, 2000, 200); 
    
    // Draw background hint
    ctxP.fillStyle = '#112'; 
    for(let i=0; i<10; i++) ctxP.fillRect(i*200 - (camX*0.5 % 200), 200, 50, 300); // Parallax BG trees/pillars

    player.draw(ctxP, camX - sx);
    enemies.forEach(e => e.draw(ctxP, camX - sx));
    particles.filter(p=>!p.isHD).forEach(p=>p.draw(ctxP, null, camX-sx));

    // 2. Render Effects (HD)
    // Draw particles / Glows / UI effects
    projectiles.forEach(p => p.draw(null, ctxH, camX - sx));
    particles.filter(p=>p.isHD).forEach(p=>p.draw(null, ctxH, camX-sx));
    
    // UI Update
    document.getElementById('bar-hp').style.width = (player.hp / player.maxHp * 100) + '%';
    document.getElementById('bar-en').style.width = (player.mana / 100 * 100) + '%';

    requestAnimationFrame(loop);
}

// === FLOW CONTROL ===

function toCharSelect() {
    document.getElementById('menu-screen').classList.add('hidden');
    document.getElementById('char-select').classList.remove('hidden');
}

function startGame(wizType) {
    document.getElementById('char-select').classList.add('hidden');
    document.getElementById('ui-layer').classList.remove('hidden');
    
    // Init Game
    gameRunning = true;
    player = new Player(wizType);
    
    enemies = [];
    // Spawn basic enemies
    for(let i=0; i<5; i++) {
        enemies.push(new Enemy(600 + i * 300, 'norm'));
    }
    enemies.push(new Enemy(2000, 'boss')); // Boss at the end

    requestAnimationFrame(loop);
}

</script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(port=5000, debug=True)
