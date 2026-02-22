import os
import datetime
import requests
from flask import Flask, render_template, render_template_string, request, redirect, url_for, session, jsonify
from pymongo import MongoClient
from bson.objectid import ObjectId
from jinja2 import DictLoader

# --- অ্যাপ কনফিগারেশন ---
app = Flask(__name__)
app.secret_key = "final_perfect_simple_movie_v100_full_unlocked_v2"

# --- ডাটাবেস কানেকশন ---
MONGO_URI = "mongodb+srv://roxiw19528:roxiw19528@cluster0.vl508y4.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client.simple_movie_db
content_col = db.contents
settings_col = db.settings
analytics_col = db.analytics 

# --- ডাটাবেস ইনিশিয়ালাইজেশন ---
def init_db():
    try:
        if not settings_col.find_one({"key": "site_config"}):
            settings_col.insert_one({"key": "site_config", "name": "MovieTok Pro"})
        
        if not settings_col.find_one({"key": "admin_auth"}):
            settings_col.insert_one({"key": "admin_auth", "username": "admin", "password": "1234"})
        
        if not settings_col.find_one({"key": "notice_config"}):
            settings_col.insert_one({
                "key": "notice_config", 
                "text": "Welcome to our site!", 
                "color": "#ffffff", 
                "size": "14", 
                "bg_color": "#e50914"
            })
        
        if not settings_col.find_one({"key": "popup_config"}):
            settings_col.insert_one({
                "key": "popup_config",
                "text": "Join our Telegram channel for latest updates!",
                "bg_color": "#1a1a1a",
                "text_color": "#ffffff",
                "text_size": "18",
                "interval_mins": "5",
                "join_link": "https://t.me/example"
            })
    except:
        pass

init_db()

# --- সঠিক দেশ ও এনালিটিক্স ট্র্যাকিং ---
def track_visitor():
    try:
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        
        # প্রথমে Cloudflare হেডার চেক করবে
        country = request.headers.get('CF-IPCountry')
        
        # যদি ক্লাউডফ্লেয়ার না থাকে বা Unknown আসে, তবে API ব্যবহার করবে
        if not country or country in ['XX', 'Unknown']:
            # ভিজিটরের IP নেওয়া
            ip = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0].strip()
            if ip and ip != '127.0.0.1':
                try:
                    res = requests.get(f"http://ip-api.com/json/{ip}", timeout=2).json()
                    country = res.get('countryCode', 'Unknown')
                except:
                    country = 'Unknown'
            else:
                country = 'Local'

        analytics_col.update_one({"date": today}, {"$inc": {f"countries.{country}": 1, "views": 1}}, upsert=True)
    except:
        pass

def track_stat(stat_type):
    try:
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        analytics_col.update_one({"date": today}, {"$inc": {stat_type: 1}}, upsert=True)
    except:
        pass

