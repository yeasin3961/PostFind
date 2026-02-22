import os, re
from flask import Flask, render_template_string, request, redirect, url_for, session
from pymongo import MongoClient
from bson.objectid import ObjectId

# --- অ্যাপ কনফিগারেশন ---
app = Flask(__name__)
app.secret_key = "absolute_zero_missing_code_final_v8"

# --- ডাটাবেস কানেকশন ---
# আপনার দেওয়া MongoDB URI সরাসরি ব্যবহার করা হয়েছে
MONGO_URI = "mongodb+srv://roxiw19528:roxiw19528@cluster0.vl508y4.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client.movie_pro_database
content_col = db.contents
settings_col = db.settings

# সাইট সেটিংস চেক ও ইনিশিয়ালাইজ করা
if not settings_col.find_one({"key": "site_config"}):
    settings_col.insert_one({"key": "site_config", "name": "MovieTok Pro"})

# --- ইউনিভার্সাল প্লেয়ার লজিক (YouTube, Telegram/Koyeb, MP4 Support) ---
def parse_universal_url(url):
    url = url.strip()
    # YouTube Handler
    if 'youtube.com' in url or 'youtu.be' in url:
        yid = re.search(r'(?:v=|\/)([0-9A-Za-z_-]{11})', url)
        if yid: return f"https://www.youtube.com/embed/{yid.group(1)}?autoplay=1&rel=0&modestbranding=1"
    # Koyeb / Telegram Stream / MKV / Watch Links (Iframe Support)
    elif 'koyeb.app' in url or '/watch/' in url or '.mkv' in url or 'hash=' in url:
        return url
    # Vimeo Handler
    elif 'vimeo.com' in url:
        vid = re.search(r'vimeo\.com\/(\d+)', url)
        if vid: return f"https://player.vimeo.com/video/{vid.group(1)}?autoplay=1"
    
    return url # সরাসরি .mp4 বা অন্য লিঙ্ক

# --- প্রিমিয়াম সিএসএস (Premium Dark UI) ---
GLOBAL_CSS = '''
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;800&display=swap');
    :root { --primary: #ff0050; --secondary: #00f2ea; --bg: #000; --card: #111; }
    body { background: var(--bg); color: #fff; font-family: 'Poppins', sans-serif; margin: 0; padding: 0; overflow-x: hidden; }
    a { text-decoration: none; color: inherit; }
    
    /* Navigation Bottom with Emojis */
    .nav-bottom { position: fixed; bottom: 0; width: 100%; background: rgba(10, 10, 10, 0.95); backdrop-filter: blur(15px); 
                  display: flex; justify-content: space-around; padding: 10px 0; border-top: 1px solid #222; z-index: 1000; }
    .nav-link { color: #888; font-size: 13px; font-weight: 600; text-align: center; flex: 1; transition: 0.3s; }
    .nav-link.active { color: var(--primary); text-shadow: 0 0 10px var(--primary); }
    .nav-link span { display: block; font-size: 20px; margin-bottom: 2px; }

    /* Auto Slider */
    .slider-container { width: 100%; overflow: hidden; position: relative; margin-top: 5px; }
    .slider { display: flex; transition: transform 0.6s cubic-bezier(0.25, 1, 0.5, 1); }
    .slide-item { min-width: 90%; margin: 0 5%; height: 210px; position: relative; border-radius: 20px; overflow: hidden; border: 1px solid #333; }
    .slide-item img { width: 100%; height: 100%; object-fit: cover; opacity: 0.6; }
    .slide-info { position: absolute; bottom: 0; background: linear-gradient(transparent, #000); width: 100%; padding: 20px 15px; }

    /* Grid Layout & Corner Badges */
    .grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; padding: 15px; margin-bottom: 85px; }
    @media(min-width: 768px) { .grid { grid-template-columns: repeat(4, 1fr); } }
    .card { position: relative; background: var(--card); border-radius: 15px; overflow: hidden; border: 1px solid #222; }
    .card img { width: 100%; height: 250px; object-fit: cover; }
    .card-title { padding: 10px; font-size: 13px; text-align: center; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .m-badge { position: absolute; top: 10px; left: 10px; padding: 4px 10px; border-radius: 6px; font-size: 10px; font-weight: 800; z-index: 10; text-transform: uppercase; }

    .section-head { padding: 15px 20px 0; font-size: 18px; font-weight: 700; border-left: 4px solid var(--primary); margin-left: 10px; color: #eee; }
</style>
'''

