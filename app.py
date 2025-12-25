import random
from flask import Flask, render_template_string, session, request, redirect

app = Flask(__name__)
app.secret_key = "ULTIMATE_ARCADE_KEY_2025"  # מפתח הצפנה לשמירת משחקים

# ==============================================================================
# חלק 1: התפריט הראשי (MAIN MENU)
# הלובי שמחבר את כל 12 המשחקים האחרים
# ==============================================================================
MENU_HTML = """
<!DOCTYPE html>
<html dir="rtl">
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Aviel's 12-Game Arcade</title>
    <style>
        body { background: #111; color: white; font-family: sans-serif; text-align: center; margin: 0; }
        header { background: #222; padding: 20px; border-bottom: 3px solid gold; margin-bottom: 20px; }
        h1 { margin: 0; color: gold; font-size: 24px; text-transform: uppercase; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 15px; padding: 15px; max-width: 800px; margin: 0 auto; }
        .card { 
            background: #1e1e1e; padding: 15px; border-radius: 12px; text-decoration: none; color: white; border: 1px solid #333; 
            transition: 0.2s; display: flex; flex-direction: column; justify-content: center; height: 120px;
        }
        .card:hover { transform: scale(1.05); background: #2a2a2a; border-color: gold; }
        .icon { font-size: 40px; margin-bottom: 5px; }
        .name { font-weight: bold; font-size: 14px; }
        .btn-reset { margin-top: 30px; background: #333; color: #777; border: none; padding: 10px; cursor: pointer; border-radius: 5px; margin-bottom: 50px; }
    </style>
</head>
<body>
    <header><h1>👾 אולר המשחקים (12 In 1)</h1></header>
    <div class="grid">
        <a href="/snake" class="card"><div class="icon">🐍</div><div class="name">1. סנייק</div></a>
        <a href="/survival" class="card"><div class="icon">💀</div><div class="name">2. הישרדות</div></a>
        <a href="/rpg" class="card"><div class="icon">⚔️</div><div class="name">3. RPG Legend</div></a>
        <a href="/manager" class="card"><div class="icon">⚽</div><div class="name">4. מנג'ר</div></a>
        <a href="/gang" class="card"><div class="icon">🔫</div><div class="name">5. Gang Wars</div></a>
        <a href="/army" class="card"><div class="icon">🪖</div><div class="name">6. Iron Legion</div></a>
        <a href="/space" class="card"><div class="icon">🚀</div><div class="name">7. Space Tycoon</div></a>
        <a href="/stock" class="card"><div class="icon">📉</div><div class="name">8. הבורסה</div></a>
        <a href="/blackjack" class="card"><div class="icon">🃏</div><div class="name">9. בלאק ג'ק</div></a>
        <a href="/miner" class="card"><div class="icon">⛏️</div><div class="name">10. כורה זהב</div></a>
        <a href="/chrono" class="card"><div class="icon">⏱️</div><div class="name">11. רפלקס</div></a>
        <a href="/guess" class="card"><div class="icon">🔢</div><div class="name">12. כספת</div></a>
    </div>
    <a href="/reset"><button class="btn-reset">🗑️ אפס הכל</button></a>
</body>
</html>
"""
@app.route('/')
def menu(): return render_template_string(MENU_HTML)
@app.route('/reset')
def reset(): session.clear(); return redirect('/')

