from flask import Flask, render_template_string, request, jsonify, session, url_for
import json
import uuid
import os

# === הוספנו את הספריה של OpenAI ===
try:
    from openai import OpenAI
    HAS_OPENAI_LIB = True
except ImportError:
    HAS_OPENAI_LIB = False
    print("Error: Please run 'pip install openai' in terminal")

app = Flask(__name__)
app.secret_key = 'shadow_maze_secret_key'

# ==========================================
# 🛑 כאן מדביקים את המפתח שלך 🛑
# ==========================================
MY_OPENAI_KEY = "sk-..."  # <--- תמחוק את זה ותדביק את המפתח הארוך שלך כאן במרכאות

# הגדרת הלקוח
client = None
if HAS_OPENAI_LIB and "sk-" in MY_OPENAI_KEY:
    try:
        client = OpenAI(api_key=MY_OPENAI_KEY)
        print(">> OpenAI Client Connected successfully.")
    except Exception as e:
        print(f">> Error connecting to OpenAI: {e}")

# --- נתוני עולם (נשאר זהה - ודא שלא מחקת את WORLD_DATA הקודם) ---
GAME_DATA = {
    "start_room": "cell",
    "rooms": {
        "cell": {
            "name": "תא כלא עזוב",
            "desc": "אתה כלוא בתא אבן לח. טיפות מים נופלות מהתקרה. הדלת נעולה.",
            "exits": {"out": "corridor"}, # נעול
            "items": ["rusted_spoon"],
            "interactables": {
                "door": {"desc": "דלת ברזל חזקה. היא נעולה.", "locked": True, "key_needed": "bone_key"}
            }
        },
        "corridor": {
            "name": "המסדרון הארוך",
            "desc": "המסדרון חשוך ומלא קורי עכביש. יש כאן ריח של ריקבון.",
            "exits": {"cell": "cell", "north": "armory"},
            "items": [],
            "enemies": ["skeleton"]
        },
        "armory": {
            "name": "חדר הנשק",
            "desc": "חדר מבולגן. רוב הנשקים חלודים.",
            "exits": {"south": "corridor"},
            "items": ["old_sword", "bone_key"]
        }
    },
    "items": {
        "rusted_spoon": {"name": "כף חלודה", "desc": "אפשר לחפור איתה קצת, או לאכול מרק."},
        "old_sword": {"name": "חרב ישנה", "desc": "עדיין חדה מספיק כדי לחתוך."},
        "bone_key": {"name": "מפתח עצם", "desc": "מפתח מגולף מעצם לבנה. נראה שהוא פותח משהו..."}
    },
    "enemies": {
        "skeleton": {"name": "שלד מהלך", "hp": 15, "desc": "שרידים של שומר קדום."}
    }
}