# --- ডিজাইন ও টেমপ্লেট ---
GLOBAL_CSS = '''
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;800&display=swap');
    :root { --primary: #e50914; --bg: #000; --card: #141414; }
    body { background: var(--bg); color: #fff; font-family: 'Poppins', sans-serif; margin: 0; padding: 0; overflow-x: hidden; }
    a { text-decoration: none; color: inherit; }
    .notice-bar { width: 100%; padding: 8px 10px; text-align: center; font-weight: 600; position: relative; z-index: 2500; display: block; box-sizing: border-box; }
    
    #popupOverlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.85); z-index: 9999; display: none; align-items: center; justify-content: center; backdrop-filter: blur(5px); }
    .popup-content { width: 90%; max-width: 450px; border-radius: 20px; padding: 35px 20px; position: relative; text-align: center; border: 1px solid #333; box-shadow: 0 10px 40px rgba(0,0,0,0.5); }
    .popup-header { position: absolute; top: 10px; left: 0; width: 100%; display: flex; justify-content: space-between; padding: 0 15px; box-sizing: border-box; }
    .btn-popup-join { background: #0088cc; color: #fff; font-size: 11px; padding: 5px 12px; border-radius: 50px; font-weight: bold; }
    .btn-popup-close { background: #444; color: #fff; font-size: 14px; width: 25px; height: 25px; border-radius: 50%; border: none; cursor: pointer; display: flex; align-items: center; justify-content: center; }
    
    .bottom-nav { position: fixed; bottom: 0; width: 100%; background: rgba(10, 10, 10, 0.98); backdrop-filter: blur(15px); display: flex; justify-content: space-around; padding: 12px 0; border-top: 1px solid #222; z-index: 2000; }
    .nav-link { color: #888; font-size: 12px; font-weight: 600; text-align: center; flex: 1; transition: 0.3s; }
    .nav-link.active { color: var(--primary); text-shadow: 0 0 10px var(--primary); }
    .nav-link span { display: block; font-size: 20px; margin-bottom: 2px; }
    
    .grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; padding: 15px; margin-bottom: 90px; }
    @media(min-width: 768px) { .grid { grid-template-columns: repeat(5, 1fr); } }
    
    .card { position: relative; background: var(--card); border-radius: 10px; overflow: hidden; border: 1px solid #222; transition: 0.3s; height: 100%; display: flex; flex-direction: column; }
    .card img { width: 100%; aspect-ratio: 2/3; object-fit: cover; display: block; }
    .card-title { padding: 10px 8px; font-size: 13px; text-align: center; font-weight: bold; line-height: 1.4; color: #fff; flex-grow: 1; display: flex; align-items: center; justify-content: center; }
    
    .m-badge { position: absolute; top: 8px; left: 8px; padding: 3px 8px; border-radius: 4px; font-size: 10px; font-weight: 800; z-index: 10; text-transform: uppercase; color: #fff; }
    .view-badge { position: absolute; top: 8px; right: 8px; background: rgba(0,0,0,0.6); padding: 3px 6px; border-radius: 4px; font-size: 10px; color: #00ff00; z-index: 10; font-weight: bold; }
    
    .slider-wrap { width: 100%; overflow: hidden; position: relative; margin-top: 10px; }
    .slider { display: flex; transition: transform 0.6s cubic-bezier(0.25, 1, 0.5, 1); }
    .slide-item { min-width: 90%; margin: 0 5%; height: 220px; position: relative; border-radius: 15px; overflow: hidden; border: 1px solid #333; }
    .slide-item img { width: 100%; height: 100%; object-fit: cover; opacity: 0.7; }
    .slide-info { position: absolute; bottom: 0; background: linear-gradient(transparent, #000); width: 100%; padding: 20px; font-size: 18px; font-weight: bold; }
    
    .search-box { padding: 15px; background: #000; position: sticky; top: 0; z-index: 1500; text-align: center; border-bottom: 1px solid #222; }
    .search-input { width: 90%; max-width: 600px; padding: 12px 20px; border-radius: 30px; border: 1px solid #333; background: #1a1a1a; color: #fff; outline: none; }
    .int-box { display: flex; gap: 15px; margin: 15px 0; justify-content: center; }
    .btn-int { background: #1a1a1a; padding: 10px 18px; border-radius: 10px; font-size: 14px; cursor: pointer; border: 1px solid #333; color: #fff; font-weight: bold; display: flex; align-items: center; gap: 5px; }
    .section-head { padding: 15px 20px 0; font-size: 18px; font-weight: 700; color: #eee; border-left: 4px solid var(--primary); margin-left: 15px; }
</style>
'''

POPUP_SNIPPET = '''
<div id="popupOverlay">
    <div class="popup-content" style="background: {{ popup.bg_color }};">
        <div class="popup-header">
            <a href="{{ popup.join_link }}" target="_blank" class="btn-popup-join">🔗 Join Media</a>
            <button class="btn-popup-close" onclick="closePopup()">✕</button>
        </div>
        <div style="color: {{ popup.text_color }}; font-size: {{ popup.text_size }}px; font-weight: 600; line-height: 1.5; margin-top: 15px;">
            {{ popup.text }}
        </div>
    </div>
</div>
<script>
    function showPopup() {
        const lastShown = localStorage.getItem('popup_timer_key');
        const interval = {{ popup.interval_mins }} * 60 * 1000;
        const now = new Date().getTime();
        if (!lastShown || (now - lastShown) > interval) {
            document.getElementById('popupOverlay').style.display = 'flex';
        }
    }
    function closePopup() {
        document.getElementById('popupOverlay').style.display = 'none';
        localStorage.setItem('popup_timer_key', new Date().getTime());
    }
    window.onload = () => { setTimeout(showPopup, 2000); };
</script>
'''