# ==============================================================================
# חלק 2: משחק סנייק (SNAKE)
# משחק קלאסי שרץ על גבי הדפדפן (JS)
# ==============================================================================
SNAKE_HTML = """
<!DOCTYPE html><html dir="rtl"><head><meta name="viewport" content="width=device-width, initial-scale=1, user-scalable=no"><style>
body{background:#9fac00;font-family:monospace;display:flex;flex-direction:column;align-items:center;height:100vh;margin:0;overflow:hidden}
#g{background:#8f9c00;border:4px solid black;display:grid;grid-template-columns:repeat(20,15px);grid-template-rows:repeat(20,15px)}
.p{width:15px;height:15px}.s{background:black}.f{background:black;border-radius:50%}
.c{display:grid;grid-template-columns:60px 60px 60px;gap:5px;margin-top:10px}
button{height:50px;background:#222;color:#9fac00;font-size:24px;border-radius:10px;border:none}
a{position:absolute;top:5px;left:5px;text-decoration:none;font-size:20px}
</style></head><body><a href="/">🏠</a><h2><span id="sc">0</span></h2><div id="g"></div>
<div class="c"><div></div><button onclick="d(0,-1)">⬆️</button><div></div><button onclick="d(-1,0)">⬅️</button><button onclick="d(0,1)">⬇️</button><button onclick="d(1,0)">➡️</button></div>
<script>
const B=document.getElementById('g');let sn=[{x:10,y:10}],f={x:5,y:5},dx=0,dy=0,s=0;
function dr(){B.innerHTML='';for(let y=0;y<20;y++)for(let x=0;x<20;x++){let d=document.createElement('div');d.className='p';
if(sn.some(z=>z.x==x&&z.y==y))d.classList.add('s');if(f.x==x&&f.y==y)d.classList.add('f');B.appendChild(d)}}
function u(){if(dx==0&&dy==0)return;let h={x:sn[0].x+dx,y:sn[0].y+dy};
if(h.x<0||h.x>=20||h.y<0||h.y>=20||sn.some(z=>z.x==h.x&&z.y==h.y)){alert('Game Over: '+s);location.reload()}
sn.unshift(h);if(h.x==f.x&&h.y==f.y){s++;document.getElementById('sc').innerText=s;f={x:Math.floor(Math.random()*20),y:Math.floor(Math.random()*20)}}else sn.pop();dr()}
function d(x,y){if(dx!=-x&&dy!=-y){dx=x;dy=y}}
setInterval(u,150);dr();
</script></body></html>
"""
@app.route('/snake')
def snake(): return render_template_string(SNAKE_HTML)

# ==============================================================================
# חלק 3: הישרדות (THE LAST DAY)
# משחק ניהול משאבים טקסטואלי
# ==============================================================================
@app.route('/survival', methods=['GET', 'POST'])
def survival():
    s = session.get('srv', {'hp':100, 'fd':100, 'wt':100, 'day':1, 'log':['התעוררת. העולם הרוס.']})
    if request.method=='POST':
        a = request.form['act']
        msg=""
        if a=='find':
            s['fd']-=10;s['wt']-=10
            if random.random()>0.4: msg="מצאת קופסת שימורים!"; s['fd']=min(100,s['fd']+30)
            else: msg="נתקלת בזומבי ונפצעת!"; s['hp']-=20
        elif a=='eat': s['fd']=min(100,s['fd']+40); msg="אכלת."
        elif a=='drink': s['wt']=min(100,s['wt']+40); msg="שתית."
        elif a=='sleep': s['hp']=min(100,s['hp']+15); s['fd']-=20; s['wt']-=20; s['day']+=1; msg=f"בוקר טוב ליום {s['day']}."
        
        if s['fd']<=0 or s['wt']<=0: s['hp']-=15; msg+=" אתה גווע!"
        if s['hp']<=0: s={'hp':100,'fd':100,'wt':100,'day':1,'log':['מתת. משחק חדש.']}; msg="💀"
        s['log'].insert(0,msg)
        session['srv']=s
    
    HTML="""<body style='background:#222;color:#eee;font-family:sans-serif;text-align:center;padding:10px'>
    <h3>🧟 יום {{day}}</h3><div>❤️ {{hp}} | 🍖 {{fd}} | 💧 {{wt}}</div>
    <div style='background:#000;height:100px;overflow:auto;margin:10px;padding:5px;border:1px solid #555'>{%for l in log%}<div>{{l}}</div>{%endfor%}</div>
    <form method='post'><button name='act' value='find' style='width:100%;padding:10px;margin:2px'>🔍 חפש (מסוכן)</button>
    <button name='act' value='eat' style='width:48%;padding:10px;margin:2px'>🍖 לאכול</button>
    <button name='act' value='drink' style='width:48%;padding:10px;margin:2px'>💧 לשתות</button>
    <button name='act' value='sleep' style='width:100%;padding:10px;margin:2px;background:#0d47a1;color:white'>💤 לישון</button></form>
    <br><a href='/' style='color:grey'>תפריט</a></body>"""
    return render_template_string(HTML, **s)

