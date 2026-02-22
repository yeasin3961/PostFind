import os
import datetime
from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
from pymongo import MongoClient
from bson.objectid import ObjectId

# --- অ্যাপ কনফিগারেশন ---
app = Flask(__name__)
app.secret_key = "final_perfect_simple_movie_v100"

# --- ডাটাবেস কানেকশন ---
MONGO_URI = "mongodb+srv://roxiw19528:roxiw19528@cluster0.vl508y4.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client.simple_movie_db
content_col = db.contents
settings_col = db.settings
analytics_col = db.analytics 

# --- ডাটাবেস ইনিশিয়ালাইজেশন ---
def init_db():
    if not settings_col.find_one({"key": "site_config"}):
        settings_col.insert_one({"key": "site_config", "name": "MovieTok Pro"})
    if not settings_col.find_one({"key": "admin_auth"}):
        settings_col.insert_one({"key": "admin_auth", "username": "admin", "password": "1234"})
    if not settings_col.find_one({"key": "notice_config"}):
        settings_col.insert_one({"key": "notice_config", "text": "Welcome!", "color": "#fff", "size": "14", "bg_color": "#e50914"})
    if not settings_col.find_one({"key": "popup_config"}):
        settings_col.insert_one({"key": "popup_config", "text": "Join Us!", "bg_color": "#1a1a1a", "text_color": "#fff", "text_size": "18", "interval_mins": "5", "join_link": "#"})

init_db()

# --- হেল্পার ফাংশন (Analytics) ---
def track_stat(stat_type):
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    analytics_col.update_one({"date": today}, {"$inc": {stat_type: 1}}, upsert=True)

def track_visitor():
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    country = request.headers.get('CF-IPCountry', 'Unknown') 
    analytics_col.update_one({"date": today}, {"$inc": {f"countries.{country}": 1}}, upsert=True)

# --- ডিজাইন (CSS) ---
GLOBAL_CSS = '''
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;800&display=swap');
    :root { --primary: #e50914; --bg: #000; --card: #141414; }
    body { background: var(--bg); color: #fff; font-family: 'Poppins', sans-serif; margin: 0; padding: 0; overflow-x: hidden; }
    a { text-decoration: none; color: inherit; }
    
    .notice-bar { width: 100%; padding: 8px 10px; text-align: center; font-weight: 600; position: relative; z-index: 2500; display: block; box-sizing: border-box; }

    #popupOverlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.85); z-index: 9999; display: none; align-items: center; justify-content: center; backdrop-filter: blur(5px); }
    .popup-content { width: 90%; max-width: 450px; border-radius: 20px; padding: 30px 20px; position: relative; text-align: center; border: 1px solid #333; }
    .btn-popup-join { background: #0088cc; color: #fff; font-size: 11px; padding: 5px 12px; border-radius: 50px; }

    .bottom-nav { position: fixed; bottom: 0; width: 100%; background: rgba(10, 10, 10, 0.98); backdrop-filter: blur(15px); display: flex; justify-content: space-around; padding: 12px 0; border-top: 1px solid #222; z-index: 2000; }
    .nav-link { color: #888; font-size: 13px; text-align: center; flex: 1; }
    .nav-link.active { color: var(--primary); }

    .slider-wrap { width: 100%; overflow: hidden; position: relative; margin-top: 10px; }
    .slider { display: flex; transition: 0.6s cubic-bezier(0.25, 1, 0.5, 1); }
    .slide-item { min-width: 90%; margin: 0 5%; height: 220px; position: relative; border-radius: 15px; overflow: hidden; border: 1px solid #333; }
    .slide-item img { width: 100%; height: 100%; object-fit: cover; opacity: 0.7; }
    .slide-info { position: absolute; bottom: 0; background: linear-gradient(transparent, #000); width: 100%; padding: 20px; font-weight: bold; }

    .search-box { padding: 15px; background: #000; position: sticky; top: 0; z-index: 1500; text-align: center; }
    .search-input { width: 90%; max-width: 600px; padding: 12px 20px; border-radius: 30px; border: 1px solid #333; background: #1a1a1a; color: #fff; outline: none; }

    .grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; padding: 15px; margin-bottom: 90px; }
    @media(min-width: 768px) { .grid { grid-template-columns: repeat(4, 1fr); } }
    
    .card { position: relative; background: var(--card); border-radius: 10px; overflow: hidden; border: 1px solid #222; }
    .card img { width: 100%; height: 240px; object-fit: cover; }
    .card-title { padding: 8px; font-size: 13px; text-align: center; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    
    .m-badge { position: absolute; top: 8px; left: 8px; padding: 3px 8px; border-radius: 4px; font-size: 10px; font-weight: 800; z-index: 10; text-transform: uppercase; }
    .section-head { padding: 15px 20px 0; font-size: 18px; font-weight: 700; color: #eee; border-left: 4px solid var(--primary); margin-left: 15px; }

    .int-box { display: flex; gap: 15px; margin: 15px 0; }
    .btn-int { background: #1a1a1a; padding: 8px 15px; border-radius: 8px; font-size: 14px; cursor: pointer; border: 1px solid #333; }
    .btn-int:hover { border-color: var(--primary); }

    .admin-nav { background: #111; padding: 10px; display: flex; gap: 10px; overflow-x: auto; position: sticky; top: 0; z-index: 100; border-bottom: 1px solid #333; }
    .admin-nav a { padding: 8px 15px; background: #222; border-radius: 5px; font-size: 13px; white-space: nowrap; }
    .admin-nav a.active { background: var(--primary); }
</style>
'''