INDEX_HTML = GLOBAL_CSS + '''
<!DOCTYPE html>
<html>
<head><meta name="viewport" content="width=device-width, initial-scale=1"><title>{{ site_name }}</title></head>
<body>
    ''' + POPUP_SNIPPET + '''
    <div class="notice-bar" style="background: {{ notice.bg_color }}; color: {{ notice.color }}; font-size: {{ notice.size }}px;">{{ notice.text }}</div>
    <div style="padding: 20px; text-align: center; font-size: 26px; font-weight: 900; color: var(--primary); text-transform: uppercase;">{{ site_name }}</div>
    <div class="search-box">
        <form action="{{ request.path }}" method="GET">
            <input type="text" name="q" class="search-input" placeholder="Search movies or drama..." value="{{ q }}">
        </form>
    </div>
    {% if page_type == 'home' and not q %}
    <div class="slider-wrap"><div class="slider" id="mainSlider">
        {% for s in slider_items %}<a href="/details/{{ s['_id']|string }}" class="slide-item">
            <div class="m-badge" style="background: {{ s['badge_color'] }};">{{ s['badge_text'] }}</div>
            <img src="{{ s['thumbnail'] if s['thumbnail'] else s['poster'] }}">
            <div class="slide-info">{{ s['title'] }}</div>
        </a>{% endfor %}
    </div></div>
    <script>
        let cur = 0; const sld = document.getElementById('mainSlider'); const total = {{ slider_items|length }};
        if(total > 0) { setInterval(() => { cur = (cur + 1) % total; sld.style.transform = `translateX(-${cur * 100}%)`; }, 4500); }
    </script>
    {% endif %}
    <div class="section-head">{{ section_title }}</div>
    <div class="grid">
        {% for item in contents %}
        <a href="/details/{{ item['_id']|string }}" class="card">
            <div class="m-badge" style="background: {{ item['badge_color'] }};">{{ item['badge_text'] }}</div>
            <div class="view-badge">👁️ {{ item.get('views', 0) }}</div>
            <img src="{{ item['poster'] }}">
            <div class="card-title">{{ item['title'] }}</div>
        </a>
        {% endfor %}
    </div>
    <div class="bottom-nav">
        <a href="/" class="nav-link {{ 'active' if page_type=='home' }}"><span>🏠</span>Home</a>
        <a href="/movies" class="nav-link {{ 'active' if page_type=='movies' }}"><span>🎬</span>Movies</a>
        <a href="/drama" class="nav-link {{ 'active' if page_type=='drama' }}"><span>📺</span>Drama</a>
    </div>
</body>
</html>
'''