# ==========================================
# מנוע חכם עם AI
# ==========================================
class GameEngine:
    def __init__(self, state=None):
        if state:
            self.state = state
        else:
            self.state = {
                "loc": "cell",
                "inv": [],
                "hp": 30,
                "log": [{"text": "התעוררת... המקום חשוך. (המערכת מחוברת לבינה מלאכותית)", "type": "game"}],
                "flags": {}
            }

    def add_msg(self, text, type="game"):
        self.state["log"].append({"text": text, "type": type})

    def get_room(self):
        return GAME_DATA["rooms"][self.state["loc"]]

    def process_input(self, user_input):
        cmd_parts = user_input.strip().lower().split()
        if not cmd_parts: return self.state

        action = cmd_parts[0]
        # זיהוי פקודות בסיסיות (כדי שהמשחק יהיה מהיר)
        commands = {
            "go": self._go, "לך": self._go,
            "take": self._take, "קח": self._take,
            "look": self._look, "הסתכל": self._look, "ראה": self._look,
            "inv": self._inv, "i": self._inv, "תיק": self._inv,
            "use": self._use, "השתמש": self._use,
            "attack": self._attack, "תקוף": self._attack,
            "help": self._help, "עזרה": self._help
        }

        if action in commands:
            arg = cmd_parts[1] if len(cmd_parts) > 1 else None
            commands[action](arg)
        else:
            # 💡 כאן ה-AI נכנס לפעולה!
            response = self.ask_ai_guide(user_input)
            self.add_msg(response, "ai")
        
        return self.state

    # --- פונקציות בסיסיות (העתק-הדבק מהקוד הקודם, אני אשים פה גרסה מקוצרת כדי לא לחרוג) ---
    def _look(self, arg):
        r = self.get_room()
        # תיאור טקסטואלי לקוני למערכת הלוגים
        self.add_msg(f"אתה נמצא ב{r['name']}. {r['desc']}", "game")
        # בפועל, ב-CSS אנחנו מציגים את השם למעלה
        if r["items"]: self.add_msg("חפצים על הרצפה: " + ", ".join(r["items"]), "game info")
    
    def _inv(self, arg):
        self.add_msg(f"מלאי: {self.state['inv']}", "game info")
        
    def _go(self, d): 
        # לוגיקה מקוצרת להדגמה - תוודא שהעתקת את המלאה מקודם אם תרצה חסימות
        room = self.get_room()
        direction_map = {"קדימה": "north", "אחורה": "south", "יציאה": "out"}
        d = direction_map.get(d, d)
        if d in room["exits"]:
            self.state["loc"] = room["exits"][d]
            self.add_msg(f"עברת ל-{d}", "game success")
            self._look(None)
        else:
            self.add_msg("אין דרך לשם.", "game warning")
            
    def _take(self, item): self.add_msg(f"ניסית לקחת {item}...", "game")
    def _use(self, item): self.add_msg(f"מנסה להשתמש ב-{item}...", "game")
    def _attack(self, item): self.add_msg(f"תקפת!", "game")
    def _help(self, arg): self.add_msg("פקודות: לך, קח, הסתכל, השתמש...", "game")

    # ===============================================
    # 🧠 המוח האמיתי: החיבור ל-OpenAI 🧠
    # ===============================================
    def ask_ai_guide(self, question):
        if not client:
            return "חיבור ה-AI לא הוגדר (בדוק את המפתח בקוד)."

        # אנחנו מכינים ל-AI את כל ההקשר של המשחק כדי שיענה כמו מדריך
        current_room_data = self.get_room()
        inventory_list = self.state['inv'] if self.state['inv'] else "כלום"
        
        prompt = f"""
        אתה "מדריך המבוך" (Dungeon Master) במשחק הרפתקאות טקסטואלי אפל.
        השחקן שואל: "{question}"
        
        המצב הנוכחי:
        - מיקום: {current_room_data['name']}
        - תיאור חדר: {current_room_data['desc']}
        - חפצים בחדר: {current_room_data.get('items', [])}
        - חפצים בידי השחקן: {inventory_list}
        
        הוראות:
        1. ענה בעברית, בטון מסתורי אבל עוזר.
        2. תהיה קצר (עד 20 מילים).
        3. אל תיתן הוראות טכניות (כמו "לחץ על כפתור"), אלא סיפוריות.
        4. אם הוא שואל מה לעשות, תן לו רמז עדין על סמך החפצים שיש או אין לו.
        """

        try:
            completion = client.chat.completions.create(
                model="gpt-3.5-turbo", # או gpt-4 אם יש לך גישה ותקציב
                messages=[
                    {"role": "system", "content": prompt}
                ]
            )
            return "המדריך: " + completion.choices[0].message.content
        except Exception as e:
            return f"תקלת AI: {str(e)}"