POPUP_SNIPPET = '''
<div id="popupOverlay">
    <div class="popup-content" style="background: {{ popup.bg_color }};">
        <div style="position: absolute; top: 10px; left: 10px;"><a href="{{ popup.join_link }}" target="_blank" class="btn-popup-join">💬 Join Media</a></div>
        <div style="position: absolute; top: 10px; right: 10px;"><button style="background:none; border:none; color:#fff; cursor:pointer;" onclick="closePopup()">✕</button></div>
        <div style="color: {{ popup.text_color }}; font-size: {{ popup.text_size }}px; margin-top: 25px;">{{ popup.text }}</div>
    </div>
</div>
<script>
    function showPopup() {
        const last = localStorage.getItem('p_last');
        const now = new Date().getTime();
        if (!last || (now - last) > ({{ popup.interval_mins }} * 60000)) {
            document.getElementById('popupOverlay').style.display = 'flex';
        }
    }
    function closePopup() {
        document.getElementById('popupOverlay').style.display = 'none';
        localStorage.setItem('p_last', new Date().getTime());
    }
    window.onload = () => setTimeout(showPopup, 2000);
</script>
'''

# --- টেমপ্লেটস ---

INDEX_HTML = GLOBAL_CSS + '''
<!DOCTYPE html>
<html>
<head><meta name="viewport" content="width=device-width, initial-scale=1"><title>{{ site_name }}</title></head>
<body>
    ''' + POPUP_SNIPPET + '''
    <div class="notice-bar" style="background: {{ notice.bg_color }}; color: {{ notice.color }}; font-size: {{ notice.size }}px;">{{ notice.text }}</div>
    <div style="padding: 20px; text-align: center; font-size: 24px; font-weight: 900; color: var(--primary);">{{ site_name }}</div>
    <div class="search-box"><form action="{{ request.path }}" method="GET"><input type="text" name="q" class="search-input" placeholder="Search..." value="{{ q }}"></form></div>
    
    {% if page_type == 'home' and not q %}
    <div class="slider-wrap"><div class="slider" id="mainSlider">
        {% for s in slider_items %}<a href="/details/{{ s['_id']|string }}" class="slide-item"><div class="m-badge" style="background: {{ s['badge_color'] }};">{{ s['badge_text'] }}</div><img src="{{ s['poster'] }}"><div class="slide-info">{{ s['title'] }}</div></a>{% endfor %}
    </div></div>
    {% endif %}

    <div class="section-head">{{ section_title }}</div>
    <div class="grid">
        {% for item in contents %}<a href="/details/{{ item['_id']|string }}" class="card"><div class="m-badge" style="background: {{ item['badge_color'] }};">{{ item['badge_text'] }}</div><img src="{{ item['poster'] }}"><div class="card-title">{{ item['title'] }}</div></a>{% endfor %}
    </div>

    <div class="bottom-nav">
        <a href="/" class="nav-link {{ 'active' if page_type=='home' }}">🏠<br>Home</a>
        <a href="/movies" class="nav-link {{ 'active' if page_type=='movies' }}">🎬<br>Movies</a>
        <a href="/drama" class="nav-link {{ 'active' if page_type=='drama' }}">📺<br>Drama</a>
    </div>
</body>
</html>
'''

