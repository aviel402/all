"""
================================================================================
   ARCADE STATION - ENTERPRISE EDITION v9.0.1
   CODENAME: LEVIATHAN
================================================================================

   AUTHOR:      System Architect
   DATE:        2024
   LICENSE:     PROPRIETARY / INTERNAL USE ONLY
   DESCRIPTION: A scalable, modular, robust, thread-safe, distinct-service
                oriented architecture for hosting arcade micro-frontends.

   ARCHITECTURAL LAYERS:
   1. CORE INFRASTRUCTURE (Logging, Config, Signals)
   2. DATA ABSTRACTION LAYER (Mock ORM)
   3. SERVICE LAYER (Game Logic, Asset Management)
   4. PRESENTATION LAYER (Flask Controllers, Jinja2 Templates)
   5. GATEWAY INTERFACE (WSGI Dispatcher)

================================================================================
"""

import os
import sys
import time
import json
import uuid
import random
import signal
import logging
import threading
import datetime
import functools
import dataclasses
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Callable, Tuple

# --- Third Party Imports ---
try:
    from werkzeug.middleware.dispatcher import DispatcherMiddleware
    from werkzeug.serving import run_simple
    from werkzeug.wrappers import Request, Response
    from flask import Flask, render_template_string, redirect, url_for, request, jsonify, make_response, session
except ImportError as e:
    print(f"CRITICAL SYSTEM FAILURE: MISSING DEPENDENCY -> {e}")
    sys.exit(1)

# ==============================================================================
# SECTION 1: CORE INFRASTRUCTURE & CONFIGURATION
# ==============================================================================

class SystemConfig:
    """Singleton Configuration Manager ensuring immutable system constants."""
    _instance = None
    
    ENV = "PRODUCTION"
    DEBUG = True
    SECRET_KEY = os.urandom(32).hex()
    HOST = '0.0.0.0'
    PORT = 5000
    MAX_THREADS = 4
    LOG_LEVEL = logging.DEBUG
    APP_NAME = "Arcade Station Enterprise"
    VERSION = "9.0.1"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SystemConfig, cls).__new__(cls)
        return cls._instance

    @staticmethod
    def get_db_uri():
        return "sqlite:///:memory:"

class LoggerFactory:
    """Factory for creating structured loggers with context tracking."""
    
    @staticmethod
    def get_logger(name: str) -> logging.Logger:
        logger = logging.getLogger(name)
        logger.setLevel(SystemConfig.LOG_LEVEL)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '[%(asctime)s] [%(name)s] [%(levelname)s] - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger

sys_logger = LoggerFactory.get_logger("SystemCore")

# ==============================================================================
# SECTION 2: UTILITIES & DECORATORS
# ==============================================================================

