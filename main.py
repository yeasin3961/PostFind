import os, re
from flask import Flask, render_template_string, request, redirect, url_for, session
from pymongo import MongoClient
from bson.objectid import ObjectId

# --- APP CONFIGURATION ---
app = Flask(__name__)
app.secret_key = "zero_missing_absolute_final_master_v20"

# --- DATABASE CONNECTION ---
# আপনার দেওয়া MongoDB URI সরাসরি যুক্ত করা হয়েছে
MONGO_URI = "mongodb+srv://roxiw19528:roxiw19528@cluster0.vl508y4.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client.movie_pro_database
content_col = db.contents
settings_col = db.settings

# সাইট সেটিংস ইনিশিয়ালাইজ করা (প্রথমবার রান করার জন্য)
if not settings_col.find_one({"key": "site_config"}):
    settings_col.insert_one({"key": "site_config", "name": "MovieTok Pro"})

# --- UNIVERSAL URL PARSER ---
def parse_url_for_player(url):
    """লিঙ্কটি প্রসেস করে প্লেয়ারের জন্য তৈরি করে"""
    url = url.strip()
    # YouTube লিঙ্ক হলে এমবেড ভার্সনে রূপান্তর
    if 'youtube.com' in url or 'youtu.be' in url:
        yid = re.search(r'(?:v=|\/)([0-9A-Za-z_-]{11})', url)
        if yid: return f"https://www.youtube.com/embed/{yid.group(1)}?autoplay=1&rel=0"
    return url

# --- UI DESIGN (PREMIUM GLOBAL CSS) ---
GLOBAL_CSS = '''
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;800&display=swap');
    :root { --primary: #ff0050; --purple: #9333ea; --bg: #000; --card: #151515; }
    body { background: var(--bg); color: #fff; font-family: 'Poppins', sans-serif; margin: 0; padding: 0; overflow-x: hidden; }
    a { text-decoration: none; color: inherit; }
    
    /* Navigation Bar */
    .nav-bottom { position: fixed; bottom: 0; width: 100%; background: rgba(10, 10, 10, 0.98); backdrop-filter: blur(15px); 
                  display: flex; justify-content: space-around; padding: 12px 0; border-top: 1px solid #222; z-index: 2000; }
    .nav-link { color: #888; font-size: 13px; font-weight: 600; text-align: center; flex: 1; transition: 0.3s; }
    .nav-link.active { color: var(--primary); text-shadow: 0 0 10px var(--primary); }
    .nav-link span { display: block; font-size: 22px; margin-bottom: 2px; }

    /* Search Bar */
    .search-box { padding: 12px; background: #000; position: sticky; top: 0; z-index: 1500; text-align: center; border-bottom: 1px solid #222; }
    .search-input { width: 90%; max-width: 500px; padding: 12px 20px; border-radius: 25px; border: 1px solid #333; background: #1a1a1a; color: #fff; outline: none; font-size: 14px; }
    .search-input:focus { border-color: var(--primary); }

    /* Auto Slider */
    .slider-container { width: 100%; overflow: hidden; position: relative; margin-top: 5px; }
    .slider { display: flex; transition: transform 0.6s cubic-bezier(0.25, 1, 0.5, 1); }
    .slide-item { min-width: 90%; margin: 0 5%; height: 210px; position: relative; border-radius: 20px; overflow: hidden; border: 1px solid #333; }
    .slide-item img { width: 100%; height: 100%; object-fit: cover; opacity: 0.6; }
    .slide-info { position: absolute; bottom: 0; background: linear-gradient(transparent, #000); width: 100%; padding: 25px 15px; }

    /* Grid Layout & Corner Badge */
    .grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; padding: 15px; margin-bottom: 85px; }
    @media(min-width: 768px) { .grid { grid-template-columns: repeat(4, 1fr); } }
    .card { position: relative; background: var(--card); border-radius: 15px; overflow: hidden; border: 1px solid #222; transition: 0.3s; }
    .card img { width: 100%; height: 260px; object-fit: cover; }
    .card-title { padding: 10px; font-size: 13px; text-align: center; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    
    /* Manual Badge */
    .m-badge { position: absolute; top: 10px; left: 10px; padding: 4px 10px; border-radius: 6px; font-size: 10px; font-weight: 800; z-index: 10; text-transform: uppercase; box-shadow: 0 4px 10px rgba(0,0,0,0.5); }
    .section-head { padding: 15px 20px 0; font-size: 18px; font-weight: 700; border-left: 4px solid var(--primary); margin-left: 10px; }
</style>
'''