# ==============================================================================
# חלק 4: RPG LEGEND
# חרבות, קסמים ורמות
# ==============================================================================
@app.route('/rpg', methods=['GET','POST'])
def rpg():
    r = session.get('rpg', {'hp':100, 'gold':0, 'lvl':1, 'loc':'Town', 'msg':'הגעת לעיר.'})
    if request.method == 'POST':
        a = request.form['a']
        if a=='rest':
            if r['gold']>=10: r['gold']-=10; r['hp']=100+(r['lvl']*10); r['msg']="נחת."
        elif a in ['forest','boss']: r['loc']=a; r['msg']="יצאת לקרב..."
        elif a=='town': r['loc']='Town'
        elif a=='atk':
            en_pwr = 10 if r['loc']=='forest' else 50
            if random.random()>0.3:
                r['gold']+=en_pwr; r['msg']="ניצחת!"
                if r['loc']=='boss': r['lvl']+=1; r['msg']="עלית רמה!"
            else:
                r['hp']-=en_pwr; r['msg']=f"נפגעת (-{en_pwr})!"
                if r['hp']<=0: r={'hp':100,'gold':0,'lvl':1,'loc':'Town','msg':'מתת.'}
        session['rpg']=r
        
    HTML="""<body style='background:#1a1a2e;color:#fff;text-align:center'><h2>RPG ⚔️</h2>
    <div>Lv.{{lvl}} | ❤️ {{hp}} | 💰 {{gold}}</div><br><b>{{loc}}</b>: {{msg}}<hr>
    {% if loc=='Town' %}<form method='post'><button name='a' value='rest'>🏨 מלון (10$)</button><button name='a' value='forest'>🌲 יער</button><button name='a' value='boss'>👹 בוס</button></form>
    {% else %}<form method='post'><button name='a' value='atk' style='padding:20px;width:100%;background:red;color:white'>⚔️ תקוף</button><button name='a' value='town'>🏃 ברח</button></form>{% endif %}
    <br><a href='/' style='color:#aaa'>יציאה</a></body>"""
    return render_template_string(HTML, **r)

# ==============================================================================
# חלק 5: SUPER LIGA (מנג'ר כדורגל)
# ==============================================================================
@app.route('/manager', methods=['GET','POST'])
def manager():
    fm = session.get('fm', {'$$':5000, 'wk':1, 'att':50, 'def':50, 'pts':0, 'msg':['העונה החלה!']})
    if request.method == 'POST':
        a = request.form['a']
        if a=='train' and fm['$$']>=500:
            fm['$$']-=500; fm['att']+=2; fm['def']+=2; fm['msg'].insert(0,"אימנת את הקבוצה (+2).")
        elif a=='match':
            s1 = int(random.random() * fm['att']/10); s2 = int(random.random() * 5)
            res = "ניצחון" if s1>s2 else ("הפסד" if s2>s1 else "תיקו")
            bns = 1000 if s1>s2 else 200
            fm['$$']+=bns; fm['pts']+=(3 if s1>s2 else (1 if s1==s2 else 0)); fm['wk']+=1
            fm['msg'].insert(0, f"מחזור {fm['wk']-1}: {s1}-{s2} ({res}) +{bns}$")
        session['fm'] = fm
        
    HTML="""<body style='background:#e8f5e9;font-family:sans-serif;padding:10px;text-align:center'>
    <h3>⚽ ליגת העל: מחזור {{wk}}</h3><div style='background:#2e7d32;color:white;padding:10px;border-radius:5px'>תקציב: {{$$}}$ | נקודות: {{pts}}</div>
    <div>התקפה: {{att}} | הגנה: {{def}}</div>
    <div style='background:white;height:100px;overflow:auto;margin:10px 0;border:1px solid green;font-size:12px'>{%for m in msg%}<div>{{m}}</div>{%endfor%}</div>
    <form method='post'><button name='a' value='match' style='width:100%;padding:15px;background:#1b5e20;color:white'>⚽ שחק משחק</button>
    <button name='a' value='train' style='margin-top:10px;padding:10px'>🏋️ אימון (500$)</button></form><br><a href='/'>יציאה</a></body>"""
    return render_template_string(HTML, **fm)