DETAILS_HTML = GLOBAL_CSS + '''
<!DOCTYPE html>
<html>
<head><meta name="viewport" content="width=device-width, initial-scale=1"><title>{{ item['title'] }}</title></head>
<body>
    <div class="notice-bar" style="background: {{ notice.bg_color }}; color: {{ notice.color }}; font-size: {{ notice.size }}px;">{{ notice.text }}</div>
    <div style="padding: 20px; max-width: 800px; margin: auto; margin-bottom: 100px;">
        <img src="{{ item['thumbnail'] if item['thumbnail'] else item['poster'] }}" style="width: 100%; border-radius: 15px; border: 1px solid #333; box-shadow: 0 10px 30px rgba(0,0,0,0.5);">
        <h1 style="color: var(--primary); margin: 25px 0 10px; font-size: 28px;">{{ item['title'] }}</h1>
        <div style="color:#888; margin-bottom: 15px; font-size:14px;">👁️ Total Views: {{ item.get('views', 0) }}</div>
        <div class="int-box">
            <form action="/like/{{ item['_id']|string }}" method="POST"><button class="btn-int">👍 {{ item.get('likes', 0) }}</button></form>
            <button class="btn-int" onclick="document.getElementById('comments').scrollIntoView();">💬 {{ item.get('comments', [])|length }}</button>
            <button class="btn-int" onclick="copyShare()">🔗 <span id="shTxt">Share</span></button>
        </div>
        <div style="background: #111; padding: 25px; border-radius: 15px; border: 1px solid #222; margin-top: 25px;">
            <h3 style="margin-top: 0; color: #888;">📥 Watch / Download Links</h3>
            {% for l in item['links'] %}<a href="{{ l['url'] }}" target="_blank" style="display:block; background: var(--primary); color:#fff; padding: 15px; border-radius: 10px; text-align:center; font-weight:bold; margin-bottom: 12px; font-size: 16px;">📥 {{ l['label'] }}</a>{% endfor %}
        </div>
        <div id="comments" style="margin-top: 40px;">
            <h3>Comments</h3>
            <form action="/comment/{{ item['_id']|string }}" method="POST">
                <input name="user" placeholder="Your Name" style="width:100%; padding:12px; background:#111; border:1px solid #333; color:#fff; border-radius:8px; margin-bottom:12px;" required>
                <textarea name="text" placeholder="Write a comment..." style="width:100%; padding:12px; background:#111; border:1px solid #333; color:#fff; border-radius:8px; height:80px; font-family:inherit;" required></textarea>
                <button style="width:100%; padding:12px; background:#333; color:#fff; border:none; border-radius:8px; margin-top:10px; cursor:pointer; font-weight:bold;">Post Comment</button>
            </form>
            <div style="margin-top: 25px; border-top: 1px solid #222;">
                {% for c in item.get('comments', [])[::-1] %}
                <div style="padding: 12px; border-bottom: 1px solid #111;"><strong>{{ c.user }}</strong>: {{ c.text }}</div>
                {% endfor %}
            </div>
        </div>
    </div>
    <script>
        function copyShare() {
            const url = window.location.href;
            navigator.clipboard.writeText(url).then(() => {
                document.getElementById('shTxt').innerText = "Copied!";
                fetch('/share/{{ item["_id"]|string }}', { method: 'POST' });
                setTimeout(() => { document.getElementById('shTxt').innerText = "Share"; }, 2000);
            }).catch(err => { alert("Copy failed"); });
        }
    </script>
    <div class="bottom-nav">
        <a href="/" class="nav-link"><span>🏠</span>Home</a>
        <a href="/movies" class="nav-link"><span>🎬</span>Movies</a>
        <a href="/drama" class="nav-link"><span>📺</span>Drama</a>
    </div>
</body>
</html>
'''

ADMIN_LAYOUT = '''
<!DOCTYPE html>
<html>
<head><meta name="viewport" content="width=device-width, initial-scale=1">
<style>
    body { font-family: sans-serif; background: #000; color: #fff; margin: 0; padding: 0; }
    .sidebar { background: #111; width: 240px; height: 100vh; position: fixed; border-right: 1px solid #222; overflow-y: auto; }
    .sidebar a { display: block; padding: 15px 20px; color: #888; text-decoration: none; border-bottom: 1px solid #222; font-size: 14px; }
    .sidebar a.active { color: #fff; background: #e50914; font-weight: bold; }
    .main { margin-left: 240px; padding: 30px; width: calc(100% - 240px); box-sizing: border-box; }
    @media (max-width: 768px) { .sidebar { width: 60px; } .sidebar span { display: none; } .main { margin-left: 60px; width: calc(100% - 60px); } }
    .card-stat { background: #111; padding: 25px; border-radius: 15px; border: 1px solid #222; text-align: center; }
    .box { background: #111; padding: 25px; border-radius: 15px; border: 1px solid #222; margin-bottom: 30px; }
    input, select, textarea { width: 100%; padding: 12px; margin: 8px 0; background: #000; border: 1px solid #333; color: #fff; border-radius: 8px; box-sizing: border-box; }
    .btn { background: #e50914; color: #fff; border: none; padding: 12px 25px; border-radius: 8px; cursor: pointer; font-weight: bold; width: 100%; }
    table { width: 100%; border-collapse: collapse; margin-top: 20px; }
    th, td { text-align: left; padding: 15px; border-bottom: 1px solid #222; font-size: 14px; }
</style>
</head>
<body>
    <div class="sidebar">
        <div style="padding: 25px; font-weight: 900; color: #e50914; font-size: 22px;">MovieTok <span>ADMIN</span></div>
        <a href="/admin/dashboard" class="{{ 'active' if menu=='dash' }}">📊 <span>Dashboard</span></a>
        <a href="/admin/manage" class="{{ 'active' if menu=='manage' }}">🎬 <span>Manage Content</span></a>
        <a href="/admin/settings" class="{{ 'active' if menu=='settings' }}">⚙️ <span>Site Settings</span></a>
        <a href="/admin/security" class="{{ 'active' if menu=='security' }}">🔒 <span>Admin Security</span></a>
        <a href="/" target="_blank">🏠 <span>Visit Site</span></a>
    </div>
    <div class="main">{% block content %}{% endblock %}</div>
</body>
</html>
'''

