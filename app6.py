from flask import Flask, render_template_string, request, jsonify, session, url_for
import json
import uuid

# ==========================================
# 💎 הגדרת Google Gemini (תיקון גרסאות) 💎
# ==========================================

MY_GOOGLE_KEY = "AIzaSyDOXGXKRgzSVtiE-lSFe8V8daIzH83OdI4" # <-- וודא שהמפתח שלך כאן
model_name = "models/gemini-3-pro-preview"

GEMINI_AVAILABLE = False
try:
    import google.generativeai as genai
    
    # חיבור המפתח
    genai.configure(api_key=MY_GOOGLE_KEY)
    
    # --- התיקון כאן ---
    # במקום gemini-pro, אנחנו משתמשים בגרסה המעודכנת:
    
    model = genai.GenerativeModel(model_name)
    GEMINI_AVAILABLE = True
    print(f">> מחובר בהצלחה למודל: {model_name}")

except Exception as e:
    print(f"❌ שגיאה בחיבור ל-Gemini: {e}")
    # אם יש שגיאה, נדפיס לרשימת המודלים הפנויים כדי שנדע מה לבחור
    try:
        import google.generativeai as genai
        genai.configure(api_key=MY_GOOGLE_KEY)
        print("המודלים הזמינים עבורך הם:")
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"- {m.name}")
    except:
        pass

app = Flask(__name__)
app.secret_key = 'shadow_maze_secret_key'