# --- Routes וכל השאר נשאר זהה למה ששלחתי ב-App6 קודם ---    def add_msg(self, text, type="game"):
        self.state["log"].append({"text": text, "type": type})

    def get_room(self):
        return GAME_DATA["rooms"][self.state["loc"]]

    # המוח שמחליט: האם זו פקודה או שאלה?
    def process_input(self, user_input):
        cmd_parts = user_input.strip().lower().split()
        if not cmd_parts: return self.state

        action = cmd_parts[0]
        # מילון מילים נרדפות לפקודות
        commands = {
            "go": self._go, "לך": self._go, "move": self._go,
            "take": self._take, "קח": self._take, "get": self._take, "הרם": self._take,
            "look": self._look, "הסתכל": self._look, "ראה": self._look, "s": self._look,
            "inv": self._inv, "i": self._inv, "תיק": self._inv, "חפצים": self._inv,
            "use": self._use, "השתמש": self._use,
            "attack": self._attack, "תקוף": self._attack, "kill": self._attack,
            "help": self._help, "עזרה": self._help, "h": self._help, "?": self._help
        }

        # 1. ניסיון לבצע פקודת משחק
        if action in commands:
            arg = cmd_parts[1] if len(cmd_parts) > 1 else None
            commands[action](arg)
        else:
            # 2. אם לא זוהתה פקודה - הפנייה לבינה מלאכותית (או חיקוי)
            response = self.ask_ai_guide(user_input)
            self.add_msg(response, "ai")
        
        return self.state

    # --- פונקציות המשחק ---
    
    def _help(self, arg):
        commands_list = """
        <br><b>פקודות בסיסיות:</b><br>
        - <b>הסתכל</b>: מתאר את החדר שוב.<br>
        - <b>לך [כיוון]</b>: מעבר חדר (צפון/דרום/יציאה).<br>
        - <b>קח [חפץ]</b>: איסוף פריט (למשל: 'קח כף').<br>
        - <b>תיק</b>: מה יש לי בכיס?<br>
        - <b>השתמש ב[חפץ]</b>: פתיחת דלתות ופתרון חידות.<br>
        - <b>שאלה חופשית</b>: כתוב כל דבר אחר כדי לדבר עם המדריך.
        """
        self.add_msg(commands_list, "game info")

    def _go(self, direction):
        room = self.get_room()
        # מיפוי קצר של כיוונים בעברית
        direction_map = {"קדימה": "north", "אחורה": "south", "יציאה": "out", "החוצה": "out"}
        clean_dir = direction_map.get(direction, direction)
        
        # טיפול בדלת נעולה (ייחודי למשחק הזה)
        if self.state["loc"] == "cell" and (clean_dir == "out" or direction == "דלת"):
            if "door" in room["interactables"] and room["interactables"]["door"]["locked"]:
                self.add_msg("הדלת נעולה. נסה למצוא דרך לפתוח אותה.", "game warning")
                return

        if clean_dir in room["exits"]:
            self.state["loc"] = room["exits"][clean_dir]
            self.add_msg(f"זזת ל-{clean_dir}.", "game")
            self._look(None)
        else:
            self.add_msg("אי אפשר ללכת לשם.", "game warning")

    def _look(self, arg):
        r = self.get_room()
        desc = r["desc"] + "<br>"
        
        # בדיקת חפצים
        items_here = [i for i in r["items"] if i not in self.state["flags"]]
        if items_here:
            names = [GAME_DATA["items"][i]["name"] for i in items_here]
            desc += f"<span style='color:yellow'>חפצים בולטים: {', '.join(names)}</span><br>"
        
        exits = r["exits"].keys()
        desc += f"יציאות: {', '.join(exits)}"
        
        self.add_msg(desc, "game")

    def _take(self, item_name):
        room = self.get_room()
        # מיפוי פשוט לשם הזיהוי
        mapping = {"כף": "rusted_spoon", "חרב": "old_sword", "מפתח": "bone_key"}
        target_id = mapping.get(item_name, item_name)
        
        # לוגיקה פשוטה להדגמה (בלי Persistent removal אמיתי ב-DB)
        if target_id in room["items"]:
            self.state["inv"].append(target_id)
            room["items"].remove(target_id) 
            self.add_msg(f"לקחת את ה{GAME_DATA['items'][target_id]['name']}.", "game success")
        else:
            self.add_msg("אין כאן דבר כזה.", "game warning")

    def _inv(self, arg):
        if not self.state["inv"]:
            self.add_msg("התיק שלך ריק.", "game")
        else:
            names = [GAME_DATA["items"][i]["name"] for i in self.state["inv"]]
            self.add_msg(f"בתיק שלך: {', '.join(names)}", "game info")

    def _use(self, arg):
        if "מפתח" in str(arg) and "bone_key" in self.state["inv"]:
            if self.state["loc"] == "cell":
                 GAME_DATA["rooms"]["cell"]["interactables"]["door"]["locked"] = False
                 GAME_DATA["rooms"]["cell"]["exits"]["out"] = "corridor" # פתיחת הנתיב
                 self.add_msg("סובבת את מפתח העצם... קנאק! הדלת נפתחה.", "game success")
            else:
                 self.add_msg("אין פה מה לפתוח עם המפתח.", "game")
        else:
            self.add_msg("זה לא עשה כלום.", "game")

    def _attack(self, arg):
         self.add_msg("ניסית לתקוף את האוויר בדרמטיות.", "game")

    # --- מנוע ה-AI / Chatbot ---
    
    def ask_ai_guide(self, question):
        """
        פונקציה שמדמה (או מבצעת) אינטראקציה עם מדריך מבוסס בינה
        """
        context_room = GAME_DATA["rooms"][self.state["loc"]]["name"]
        
        # אופציה א': בינה מלאכותית מדומה (לשימוש מיידי)
        # זה מנתח מילים בשאלה שלך ונותן תשובה מתאימה להקשר
        if not USE_REAL_AI:
            q = question.lower()
            if "איפה" in q or "מקום" in q:
                return f"המדריך: כרגע אתה נמצא ב{context_room}. נסה להביט סביב."
            elif "מפתח" in q:
                return "המדריך: דלתות נעולות דורשות מפתחות. אולי באזור הנשקייה?"
            elif "לצאת" in q or "לברוח" in q:
                return "המדריך: נסה למצוא את היציאה או לפתוח את הדלת הדרומית."
            elif "חרב" in q or "להרוג" in q:
                return "המדריך: כדי לשרוד את המבוך, תצטרך להגן על עצמך. חפש נשק."
            elif "סיפור" in q or "עלילה" in q:
                return "המדריך: האגדה מספרת שהכלא הזה נבנה על ידי המלך המטורף. איש לא ברח מכאן."
            elif "תודה" in q:
                return "המדריך: בשמחה. אל תמות."
            else:
                return f"המדריך: זו שאלה מעניינת ({question}), אבל אני מציע שתתמקד בחפצים שבחדר."

        # אופציה ב': שימוש אמיתי ב-OpenAI (דורש התקנת ספרית openai וקוד פעיל)
        else:
            try:
                # import openai
                # openai.api_key = OPENAI_API_KEY
                # response = openai.ChatCompletion.create(...)
                # return response['choices'][0]['message']['content']
                pass
            except:
                return "שגיאת חיבור ל-AI."