DETAILS_HTML = GLOBAL_CSS + '''
<!DOCTYPE html>
<html>
<head><meta name="viewport" content="width=device-width, initial-scale=1"><title>{{ item['title'] }}</title></head>
<body>
    <div class="dt-container" style="padding: 20px; max-width: 800px; margin: auto; margin-bottom: 100px;">
        <img src="{{ item['poster'] }}" style="width: 100%; border-radius: 15px; border: 1px solid #333;">
        <h1 style="color: var(--primary); margin-top: 15px;">{{ item['title'] }}</h1>
        
        <div class="int-box">
            <form action="/like/{{ item['_id']|string }}" method="POST"><button class="btn-int">👍 {{ item.get('likes', 0) }} Likes</button></form>
            <button class="btn-int" onclick="document.getElementById('c-sec').scrollIntoView();">💬 {{ item.get('comments', [])|length }} Comments</button>
            <form action="/share/{{ item['_id']|string }}" method="POST"><button class="btn-int">🔗 {{ item.get('shares', 0) }} Shares</button></form>
        </div>

        <div style="background: #111; padding: 20px; border-radius: 10px; margin: 20px 0;">
            <h3 style="margin:0 0 10px 0;">Download Links</h3>
            {% for l in item['links'] %}<a href="{{ l['url'] }}" target="_blank" style="display:block; background: var(--primary); padding: 12px; border-radius: 8px; text-align:center; font-weight:bold; margin-bottom: 10px;">📥 {{ l['label'] }}</a>{% endfor %}
        </div>

        <div id="c-sec">
            <h3>Comments</h3>
            <form action="/comment/{{ item['_id']|string }}" method="POST">
                <input name="user" placeholder="Your Name" style="width:100%; padding:10px; background:#111; border:1px solid #333; color:#fff; margin-bottom:10px;">
                <textarea name="text" placeholder="Write comment..." style="width:100%; padding:10px; background:#111; border:1px solid #333; color:#fff; height:80px;"></textarea>
                <button style="width:100%; padding:10px; background:#333; color:#fff; border:none; margin-top:5px;">Post Comment</button>
            </form>
            <div style="margin-top:20px;">
                {% for c in item.get('comments', [])[::-1] %}
                <div style="padding:10px; border-bottom:1px solid #222;"><b>{{ c.user }}</b>: {{ c.text }}</div>
                {% endfor %}
            </div>
        </div>
    </div>
    <div class="bottom-nav"><a href="/" class="nav-link">🏠<br>Home</a><a href="/movies" class="nav-link">🎬<br>Movies</a><a href="/drama" class="nav-link">📺<br>Drama</a></div>
</body>
</html>
'''

# --- অ্যাডমিন প্যানেল টেমপ্লেটস ---