# --- টেমপ্লেটস (Templates) ---

# ১. হোম, মুভি ও ড্রামা পেজ
INDEX_HTML = GLOBAL_CSS + '''
<!DOCTYPE html>
<html lang="en">
<head><meta name="viewport" content="width=device-width, initial-scale=1"><title>{{ site_name }}</title></head>
<body>
    <div style="padding: 20px; text-align: center; font-size: 25px; font-weight: 900; color: var(--primary); letter-spacing: 1px; text-transform: uppercase;">{{ site_name }}</div>
    
    {% if page_type == 'home' %}
    <div class="slider-container">
        <div class="slider" id="mainSlider">
            {% for s in slider_items %}
            <a href="/watch/{{ s['_id'] }}" class="slide-item">
                <div class="m-badge" style="background: {{ s['badge_color'] }}; color: #fff;">{{ s['badge_text'] }}</div>
                <img src="{{ s['poster'] }}">
                <div class="slide-info"><b style="font-size: 18px;">{{ s['title'] }}</b></div>
            </a>
            {% endfor %}
        </div>
    </div>
    <script>
        let cur = 0;
        const sld = document.getElementById('mainSlider');
        setInterval(() => {
            cur = (cur + 1) % {{ slider_items|length }};
            sld.style.transform = `translateX(-${cur * 100}%)`;
        }, 4000);
    </script>
    {% endif %}

    <div class="section-head">{{ section_title }}</div>
    <div class="grid">
        {% for item in contents %}
        <a href="/watch/{{ item['_id'] }}" class="card">
            <div class="m-badge" style="background: {{ item['badge_color'] }}; color: #fff;">{{ item['badge_text'] }}</div>
            <img src="{{ item['poster'] }}">
            <div class="card-title">{{ item['title'] }}</div>
        </a>
        {% endfor %}
    </div>

    <div class="nav-bottom">
        <a href="/" class="nav-link {{ 'active' if page_type=='home' }}"><span>🏠</span>Home</a>
        <a href="/movies" class="nav-link {{ 'active' if page_type=='movies' }}"><span>🎬</span>Movies</a>
        <a href="/drama" class="nav-link {{ 'active' if page_type=='drama' }}"><span>📺</span>Drama</a>
    </div>
</body>
</html>
'''