DASHBOARD_HTML = '''
{% extends "admin_layout" %}
{% block content %}
<h2>System Analytics</h2>
<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px;">
    <div class="card-stat" style="border-top: 4px solid #007bff;"><h3>Movies</h3><p style="font-size: 28px; font-weight: bold;">{{ total_movies }}</p></div>
    <div class="card-stat" style="border-top: 4px solid #ffc107;"><h3>Dramas</h3><p style="font-size: 28px; font-weight: bold;">{{ total_dramas }}</p></div>
    <div class="card-stat" style="border-top: 4px solid #e50914;"><h3>Views (Today)</h3><p style="font-size: 28px; font-weight: bold;">{{ today_stats.get('views', 0) }}</p></div>
</div>
<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 25px;">
    <div class="box">
        <h3>🔥 Top 10 Popular Content</h3>
        <table>
            <tr><th>Title</th><th>Total Views</th></tr>
            {% for i in top_content %}
            <tr><td>{{ i.title }}</td><td>{{ i.get('views', 0) }}</td></tr>
            {% endfor %}
        </table>
    </div>
    <div class="box">
        <h3>🌍 Visitor Countries (Today)</h3>
        <table>
            <tr><th>Country</th><th>Views</th></tr>
            {% if today_stats.get('countries') %}
                {% for c, v in today_stats.get('countries').items() %}
                <tr><td>{{ c }}</td><td>{{ v }}</td></tr>
                {% endfor %}
            {% else %}
                <tr><td colspan="2">No data yet</td></tr>
            {% endif %}
        </table>
    </div>
</div>
{% endblock %}
'''