ADMIN_LAYOUT = '''
<!DOCTYPE html>
<html>
<head><meta name="viewport" content="width=device-width, initial-scale=1">
<style>
    body { font-family: sans-serif; background: #000; color: #fff; margin: 0; padding: 0; }
    .sidebar { background: #111; width: 220px; height: 100vh; position: fixed; border-right: 1px solid #222; }
    .sidebar a { display: block; padding: 15px 20px; color: #888; text-decoration: none; border-bottom: 1px solid #222; }
    .sidebar a.active { color: #fff; background: #e50914; }
    .main { margin-left: 220px; padding: 25px; }
    @media (max-width: 768px) { .sidebar { width: 100%; height: auto; position: relative; display: flex; overflow-x: auto; } .main { margin-left: 0; } }
    .stat-card { background: #111; padding: 20px; border-radius: 10px; border: 1px solid #222; margin-bottom: 20px; }
    .box { background: #111; padding: 20px; border-radius: 10px; border: 1px solid #222; margin-bottom: 20px; }
    input, select, textarea { width: 100%; padding: 12px; margin: 8px 0; background: #000; border: 1px solid #333; color: #fff; border-radius: 5px; box-sizing: border-box; }
    .btn { background: #e50914; color: #fff; border: none; padding: 12px 20px; border-radius: 5px; cursor: pointer; font-weight: bold; }
    table { width: 100%; border-collapse: collapse; margin-top: 15px; }
    th, td { text-align: left; padding: 12px; border-bottom: 1px solid #222; }
</style>
</head>
<body>
    <div class="sidebar">
        <div style="padding: 20px; font-weight: 900; color: #e50914;">ADMIN PANEL</div>
        <a href="/admin/dashboard" class="{{ 'active' if menu=='dash' }}">📊 Dashboard</a>
        <a href="/admin/manage" class="{{ 'active' if menu=='manage' }}">🎬 Manage Content</a>
        <a href="/admin/settings" class="{{ 'active' if menu=='settings' }}">⚙️ Site Settings</a>
        <a href="/admin/security" class="{{ 'active' if menu=='security' }}">🔒 Admin Security</a>
        <a href="/">🏠 View Site</a>
    </div>
    <div class="main">{% block content %}{% endblock %}</div>
</body>
</html>
'''

DASHBOARD_HTML = '''
{% extends "admin_layout" %}
{% block content %}
<h2>System & Daily Analytics</h2>

<!-- ডাটাবেস ও কন্টেন্ট স্ট্যাটাস -->
<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 25px;">
    <div class="stat-card" style="border-top: 4px solid #007bff;"><h3>Total Movies</h3><p style="font-size: 28px; font-weight: bold; color: #007bff;">{{ total_movies }}</p></div>
    <div class="stat-card" style="border-top: 4px solid #ffc107;"><h3>Total Dramas</h3><p style="font-size: 28px; font-weight: bold; color: #ffc107;">{{ total_dramas }}</p></div>
    <div class="stat-card" style="border-top: 4px solid #28a745;"><h3>DB Storage</h3><p style="font-size: 28px; font-weight: bold; color: #28a745;">{{ db_storage }} MB</p></div>
</div>

<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
    <div class="stat-card"><h3>Daily Views</h3><p style="font-size: 24px;">{{ today_stats.get('views', 0) }}</p></div>
    <div class="stat-card"><h3>Daily Likes</h3><p style="font-size: 24px;">{{ today_stats.get('likes', 0) }}</p></div>
    <div class="stat-card"><h3>Daily Comments</h3><p style="font-size: 24px;">{{ today_stats.get('comments', 0) }}</p></div>
    <div class="stat-card"><h3>Daily Shares</h3><p style="font-size: 24px;">{{ today_stats.get('shares', 0) }}</p></div>
</div>

<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 25px;">
    <div class="box">
        <h3>🔥 Top 10 Viewed Content</h3>
        <table>
            <tr><th>Title</th><th>Views</th></tr>
            {% for i in top_content %}
            <tr><td>{{ i.title }}</td><td>{{ i.get('views', 0) }}</td></tr>
            {% endfor %}
        </table>
    </div>
    <div class="box">
        <h3>🌍 Visitor Countries (Today)</h3>
        <table>
            <tr><th>Country</th><th>Views</th></tr>
            {% for c, v in today_stats.get('countries', {}).items() %}
            <tr><td>{{ c }}</td><td>{{ v }}</td></tr>
            {% endfor %}
        </table>
    </div>
</div>
{% endblock %}
'''

