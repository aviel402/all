from flask import Flask, render_template_string

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="UTF-8">
<title>תגובה קטלנית</title>
<style>
body {
    background:#0f0f0f;
    color:white;
    font-family:Arial;
    text-align:center;
    height:100vh;
    display:flex;
    justify-content:center;
    align-items:center;
}
.box {
    background:#1c1c1c;
    padding:30px;
    border-radius:15px;
    width:320px;
    box-shadow:0 0 30px black;
}
#btn {
    width:100%;
    padding:25px;
    font-size:22px;
    border:none;
    border-radius:10px;
    margin-top:20px;
    cursor:pointer;
    background:#444;
    color:white;
}
#btn.green { background:#2e7d32; }
#btn.red { background:#b71c1c; }
#score { font-size:20px; margin-top:10px; }
#msg { margin-top:15px; color:#aaa; }
</style>
</head>
<body>

<div class="box">
    <h2>⚡ תגובה קטלנית</h2>
    <div id="score">ניקוד: 0</div>
    <button id="btn" onclick="press()">חכה...</button>
    <div id="msg">אל תלחץ עד שזה ירוק!</div>
</div>

<script>
let ready = false;
let score = 0;
let timer;

function startRound() {
    ready = false;
    btn.className = "";
    btn.innerText = "חכה...";
    let delay = Math.random() * 2000 + 800;
    timer = setTimeout(() => {
        ready = true;
        btn.className = "green";
        btn.innerText = "לחץ עכשיו!";
    }, delay);
}

function press() {
    if (!ready) {
        gameOver("לחצת מוקדם מדי!");
        return;
    }
    score++;
    document.getElementById("score").innerText = "ניקוד: " + score;
    startRound();
}

function gameOver(reason) {
    clearTimeout(timer);
    btn.className = "red";
    btn.innerText = "הפסדת";
    document.getElementById("msg").innerText = reason + " | ניקוד סופי: " + score;
    ready = false;
}

startRound();
</script>

</body>
</html>
"""

@app.route("/")
def game():
    return render_template_string(HTML)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
