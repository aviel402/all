from flask import Flask, render_template_string

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="UTF-8">
<title>Overload Reaction</title>
<style>
body{background:#0c0c0c;color:#eee;font-family:Arial;text-align:center;margin:0;padding:0;height:100vh;display:flex;flex-direction:column;justify-content:center;align-items:center;}
#btn{width:200px;padding:25px;font-size:24px;border:none;border-radius:12px;background:#444;color:white;cursor:pointer;transition:0.2s;}
#btn.green{background:#00c853;}
#btn.red{background:#d50000;}
#stats{margin-top:15px;font-size:18px;}
#log{margin-top:15px;height:120px;width:300px;background:#111;overflow:auto;padding:10px;font-size:13px;text-align:right;}
</style>
</head>
<body>

<h1>⚡ Overload Reaction ⚡</h1>
<button id="btn">חכה...</button>
<div id="stats">HP: <span id="hp">100</span> | Score: <span id="score">0</span></div>
<div id="log"></div>

<script>
let hp = 100;
let score = 0;
let ready = false;
let timer;

function log(msg){const l=document.getElementById("log");l.innerHTML="• "+msg+"<br>"+l.innerHTML;}

function startRound(){
    ready=false;
    const btn=document.getElementById("btn");
    btn.className="";
    btn.innerText="חכה...";
    let delay=Math.random()*1500+500;
    timer=setTimeout(()=>{
        ready=true;
        btn.className="green";
        btn.innerText="לחץ עכשיו!";
    },delay);
}

document.getElementById("btn").onclick=function(){
    if(!ready){
        hp-=10;
        log("לחצת מוקדם! -10 HP");
    } else {
        score++;
        log("לחצת בזמן! +1 Score");
        startRound();
    }
    if(hp<=0){
        document.body.innerHTML="<h1 style='color:red'>Game Over! Score: "+score+"</h1>";
    }
    document.getElementById("hp").innerText=hp;
    document.getElementById("score").innerText=score;
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