# ২. ওয়াচ পেজ (টিকটক স্টাইল ভার্টিক্যাল ফিড)
WATCH_HTML = '''
<!DOCTYPE html>
<html>
<head><meta name="viewport" content="width=device-width, initial-scale=1">
<style>
    body, html { margin: 0; padding: 0; height: 100%; overflow: hidden; background: #000; font-family: sans-serif; }
    .feed { height: 100vh; overflow-y: scroll; scroll-snap-type: y mandatory; scrollbar-width: none; }
    .v-unit { height: 100vh; width: 100%; scroll-snap-align: start; position: relative; display: flex; align-items: center; }
    iframe, video { width: 100%; height: 100%; border: none; background: #000; }
    .ui-data { position: absolute; bottom: 100px; left: 20px; z-index: 10; pointer-events: none; text-shadow: 2px 2px 10px #000; }
    .sidebar { position: absolute; right: 15px; bottom: 150px; display: flex; flex-direction: column; gap: 15px; z-index: 20; }
    .btn-link { background: #ff0050; color: #fff; border: none; padding: 12px 10px; border-radius: 12px; font-weight: bold; cursor: pointer; font-size: 11px; min-width: 65px; box-shadow: 0 5px 15px rgba(0,0,0,0.5); }
    .back { position: absolute; top: 25px; left: 20px; font-size: 24px; color: white; z-index: 100; text-decoration: none; background: rgba(0,0,0,0.4); width: 45px; height: 45px; display: flex; align-items: center; justify-content: center; border-radius: 50%; }
</style>
</head>
<body>
    <a href="/" class="back">✕</a>
    <div class="feed">
        {{ render_player(current) }}
        {% for item in others %} {{ render_player(item) }} {% endfor %}
    </div>

    {% macro render_player(item) %}
    <div class="v-unit">
        {% set play_url = get_embed(item['links'][0]['url']) %}
        {# প্লেয়ার ডিসিশন লজিক #}
        {% if 'koyeb.app' in play_url or 'watch' in play_url or 'youtube' in play_url or '.mkv' in play_url %}
            <iframe id="frame-{{ item['_id'] }}" src="{{ play_url }}" allow="autoplay; fullscreen"></iframe>
        {% else %}
            <video id="vid-{{ item['_id'] }}" src="{{ play_url }}" loop playsinline muted autoplay onclick="this.paused?this.play():this.pause()"></video>
        {% endif %}
        
        <div class="ui-data">
            <span style="background:{{ item['badge_color'] }}; padding:3px 10px; border-radius:5px; font-size:10px; font-weight:bold; text-transform:uppercase;">{{ item['badge_text'] }}</span>
            <h2 style="margin: 10px 0; color: #fff;">{{ item['title'] }}</h2>
        </div>
        
        <div class="sidebar">
            {% for l in item['links'] %}
            <button class="btn-link" onclick="updateV('{{ item['_id'] }}', '{{ l['url'] }}')">{{ l['label'] }}</button>
            {% endfor %}
        </div>
    </div>
    {% endmacro %}

    <script>
        function updateV(id, raw) {
            const f = document.getElementById('frame-'+id);
            const v = document.getElementById('vid-'+id);
            let u = raw;
            if(raw.includes('youtube.com') || raw.includes('youtu.be')) {
                let y = raw.match(/(?:v=|\\/)([0-9A-Za-z_-]{11})/);
                if(y) u = "https://www.youtube.com/embed/" + y[1] + "?autoplay=1";
            }
            if(f) f.src = u;
            if(v) { v.src = u; v.play(); }
        }
        const obs = new IntersectionObserver((es) => {
            es.forEach(e => { if(e.target.tagName === 'VIDEO') { if(e.isIntersecting) e.target.play(); else e.target.pause(); } });
        }, { threshold: 0.6 });
        document.querySelectorAll('video').forEach(v => obs.observe(v));
    </script>
</body>
</html>
'''

