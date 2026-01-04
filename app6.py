from flask import Flask, render_template_string, request, session, redirect, url_for
import json

app = Flask(__name__)
app.secret_key = 'super_secret_key_for_game_session'  # נדרש כדי לשמור מידע בין רענוני דף

# --- נתונים (אותו הדבר כמו קודם) ---
WORLD_DATA = {
    "start_cave": {
        "name": "מערת ההתחלה החשוכה",
        "description": "אתה מתעורר בקור, רטוב. אור עמום מגיע מפתח צר.",
        "exits": {"out": "forest_edge"},
        "items": ["old_bandage"],
        "npc": None
    },
    "forest_edge": {
        "name": "קצה היער המעורפל",
        "description": "האוויר כאן כבד. אתה שומע יללות חלשות.",
        "exits": {"cave": "start_cave"},
        "items": ["sharp_stone"],
        "npc": "wounded_wolf"
    }
}

NPC_DATA = {
    "wounded_wolf": {
        "name": "זאב פצוע",
        "description": "זאב גדול שוכב מולך, רגלו מדממת.",
        "options": [
            {"cmd": "heal", "desc": "רפא את הזאב (heal)", "req": "old_bandage"},
            {"cmd": "ignore", "desc": "התעלם (ignore)"}
        ]
    }
}

# --- לוגיקה שמותאמת ל-WEB ---

def get_initial_state():
    return {
        "current_location_id": "start_cave",
        "inventory": [],
        "flags": {},
        "log": ["התעוררת בעולם חדש..."],  # יומן אירועים שמוצג על המסך
        "turn": 0
    }

def process_command(state, command):
    """
    מקבל את המצב הנוכחי ופקודה, מחזיר טקסט לתצוגה ומעדכן את המצב.
    """
    cmd_parts = command.lower().strip().split()
    if not cmd_parts: return "לא כתבת כלום."
    
    action = cmd_parts[0]
    target = cmd_parts[1] if len(cmd_parts) > 1 else None
    
    current_loc = WORLD_DATA[state['current_location_id']]
    output = ""

    # תנועה
    if action in ["go", "move"]:
        if target in current_loc["exits"]:
            state['current_location_id'] = current_loc["exits"][target]
            new_loc = WORLD_DATA[state['current_location_id']]
            output = f"הלכת ל-{new_loc['name']}."
        else:
            output = "אי אפשר ללכת לשם."

    # לקיחת חפצים
    elif action in ["take", "get"]:
        if target in current_loc["items"]:
            state['inventory'].append(target)
            # בהדגמה פשוטה זו אנחנו לא מוחקים מהדאטה הגלובלי כדי לא להרוס לאחרים
            # במשחק אמיתי מעתיקים את ה-World Data לתוך ה-Session
            output = f"לקחת את {target}."
        else:
            output = "אין כאן את החפץ הזה."

    # אינטראקציה פשוטה (hardcoded לצורך הדגמה)
    elif action == "heal" and state['current_location_id'] == "forest_edge":
        if "old_bandage" in state['inventory']:
            state['inventory'].remove("old_bandage")
            state['flags']['wolf_friend'] = True
            output = "השתמשת בתחבושת. הזאב מלקק את ידך ומדדה משם."
        else:
            output = "אין לך תחבושת!"

    elif action == "inv":
        output = f"בתיק שלך: {', '.join(state['inventory'])}"
    
    else:
        output = "פקודה לא מזוהה. נסה: go [kivun], take [item], heal, inv."

    return output

# --- ה-View (דפי ה-HTML) ---

# תבנית HTML פשוטה בתוך הקוד (כדי שיהיה קל להעתיק)
HTML_TEMPLATE = """
<!doctype html>
<html dir="rtl" lang="he">
<head>
    <title>הרפתקה בטקסט</title>
    <style>
        body { font-family: sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; background: #222; color: #eee; }
        .log { background: #333; padding: 10px; height: 300px; overflow-y: scroll; border: 1px solid #555; margin-bottom: 20px;}
        .info { border-bottom: 1px solid #777; padding-bottom: 10px; margin-bottom: 10px; }
        input[type="text"] { width: 70%; padding: 10px; font-size: 16px;}
        input[type="submit"] { width: 25%; padding: 10px; font-size: 16px; cursor: pointer; background: #d35400; color: white; border: none;}
        .highlight { color: #f39c12; }
    </style>
</head>
<body>
    <h1>המסע לעולם המסתורי</h1>
    
    <div class="info">
        <h2>מיקום: {{ location['name'] }}</h2>
        <p>{{ location['description'] }}</p>
        <p>יציאות: <span class="highlight">{{ location['exits'].keys() | join(', ') }}</span></p>
        {% if location['items'] %}
        <p>חפצים: <span class="highlight">{{ location['items'] | join(', ') }}</span></p>
        {% endif %}
        {% if location['npc'] %}
        <p>דמויות: <strong>{{ location['npc'] }}</strong></p>
        {% endif %}
        <p>מלאי: {{ inventory | join(', ') }}</p>
    </div>

    <div class="log" id="logBox">
        {% for line in log %}
            <div>>> {{ line }}</div>
        {% endfor %}
    </div>

    <form method="POST">
        <input type="text" name="command" placeholder="מה לעשות? (למשל: go out, take old_bandage)" autofocus autocomplete="off">
        <input type="submit" value="שלח">
    </form>
    
    <form action="/reset" method="post" style="margin-top:20px;">
        <button type="submit" style="background:none; border:none; color: #777; cursor:pointer;">איפוס משחק</button>
    </form>

    <script>
        // גלילה אוטומטית למטה
        var elem = document.getElementById('logBox');
        elem.scrollTop = elem.scrollHeight;
    </script>
</body>
</html>
"""

# --- Routes (ניתובים) ---

@app.route("/", methods=["GET", "POST"])
def game():
    # אתחול משחק אם לא קיים ב-Session
    if 'game_state' not in session:
        session['game_state'] = get_initial_state()
    
    state = session['game_state']
    
    if request.method == "POST":
        user_cmd = request.form.get("command")
        if user_cmd:
            # הרצת לוגיקה
            result_text = process_command(state, user_cmd)
            
            # עדכון היומן והתור
            state['log'].append(f"{user_cmd} : {result_text}")
            state['turn'] += 1
            
            # שמירה חזרה ל-Session (חשוב מאוד!)
            session['game_state'] = state
    
    # שליפת המידע להצגה
    current_loc_data = WORLD_DATA.get(state['current_location_id'], {})
    
    return render_template_string(
        HTML_TEMPLATE, 
        location=current_loc_data, 
        inventory=state['inventory'],
        log=state['log']
    )

@app.route("/reset", methods=["POST"])
def reset():
    session.clear()
    return redirect(url_for('game'))

if __name__ == "__main__":
    # הרצת השרת במצב פיתוח
    app.run(debug=True, port=5000)