def measure_execution_time(func):
    """Decorator to measure telemetry of function execution."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        sys_logger.debug(f"Execution of {func.__name__} took {end_time - start_time:.4f}s")
        return result
    return wrapper

class ServiceLocator:
    """Registry for dependency injection across the platform."""
    _services = {}

    @classmethod
    def register(cls, name: str, service: Any):
        sys_logger.info(f"Registering Service: {name}")
        cls._services[name] = service

    @classmethod
    def get(cls, name: str) -> Any:
        return cls._services.get(name)

# ==============================================================================
# SECTION 3: ASSET MANAGEMENT & UI THEMES
# ==============================================================================

@dataclasses.dataclass
class ThemePalette:
    primary: str
    secondary: str
    accent: str
    background: str
    text: str
    font_family: str

class ThemeManager:
    """Manages dynamic CSS injection and theme swapping strategies."""
    
    DARK_CYBERPUNK = ThemePalette(
        primary="#6c7ce7",
        secondary="#a29bfe",
        accent="#00cec9",
        background="#0a0a0c",
        text="#dfe6e9",
        font_family="'Heebo', 'Roboto', sans-serif"
    )

    RETRO_WAVE = ThemePalette(
        primary="#ff00ff",
        secondary="#00ffff",
        accent="#ff9900",
        background="#2c003e",
        text="#ffffff",
        font_family="'Courier New', monospace"
    )

    @staticmethod
    def generate_css(theme: ThemePalette) -> str:
        return f"""
        :root {{
            --primary: {theme.primary};
            --secondary: {theme.secondary};
            --accent: {theme.accent};
            --bg-dark: {theme.background};
            --text-main: {theme.text};
            --font-main: {theme.font_family};
        }}
        body {{
            background-color: var(--bg-dark);
            color: var(--text-main);
            font-family: var(--font-main);
            margin: 0; padding: 0;
            transition: all 0.5s ease;
        }}
        """

# ==============================================================================
# SECTION 4: GAME ENGINE ABSTRACTION
# ==============================================================================

class IGameModule(ABC):
    """Interface for all pluggable game modules."""
    
    @abstractmethod
    def get_id(self) -> str: pass
    
    @abstractmethod
    def get_name(self) -> str: pass
    
    @abstractmethod
    def get_icon(self) -> str: pass
    
    @abstractmethod
    def render(self) -> str: pass

class SnakeGame(IGameModule):
    """Implementation of Classic Snake using HTML5 Canvas & JS Injection."""

    def get_id(self) -> str: return "snake_v1"
    def get_name(self) -> str: return "Python Snake Elite"
    def get_icon(self) -> str: return "🐍"

    def render(self) -> str:
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Snake Elite</title>
            <style>
                body { background: #111; color: #0f0; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; margin: 0; font-family: monospace; }
                canvas { border: 2px solid #0f0; box-shadow: 0 0 20px #0f0; }
                h1 { text-shadow: 0 0 10px #0f0; margin-bottom: 10px; }
                #score { font-size: 24px; margin-bottom: 20px; }
                .btn { padding: 10px 20px; background: #0f0; color: #000; border: none; cursor: pointer; font-weight: bold; margin-top: 20px; }
            </style>
        </head>
        <body>
            <h1>SNAKE ELITE</h1>
            <div id="score">Score: 0</div>
            <canvas id="gc" width="400" height="400"></canvas>
            <button class="btn" onclick="location.href='/'">EXIT TO LOBBY</button>
            <script>
                window.onload=function() {
                    canv=document.getElementById("gc");
                    ctx=canv.getContext("2d");
                    document.addEventListener("keydown",keyPush);
                    setInterval(game,1000/15);
                }
                px=py=10; gs=tc=20; ax=ay=15; xv=yv=0; trail=[]; tail = 5; score=0;
                function game() {
                    px+=xv; py+=yv;
                    if(px<0) { px= tc-1; }
                    if(px>tc-1) { px= 0; }
                    if(py<0) { py= tc-1; }
                    if(py>tc-1) { py= 0; }
                    ctx.fillStyle="black";
                    ctx.fillRect(0,0,canv.width,canv.height);
                    ctx.fillStyle="lime";
                    for(var i=0;i<trail.length;i++) {
                        ctx.fillRect(trail[i].x*gs,trail[i].y*gs,gs-2,gs-2);
                        if(trail[i].x==px && trail[i].y==py) {
                            if(tail > 5) { score = 0; document.getElementById("score").innerText = "Score: " + score; }
                            tail = 5;
                        }
                    }
                    trail.push({x:px,y:py});
                    while(trail.length>tail) {
                        trail.shift();
                    }
                    if(ax==px && ay==py) {
                        tail++;
                        score += 10;
                        document.getElementById("score").innerText = "Score: " + score;
                        ax=Math.floor(Math.random()*tc);
                        ay=Math.floor(Math.random()*tc);
                    }
                    ctx.fillStyle="red";
                    ctx.fillRect(ax*gs,ay*gs,gs-2,gs-2);
                }
                function keyPush(evt) {
                    switch(evt.keyCode) {
                        case 37: xv=-1;yv=0;break;
                        case 38: xv=0;yv=-1;break;
                        case 39: xv=1;yv=0;break;
                        case 40: xv=0;yv=1;break;
                    }
                }
            </script>
        </body>
        </html>
        """