# ৩. এডমিন প্যানেল
ADMIN_HTML = '''
<!DOCTYPE html>
<html>
<head><meta name="viewport" content="width=device-width, initial-scale=1">
<style>
    body { font-family: sans-serif; background: #f0f2f5; padding: 20px; }
    .container { max-width: 700px; margin: auto; }
    .box { background: #fff; padding: 25px; border-radius: 15px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); margin-bottom: 25px; }
    input, select { width: 100%; padding: 12px; margin: 8px 0; border: 1px solid #ddd; border-radius: 8px; box-sizing: border-box; }
    .btn-main { background: #000; color: #fff; border: none; padding: 15px; width: 100%; border-radius: 8px; font-weight: bold; cursor: pointer; margin-top: 10px; }
    .btn-green { background: #28a745; }
    .row { display: flex; justify-content: space-between; align-items: center; padding: 12px 0; border-bottom: 1px solid #eee; }
    .action-btn { padding: 6px 12px; border-radius: 5px; text-decoration: none; color: #fff; font-size: 12px; margin-left: 5px; }
</style>
</head>
<body>
    <div class="container">
        <div class="box">
            <h3>⚙️ Site Name Settings</h3>
            <form method="POST" action="/admin/site_name">
                <input name="site_name" value="{{ site_name }}" placeholder="Your Website Name">
                <button class="btn-main">Update Name</button>
            </form>
        </div>

        <div class="box">
            <h3>{% if edit_item %}📝 Edit Content {% else %}🎬 Add New Content {% endif %}</h3>
            <form method="POST" action="{% if edit_item %}/admin/update/{{ edit_item['_id'] }}{% else %}/admin/add{% endif %}">
                <input name="title" placeholder="Title Name" value="{{ edit_item['title'] if edit_item }}" required>
                <input name="poster" placeholder="Poster URL" value="{{ edit_item['poster'] if edit_item }}" required>
                <div style="display:flex; gap:10px;">
                    <input name="badge_text" placeholder="Badge (New, 4K, Ep 01)" value="{{ edit_item['badge_text'] if edit_item }}" style="flex:2;">
                    <input name="badge_color" type="color" value="{{ edit_item['badge_color'] if edit_item else '#ff0050' }}" style="flex:1; height:45px; padding:0; border:none; background:none;">
                </div>
                <select name="category">
                    <option value="movie" {{ 'selected' if edit_item and edit_item['category']=='movie' }}>Movie</option>
                    <option value="drama" {{ 'selected' if edit_item and edit_item['category']=='drama' }}>Drama</option>
                </select>
                <div id="link-container">
                    {% if edit_item %}
                        {% for l in edit_item['links'] %}
                        <div style="display:flex; gap:5px; margin-bottom:5px;">
                            <input name="labels[]" value="{{ l['label'] }}" placeholder="Label" style="width:30%;">
                            <input name="urls[]" value="{{ l['url'] }}" placeholder="Video URL" style="width:70%;">
                        </div>
                        {% endfor %}
                    {% else %}
                        <div style="display:flex; gap:5px; margin-bottom:5px;">
                            <input name="labels[]" placeholder="Label (1080p)" style="width:30%;">
                            <input name="urls[]" placeholder="URL" style="width:70%;">
                        </div>
                    {% endif %}
                </div>
                <button type="button" onclick="addL()" style="width:100%; padding:10px; margin-bottom:10px; cursor:pointer; border-radius:8px; border:1px dashed #666;">+ Add More Quality/Episode</button>
                <button type="submit" class="btn-main btn-green">{% if edit_item %} ✅ UPDATE NOW {% else %} 🚀 PUBLISH NOW {% endif %}</button>
            </form>
        </div>

        <div class="box">
            <h3>📂 Contents Management</h3>
            {% for i in contents %}
            <div class="row">
                <span>{{ i['title'] }}</span>
                <div>
                    <a href="/admin/edit/{{ i['_id'] }}" class="action-btn" style="background:#007bff;">Edit</a>
                    <a href="/admin/delete/{{ i['_id'] }}" class="action-btn" style="background:#dc3545;" onclick="return confirm('Delete?')">Delete</a>
                </div>
            </div>
            {% endfor %}
            <br><a href="/" style="display:block; text-align:center; color:#888;">Logout & Go Home</a>
        </div>
    </div>
    <script>
        function addL() {
            const d = document.createElement('div'); d.style.display='flex'; d.style.gap='5px'; d.style.marginBottom='5px';
            d.innerHTML = '<input name="labels[]" placeholder="Label" style="width:30%;"> <input name="urls[]" placeholder="URL" style="width:70%;">';
            document.getElementById('link-container').appendChild(d);
        }
    </script>
</body>
</html>
'''

# --- ব্যাকেন্ড লজিক (BACKEND CORE) ---

@app.context_processor
def utility_processor():
    return dict(get_embed=parse_universal_url)

def get_site_settings():
    c = settings_col.find_one({"key": "site_config"})
    return c['name'] if c else "MovieTok"