MANAGE_HTML = '''
{% extends "admin_layout" %}
{% block content %}
<div class="box">
    <h3>{% if edit_item %}📝 Edit Item{% else %}🎬 Add New Content{% endif %}</h3>
    <form method="POST" action="{% if edit_item %}/admin/update/{{ edit_item['_id'] }}{% else %}/admin/add{% endif %}">
        <label>Title</label>
        <input name="title" placeholder="Title" value="{{ edit_item.title if edit_item }}" required>
        <input name="poster" placeholder="Poster URL (Portrait/Vertical)" value="{{ edit_item.poster if edit_item }}" required>
        <input name="thumbnail" placeholder="Thumbnail URL (Wide for Slider)" value="{{ edit_item.thumbnail if edit_item }}">
        <div style="display:flex; gap:10px;">
            <div style="flex:2;"><label>Badge Text</label><input name="badge_text" placeholder="e.g. 4K, HD" value="{{ edit_item.badge_text if edit_item }}"></div>
            <div style="flex:1;"><label>Badge Color</label><input name="badge_color" type="color" value="{{ edit_item.badge_color if edit_item else '#e50914' }}" style="height:48px;"></div>
        </div>
        <select name="category">
            <option value="movie" {{ 'selected' if edit_item and edit_item.category=='movie' }}>Movie</option>
            <option value="drama" {{ 'selected' if edit_item and edit_item.category=='drama' }}>Drama</option>
        </select>
        <div id="link_container">
            {% if edit_item %}{% for l in edit_item.links %}<div style="display:flex; gap:5px; margin-bottom:5px;"><input name="labels[]" value="{{ l.label }}" style="width:30%;"><input name="urls[]" value="{{ l.url }}" style="width:70%;"></div>{% endfor %}
            {% else %}<div style="display:flex; gap:5px; margin-bottom:5px;"><input name="labels[]" placeholder="Label" style="width:30%;"><input name="urls[]" placeholder="URL" style="width:70%;"></div>{% endif %}
        </div>
        <button type="button" onclick="addLinkRow()" style="background:#333; color:#fff; padding:10px; border:none; border-radius:5px; margin:10px 0; width:100%; cursor:pointer;">+ Add More Download Link</button>
        <button class="btn">{% if edit_item %}Update Changes{% else %}Publish Now{% endif %}</button>
    </form>
</div>
<div class="box">
    <h3>📂 Manage Contents</h3>
    <div style="margin-bottom: 20px;">
        <form method="GET" action="/admin/manage" style="display: flex; gap: 10px;">
            <input name="q_admin" placeholder="সার্চ মুভি বা ড্রামা..." value="{{ q_admin }}" style="margin: 0; flex: 1;">
            <button type="submit" class="btn" style="width: 120px;">Search</button>
        </form>
    </div>
    <table>
        <tr><th>Title</th><th>Type</th><th>Views</th><th>Action</th></tr>
        {% for i in contents %}
        <tr>
            <td>{{ i.title }}</td><td>{{ i.category }}</td><td>{{ i.get('views', 0) }}</td>
            <td><a href="/admin/manage?edit_id={{ i['_id']|string }}" style="color:cyan;">Edit</a> | <a href="/admin/delete/{{ i['_id']|string }}" style="color:red;" onclick="return confirm('Are you sure?')">Delete</a></td>
        </tr>
        {% endfor %}
    </table>
</div>
<script>function addLinkRow(){ let d=document.createElement('div'); d.style.display='flex'; d.style.gap='5px'; d.style.marginBottom='5px'; d.innerHTML='<input name="labels[]" placeholder="Label" style="width:30%;"><input name="urls[]" placeholder="URL" style="width:70%;">'; document.getElementById('link_container').appendChild(d); }</script>
{% endblock %}
'''

SETTINGS_HTML = '''
{% extends "admin_layout" %}
{% block content %}
<div class="box">
    <h3>⚙️ Branding</h3>
    <form method="POST" action="/admin/site_name"><label>Site Name</label><input name="site_name" value="{{ site_name }}"><button class="btn">Update Site Name</button></form>
</div>
<div class="box">
    <h3>📢 Top Notice Bar Settings</h3>
    <form method="POST" action="/admin/update_notice">
        <label>Notice Text</label><input name="notice_text" value="{{ notice.text }}">
        <div style="display:grid; grid-template-columns: 1fr 1fr 1fr; gap:10px;">
            <div><label>Text Color</label><input name="notice_color" type="color" value="{{ notice.color }}"></div>
            <div><label>BG Color</label><input name="notice_bg" type="color" value="{{ notice.bg_color }}"></div>
            <div><label>Size (px)</label><input name="notice_size" type="number" value="{{ notice.size }}"></div>
        </div>
        <button class="btn">Update Notice Bar</button>
    </form>
</div>
<div class="box">
    <h3>✨ Pop-up Notice Settings</h3>
    <form method="POST" action="/admin/update_popup">
        <label>Popup Message</label><input name="popup_text" value="{{ popup.text }}">
        <label>Media Link (Join Button)</label><input name="join_link" value="{{ popup.join_link }}">
        <div style="display:grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap:10px;">
            <div><label>Text Color</label><input name="popup_color" type="color" value="{{ popup.text_color }}"></div>
            <div><label>BG Color</label><input name="popup_bg" type="color" value="{{ popup.bg_color }}"></div>
            <div><label>Size</label><input name="popup_size" type="number" value="{{ popup.text_size }}"></div>
            <div><label>Minutes</label><input name="popup_interval" type="number" value="{{ popup.interval_mins }}"></div>
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
        <button class="btn">Update Credentials</button>
    </form>
</div>
{% endblock %}
'''

# --- JINJA DICT LOADER ---
app.jinja_loader = DictLoader({
    "admin_layout": ADMIN_LAYOUT,
    "dashboard": DASHBOARD_HTML,
    "manage": MANAGE_HTML,
    "settings": SETTINGS_HTML,
    "security": SECURITY_HTML
})