MANAGE_HTML = '''
{% extends "admin_layout" %}
{% block content %}
<div class="box">
    <h3>{% if edit_item %}📝 Edit{% else %}🎬 Add New{% endif %}</h3>
    <form method="POST" action="{% if edit_item %}/admin/update/{{ edit_item['_id'] }}{% else %}/admin/add{% endif %}">
        <input name="title" placeholder="Title" value="{{ edit_item.title if edit_item }}" required>
        <input name="poster" placeholder="Poster URL" value="{{ edit_item.poster if edit_item }}" required>
        <div style="display:flex; gap:10px;">
            <input name="badge_text" placeholder="Badge" value="{{ edit_item.badge_text if edit_item }}" style="flex:2;">
            <input name="badge_color" type="color" value="{{ edit_item.badge_color if edit_item else '#e50914' }}" style="flex:1;">
        </div>
        <select name="category">
            <option value="movie" {{ 'selected' if edit_item and edit_item.category=='movie' }}>Movie</option>
            <option value="drama" {{ 'selected' if edit_item and edit_item.category=='drama' }}>Drama</option>
        </select>
        <div id="links">
            {% if edit_item %}{% for l in edit_item.links %}<div style="display:flex; gap:5px;"><input name="labels[]" value="{{ l.label }}" style="width:30%;"><input name="urls[]" value="{{ l.url }}" style="width:70%;"></div>{% endfor %}
            {% else %}<div style="display:flex; gap:5px;"><input name="labels[]" placeholder="Label" style="width:30%;"><input name="urls[]" placeholder="URL" style="width:70%;"></div>{% endif %}
        </div>
        <button type="button" onclick="addLink()" style="margin: 10px 0;">+ Add More Link</button><br>
        <button class="btn">{% if edit_item %}Update Changes{% else %}Publish Content{% endif %}</button>
    </form>
</div>

<div class="box">
    <h3>📂 Content List</h3>
    <form method="GET"><input name="adm_q" placeholder="Search..." value="{{ adm_q }}"></form>
    <table>
        <tr><th>Title</th><th>Type</th><th>Views</th><th>Action</th></tr>
        {% for i in contents %}
        <tr>
            <td>{{ i.title }}</td><td>{{ i.category }}</td><td>{{ i.get('views', 0) }}</td>
            <td><a href="/admin/manage?edit_id={{ i['_id']|string }}" style="color:cyan;">Edit</a> | <a href="/admin/delete/{{ i['_id']|string }}" style="color:red;">Del</a></td>
        </tr>
        {% endfor %}
    </table>
</div>
<script>function addLink(){ let d=document.createElement('div'); d.style.display='flex'; d.style.gap='5px'; d.innerHTML='<input name="labels[]" placeholder="Label" style="width:30%;"><input name="urls[]" placeholder="URL" style="width:70%;">'; document.getElementById('links').appendChild(d); }</script>
{% endblock %}
'''

SETTINGS_HTML = '''
{% extends "admin_layout" %}
{% block content %}
<div class="box">
    <h3>⚙️ Site Branding</h3>
    <form method="POST" action="/admin/site_name"><input name="site_name" value="{{ site_name }}"><button class="btn">Update Name</button></form>
</div>
<div class="box">
    <h3>📢 Top Notice Bar</h3>
    <form method="POST" action="/admin/update_notice">
        <input name="notice_text" value="{{ notice.text }}">
        <div style="display:flex; gap:10px;">
            <input name="notice_color" type="color" value="{{ notice.color }}">
            <input name="notice_bg" type="color" value="{{ notice.bg_color }}">
            <input name="notice_size" type="number" value="{{ notice.size }}">
        </div>
        <button class="btn">Update Notice</button>
    </form>
</div>
<div class="box">
    <h3>✨ Pop-up Settings</h3>
    <form method="POST" action="/admin/update_popup">
        <input name="popup_text" value="{{ popup.text }}">
        <input name="join_link" value="{{ popup.join_link }}">
        <div style="display:flex; gap:10px;">
            <input name="popup_color" type="color" value="{{ popup.text_color }}">
            <input name="popup_bg" type="color" value="{{ popup.bg_color }}">
            <input name="popup_size" type="number" value="{{ popup.text_size }}">
            <input name="popup_interval" type="number" value="{{ popup.interval_mins }}">
        </div>
        <button class="btn">Update Pop-up</button>
    </form>
</div>
{% endblock %}
'''

SECURITY_HTML = '''
{% extends "admin_layout" %}
{% block content %}
<div class="box">
    <h3>🔒 Change Admin Access</h3>
    <form method="POST" action="/admin/update_auth">
        <label>New Username</label><input name="new_username" required>
        <label>New Password</label><input name="new_password" type="password" required>
        <button class="btn">Save New Credentials</button>
    </form>
</div>
{% endblock %}
'''

