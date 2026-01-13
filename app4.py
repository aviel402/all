from flask import Flask, render_template_string, request, jsonify
import random

app = Flask(__name__)

state = {
    "day": 1,
    "food": 50,
    "water": 50,
    "power": 50,
    "morale": 50,
    "alive": True,
    "log": ["המקלט נפתח. האחריות עליך."]
}

HTML = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="UTF-8">
<title>Shelter Command</title>
<style>
body {
    background:#111;
    color:#eee;
    font-family:Arial;
    display:flex;
    justify-content:center;
}
.panel {
    width:400px;
    background:#1b1b1b;
    padding:20px;
    margin-top:30px;
    border-radius:10px;
}
.stat { margin:6px 0; }
button {
    width:100%;
    margin-top:8px;
    padding:10px;
    background:#333;
    color:white;
    border:none;
    cursor:pointer;
}
button:hover { background:#555; }
.log {
    background:#000;
    margin-top:10px;
    padding:10px;
    height:120px;
    overflow:auto;
    font-size:13px;
}
.dead { color:red; font-size:22px; text-align:center; }
</style>
</head>
<body>

<div class="panel">
<h2>🏠 Shelter Command</h2>

<div id="stats"></div>

<button onclick="act('food')">הקצה צוות לאיסוף מזון</button>
<button onclick="act('water')">טפל במערכת המים</button>
<button onclick="act('power')">תחזק גנרטור</button>
<button onclick="act('morale')">דבר עם האנשים</button>

<div class="log" id="log"></div>
</div>

<script>
function update(data){
    if(!data.alive){
        document.body.innerHTML = "<div class='dead'>המקלט קרס<br>שרדת " + data.day + " ימים</div>";
        return;
    }

    document.getElementById("stats").innerHTML =
        "יום: " + data.day + "<br>" +
        "🍞 מזון: " + data.food + "<br>" +
        "💧 מים: " + data.water + "<br>" +
        "⚡ חשמל: " + data.power + "<br>" +
        "🙂 מורל: " + data.morale;

    document.getElementById("log").innerHTML =
        data.log.map(x => "• " + x).join("<br>");
}

function act(type){
    fetch("/act", {
        method:"POST",
        headers:{ "Content-Type":"application/json" },
        body:JSON.stringify({action:type})
    })
    .then(r=>r.json())
    .then(update);
}

fetch("/state").then(r=>r.json()).then(update);
</script>

</body>
</html>
"""

@app.route("/")
def game():
    return render_template_string(HTML)

@app.route("/state")
def get_state():
    return jsonify(state)

@app.route("/act", methods=["POST"])
def act():
    if not state["alive"]:
        return jsonify(state)

    a = request.json["action"]
    state["day"] += 1

    for k in ["food","water","power","morale"]:
        state[k] -= random.randint(3,6)

    if a == "food":
        state["food"] += random.randint(10,15)
        state["log"].append("נשלח צוות – חזר עם מזון.")
    elif a == "water":
        state["water"] += random.randint(10,15)
        state["log"].append("המערכת תוקנה זמנית.")
    elif a == "power":
        state["power"] += random.randint(10,15)
        state["log"].append("הגנרטור חזר לפעול.")
    elif a == "morale":
        state["morale"] += random.randint(10,15)
        state["log"].append("שיחה קשה, אבל הרגיעה.")

    if min(state["food"],state["water"],state["power"],state["morale"]) <= 0:
        state["alive"] = False
        state["log"].append("המערכת קרסה.")

    return jsonify(state)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
