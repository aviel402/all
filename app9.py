from flask import Flask, render_template_string, jsonify, request
import random
import json

app = Flask(__name__)
app.secret_key = 'clover_master_key_v99'

# Placeholder for persistent improvement storage (in a real app, use a DB)
# Using a simple file-based or global variable approach for this session

PLAYER_DATA = {
    "shards": 0,
    "unlocks": ["fire", "warrior"], # Default unlocked classes
    "upgrades": {
        "hp": 0,
        "energy_charge": 0,
        "potion": 0
    }
}

@app.route('/')
def idx():
    return render_template_string(GAME_HTML)

@app.route('/save', methods=['POST'])
def save_progress():
    global PLAYER_DATA
    data = request.json
    PLAYER_DATA["shards"] += data.get("shards", 0)
    return jsonify(PLAYER_DATA)

@app.route('/data')
def get_data():
    return jsonify(PLAYER_DATA)

@app.route('/unlock', methods=['POST'])
def unlock_class():
    # Logic to buy classes/upgrades
    return jsonify({"status": "ok"})

GAME_HTML = """

<!DOCTYPE html>

<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CLOVER - Elemental Chronicles</title>
    <link href="                                                                    " rel="stylesheet">
    <style>
        :root {
            --bg-sky: #87CEEB;
            --bg-sunset: #FF7F50;
            --ui-bg: rgba(20, 20, 30, 0.9);
            --text-color: #eee;
        }
        body { margin: 0; overflow: hidden; background: #111; font-family: 'Press Start 2P', cursive; color: var(--text-color); }
        canvas { display: block; image-rendering: pixelated; }

#ui-layer {
        position: absolute;
        top: 0; left: 0;
        width: 100%; height: 100%;
        pointer-events: none;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        padding: 20px;
        box-sizing: border-box;
    }

    .hud-bar { display: flex; gap: 20px; align-items: center; }
    .bar-container { position: relative; width: 200px; height: 20px; background: #333; border: 2px solid #fff; }
    .bar-fill { height: 100%; transition: width 0.1s; }
    .hp-fill { background: #f00; }
    .en-fill { background: #0df; }
    
    #menu-screen, #char-select, #shop-screen {
        position: absolute;
        top: 0; left: 0;
        width: 100%; height: 100%;
        background: rgba(0,0,0,0.85);
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        pointer-events: auto;
        z-index: 100;
    }
    
    .hidden { display: none !important; }
    
    h1 { font-size: 40px; color: #fff; text-shadow: 4px 4px 0 #000; margin-bottom: 40px; }
    h2 { color: gold; margin-bottom: 20px; }
    
    .btn {
        background: #333;
        border: 4px solid #fff;
        color: #fff;
        padding: 15px 30px;
        font-family: inherit;
        font-size: 16px;
        cursor: pointer;
        margin: 10px;
        text-transform: uppercase;
        transition: transform 0.1s;
    }
    .btn:hover { background: #555; transform: scale(1.05); }
    .btn:active { transform: scale(0.95); }
    
    .char-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; max-width: 800px; }
    .char-card {
        background: #222;
        border: 2px solid #555;
        padding: 10px;
        text-align: center;
        cursor: pointer;
        transition: all 0.2s;
    }
    .char-card:hover { border-color: gold; background: #333; }
    .char-card.locked { opacity: 0.5; cursor: not-allowed; }
    .char-icon { width: 64px; height: 64px; margin: 0 auto 10px; background: #000; image-rendering: pixelated;}
    
    .controls-hint {
        position: absolute; bottom: 20px; right: 20px;
        text-align: right; font-size: 10px; opacity: 0.7;
    }
    
    /* Scanline effect */
    .scanlines {
        position: fixed; top: 0; left: 0; width: 100%; height: 100%;
        background: linear-gradient(to bottom, rgba(255,255,255,0), rgba(255,255,255,0) 50%, rgba(0,0,0,0.2) 50%, rgba(0,0,0,0.2));
        background-size: 100% 4px;
        pointer-events: none;
        z-index: 999;
    }
</style>
</head>
<body>

<div class="scanlines"></div>

<!-- Game Canvas -->


<canvas id="gameCanvas"></canvas>

<!-- UI Layer -->

<div id="ui-layer" class="hidden">
    <div class="hud-top">
        <div class="hud-bar">
            <span>HP</span>
            <div class="bar-container"><div class="bar-fill hp-fill" id="hp-bar" style="width: 100%"></div></div>
        </div>
        <div class="hud-bar" style="margin-top: 5px;">
            <span>EN</span>
            <div class="bar-container"><div class="bar-fill en-fill" id="en-bar" style="width: 100%"></div></div>
        </div>
    </div>
    <div class="hud-bottom">
        <div id="shards-display">💎 0</div>
    </div>
</div>

<!-- Main Menu -->

<div id="menu-screen">
    <h1>🍀 CLOVER</h1>
    <button class="btn" onclick="openCharSelect()">Start Game</button>
    <button class="btn" disabled>Options</button>
</div>

<!-- Character Select -->

<div id="char-select" class="hidden">
    <h2>Choose Your Wizard</h2>
    <div class="char-grid" id="char-grid">
        <!-- Generated by JS -->
    </div>
    <button class="btn" onclick="backToMenu()" style="margin-top: 30px;">Back</button>
</div>

<script>
/**
 * CLOVER Game Engine
 * A simple JS engine for Platformer mechanics
 */

const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');

// Game Constants
const GRAVITY = 0.5;
const FRICTION = 0.8;
const GAME_WIDTH = 960; // 480 * 2 for sharp pixels
const GAME_HEIGHT = 540; // 270 * 2

let lastTime = 0;
let gameState = 'MENU'; // MENU, PLAY, GAMEOVER
let camera = { x: 0, y: 0 };
let shards = 0;

// Input Handling
const keys = { w:false, a:false, s:false, d:false, j:false, k:false, h:false, u:false };

window.addEventListener('keydown', e => {
    if(keys.hasOwnProperty(e.key.toLowerCase())) keys[e.key.toLowerCase()] = true;
});
window.addEventListener('keyup', e => {
    if(keys.hasOwnProperty(e.key.toLowerCase())) keys[e.key.toLowerCase()] = false;
});

window.addEventListener('resize', resize);
function resize() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    ctx.imageSmoothingEnabled = false;
}
resize();

// Classes Data
const CLASSES = {
    fire: { name: "Pyromancer", color: "#f42", skill: "Fireball", ult: "Inferno" },
    water: { name: "Hydromancer", color: "#24f", skill: "Wave", ult: "Tsunami" },
    earth: { name: "Geomancer", color: "#8a4", skill: "Rock", ult: "Quake" },
    air: { name: "Aeromancer", color: "#cdf", skill: "Windblade", ult: "Tornado" },
    warrior: { name: "Warrior", color: "#aaa", skill: "Slash", ult: "Slam" },
    light: { name: "Lightbringer", color: "#fd0", skill: "Beam", ult: "Nova" },
    dark: { name: "Voidwalker", color: "#408", skill: "Void", ult: "Blackhole" }
};

// Game Objects
let player;
let enemies = [];
let particles = [];
let projectiles = [];
let level = [];
let backgroundLayers = [];

class Entity {
    constructor(x, y, w, h, color) {
        this.x = x; this.y = y;
        this.w = w; this.h = h;
        this.vx = 0; this.vy = 0;
        this.color = color;
        this.grounded = false;
        this.facing = 1; // 1 right, -1 left
        this.hp = 100;
        this.maxHp = 100;
    }
    
    update() {
        // Physics
        this.vy += GRAVITY;
        this.x += this.vx;
        this.y += this.vy;
        
        // Ground Collision (Simple floor at y=400 for demo)
        if (this.y + this.h > 400) {
            this.y = 400 - this.h;
            this.vy = 0;
            this.grounded = true;
        } else {
            this.grounded = false;
        }
        
        // Friction
        this.vx *= FRICTION;
    }
    
    draw(camX) {
        ctx.fillStyle = this.color;
        ctx.fillRect(this.x - camX, this.y, this.w, this.h);
    }
}

class Player extends Entity {
    constructor(clsKey) {
        super(100, 300, 32, 64, CLASSES[clsKey].color);
        this.cls = CLASSES[clsKey];
        this.energy = 100;
        this.maxEnergy = 100;
        this.charging = false;
        this.attackCooldown = 0;
    }
    
    update() {
        if (this.hp <= 0) return;
        
        // Input Movement
        if (!this.charging) {
            if (keys.a) { this.vx -= 1.5; this.facing = -1; }
            if (keys.d) { this.vx += 1.5; this.facing = 1; }
            if (keys.w && this.grounded) { this.vy = -12; this.grounded = false; }
        }
        
        // Energy Charge
        this.charging = keys.u;
        if (this.charging) {
            this.energy = Math.min(this.energy + 1, this.maxEnergy);
            this.vx *= 0.5; // Slow down
            spawnParticles(this.x + this.w/2, this.y + this.h/2, this.color, 1);
        }
        
        // Combat
        if (this.attackCooldown > 0) this.attackCooldown--;
        
        if (keys.j && this.attackCooldown <= 0 && this.energy >= 10) {
             this.attack('basic');
        }
        
        super.update();
        
        // Update UI
        document.getElementById('hp-bar').style.width = (this.hp / this.maxHp * 100) + "%";
        document.getElementById('en-bar').style.width = (this.energy / this.maxEnergy * 100) + "%";
    }
    
    attack(type) {
        this.attackCooldown = 20;
        this.energy -= 10;
        
        // Auto Aim Logic
        let target = getNearestEnemy(this);
        let angle = 0;
        if (target) {
            angle = Math.atan2((target.y + target.h/2) - (this.y + this.h/2), (target.x + target.w/2) - (this.x + this.w/2));
        } else {
            angle = this.facing === 1 ? 0 : Math.PI;
        }
        
        // Spawn Projectile
        projectiles.push(new Projectile(
            this.x + this.w/2, 
            this.y + this.h/2, 
            Math.cos(angle) * 15, 
            Math.sin(angle) * 15, 
            this.color
        ));
    }
    
    draw(camX) {
        super.draw(camX);
        // Simple Eye
        ctx.fillStyle = 'white';
        let eyeX = this.facing === 1 ? this.x + 20 : this.x + 4;
        ctx.fillRect(eyeX - camX, this.y + 10, 8, 8);
        
        if (this.charging) {
            ctx.strokeStyle = 'white';
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.arc(this.x + this.w/2 - camX, this.y + this.h/2, 40, 0, Math.PI * 2);
            ctx.stroke();
        }
    }
}

class Enemy extends Entity {
    constructor(x) {
        super(x, 300, 40, 40, '#a33');
        this.timer = 0;
    }
    
    update() {
        if (this.hp <= 0) return;
        super.update();
        
        // Simple AI
        this.timer++;
        if (this.timer % 100 < 50) this.vx = 0.5;
        else this.vx = -0.5;
        
        // Damage Player
        if (checkRectCollide(this, player)) {
             player.hp -= 1;
             player.vx += (this.x > player.x ? -5 : 5);
             shakeScreen(5);
        }
    }
}

class Projectile {
    constructor(x, y, vx, vy, color) {
        this.x = x; this.y = y; this.vx = vx; this.vy = vy;
        this.color = color;
        this.w = 10; this.h = 10;
        this.life = 60;
    }
    update() {
        this.x += this.vx;
        this.y += this.vy;
        this.life--;
        spawnParticles(this.x, this.y, this.color, 1, 0.5);
    }
    draw(camX) {
        ctx.fillStyle = this.color;
        ctx.beginPath();
        ctx.arc(this.x - camX, this.y, 8, 0, Math.PI * 2);
        ctx.fill();
        // Glow
        ctx.shadowBlur = 10;
        ctx.shadowColor = this.color;
        ctx.fill();
        ctx.shadowBlur = 0;
    }
}

class Particle {
    constructor(x, y, color, speed) {
        this.x = x; this.y = y;
        this.vx = (Math.random() - 0.5) * speed * 5;
        this.vy = (Math.random() - 0.5) * speed * 5;
        this.color = color;
        this.life = 30 + Math.random() * 20;
        this.size = Math.random() * 4 + 2;
    }
    update() {
        this.x += this.vx;
        this.y += this.vy;
        this.life--;
        this.size *= 0.95;
    }
    draw(camX) {
        ctx.fillStyle = this.color;
        ctx.globalAlpha = this.life / 50;
        ctx.fillRect(this.x - camX, this.y, this.size, this.size);
        ctx.globalAlpha = 1;
    }
}

// Helpers
function getNearestEnemy(p) {
    let nearest = null;
    let minDist = 600; // range
    for (let e of enemies) {
        let dist = Math.hypot(e.x - p.x, e.y - p.y);
        if (dist < minDist) {
            minDist = dist;
            nearest = e;
        }
    }
    return nearest;
}

function checkRectCollide(r1, r2) {
    return (r1.x < r2.x + r2.w && r1.x + r1.w > r2.x &&
            r1.y < r2.y + r2.h && r1.y + r1.h > r2.y);
}

function spawnParticles(x, y, color, count, speed=1) {
    for(let i=0; i<count; i++) particles.push(new Particle(x, y, color, speed));
}

let shake = 0;
function shakeScreen(amount) { shake = amount; }

// Core Loops
function initGame(clsKey) {
    player = new Player(clsKey);
    enemies = [];
    particles = [];
    projectiles = [];
    
    // Spawn random enemies
    for(let i=0; i<10; i++) {
        enemies.push(new Enemy(600 + i * 400));
    }
    
    document.getElementById('menu-screen').classList.add('hidden');
    document.getElementById('char-select').classList.add('hidden');
    document.getElementById('ui-layer').classList.remove('hidden');
    
    gameState = 'PLAY';
    loop();
}

function update() {
    if (gameState !== 'PLAY') return;
    
    player.update();
    
    // Camera follow
    camera.x += (player.x - 300 - camera.x) * 0.1;
    
    // update entities
    enemies = enemies.filter(e => e.hp > 0);
    enemies.forEach(e => e.update());
    
    projectiles = projectiles.filter(p => p.life > 0);
    projectiles.forEach(p => {
        p.update();
        // Collision with enemies
        for (let e of enemies) {
            if (checkRectCollide(p, e)) {
                e.hp -= 20;
                p.life = 0;
                spawnParticles(e.x + e.w/2, e.y + e.h/2, '#fff', 10);
                shakeScreen(2);
                break;
            }
        }
    });
    
    particles = particles.filter(p => p.life > 0);
    particles.forEach(p => p.update());
    
    if (player.hp <= 0) {
        // Game Over logic
        gameState = 'GAMEOVER';
        alert("GAME OVER - You died!");
        location.reload();
    }
}

function draw() {
    // Clear
    ctx.fillStyle = '#111';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    // Parallax Background
    // Sky
    let grad = ctx.createLinearGradient(0, 0, 0, canvas.height);
    grad.addColorStop(0, '#000');
    grad.addColorStop(1, '#224');
    ctx.fillStyle = grad;
    ctx.fillRect(0,0, canvas.width, canvas.height);
    
    // Stars
    ctx.fillStyle = '#fff';
    for(let i=0; i<100; i++) {
        ctx.fillRect(((i*67) - camera.x * 0.1) % canvas.width, (i * 43) % 400, 2, 2);
    }
    
    // Shake
    let sx = 0, sy = 0;
    if (shake > 0) {
        sx = (Math.random() - 0.5) * shake;
        sy = (Math.random() - 0.5) * shake;
        shake *= 0.9;
        if(shake < 0.5) shake = 0;
    }
    
    ctx.save();
    ctx.translate(-camera.x + sx, sy);
    
    // Floor
    ctx.fillStyle = '#444';
    ctx.fillRect(0, 400, 10000, 500);
    
    // Draw Game Objects
    enemies.forEach(e => e.draw(0)); // 0 because we already translated context
    player.draw(0);
    projectiles.forEach(p => p.draw(0));
    particles.forEach(p => p.draw(0));
    
    ctx.restore();
}

function loop(timestamp) {
    if (gameState === 'PLAY') {
         update();
         draw();
         requestAnimationFrame(loop);
    }
}

// Menu Functions
function openCharSelect() {
    document.getElementById('menu-screen').classList.add('hidden');
    document.getElementById('char-select').classList.remove('hidden');
    
    const grid = document.getElementById('char-grid');
    grid.innerHTML = '';
    
    for (let k in CLASSES) {
        let cls = CLASSES[k];
        let el = document.createElement('div');
        el.className = 'char-card';
        el.innerHTML = `
            <div class="char-icon" style="background:${cls.color}"></div>
            <h3>${cls.name}</h3>
            <p style="font-size:10px; color:#aaa">Skill: ${cls.skill}</p>
        `;
        el.onclick = () => initGame(k);
        grid.appendChild(el);
    }
}

function backToMenu() {
    document.getElementById('char-select').classList.add('hidden');
    document.getElementById('menu-screen').classList.remove('hidden');
}

</script>

</body>
</html>
"""


if __name__ == "__main__":
    app.run(port=5007, debug=True)