# ==========================================
# שרת וניתובים (Flask)
# ==========================================

@app.route("/")
def index():
    if "uid" not in session: session["uid"] = str(uuid.uuid4())
    api_url = url_for('api_command')
    reset_url = url_for('api_reset')
    return render_template_string(CHAT_HTML, api_url=api_url, reset_url=reset_url)

@app.route("/api/command", methods=["POST"])
def api_command():
    data = request.get_json(silent=True) or {}
    user_txt = data.get("command")
    
    state = session.get("game_state", None)
    engine = GameEngine(state)
    
    # אם המשתמש כתב משהו, נעבד. אחרת זה רק רענון
    if user_txt:
        engine.add_msg(user_txt, "user") # להוסיף את מה שכתבת ללוג
        engine.process_input(user_txt)
    
    session["game_state"] = engine.state
    
    # סינון: מחזירים רק הודעות חדשות אם היינו רוצים להיות יעילים יותר
    # כאן מחזירים הכל לרינדור קל
    return jsonify({
        "log": engine.state["log"],
        "loc_name": GAME_DATA["rooms"][engine.state["loc"]]["name"]
    })

@app.route("/api/reset", methods=["POST"])
def api_reset():
    session.clear()
    return jsonify({"status": "ok"})


# ==========================================
# הממשק המעוצב (Chat UI + Side Menu)
# ==========================================