# ==============================================================================
# חלק 6: GANG WARS (טריטוריה)
# ==============================================================================
@app.route('/gang', methods=['GET','POST'])
def gang():
    g = session.get('gn', {'cash':100, 'men':5, 'zones': [{'n':'שכונה','d':10,'own':True},{'n':'מרכז','d':50,'own':False},{'n':'נמל','d':100,'own':False}]})
    msg=""
    if request.method=='POST':
        a = request.form['a']
        if a=='rec': 
            if g['cash']>=50: g['cash']-=50; g['men']+=2; msg="גייסת 2 חיילים."
        elif a=='col':
            inc = sum(20 for z in g['zones'] if z['own'])
            g['cash']+=inc; msg=f"אספת {inc}$ דמי חסות."
        elif a.startswith('atk'):
            i=int(a.split('_')[1]); z=g['zones'][i]
            if g['men'] > z['d']/5:
                z['own']=True; g['men']-=int(z['d']/10); msg=f"כבשת את {z['n']}!"
            else:
                g['men']=int(g['men']*0.5); msg="ההתקפה נכשלה!"
        session['gn']=g
        
    HTML="""<body style='background:#000;color:lime;font-family:monospace;text-align:center'><h3>🔫 מלחמת כנופיות</h3>
    <div>💵 {{cash}}$ | 🙍 {{men}}</div><div style='color:white'>{{msg}}</div><hr>
    {% for z in zones %}<div style='border:1px dashed;margin:5px;padding:5px;color:{{ "lime" if z.own else "red" }}'>
    {{z.n}} (הגנה: {{z.d}}) {%if not z.own%}<form method='post' style='display:inline'><button name='a' value='atk_{{loop.index0}}'>תקוף</button></form>{%endif%}
    </div>{% endfor %}
    <form method='post'><button name='a' value='rec'>גייס (50$)</button> <button name='a' value='col'>אסוף כסף</button></form>
    <br><a href='/' style='color:grey'>תפריט</a></body>"""
    return render_template_string(HTML, **g, msg=msg)

# ==============================================================================
# חלק 7: IRON LEGION (בניית צבא IDLE)
# ==============================================================================
@app.route('/army', methods=['GET','POST'])
def army():
    ar = session.get('army', {'g':200, 'w':1, 'u':0, 't':0, 'l':''})
    if request.method=='POST':
        a = request.form['a']
        if a=='buy_u' and ar['g']>=50: ar['g']-=50; ar['u']+=1
        elif a=='buy_t' and ar['g']>=300: ar['g']-=300; ar['t']+=1
        elif a=='f':
            pwr = ar['u']*10 + ar['t']*60
            if pwr >= ar['w']*50:
                rw = ar['w']*100; ar['g']+=rw; ar['w']+=1
                ar['u']=int(ar['u']*0.9); ar['l']=f"ניצחון! {rw}$"
            else:
                ar['u']=int(ar['u']*0.5); ar['l']="תבוסה כואבת..."
        session['army']=ar
        
    HTML="""<body style='background:#222;color:#ccc;text-align:center'><h3>🪖 לגיון הברזל</h3>
    <div>💰 {{g}} | גל {{w}} | כוח: {{u*10 + t*60}}</div>
    <div style='color:gold;margin:10px'>{{l}}</div>
    <form method='post'><button name='a' value='f' style='padding:15px;width:100%;background:#b71c1c;color:white;border:none'>⚔️ צא לקרב (גל {{w}})</button>
    <div style='margin-top:20px'><button name='a' value='buy_u'>🔫 חייל (50$)</button> כמות: {{u}}</div>
    <div style='margin-top:5px'><button name='a' value='buy_t'>🚜 טנק (300$)</button> כמות: {{t}}</div></form>
    <br><a href='/'>חזרה</a></body>"""
    return render_template_string(HTML, **ar)

# ==============================================================================
# חלק 8: SPACE TYCOON (חלל)
# ==============================================================================
@app.route('/space', methods=['GET','POST'])
def space():
    sp = session.get('spc', {'wk':1, 'pop':100, 'food':100, 'fuel':100, 'msg':"המראה."})
    if request.method=='POST':
        a = request.form['a']
        if a=='scv': sp['fuel']-=10; sp['food']+=random.randint(10,30); sp['msg']="אספת מזון."
        elif a=='fly': sp['fuel']-=20; sp['wk']+=1; sp['food']-=20; sp['msg']=f"עברת לשבוע {sp['wk']}."
        if sp['food']<=0: sp['pop']-=10; sp['msg']="אנשים מתו ברעב!"
        if sp['pop']<=0: sp={'wk':1, 'pop':100, 'food':100, 'fuel':100, 'msg':"המושבה הושמדה."}
        session['spc']=sp
        
    HTML="""<body style='background:#0d1117;color:#58a6ff;text-align:center;font-family:sans-serif'><h3>🚀 חלל: שבוע {{wk}}</h3>
    <div>👥 {{pop}} | 🍏 {{food}} | ⛽ {{fuel}}</div>
    <p style='color:white'>{{msg}}</p>
    <form method='post'><button name='a' value='scv' style='padding:10px'>נחיתה לאיסוף משאבים</button>
    <button name='a' value='fly' style='padding:10px'>המשך טיסה (שורף דלק)</button></form><br><a href='/'>תפריט</a></body>"""
    return render_template_string(HTML, **sp)