# --- נתוני עולם (WORLD DATA) ---
GAME_DATA = {
    "start_room": "cell",
    "rooms": {
        "cell": {
            "name": "תא כלא עזוב",
            "desc": "אתה כלוא בתא אבן לח. טיפות מים נופלות מהתקרה. הדלת נעולה.",
            "exits": {"out": "corridor"}, # בפועל נעול ע"י ה-door
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
# לוגיקה חכמה (Engine)
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
                "log": [{"text": "התעוררת... (המדריך של גוגל מחובר)", "type": "game"}],
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
        commands = {
            "go": self._go, "לך": self._go, 
            "take": self._take, "קח": self._take,
            "look": self._look, "הסתכל": self._look,
            "inv": self._inv, "i": self._inv, "תיק": self._inv,
            "use": self._use, "השתמש": self._use,
            "help": self._help, "עזרה": self._help
        }

        # אם זו פקודה טכנית - בצע אותה. אחרת - שלח לג'מיני
        if action in commands:
            arg = cmd_parts[1] if len(cmd_parts) > 1 else None
            commands[action](arg)
        else:
            # 💡 קריאה ל-Gemini
            self.add_msg(user_input, "user") # להוסיף את שאלת המשתמש ללוג לפני התשובה (אם עוד לא הוספה)
            response = self.ask_gemini_guide(user_input)
            self.add_msg(response, "ai")
        
        return self.state

    # --- פונקציות משחק ---
    
    def _help(self, arg):
        self.add_msg("פקודות: לך [כיוון], קח [חפץ], הסתכל, תיק, השתמש ב[חפץ]. או שאל אותי שאלה חופשית.", "game info")

    def _go(self, d):
        r = self.get_room()
        direction_map = {"קדימה": "north", "אחורה": "south", "יציאה": "out"}
        d = direction_map.get(d, d)
        
        # טיפול בדלת נעולה
        if self.state["loc"] == "cell" and d == "out":
            door = r["interactables"]["door"]
            if door["locked"]:
                self.add_msg("הדלת נעולה. תצטרך מפתח.", "game warning")
                return

        if d in r["exits"]:
            self.state["loc"] = r["exits"][d]
            self.add_msg(f"הלכת ל-{d}.", "game")
            self._look(None)
        else:
            self.add_msg("אי אפשר ללכת לשם.", "game warning")

    def _look(self, arg):
        r = self.get_room()
        txt = f"אתה ב{r['name']}. {r['desc']}"
        if r["items"]: txt += f"<br>יש פה: {', '.join(r['items'])}"
        self.add_msg(txt, "game")

    def _take(self, item):
        mapping = {"מפתח": "bone_key", "כף": "rusted_spoon", "חרב": "old_sword"}
        item_id = mapping.get(item, item)
        r = self.get_room()
        if item_id in r["items"]:
            self.state["inv"].append(item_id)
            r["items"].remove(item_id)
            self.add_msg(f"לקחת את ה{item_id}.", "game success")
        else:
             self.add_msg("אין כאן את זה.", "game warning")

    def _inv(self, arg):
        self.add_msg(f"תיק: {self.state['inv']}", "game info")

    def _use(self, arg):
        # שימוש פשוט במפתח
        if ("key" in str(arg) or "מפתח" in str(arg)) and "bone_key" in self.state["inv"]:
             if self.state["loc"] == "cell":
                 GAME_DATA["rooms"]["cell"]["interactables"]["door"]["locked"] = False
                 self.add_msg("קליק! הדלת נפתחה.", "game success")
             else:
                 self.add_msg("שום דבר לא קרה.", "game")
        else:
             self.add_msg("אי אפשר להשתמש בזה כרגע.", "game")

# ===============================================
    # 🧠 החיבור לגוגל ג'מיני (מצב דיבאג מלא למסך) 🧠
    # ===============================================
    def ask_gemini_guide(self, question):
        if not GEMINI_AVAILABLE:
            return "<span style='color:red'>הספרייה לא הותקנה או שחסר מפתח API בקוד.</span>"

        r = self.get_room()
        
        prompt = f"""
        אתה מדריך במשחק מבוכים. השחקן ב{r['name']}. הוא שאל: "{question}".
        ענה לו במשפט קצר ומסתורי בעברית.
        """
        
        try:
            # 1. ניסיון רגיל לשלוח לגוגל
            response = model.generate_content(prompt)
            return "🤖 " + response.text
            
        except Exception as e:
            # 2. אם יש שגיאה (כמו מודל לא נמצא), נבצע חקירה:
            error_message = str(e)
            
            # ניסיון לשלוף את רשימת המודלים האמיתית שזמינה לך כרגע
            available_list_html = ""
            try:
                import google.generativeai as genai
                # שליפת מודלים שתומכים ב-generateContent (יצירת טקסט)
                models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                
                # עיצוב הרשימה ל-HTML
                for m_name in models:
                    available_list_html += f"<code>{m_name}</code><br>"
                    
            except Exception as ex:
                available_list_html = f"לא ניתן היה לשלוף רשימה: {ex}"

            # 3. החזרת הודעה מעוצבת למשתמש
            return f"""
            <div style="border: 1px solid red; background: #3d0000; padding: 10px; border-radius: 5px; color: #ffcccc;">
                <strong>⚠️ שגיאת מערכת AI</strong><br>
                {error_message}
                <hr style="border-color: #ff5555; opacity: 0.3;">
                <strong>💡 מודלים זמינים בחשבון שלך:</strong><br>
                <div style="margin-top:5px; color: lightgreen; font-family: monospace;">
                    {available_list_html}
                </div>
                <br>
                <em>טיפ: העתק את אחד השמות הירוקים והדבק בקוד בשורה: <br> model = genai.GenerativeModel('כאן')</em>
            </div>
            """
        r = self.get_room()
        inv_str = ", ".join(self.state['inv']) if self.state['inv'] else "כלום"
        
        # בניית ה"פרומפט" - מה ג'מיני יודע על המצב שלך
        prompt = f"""
        תפקידך: אתה ה-Dungeon Master במשחק מסתורי.
        
        מצב נוכחי במשחק:
        - מיקום: {r['name']} ({r['desc']})
        - חפצים בחדר: {r.get('items', [])}
        - ציוד השחקן: {inv_str}
        
        שאלה/פעולה של השחקן: "{question}"
        
        הנחיות:
        1. ענה בעברית, תשובה קצרה ומסתורית (עד 2 משפטים).
        2. אל תגלה לו פתרונות ישירים, תן רמזים.
        3. אם השחקן אומר סתם אותיות לא מובנות, תענה בסגנון משחקי כמו "הרוח שורקת אך אינה מבינה אותך".
        """
        
        try:
            # שליחה לגוגל
            response = model.generate_content(prompt)
            return "🤖 " + response.text
        except Exception as e:
            return f"שגיאת תקשורת עם גוגל: {e}"

# ==========================================
# שרת WEB (FLASK)
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
    user_txt = data.get("command", "")
    
    state = session.get("game_state", None)
    engine = GameEngine(state)
    
    if user_txt:
        # ההודעה מתווספת ללוג בתוך ה-engine בחלק מהפונקציות,
        # אם זה AI הוא כבר טיפל בהוספה, אם זה פקודה רגילה, לא תמיד הוספנו "User Says"
        # לצורך הפשטות נוסיף כאן ידנית רק אם לא טופל
        pass 
    
    engine.process_input(user_txt)
    session["game_state"] = engine.state
    
    return jsonify({
        "log": engine.state["log"],
        "loc_name": GAME_DATA["rooms"][engine.state["loc"]]["name"]
    })

@app.route("/api/reset", methods=["POST"])
def api_reset():
    session.clear()
    return jsonify({"status": "ok"})

# ממשק ה-HTML (אותו אחד יפה מקודם)
CHAT_HTML = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>הרפתקה עם Gemini</title>
    <style>
        body { background: #1a1a1d; color: #fff; font-family: sans-serif; display: flex; height: 100vh; margin:0;}
        .sidebar { width: 220px; background: #25252b; padding: 20px; border-left: 1px solid #333; }
        .sidebar div { background: #333; padding: 10px; margin-bottom: 5px; cursor: pointer; border-radius: 4px; }
        .sidebar div:hover { background: #444; color: cyan; }
        .chat { flex-grow: 1; display: flex; flex-direction: column; max-width: 900px; margin: 0 auto; background: #0f0f12; }
        .header { padding: 15px; border-bottom: 1px solid #333; font-weight: bold; font-size: 1.2rem; }
        .msgs { flex-grow: 1; padding: 20px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; }
        .input-box { padding: 15px; background: #1a1a1d; display: flex; }
        input { flex-grow: 1; padding: 10px; background: #333; color: white; border: none; font-size: 1.1rem; }
        button { padding: 10px 20px; background: #6c5ce7; border: none; color: white; cursor: pointer; }
        
        .bubble { padding: 10px 15px; border-radius: 10px; max-width: 80%; }
        .bubble.user { align-self: flex-start; background: #00cec9; color: black; border-bottom-right-radius: 0; }
        .bubble.game { align-self: flex-end; background: #333; color: #ddd; border-bottom-left-radius: 0; }
        .bubble.ai { align-self: flex-end; background: linear-gradient(135deg, #e056fd, #686de0); color: white; }
        .bubble.info { color: cyan; border: 1px solid cyan; background: transparent; align-self: center;}
    </style>
</head>
<body>
    <div class="sidebar">
        <h3>פקודות</h3>
        <div onclick="cmd('הסתכל')">👁️ הסתכל</div>
        <div onclick="cmd('תיק')">🎒 מלאי</div>
        <div onclick="cmd('לך החוצה')">🚪 יציאה</div>
        <div onclick="cmd('קח מפתח')">🔑 קח מפתח</div>
        <div onclick="reset()" style="color:salmon">🔄 איפוס</div>
        <p style="font-size:0.8rem; color:#777; margin-top:50px;">מחובר לגוגל Gemini</p>
    </div>
    <div class="chat">
        <div class="header" id="title">טוען חדר...</div>
        <div class="msgs" id="log"></div>
        <div class="input-box">
            <input type="text" id="inp" placeholder="כתוב משהו למדריך..." onkeydown="if(event.key==='Enter') send()">
            <button onclick="send()">שלח</button>
        </div>
    </div>

    <script>
        const API = "{{ api_url }}";
        
        async function send() {
            let val = document.getElementById('inp').value;
            document.getElementById('inp').value = '';
            
            // עדכון אופטימי (מציג למשתמש לפני התשובה)
            if(val) appendMsg(val, 'user');

            let res = await fetch(API, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({command: val})
            });
            let data = await res.json();
            
            render(data.log);
            document.getElementById('title').innerText = data.loc_name;
        }

        function cmd(txt) {
            document.getElementById('inp').value = txt;
            send();
        }

        function render(log) {
            let el = document.getElementById('log');
            el.innerHTML = '';
            log.forEach(msg => appendMsg(msg.text, msg.type));
        }

        function appendMsg(txt, type) {
            let el = document.getElementById('log');
            let d = document.createElement('div');
            d.className = 'bubble ' + type;
            d.innerHTML = txt;
            el.appendChild(d);
            el.scrollTop = el.scrollHeight;
        }
        
        async function reset() { await fetch("{{ reset_url }}", {method:'POST'}); location.reload(); }
        
        send(); // אתחול
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(port=5006, debug=True)