class MatrixRain(IGameModule):
    """Implementation of Matrix Digital Rain."""

    def get_id(self) -> str: return "matrix_v1"
    def get_name(self) -> str: return "The Matrix Connect"
    def get_icon(self) -> str: return "💊"

    def render(self) -> str:
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { margin: 0; overflow: hidden; background: black; }
                canvas { display: block; }
                .overlay { position: absolute; top: 20px; left: 20px; color: #0F0; font-family: monospace; z-index: 100; font-size: 20px; background: rgba(0,0,0,0.7); padding: 10px; border: 1px solid #0F0; }
                a { color: white; text-decoration: none; font-weight: bold; }
            </style>
        </head>
        <body>
            <div class="overlay">SYSTEM BREACH DETECTED... <br><br> <a href="/">[ DISCONNECT ]</a></div>
            <canvas id="c"></canvas>
            <script>
                var c = document.getElementById("c");
                var ctx = c.getContext("2d");
                c.height = window.innerHeight;
                c.width = window.innerWidth;
                var matrix = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ123456789@#$%^&*()*&^%+-/~{[|`]}";
                matrix = matrix.split("");
                var font_size = 14;
                var columns = c.width/font_size; 
                var drops = [];
                for(var x = 0; x < columns; x++)
                    drops[x] = 1; 

                function draw() {
                    ctx.fillStyle = "rgba(0, 0, 0, 0.04)";
                    ctx.fillRect(0, 0, c.width, c.height);
                    ctx.fillStyle = "#0F0"; 
                    ctx.font = font_size + "px arial";
                    for(var i = 0; i < drops.length; i++) {
                        var text = matrix[Math.floor(Math.random()*matrix.length)];
                        ctx.fillText(text, i*font_size, drops[i]*font_size);
                        if(drops[i]*font_size > c.height && Math.random() > 0.975)
                            drops[i] = 0;
                        drops[i]++;
                    }
                }
                setInterval(draw, 35);
            </script>
        </body>
        </html>
        """

# ==============================================================================
# SECTION 5: APPLICATION FACTORY & ROUTING LOGIC
# ==============================================================================

class ArcadeAppFactory:
    """Builder pattern for constructing Flask micro-apps."""
    
    @staticmethod
    def create_game_app(game_module: IGameModule) -> Flask:
        app = Flask(game_module.get_id())
        
        # Security Headers Middleware (simulated)
        @app.after_request
        def add_security_headers(response):
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'SAMEORIGIN'
            return response

        @app.route('/')
        @measure_execution_time
        def index():
            sys_logger.info(f"User entered game: {game_module.get_name()}")
            return game_module.render()
            
        return app

    @staticmethod
    def create_main_app(games: List[IGameModule]) -> Flask:
        app = Flask("MainPortal")
        app.secret_key = SystemConfig.SECRET_KEY
        
        css = ThemeManager.generate_css(ThemeManager.DARK_CYBERPUNK)
        
        # --- HTML TEMPLATE GENERATION (DYNAMIC) ---
        def get_portal_html():
            game_cards = ""
            for g in games:
                game_cards += f"""
                <a href="/{g.get_id()}/" class="card">
                    <div class="emoji-icon">{g.get_icon()}</div>
                    <h2>{g.get_name()}</h2>
                    <div class="status-indicator">● ONLINE</div>
                </a>
                """
                
            return f"""
            <!DOCTYPE html>
            <html lang="he" dir="rtl">
            <head>
                <meta charset="UTF-8">
                <title>{SystemConfig.APP_NAME}</title>
                <link href="https://fonts.googleapis.com/css2?family=Heebo:wght@400;700;900&display=swap" rel="stylesheet">
                <style>
                    {css}
                    
                    /* Advanced CSS Grid & Animations */
                    .grid {{
                        display: grid;
                        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                        gap: 40px;
                        max-width: 1400px;
                        margin: 0 auto;
                        padding: 20px;
                    }}
                    
                    h1 {{
                        font-size: 4rem;
                        background: linear-gradient(90deg, #a29bfe, #74b9ff, #00cec9);
                        -webkit-background-clip: text;
                        -webkit-text-fill-color: transparent;
                        text-transform: uppercase;
                        letter-spacing: 3px;
                        margin-bottom: 5px;
                    }}
                    
                    .card {{
                        background: rgba(30, 30, 36, 0.8);
                        backdrop-filter: blur(10px);
                        border-radius: 24px;
                        padding: 40px;
                        text-decoration: none;
                        color: white;
                        border: 1px solid rgba(255,255,255,0.05);
                        position: relative;
                        overflow: hidden;
                        display: flex;
                        flex-direction: column;
                        align-items: center;
                    }}
                    
                    .card::before {{
                        content: '';
                        position: absolute;
                        top: 0; left: 0; width: 100%; height: 5px;
                        background: linear-gradient(90deg, var(--primary), var(--accent));
                        transform: scaleX(0);
                        transform-origin: left;
                        transition: transform 0.4s ease;
                    }}
                    
                    .card:hover::before {{ transform: scaleX(1); }}
                    .card:hover {{ transform: translateY(-10px); box-shadow: 0 20px 40px rgba(0,0,0,0.4); }}
                    
                    .emoji-icon {{ font-size: 64px; margin-bottom: 20px; animation: float 3s ease-in-out infinite; }}
                    
                    @keyframes float {{
                        0% {{ transform: translateY(0px); }}
                        50% {{ transform: translateY(-10px); }}
                        100% {{ transform: translateY(0px); }}
                    }}
                    
                    .status-indicator {{
                        margin-top: 15px;
                        font-size: 0.8rem;
                        color: #00b894;
                        font-weight: bold;
                        letter-spacing: 1px;
                    }}

                    .console-log {{
                        position: fixed;
                        bottom: 0; left: 0; right: 0;
                        background: rgba(0,0,0,0.9);
                        color: #0f0;
                        font-family: monospace;
                        padding: 10px;
                        font-size: 12px;
                        height: 30px;
                        overflow: hidden;
                        white-space: nowrap;
                        text-align: left;
                        direction: ltr;
                        border-top: 1px solid #333;
                    }}
                </style>
            </head>
            <body>
                <br><br>
                <h1>{SystemConfig.APP_NAME}</h1>
                <p style="color: #b2bec3; font-size: 1.5rem;">Secure Gaming Environment v{SystemConfig.VERSION}</p>
                
                <div class="grid">
                    {game_cards}
                    
                    <a href="/random/" class="card" style="border-color: var(--secondary);">
                        <div class="emoji-icon">🎲</div>
                        <h2>Random Protocol</h2>
                        <div class="status-indicator" style="color: #fdcb6e">● READY</div>
                    </a>
                </div>

                <footer>
                    <p>&copy; {datetime.datetime.now().year} Aviel Aluf Enterprises. Server Time: {datetime.datetime.now().isoformat()}</p>
                </footer>
                
                <div class="console-log" id="syslog">
                    [SYSTEM] Gateway Initialized. Waiting for input...
                </div>
            </body>
            </html>
            """

        @app.route('/')
        def portal_index():
            return render_template_string(get_portal_html())

        @app.route('/random/')
        def random_routing_logic():
            # Advanced random logic (mocking load balancing)
            target = random.choice(games)
            sys_logger.info(f"Routing user to random destination: {target.get_id()}")
            return redirect(f'/{target.get_id()}/')
            
        return app

# ==============================================================================
# SECTION 6: BACKGROUND SERVICES
# ==============================================================================

class HealthMonitor(threading.Thread):
    """Background daemon to monitor system resources."""
    
    def __init__(self):
        super().__init__()
        self.daemon = True
        self.running = True
        
    def run(self):
        sys_logger.info("Health Monitor Service Started")
        while self.running:
            # Simulate checking CPU/Memory
            # sys_logger.debug("System Health: OK | CPU: 12% | MEM: 450MB")
            time.sleep(30)
            
    def stop(self):
        self.running = False

# ==============================================================================
# SECTION 7: MAIN ENTRY POINT & DISPATCHER CONFIGURATION
# ==============================================================================

def boot_system():
    """Bootstraps the entire application ecosystem."""
    
    # 1. Initialize Services
    monitor = HealthMonitor()
    monitor.start()
    
    # 2. Register Games
    games_list = [
        SnakeGame(),
        MatrixRain()
    ]
    
    # 3. Build Micro-Frontends
    app_instances = {}
    for game in games_list:
        app_instances[f'/{game.get_id()}'] = ArcadeAppFactory.create_game_app(game)
    
    # 4. Build Main Portal
    main_portal = ArcadeAppFactory.create_main_app(games_list)
    
    # 5. Configure Dispatcher (The "Router")
    # This combines the main app with the sub-apps based on URL prefix
    master_application = DispatcherMiddleware(
        main_portal,
        app_instances
    )
    
    return master_application

# Global Application Instance for WSGI Servers (Gunicorn/uWSGI)
application = boot_system()

if __name__ == "__main__":
    banner = f"""
    ██████╗ ██╗███████╗██████╗  █████╗ ████████╗██╗  ██╗███████╗██████╗ 
    ██╔══██╗██║██╔════╝██╔══██╗██╔══██╗╚══██╔══╝██║  ██║██╔════╝██╔══██╗
    ██║  ██║██║███████╗██████╔╝███████║   ██║   ███████║█████╗  ██████╔╝
    ██║  ██║██║╚════██║██╔═══╝ ██╔══██║   ██║   ██╔══██║██╔══╝  ██╔══██╗
    ██████╔╝██║███████║██║     ██║  ██║   ██║   ██║  ██║███████╗██║  ██║
    ╚═════╝ ╚═╝╚══════╝╚═╝     ╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝
    
    >> SYSTEM ONLINE
    >> LISTENING ON PORT {SystemConfig.PORT}
    >> MODE: {SystemConfig.ENV}
    """
    print(banner)
    
    # Using run_simple to simulate a production-like serving environment locally
    # threaded=True simulates handling multiple concurrent users
    run_simple(
        SystemConfig.HOST, 
        SystemConfig.PORT, 
        application, 
        use_reloader=True, 
        use_debugger=SystemConfig.DEBUG,
        threaded=True
    )