# --- TEMPLATES ---

# ১. ইউজার পেজ (Home, Movies, Drama - সার্চ সহ)
INDEX_HTML = GLOBAL_CSS + '''
<!DOCTYPE html>
<html>
<head><meta name="viewport" content="width=device-width, initial-scale=1"><title>{{ site_name }}</title></head>
<body>
    <div style="padding: 20px; text-align: center; font-size: 26px; font-weight: 900; color: var(--primary); letter-spacing: 1px; text-transform: uppercase;">{{ site_name }}</div>
    
    <div class="search-box">
        <form action="{{ request.path }}" method="GET">
            <input type="text" name="q" class="search-input" placeholder="Search in {{ page_type }}..." value="{{ q }}">
        </form>
    </div>

    {% if page_type == 'home' and not q %}
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
        const total = {{ slider_items|length }};
        const sld = document.getElementById('mainSlider');
        if (total > 0) {
            setInterval(() => {
                cur = (cur + 1) % total;
                sld.style.transform = `translateX(-${cur * 100}%)`;
            }, 4000);
        }
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

# ২. ওয়াচ পেজ (টিকটক ভার্টিক্যাল ফিড - আপনার দেওয়া স্পেশাল আইফ্রেম ডিজাইন সহ)
WATCH_HTML = '''
<!DOCTYPE html>
<html>
<head><meta name="viewport" content="width=device-width, initial-scale=1">
<style>
    body, html { margin: 0; padding: 0; height: 100%; overflow: hidden; background: #000; font-family: sans-serif; }
    .feed { height: 100vh; overflow-y: scroll; scroll-snap-type: y mandatory; scrollbar-width: none; }
    .v-unit { height: 100vh; width: 100%; scroll-snap-align: start; position: relative; display: flex; align-items: center; justify-content: center; }
    
    /* আপনার দেওয়া সেই নির্দিষ্ট আইফ্রেম কোড স্টাইল */
    .player-box { width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; background: #000; }
    iframe { width: 100%; height: 100%; scrolling: no; border: 3px solid #9333ea; marginwidth: 0; marginheight: 0; allowfullscreen: true; background: #000; }
    
    .ui-data { position: absolute; bottom: 100px; left: 20px; z-index: 10; pointer-events: none; text-shadow: 2px 2px 10px #000; max-width: 80%; }
    .sidebar { position: absolute; right: 15px; bottom: 150px; display: flex; flex-direction: column; gap: 15px; z-index: 20; }
    .btn-link { background: #ff0050; color: #fff; border: none; padding: 12px 10px; border-radius: 12px; font-weight: bold; cursor: pointer; font-size: 11px; min-width: 65px; box-shadow: 0 5px 15px rgba(0,0,0,0.5); }
    .back { position: absolute; top: 25px; left: 20px; font-size: 24px; color: white; z-index: 100; text-decoration: none; background: rgba(0,0,0,0.4); width: 45px; height: 45px; display: flex; align-items: center; justify-content: center; border-radius: 50%; }
</style>
</head>
<body>
    <a href="/" class="back">✕</a>
    <div class="feed">
        {{ render_v(current) }}
        {% for item in others %} {{ render_v(item) }} {% endfor %}
    </div>

    {% macro render_v(item) %}
    <div class="v-unit">
        <div class="player-box">
            {% set play_url = parse_url(item['links'][0]['url']) %}
            <!-- এডমিন প্যানেলের লিঙ্ক আপনার দেওয়া আইফ্রেম কোড অনুযায়ী চলছে -->
            <iframe id="vid-{{ item['_id'] }}" 
                    src="{{ play_url }}" 
                    scrolling="no" 
                    style="border:3px solid #9333ea;" 
                    marginwidth="0" 
                    marginheight="0" 
                    allowfullscreen>
            </iframe>
        </div>
        
        <div class="ui-data">
            <span style="background:{{ item['badge_color'] }}; padding:3px 10px; border-radius:5px; font-size:10px; font-weight:bold; text-transform:uppercase;">{{ item['badge_text'] }}</span>
            <h2 style="margin: 10px 0; color: #fff; font-size: 22px;">{{ item['title'] }}</h2>
        </div>
        
        <div class="sidebar">
            {% for l in item['links'] %}
            <button class="btn-link" onclick="updatePlayer('vid-{{ item[\'_id\'] }}', '{{ l[\'url\'] }}')">{{ l['label'] }}</button>
            {% endfor %}
        </div>
    </div>
    {% endmacro %}

    <script>
        function updatePlayer(id, raw) {
            const player = document.getElementById(id);
            let target = raw;
            if(raw.includes('youtube.com') || raw.includes('youtu.be')) {
                let yid = raw.match(/(?:v=|\\/)([0-9A-Za-z_-]{11})/);
                if(yid) target = "https://www.youtube.com/embed/" + yid[1] + "?autoplay=1";
            }
            player.src = target;
        }
    </script>
</body>
</html>
'''

# ৩. এডমিন প্যানেল (সার্চ, এডিট, ডিলিট এবং সাইট নেম সহ)
ADMIN_HTML = '''
<!DOCTYPE html>
<html>
<head><meta name="viewport" content="width=device-width, initial-scale=1">
<style>
    body { font-family: sans-serif; background: #f4f7f6; padding: 20px; color: #333; }
    .container { max-width: 700px; margin: auto; }
    .box { background: #fff; padding: 25px; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.05); margin-bottom: 25px; }
    input, select { width: 100%; padding: 12px; margin: 8px 0; border: 1px solid #ddd; border-radius: 8px; box-sizing: border-box; }
    .btn-main { background: #000; color: #fff; border: none; padding: 15px; width: 100%; border-radius: 8px; font-weight: bold; cursor: pointer; }
    .btn-green { background: #28a745; color: #fff; }
    .item-row { display: flex; justify-content: space-between; align-items: center; padding: 12px 0; border-bottom: 1px solid #eee; }
    .search-adm { padding: 10px; margin-bottom: 15px; width: 100%; border: 2px solid #000; border-radius: 10px; }
    .action-link { padding: 6px 12px; border-radius: 5px; text-decoration: none; color: white; font-size: 12px; margin-left: 5px; }
</style>
</head>
<body>
    <div class="container">
        <div class="box">
            <h3>⚙️ Site Name Settings</h3>
            <form method="POST" action="/admin/site_name">
                <input name="site_name" value="{{ site_name }}" placeholder="Website Name">
                <button class="btn-main">Save Site Name</button>
            </form>
        </div>

        <div class="box">
            <h3>{% if edit_item %}📝 Edit Content {% else %}🎬 Add New Content {% endif %}</h3>
            <form method="POST" action="{% if edit_item %}/admin/update/{{ edit_item['_id'] }}{% else %}/admin/add{% endif %}">
                <input name="title" placeholder="Title" value="{{ edit_item['title'] if edit_item }}" required>
                <input name="poster" placeholder="Poster URL" value="{{ edit_item['poster'] if edit_item }}" required>
                <div style="display:flex; gap:10px;">
                    <input name="badge_text" placeholder="Badge (New, 4K, Ep 01)" value="{{ edit_item['badge_text'] if edit_item }}" style="flex:2;">
                    <input name="badge_color" type="color" value="{{ edit_item['badge_color'] if edit_item else '#ff0050' }}" style="flex:1; height:45px; background:none; border:none;">
                </div>
                <select name="category">
                    <option value="movie" {{ 'selected' if edit_item and edit_item['category']=='movie' }}>Movie</option>
                    <option value="drama" {{ 'selected' if edit_item and edit_item['category']=='drama' }}>Drama</option>
                </select>
                <div id="link-fields">
                    {% if edit_item %}
                        {% for l in edit_item['links'] %}
                        <div style="display:flex; gap:5px; margin-bottom:5px;">
                            <input name="labels[]" value="{{ l['label'] }}" placeholder="Label" style="width:30%;">
                            <input name="urls[]" value="{{ l['url'] }}" placeholder="Video URL" style="width:70%;">
                        </div>
                        {% endfor %}
                    {% else %}
                        <div style="display:flex; gap:5px; margin-bottom:5px;">
                            <input name="labels[]" placeholder="Label" style="width:30%;">
                            <input name="urls[]" placeholder="URL" style="width:70%;">
                        </div>
                    {% endif %}
                </div>
                <button type="button" onclick="addL()" style="width:100%; padding:10px; margin-bottom:10px; cursor:pointer; border-radius:8px; border:1px dashed #333;">+ Add Link</button>
                <button type="submit" class="btn-main btn-green">{% if edit_item %} ✅ UPDATE NOW {% else %} 🚀 PUBLISH NOW {% endif %}</button>
            </form>
        </div>

        <div class="box">
            <h3>📂 List & Manage Content</h3>
            <form method="GET" action="/admin">
                <input name="adm_q" class="search-adm" placeholder="Search to edit/delete..." value="{{ adm_q }}">
            </form>
            {% for i in contents %}
            <div class="item-row">
                <span>{{ i['title'] }}</span>
                <div>
                    <a href="/admin/edit/{{ i['_id'] }}" class="action-link" style="background:blue;">Edit</a>
                    <a href="/admin/delete/{{ i['_id'] }}" class="action-link" style="background:red;" onclick="return confirm('Delete?')">Delete</a>
                </div>
            </div>
            {% endfor %}
            <br><a href="/" style="display:block; text-align:center; color:#888;">Back to Home</a>
        </div>
    </div>
    <script>
        function addL() {
            const d = document.createElement('div'); d.style.display='flex'; d.style.gap='5px'; d.style.marginBottom='5px';
            d.innerHTML = '<input name="labels[]" placeholder="Label" style="width:30%;"> <input name="urls[]" placeholder="URL" style="width:70%;">';
            document.getElementById('link-fields').appendChild(d);
        }
    </script>
</body>
</html>
'''

# --- BACKEND LOGIC (THE CORE) ---

@app.context_processor
def utility_processor():
    return dict(parse_url=parse_url_for_player)

def get_site_name_db():
    conf = settings_col.find_one({"key": "site_config"})
    return conf['name'] if conf else "MovieTok"

@app.route('/')
def home():
    q = request.args.get('q', '')
    slider = list(content_col.find().sort("_id", -1).limit(6))
    f = {"title": {"$regex": q, "$options": "i"}} if q else {}
    contents = list(content_col.find(f).sort("_id", -1))
    st = f"🔍 Search Results" if q else "🆕 Recently Uploaded"
    return render_template_string(INDEX_HTML, page_type='home', slider_items=slider, contents=contents, section_title=st, site_name=get_site_name_db(), q=q)

@app.route('/movies')
def movies_cat():
    q = request.args.get('q', '')
    f = {'category': 'movie'}
    if q: f['title'] = {"$regex": q, "$options": "i"}
    contents = list(content_col.find(f).sort("_id", -1))
    st = f"🎬 Movies: {q}" if q else "🎬 Blockbuster Movies"
    return render_template_string(INDEX_HTML, page_type='movies', contents=contents, section_title=st, site_name=get_site_name_db(), q=q)

@app.route('/drama')
def drama_cat():
    q = request.args.get('q', '')
    f = {'category': 'drama'}
    if q: f['title'] = {"$regex": q, "$options": "i"}
    contents = list(content_col.find(f).sort("_id", -1))
    st = f"📺 Drama: {q}" if q else "📺 Popular Drama"
    return render_template_string(INDEX_HTML, page_type='drama', contents=contents, section_title=st, site_name=get_site_name_db(), q=q)

@app.route('/watch/<id>')
def watch(id):
    try:
        curr = content_col.find_one({"_id": ObjectId(id)})
        others = list(content_col.find({"_id": {"$ne": ObjectId(id)}}).limit(20))
        return render_template_string(WATCH_HTML, current=curr, others=others)
    except: return redirect('/')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['u'] == 'admin' and request.form['p'] == '1234':
            session['is_admin'] = True
            return redirect('/admin')
    return '<body style="background:#000;color:#fff;text-align:center;padding-top:100px;"><h2>Secure Login</h2><form method="POST"><input name="u" placeholder="User"><br><br><input name="p" type="password" placeholder="Pass"><br><br><button type="submit" style="padding:10px 25px; background:#ff0050; border:none; color:#fff;">Login</button></form></body>'

@app.route('/admin')
def admin():
    if not session.get('is_admin'): return redirect('/login')
    q = request.args.get('adm_q', '')
    f = {"title": {"$regex": q, "$options": "i"}} if q else {}
    contents = list(content_col.find(f).sort("_id", -1))
    return render_template_string(ADMIN_HTML, contents=contents, site_name=get_site_name_db(), edit_item=None, adm_q=q)

@app.route('/admin/edit/<id>')
def edit_p(id):
    if not session.get('is_admin'): return redirect('/login')
    item = content_col.find_one({"_id": ObjectId(id)})
    contents = list(content_col.find().sort("_id", -1))
    return render_template_string(ADMIN_HTML, contents=contents, site_name=get_site_name_db(), edit_item=item, adm_q="")

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
def site_name_update():
    settings_col.update_one({"key": "site_config"}, {"$set": {"name": request.form.get('site_name')}})
    return redirect('/admin')

@app.route('/admin/delete/<id>')
def delete(id):
    if session.get('is_admin'): content_col.delete_one({"_id": ObjectId(id)})
    return redirect('/admin')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