# --- ব্যাকেন্ড ট্র্যাকিং লজিক ---
def track_visitor():
    try:
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        country = request.headers.get('CF-IPCountry')
        if not country or country in ['XX', 'Unknown']:
            ip = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0].strip()
            if ip and ip != '127.0.0.1':
                try:
                    res = requests.get(f"http://ip-api.com/json/{ip}", timeout=2).json()
                    country = res.get('countryCode', 'Unknown')
                except:
                    country = 'Unknown'
            else:
                country = 'Local'
        analytics_col.update_one({"date": today}, {"$inc": {f"countries.{country}": 1, "views": 1}}, upsert=True)
    except:
        pass

def track_stat(stat_type):
    try:
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        analytics_col.update_one({"date": today}, {"$inc": {stat_type: 1}}, upsert=True)
    except:
        pass

# --- ব্যাকেন্ড রাউটস ---

@app.route('/')
def home():
    track_visitor()
    q = request.args.get('q', '')
    slider = list(content_col.find().sort("_id", -1).limit(6))
    f = {"title": {"$regex": q, "$options": "i"}} if q else {}
    contents = list(content_col.find(f).sort("_id", -1))
    return render_template_string(INDEX_HTML, page_type='home', slider_items=slider, contents=contents, section_title="🆕 Recently Added", site_name=settings_col.find_one({"key": "site_config"})['name'], q=q, notice=settings_col.find_one({"key": "notice_config"}), popup=settings_col.find_one({"key": "popup_config"}))

@app.route('/movies')
def movies_cat():
    track_stat('views')
    q = request.args.get('q', '')
    f = {'category': 'movie'}
    if q: f['title'] = {"$regex": q, "$options": "i"}
    contents = list(content_col.find(f).sort("_id", -1))
    return render_template_string(INDEX_HTML, page_type='movies', contents=contents, section_title="🎬 Blockbuster Movies", site_name=settings_col.find_one({"key": "site_config"})['name'], q=q, notice=settings_col.find_one({"key": "notice_config"}), popup=settings_col.find_one({"key": "popup_config"}))

@app.route('/drama')
def drama_cat():
    track_stat('views')
    q = request.args.get('q', '')
    f = {'category': 'drama'}
    if q: f['title'] = {"$regex": q, "$options": "i"}
    contents = list(content_col.find(f).sort("_id", -1))
    return render_template_string(INDEX_HTML, page_type='drama', contents=contents, section_title="📺 Popular Dramas", site_name=settings_col.find_one({"key": "site_config"})['name'], q=q, notice=settings_col.find_one({"key": "notice_config"}), popup=settings_col.find_one({"key": "popup_config"}))

@app.route('/details/<id>')
def details_p(id):
    content_col.update_one({"_id": ObjectId(id)}, {"$inc": {"views": 1}})
    item = content_col.find_one({"_id": ObjectId(id)})
    if not item: return redirect('/')
    return render_template_string(DETAILS_HTML, item=item, notice=settings_col.find_one({"key": "notice_config"}))

@app.route('/like/<id>', methods=['POST'])
def handle_like(id):
    content_col.update_one({"_id": ObjectId(id)}, {"$inc": {"likes": 1}})
    track_stat('likes')
    return redirect(f'/details/{id}')

@app.route('/share/<id>', methods=['POST'])
def handle_share(id):
    content_col.update_one({"_id": ObjectId(id)}, {"$inc": {"shares": 1}})
    track_stat('shares')
    return jsonify({"status": "success"})

@app.route('/comment/<id>', methods=['POST'])
def handle_comment(id):
    u, t = request.form.get('user'), request.form.get('text')
    if t:
        content_col.update_one({"_id": ObjectId(id)}, {"$push": {"comments": {"user": u, "text": t}}})
        track_stat('comments')
    return redirect(f'/details/{id}')