# --- ব্যাকেন্ড লজিক ---

@app.route('/')
def home():
    track_visitor()
    track_stat('views')
    q = request.args.get('q', '')
    slider = list(content_col.find().sort("_id", -1).limit(6))
    f = {"title": {"$regex": q, "$options": "i"}} if q else {}
    contents = list(content_col.find(f).sort("_id", -1))
    return render_template_string(INDEX_HTML, page_type='home', slider_items=slider, contents=contents, section_title="🆕 New Uploads", site_name=settings_col.find_one({"key": "site_config"})['name'], q=q, notice=settings_col.find_one({"key": "notice_config"}), popup=settings_col.find_one({"key": "popup_config"}))

@app.route('/movies')
def movies():
    track_stat('views')
    q = request.args.get('q', '')
    f = {'category': 'movie'}
    if q: f['title'] = {"$regex": q, "$options": "i"}
    contents = list(content_col.find(f).sort("_id", -1))
    return render_template_string(INDEX_HTML, page_type='movies', contents=contents, section_title="🎬 Movies", site_name=settings_col.find_one({"key": "site_config"})['name'], q=q, notice=settings_col.find_one({"key": "notice_config"}), popup=settings_col.find_one({"key": "popup_config"}))

@app.route('/drama')
def drama():
    track_stat('views')
    q = request.args.get('q', '')
    f = {'category': 'drama'}
    if q: f['title'] = {"$regex": q, "$options": "i"}
    contents = list(content_col.find(f).sort("_id", -1))
    return render_template_string(INDEX_HTML, page_type='drama', contents=contents, section_title="📺 Drama", site_name=settings_col.find_one({"key": "site_config"})['name'], q=q, notice=settings_col.find_one({"key": "notice_config"}), popup=settings_col.find_one({"key": "popup_config"}))

@app.route('/details/<id>')
def details(id):
    content_col.update_one({"_id": ObjectId(id)}, {"$inc": {"views": 1}})
    item = content_col.find_one({"_id": ObjectId(id)})
    if not item: return redirect('/')
    return render_template_string(DETAILS_HTML, item=item, notice=settings_col.find_one({"key": "notice_config"}))

@app.route('/like/<id>', methods=['POST'])
def like(id):
    content_col.update_one({"_id": ObjectId(id)}, {"$inc": {"likes": 1}})
    track_stat('likes')
    return redirect(f'/details/{id}')

@app.route('/share/<id>', methods=['POST'])
def share(id):
    content_col.update_one({"_id": ObjectId(id)}, {"$inc": {"shares": 1}})
    track_stat('shares')
    return redirect(f'/details/{id}')

@app.route('/comment/<id>', methods=['POST'])
def comment(id):
    user = request.form.get('user', 'Anonymous')
    text = request.form.get('text')
    if text:
        content_col.update_one({"_id": ObjectId(id)}, {"$push": {"comments": {"user": user, "text": text}}})
        track_stat('comments')
    return redirect(f'/details/{id}')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        creds = settings_col.find_one({"key": "admin_auth"})
        if request.form['u'] == creds['username'] and request.form['p'] == creds['password']:
            session['is_admin'] = True
            return redirect('/admin/dashboard')
    return '<body style="background:#000;color:#fff;text-align:center;padding-top:100px;"><h2>Admin</h2><form method="POST"><input name="u" placeholder="User"><br><input name="p" type="password" placeholder="Pass"><br><button type="submit">Login</button></form></body>'

@app.context_processor
def inject_admin_layout():
    return dict(admin_layout=ADMIN_LAYOUT)