# ==============================================================================
# חלק 9: STOCK MARKET (הבורסה)
# ==============================================================================
@app.route('/stock', methods=['GET','POST'])
def stock():
    st = session.get('stk', {'$:':1000, 'S':{'NVDA':100,'TSLA':50}, 'my':{'NVDA':0,'TSLA':0}})
    if request.method=='POST':
        a = request.form['a']; id=request.form.get('id')
        if a=='next':
            for k in st['S']: st['S'][k]=int(st['S'][k]*random.uniform(0.9,1.2))
        elif a=='buy' and st['$:']>=st['S'][id]:
            st['$:']-=st['S'][id]; st['my'][id]+=1
        elif a=='sell' and st['my'][id]>0:
            st['$:']+=st['S'][id]; st['my'][id]-=1
        session['stk']=st
        
    H="""<body style='font-family:sans-serif;text-align:center'><h3>📉 הבורסה</h3><div>מזומן: {{ $: }}$</div><hr>
    {% for k,p in S.items() %}<div style='border:1px solid #ccc;margin:5px;padding:5px'>
    <b>{{k}}</b>: {{p}}$ | יש לך: {{my[k]}}
    <form method='post' style='display:inline'><input type='hidden' name='id' value='{{k}}'>
    <button name='a' value='buy' style='color:green'>קנה</button>
    <button name='a' value='sell' style='color:red'>מכור</button></form></div>{% endfor %}
    <form method='post'><button name='a' value='next' style='width:100%;padding:15px;background:#333;color:white'>📅 יום הבא</button></form><br><a href='/'>יציאה</a></body>"""
    return render_template_string(H, **st)

# ==============================================================================
# חלק 10: BLACKJACK (קזינו 21)
# ==============================================================================
@app.route('/blackjack', methods=['GET','POST'])
def blackjack():
    bj = session.get('bj', {'deck':[], 'ph':[], 'dh':[], 'cash':100, 'state':'bet'}) # state: bet, play, done
    
    def val(hand):
        v = sum(11 if c==1 else min(c,10) for c in hand)
        while v>21 and 1 in hand: v-=10; hand[hand.index(1)]=111 # fix ace
        return v
    
    if request.method=='POST':
        a=request.form['a']
        if a=='deal' and bj['cash']>=10:
            bj['cash']-=10
            bj['deck']=[1,2,3,4,5,6,7,8,9,10,10,10,10]*4
            random.shuffle(bj['deck'])
            bj['ph']=[bj['deck'].pop(), bj['deck'].pop()]
            bj['dh']=[bj['deck'].pop(), bj['deck'].pop()]
            bj['state']='play'
        elif a=='hit':
            bj['ph'].append(bj['deck'].pop())
            if val(bj['ph'])>21: bj['state']='bust'
        elif a=='stand':
            while val(bj['dh'])<17: bj['dh'].append(bj['deck'].pop())
            p=val(bj['ph']); d=val(bj['dh'])
            if d>21 or p>d: bj['state']='win'; bj['cash']+=20
            elif p==d: bj['state']='push'; bj['cash']+=10
            else: bj['state']='lose'
        session['bj']=bj
        
    pH = sum(11 if c==1 else min(c,10) for c in bj['ph']) # Simple visual sum
    msg = {'bet':'הימרת 10$', 'play':'משחקים...', 'bust':'נשרפת!','win':'ניצחת!','lose':'הפסדת!','push':'תיקו'}.get(bj['state'])
    
    H="""<body style='background:green;color:white;text-align:center'><h3>🃏 בלאק-ג'ק 21</h3>
    <div>מזומן: {{cash}}$</div><br>
    <div>דילר: {{ dh[0] if state=='play' else dh }}</div><br>
    <div>אתה: {{ ph }} ({{ calc(ph) }})</div><br>
    <h2>{{ msg }}</h2>
    {% if state=='bet' or state in ['bust','win','lose','push'] %}
    <form method='post'><button name='a' value='deal'>חלק קלפים (10$)</button></form>
    {% else %}
    <form method='post'><button name='a' value='hit'>👊 קח קלף</button> <button name='a' value='stand'>✋ עצור</button></form>
    {% endif %} <br><a href='/' style='color:black'>יציאה</a></body>"""
    return render_template_string(H, **bj, calc=val, msg=msg)