@app.route('/login', methods=['GET', 'POST'])
def login_p():
    if request.method == 'POST':
        creds = settings_col.find_one({"key": "admin_auth"})
        if request.form['u'] == creds['username'] and request.form['p'] == creds['password']:
            session['is_admin'] = True
            return redirect('/admin/dashboard')
    return '<body style="background:#000;color:#fff;text-align:center;padding-top:100px;font-family:sans-serif;"><h2>Admin Login</h2><form method="POST"><input name="u" placeholder="User" style="padding:10px;"><br><br><input name="p" type="password" placeholder="Pass" style="padding:10px;"><br><br><button type="submit" style="padding:10px 30px; background:#e50914; color:#fff; border:none; cursor:pointer;">Login</button></form></body>'

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('is_admin'): return redirect('/login')
    total_m = content_col.count_documents({"category": "movie"})
    total_d = content_col.count_documents({"category": "drama"})
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    t_stats = analytics_col.find_one({"date": today}) or {"views": 0, "likes": 0, "comments": 0, "shares": 0, "countries": {}}
    top_list = list(content_col.find().sort("views", -1).limit(10))
    return render_template("dashboard", menu='dash', today_stats=t_stats, top_content=top_list, total_movies=total_m, total_dramas=total_d)

@app.route('/admin/manage')
def admin_manage():
    if not session.get('is_admin'): return redirect('/login')
    e_id = request.args.get('edit_id')
    q_admin = request.args.get('q_admin', '')
    e_item = content_col.find_one({"_id": ObjectId(e_id)}) if e_id else None
    
    f = {"title": {"$regex": q_admin, "$options": "i"}} if q_admin else {}
    contents = list(content_col.find(f).sort("_id", -1))
    
    return render_template("manage", menu='manage', contents=contents, edit_item=e_item, q_admin=q_admin)

@app.route('/admin/add', methods=['POST'])
def add_new():
    ls, us = request.form.getlist('labels[]'), request.form.getlist('urls[]')
    links = [{'label':ls[i], 'url':us[i]} for i in range(len(ls)) if ls[i]]
    content_col.insert_one({
        'title':request.form.get('title'), 
        'poster':request.form.get('poster'), 
        'thumbnail':request.form.get('thumbnail'),
        'badge_text':request.form.get('badge_text'), 
        'badge_color':request.form.get('badge_color'), 
        'category':request.form.get('category'), 
        'links':links, 
        'views': 0, 'likes': 0, 'shares': 0, 'comments': []
    })
    return redirect('/admin/manage')

@app.route('/admin/update/<id>', methods=['POST'])
def update_item(id):
    ls, us = request.form.getlist('labels[]'), request.form.getlist('urls[]')
    links = [{'label':ls[i], 'url':us[i]} for i in range(len(ls)) if ls[i]]
    content_col.update_one({"_id":ObjectId(id)}, {"$set": {
        'title':request.form.get('title'), 
        'poster':request.form.get('poster'), 
        'thumbnail':request.form.get('thumbnail'),
        'badge_text':request.form.get('badge_text'), 
        'badge_color':request.form.get('badge_color'), 
        'category':request.form.get('category'), 
        'links':links
    }})
    return redirect('/admin/manage')

@app.route('/admin/delete/<id>')
def delete_item(id):
    if session.get('is_admin'): content_col.delete_one({"_id":ObjectId(id)})
    return redirect('/admin/manage')

@app.route('/admin/site_name', methods=['POST'])
def update_sn():
    settings_col.update_one({"key": "site_config"}, {"$set": {"name": request.form.get('site_name')}})
    return redirect('/admin/settings')

@app.route('/admin/update_notice', methods=['POST'])
def update_nt():
    settings_col.update_one({"key": "notice_config"}, {"$set": {"text": request.form.get('notice_text'), "color": request.form.get('notice_color'), "bg_color": request.form.get('notice_bg'), "size": request.form.get('notice_size')}})
    return redirect('/admin/settings')

@app.route('/admin/update_popup', methods=['POST'])
def update_pp():
    settings_col.update_one({"key": "popup_config"}, {"$set": {"text": request.form.get('popup_text'), "join_link": request.form.get('join_link'), "text_color": request.form.get('popup_color'), "bg_color": request.form.get('popup_bg'), "text_size": request.form.get('popup_size'), "interval_mins": request.form.get('popup_interval')}})
    return redirect('/admin/settings')

@app.route('/admin/update_auth', methods=['POST'])
def update_auth():
    settings_col.update_one({"key": "admin_auth"}, {"$set": {"username": request.form.get('new_username'), "password": request.form.get('new_password')}})
    return redirect('/admin/security')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