@app.route('/')
def home():
    slider = list(content_col.find().sort("_id", -1).limit(6))
    contents = list(content_col.find().sort("_id", -1))
    return render_template_string(INDEX_HTML, page_type='home', slider_items=slider, contents=contents, section_title="🔥 Recently Uploaded", site_name=get_site_settings())

@app.route('/movies')
def movies_page():
    contents = list(content_col.find({'category': 'movie'}).sort("_id", -1))
    return render_template_string(INDEX_HTML, page_type='movies', contents=contents, section_title="🎬 Blockbuster Movies", site_name=get_site_settings())

@app.route('/drama')
def drama_page():
    contents = list(content_col.find({'category': 'drama'}).sort("_id", -1))
    return render_template_string(INDEX_HTML, page_type='drama', contents=contents, section_title="📺 Popular Dramas", site_name=get_site_settings())

@app.route('/watch/<id>')
def watch(id):
    try:
        curr = content_col.find_one({"_id": ObjectId(id)})
        others = list(content_col.find({"_id": {"$ne": ObjectId(id)}}).limit(15))
        return render_template_string(WATCH_HTML, current=curr, others=others)
    except: return redirect('/')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['u'] == 'admin' and request.form['p'] == '1234':
            session['admin_auth'] = True
            return redirect('/admin')
    return '<body style="background:#000; color:#fff; text-align:center; padding-top:100px; font-family:sans-serif;"><h2>Secure Admin Login</h2><form method="POST"><input name="u" placeholder="User" style="padding:10px;"><br><br><input name="p" type="password" placeholder="Pass" style="padding:10px;"><br><br><button type="submit" style="padding:10px 20px; background:#ff0050; border:none; color:#fff;">Login</button></form></body>'

@app.route('/admin')
def admin():
    if not session.get('admin_auth'): return redirect('/login')
    contents = list(content_col.find().sort("_id", -1))
    return render_template_string(ADMIN_HTML, contents=contents, site_name=get_site_settings(), edit_item=None)

@app.route('/admin/edit/<id>')
def edit_p(id):
    if not session.get('admin_auth'): return redirect('/login')
    edit_item = content_col.find_one({"_id": ObjectId(id)})
    contents = list(content_col.find().sort("_id", -1))
    return render_template_string(ADMIN_HTML, contents=contents, site_name=get_site_settings(), edit_item=edit_item)

@app.route('/admin/add', methods=['POST'])
def add():
    ls, us = request.form.getlist('labels[]'), request.form.getlist('urls[]')
    links = [{'label': ls[i], 'url': us[i]} for i in range(len(ls)) if ls[i]]
    content_col.insert_one({
        'title': request.form.get('title'), 'poster': request.form.get('poster'),
        'badge_text': request.form.get('badge_text'), 'badge_color': request.form.get('badge_color'),
        'category': request.form.get('category'), 'links': links
    })
    return redirect('/admin')

@app.route('/admin/update/<id>', methods=['POST'])
def update(id):
    ls, us = request.form.getlist('labels[]'), request.form.getlist('urls[]')
    links = [{'label': ls[i], 'url': us[i]} for i in range(len(ls)) if ls[i]]
    content_col.update_one({"_id": ObjectId(id)}, {"$set": {
        'title': request.form.get('title'), 'poster': request.form.get('poster'),
        'badge_text': request.form.get('badge_text'), 'badge_color': request.form.get('badge_color'),
        'category': request.form.get('category'), 'links': links
    }})
    return redirect('/admin')

@app.route('/admin/site_name', methods=['POST'])
def set_site_name():
    settings_col.update_one({"key": "site_config"}, {"$set": {"name": request.form.get('site_name')}})
    return redirect('/admin')

@app.route('/admin/delete/<id>')
def delete(id):
    if session.get('admin_auth'): content_col.delete_one({"_id": ObjectId(id)})
    return redirect('/admin')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