# ==============================================================================
# חלק 11: כורה זהב (MINER CLICKER)
# משחק התמכרות - לחיצות ושדרוגים
# ==============================================================================
@app.route('/miner', methods=['GET','POST'])
def miner():
    m = session.get('mn', {'g':0, 'pick':1, 'drill':0})
    if request.method=='POST':
        a = request.form['a']
        if a=='dig': m['g'] += m['pick'] + (m['drill']*5)
        elif a=='up_pick' and m['g']>=50: m['g']-=50; m['pick']+=1
        elif a=='buy_drill' and m['g']>=500: m['g']-=500; m['drill']+=1
        session['mn']=m
        
    H="""<body style='background:#333;color:gold;text-align:center'><h3>⛏️ כורה הזהב</h3>
    <h1 style='font-size:50px'>{{g}}</h1>
    <form method='post'><button name='a' value='dig' style='width:200px;height:100px;font-size:24px;background:#555;color:white;border:none;border-radius:10px'>חפור!</button>
    <div style='margin-top:20px;color:white'>
    <div>מכוש (רמה {{pick}}): <button name='a' value='up_pick'>שדרג ב-50</button></div>
    <div style='margin-top:5px'>מקדחה ({{drill}} יח'): <button name='a' value='buy_drill'>קנה ב-500</button></div>
    </div></form><br><a href='/' style='color:#777'>תפריט</a></body>"""
    return render_template_string(H, **m)

# ==============================================================================
# חלק 12: כספת (HIGH-LOW GUESS)
# פשוט אך מעצבן
# ==============================================================================
@app.route('/guess', methods=['GET','POST'])
def guess():
    g = session.get('gs', {'target':random.randint(1,100), 'msg':'נחש מספר בין 1 ל-100', 'tries':0})
    if request.method=='POST':
        if 'reset' in request.form: 
            g={'target':random.randint(1,100), 'msg':'משחק חדש!', 'tries':0}
        else:
            try:
                n = int(request.form['num'])
                g['tries']+=1
                if n < g['target']: g['msg']="יותר גבוה! ⬆️"
                elif n > g['target']: g['msg']="יותר נמוך! ⬇️"
                else: g['msg']=f"בול! 🔓 פתחת את הכספת ב-{g['tries']} ניסיונות."
            except: pass
        session['gs']=g
        
    H="""<body style='background:#444;color:#eee;text-align:center;font-family:sans-serif;padding:30px'>
    <div style='background:#222;padding:20px;border-radius:10px;border:4px solid gold'>
    <h1>🔢 הכספת</h1><h3>{{msg}}</h3>
    <form method='post'><input type='number' name='num' style='font-size:30px;width:100px;text-align:center'>
    <br><br><button style='padding:10px 20px;font-size:20px'>פתח</button></form>
    {% if 'בול' in msg %}<form method='post'><button name='reset' style='margin-top:10px;background:gold'>משחק חדש</button></form>{%endif%}
    </div><br><a href='/' style='color:#ccc'>יציאה</a></body>"""
    return render_template_string(H, **g)

# ==============================================================================
# חלק 13: CHRONO CLICK (רפלקס)
# ==============================================================================
@app.route('/chrono')
def chrono():
    # פשוט JS טהור ללא סשן, לא צריך backend מורכב
    return """
    <!DOCTYPE html><html dir="rtl"><body style="background:black;color:white;display:flex;flex-direction:column;align-items:center;justify-content:center;height:100vh;font-family:sans-serif;text-align:center">
    <h1 id="t">לחץ כשהאדום הופך לירוק</h1>
    <div id="b" onclick="clk()" style="width:200px;height:200px;background:red;border-radius:50%;margin:20px;cursor:pointer"></div>
    <div id="res" style="font-size:30px;color:yellow"></div>
    <button onclick="st()" style="padding:10px">התחל</button><br><a href="/" style="color:grey">יציאה</a>
    <script>
    let s,tr=false; const B=document.getElementById('b'), T=document.getElementById('t');
    function st(){ B.style.background='red'; T.innerText='המתן...'; tr=false;
    setTimeout(()=>{ B.style.background='#0f0'; s=Date.now(); tr=true; }, 1000+Math.random()*3000); }
    function clk(){ if(tr){ let d=Date.now()-s; document.getElementById('res').innerText=d+' ms'; tr=false; }
    else if(B.style.background=='red') T.innerText='מוקדם מדי!'}
    </script></body></html>
    """

# ==========================================
# הרצה ראשית (עבור הרצה מקומית)
# ==========================================
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