CHAT_HTML = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>הרפתקה עם מדריך</title>
    <style>
        :root {
            --bg: #1e1e24;
            --sidebar: #15151a;
            --chat-bg: #2b2b30;
            --user-msg: #00cec9;
            --game-msg: #dfe6e9;
            --ai-msg: #6c5ce7; 
            --input-bg: #111;
        }
        * { box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', sans-serif; 
            background: var(--bg); 
            color: white; 
            margin: 0; display: flex; height: 100vh; overflow: hidden;
        }
        
        /* Sidebar - פקודות בצד */
        .sidebar {
            width: 250px;
            background: var(--sidebar);
            border-left: 1px solid #333;
            padding: 20px;
            display: flex; 
            flex-direction: column;
            gap: 10px;
        }
        .sidebar h2 { color: #81ecec; margin-top: 0; font-size:1.2rem; }
        .cmd-btn {
            background: #333;
            border: 1px solid #444;
            color: #ccc;
            padding: 10px;
            text-align: right;
            cursor: pointer;
            border-radius: 5px;
            transition: 0.2s;
        }
        .cmd-btn:hover { background: #444; color: white; border-color: #666; }
        
        /* Chat Area */
        .chat-container {
            flex-grow: 1;
            display: flex;
            flex-direction: column;
            max-width: 900px;
            margin: 0 auto;
            background: #111; /* כהה יותר */
        }
        
        header { 
            padding: 15px; 
            border-bottom: 1px solid #333; 
            display: flex; justify-content: space-between; align-items: center;
        }
        
        .messages {
            flex-grow: 1;
            padding: 20px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }
        
        /* בועות צ'אט */
        .msg {
            max-width: 80%;
            padding: 10px 15px;
            border-radius: 10px;
            line-height: 1.5;
            animation: popIn 0.2s ease-out;
            position: relative;
        }
        
        /* הודעת משתמש */
        .msg.user {
            align-self: flex-start; /* צד ימין בעברית RTL */
            background: var(--user-msg);
            color: #000;
            border-bottom-right-radius: 2px;
        }
        
        /* הודעת משחק */
        .msg.game {
            align-self: flex-end; /* צד שמאל */
            background: #444;
            color: #eee;
            border-bottom-left-radius: 2px;
            border: 1px solid #555;
        }
        
        /* הודעת AI / מדריך */
        .msg.ai {
            align-self: flex-end;
            background: linear-gradient(135deg, #6c5ce7, #a29bfe);
            color: white;
            border: 1px solid #555;
            box-shadow: 0 0 10px rgba(108, 92, 231, 0.3);
        }
        .msg.ai::before {
            content: "🤖";
            position: absolute;
            top: -15px; right: -10px; font-size: 20px;
        }
        .msg.info { color: #00d4ff; border-color: #00d4ff; background: transparent;}

        .msg.warning { border-left: 3px solid orange; }
        .msg.success { border-left: 3px solid lime; }
        
        .input-area {
            padding: 20px;
            border-top: 1px solid #333;
            display: flex; gap: 10px;
        }
        
        input {
            flex-grow: 1;
            padding: 15px;
            border-radius: 25px;
            border: none;
            background: #222;
            color: white;
            font-size: 1rem;
            outline: none;
        }
        input:focus { background: #2a2a2a; }
        
        button.send-btn {
            border-radius: 50%; width: 50px; height: 50px;
            background: var(--user-msg); border:none; cursor: pointer;
            font-weight: bold; font-size: 1.2rem;
        }

        @keyframes popIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        /* Responsive */
        @media (max-width: 600px) {
            .sidebar { display: none; } /* במובייל מחביאים את התפריט */
        }
    </style>
</head>
<body>

    <div class="sidebar">
        <h2>פקודות נפוצות</h2>
        <div class="cmd-btn" onclick="injectCmd('הסתכל')">👁️ הסתכל סביב</div>
        <div class="cmd-btn" onclick="injectCmd('תיק')">🎒 בדיקת מלאי</div>
        <div class="cmd-btn" onclick="injectCmd('השתמש במפתח')">🔑 השתמש במפתח</div>
        <div class="cmd-btn" onclick="injectCmd('עזרה')">❓ עזרה</div>
        <div class="cmd-btn" onclick="doReset()" style="margin-top:auto; color:indianred; border-color:indianred;">🔄 אפס משחק</div>
        
        <hr style="border-color:#333; width:100%">
        <small style="color:#777">טיפ: נסה לשאול שאלות כמו "איפה אני?" או "מה הסיפור פה?"</small>
    </div>

    <div class="chat-container">
        <header>
            <h3 id="room-name">טוען...</h3>
            <a href="/" style="color:#666; text-decoration:none;">תפריט ראשי</a>
        </header>

        <div class="messages" id="chat-box">
            <!-- הודעות יטענו כאן -->
        </div>

        <div class="input-area">
            <input type="text" id="user-input" placeholder="כתוב פעולה (קח, לך) או שאל את המדריך..." autofocus onkeydown="if(event.key==='Enter') send()">
            <button class="send-btn" onclick="send()">➤</button>
        </div>
    </div>

    <script>
        const API_URL = "{{ api_url }}";
        const RESET_URL = "{{ reset_url }}";
        
        function injectCmd(cmd) {
            document.getElementById('user-input').value = cmd;
            send();
        }

        async function send() {
            const inp = document.getElementById('user-input');
            const txt = inp.value;
            inp.value = ''; // ניקוי מיד כדי להרגיש מהיר
            
            // עדכון אופטימי - הוסף הודעה מיד למסך
            if(txt) addBubble(txt, 'user');

            // בקשה לשרת
            const res = await fetch(API_URL, {
                method: 'POST', 
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({command: txt})
            });
            const data = await res.json();
            
            // מחיקת כל ההודעות וציור מחדש (הדרך הבטוחה לסנכרון)
            // לגרסה מתקדמת יותר אפשר להוסיף רק את החדשות, אבל זה מספיק לכרגע
            const box = document.getElementById('chat-box');
            box.innerHTML = '';
            
            data.log.forEach(entry => {
                addBubble(entry.text, entry.type);
            });
            
            document.getElementById('room-name').innerText = data.loc_name;
        }

        function addBubble(text, type) {
            const box = document.getElementById('chat-box');
            const div = document.createElement('div');
            
            // טיפול בקלאסים כדי שה-CSS יעבוד נכון (split במידה ויש כמה סוגים)
            div.className = 'msg ' + type;
            div.innerHTML = text; // מאפשר HTML בפנים
            
            box.appendChild(div);
            box.scrollTop = box.scrollHeight;
        }

        async function doReset() {
            await fetch(RESET_URL, {method: 'POST'});
            location.reload();
        }

        // טעינה ראשונית
        send();
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(port=5006, debug=True)