@app.route('/admin/dashboard')
def admin_dash():
    if not session.get('is_admin'): return redirect('/login')
    
    # টোটাল কন্টেন্ট কাউন্ট
    total_movies = content_col.count_documents({"category": "movie"})
    total_dramas = content_col.count_documents({"category": "drama"})
    
    # ডাটাবেস স্টোরেজ স্ট্যাটাস (MB তে)
    stats = db.command("dbStats")
    db_storage = round(stats.get('storageSize', 0) / (1024 * 1024), 2)
    
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    today_stats = analytics_col.find_one({"date": today}) or {}
    top_content = list(content_col.find().sort("views", -1).limit(10))
    
    return render_template_string(DASHBOARD_HTML, menu='dash', today_stats=today_stats, 
                                  top_content=top_content, total_movies=total_movies, 
                                  total_dramas=total_dramas, db_storage=db_storage)

@app.route('/admin/manage')
def admin_manage():
    if not session.get('is_admin'): return redirect('/login')
    q = request.args.get('adm_q', '')
    edit_id = request.args.get('edit_id')
    edit_item = content_col.find_one({"_id": ObjectId(edit_id)}) if edit_id else None
    contents = list(content_col.find({"title": {"$regex": q, "$options": "i"}}).sort("_id", -1))
    return render_template_string(MANAGE_HTML, menu='manage', contents=contents, edit_item=edit_item, adm_q=q)

@app.route('/admin/settings')
def admin_settings():
    if not session.get('is_admin'): return redirect('/login')
    return render_template_string(SETTINGS_HTML, menu='settings', site_name=settings_col.find_one({"key": "site_config"})['name'], notice=settings_col.find_one({"key": "notice_config"}), popup=settings_col.find_one({"key": "popup_config"}))

@app.route('/admin/security')
def admin_security():
    if not session.get('is_admin'): return redirect('/login')
    return render_template_string(SECURITY_HTML, menu='security')

@app.route('/admin/add', methods=['POST'])
def add():
    ls, us = request.form.getlist('labels[]'), request.form.getlist('urls[]')
    links = [{'label':ls[i], 'url':us[i]} for i in range(len(ls)) if ls[i]]
    content_col.insert_one({'title':request.form.get('title'), 'poster':request.form.get('poster'), 'badge_text':request.form.get('badge_text'), 'badge_color':request.form.get('badge_color'), 'category':request.form.get('category'), 'links':links, 'views': 0, 'likes': 0, 'shares': 0, 'comments': []})
    return redirect('/admin/manage')

@app.route('/admin/update/<id>', methods=['POST'])
def update(id):
    ls, us = request.form.getlist('labels[]'), request.form.getlist('urls[]')
    links = [{'label':ls[i], 'url':us[i]} for i in range(len(ls)) if ls[i]]
    content_col.update_one({"_id":ObjectId(id)}, {"$set": {'title':request.form.get('title'), 'poster':request.form.get('poster'), 'badge_text':request.form.get('badge_text'), 'badge_color':request.form.get('badge_color'), 'category':request.form.get('category'), 'links':links}})
    return redirect('/admin/manage')

@app.route('/admin/site_name', methods=['POST'])
def update_sn():
    settings_col.update_one({"key": "site_config"}, {"$set": {"name": request.form.get('site_name')}})
    return redirect('/admin/settings')

@app.route('/admin/update_notice', methods=['POST'])
def update_notice():
    settings_col.update_one({"key": "notice_config"}, {"$set": {"text": request.form.get('notice_text'), "color": request.form.get('notice_color'), "bg_color": request.form.get('notice_bg'), "size": request.form.get('notice_size')}})
    return redirect('/admin/settings')

@app.route('/admin/update_popup', methods=['POST'])
def update_popup():
    settings_col.update_one({"key": "popup_config"}, {"$set": {"text": request.form.get('popup_text'), "join_link": request.form.get('join_link'), "text_color": request.form.get('popup_color'), "bg_color": request.form.get('popup_bg'), "text_size": request.form.get('popup_size'), "interval_mins": request.form.get('popup_interval')}})
    return redirect('/admin/settings')

@app.route('/admin/update_auth', methods=['POST'])
def update_auth():
    settings_col.update_one({"key": "admin_auth"}, {"$set": {"username": request.form.get('new_username'), "password": request.form.get('new_password')}})
    return redirect('/admin/security')

@app.route('/admin/delete/<id>')
def delete(id):
    if session.get('is_admin'): content_col.delete_one({"_id":ObjectId(id)})
    return redirect('/admin/manage')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
