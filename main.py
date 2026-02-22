import os
from flask import Flask, render_template_string, request, redirect, url_for, session
from pymongo import MongoClient
from bson.objectid import ObjectId

# --- অ্যাপ কনফিগারেশন ---
app = Flask(__name__)
app.secret_key = "tik_tok_download_fixed_final_v99"

# --- ডাটাবেস কানেকশন ---
# আপনার দেওয়া MongoDB URI সরাসরি ব্যবহার করা হয়েছে
MONGO_URI = "mongodb+srv://roxiw19528:roxiw19528@cluster0.vl508y4.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client.movie_pro_database
content_col = db.contents
settings_col = db.settings

# সাইট সেটিংস ইনিশিয়ালাইজ করা
if not settings_col.find_one({"key": "site_config"}):
    settings_col.insert_one({"key": "site_config", "name": "MovieTok Pro"})

# --- UI DESIGN (PREMIUM GLOBAL CSS) ---
GLOBAL_CSS = '''
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;800&display=swap');
    :root { --primary: #ff0050; --purple: #9333ea; --bg: #000; --card: #151515; }
    body { background: var(--bg); color: #fff; font-family: 'Poppins', sans-serif; margin: 0; padding: 0; overflow-x: hidden; }
    a { text-decoration: none; color: inherit; display: block; }
    
    /* Bottom Navigation */
    .nav-bottom { position: fixed; bottom: 0; width: 100%; background: rgba(10, 10, 10, 0.98); backdrop-filter: blur(15px); 
                  display: flex; justify-content: space-around; padding: 12px 0; border-top: 1px solid #222; z-index: 2000; }
    .nav-link { color: #888; font-size: 13px; font-weight: 600; text-align: center; flex: 1; transition: 0.3s; }
    .nav-link.active { color: var(--primary); text-shadow: 0 0 10px var(--primary); }
    .nav-link span { display: block; font-size: 22px; margin-bottom: 2px; }

    /* Search Bar */
    .search-box { padding: 12px; background: #000; position: sticky; top: 0; z-index: 1500; text-align: center; border-bottom: 1px solid #222; }
    .search-input { width: 90%; max-width: 500px; padding: 12px 20px; border-radius: 25px; border: 1px solid #333; background: #1a1a1a; color: #fff; outline: none; font-size: 14px; }

    /* Auto Slider */
    .slider-wrap { width: 100%; overflow: hidden; position: relative; margin-top: 5px; }
    .slider { display: flex; transition: transform 0.6s cubic-bezier(0.25, 1, 0.5, 1); }
    .slide-item { min-width: 90%; margin: 0 5%; height: 210px; position: relative; border-radius: 20px; overflow: hidden; border: 1px solid #333; }
    .slide-item img { width: 100%; height: 100%; object-fit: cover; opacity: 0.6; }
    .slide-info { position: absolute; bottom: 0; background: linear-gradient(transparent, #000); width: 100%; padding: 25px 15px; }

    /* Grid & Poster Badge */
    .grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; padding: 15px; margin-bottom: 85px; }
    @media(min-width: 768px) { .grid { grid-template-columns: repeat(4, 1fr); } }
    .card { position: relative; background: var(--card); border-radius: 15px; overflow: hidden; border: 1px solid #222; transition: 0.3s; }
    .card:hover { transform: scale(1.02); }
    .card img { width: 100%; height: 260px; object-fit: cover; }
    .card-title { padding: 10px; font-size: 13px; text-align: center; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    
    .m-badge { position: absolute; top: 10px; left: 10px; padding: 4px 10px; border-radius: 6px; font-size: 10px; font-weight: 800; z-index: 10; text-transform: uppercase; box-shadow: 0 4px 10px rgba(0,0,0,0.5); }
    .section-head { padding: 15px 20px 0; font-size: 18px; font-weight: 700; border-left: 4px solid var(--primary); margin-left: 10px; }
</style>
'''

# --- TEMPLATES ---

# ১. ইনডেক্স পেজ (হোম, মুভি, ড্রামা)
INDEX_HTML = GLOBAL_CSS + '''
<!DOCTYPE html>
<html>
<head><meta name="viewport" content="width=device-width, initial-scale=1"><title>{{ site_name }}</title></head>
<body>
    <div style="padding: 20px; text-align: center; font-size: 26px; font-weight: 900; color: var(--primary); text-transform: uppercase;">{{ site_name }}</div>
    
    <div class="search-box">
        <form action="{{ request.path }}" method="GET">
            <input type="text" name="q" class="search-input" placeholder="Search in {{ page_type }}..." value="{{ q }}">
        </form>
    </div>

    {% if page_type == 'home' and not q %}
    <div class="slider-wrap">
        <div class="slider" id="mainSlider">
            {% for s in slider_items %}
            <a href="/details/{{ s['_id']|string }}" class="slide-item">
                <div class="m-badge" style="background: {{ s['badge_color'] }}; color: #fff;">{{ s['badge_text'] }}</div>
                <img src="{{ s['poster'] }}">
                <div class="slide-info"><b style="font-size: 18px;">{{ s['title'] }}</b></div>
            </a>
            {% endfor %}
        </div>
    </div>
    <script>
        let cur = 0; const sld = document.getElementById('mainSlider');
        const total = {{ slider_items|length }};
        if(total > 1) {
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
        <div class="card">
            <a href="/details/{{ item['_id']|string }}">
                <div class="m-badge" style="background: {{ item['badge_color'] }}; color: #fff;">{{ item['badge_text'] }}</div>
                <img src="{{ item['poster'] }}">
                <div class="card-title">{{ item['title'] }}</div>
            </a>
        </div>
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

# ২. ডিটেইল পেজ (টিকটক সোয়াইপ ডাউনলোড সিস্টেম)
DETAILS_HTML = '''
<!DOCTYPE html>
<html>
<head><meta name="viewport" content="width=device-width, initial-scale=1">
<style>
    body, html { margin: 0; padding: 0; height: 100%; overflow: hidden; background: #000; font-family: 'Poppins', sans-serif; }
    .feed { height: 100vh; overflow-y: scroll; scroll-snap-type: y mandatory; scrollbar-width: none; }
    .feed::-webkit-scrollbar { display: none; }
    .v-unit { height: 100vh; width: 100%; scroll-snap-align: start; position: relative; display: flex; align-items: center; justify-content: center; overflow: hidden; }
    
    .bg-blur { position: absolute; width: 100%; height: 100%; object-fit: cover; filter: blur(30px) brightness(0.3); z-index: 1; transform: scale(1.2); }
    .main-poster { position: relative; width: 85%; max-width: 360px; height: 55%; border-radius: 20px; object-fit: cover; z-index: 2; border: 3px solid #9333ea; box-shadow: 0 15px 40px rgba(147, 51, 234, 0.5); }
    
    .ui-data { position: absolute; bottom: 120px; left: 20px; z-index: 10; text-shadow: 2px 2px 10px #000; max-width: 75%; pointer-events: none; }
    .sidebar { position: absolute; right: 20px; bottom: 120px; display: flex; flex-direction: column; gap: 15px; z-index: 20; }
    
    .btn-dl { background: linear-gradient(45deg, #ff0050, #9333ea); color: #fff; border: none; padding: 15px 20px; border-radius: 15px; font-weight: bold; font-size: 13px; text-align: center; box-shadow: 0 8px 20px rgba(0,0,0,0.6); min-width: 90px; text-transform: uppercase; text-decoration: none; display: inline-block; }
    .btn-dl:active { transform: scale(0.9); }
    
    .back { position: absolute; top: 25px; left: 20px; font-size: 24px; color: white; z-index: 100; background: rgba(0,0,0,0.5); width: 45px; height: 45px; display: flex; align-items: center; justify-content: center; border-radius: 50%; text-decoration: none; border: 1px solid rgba(255,255,255,0.2); }
</style>
</head>
<body>
    <a href="/" class="back">✕</a>
    <div class="feed">
        <!-- প্রথম আইটেম -->
        {{ render_item(current) }}
        
        <!-- সোয়াইপের জন্য অন্যগুলো -->
        {% for item in others %}
            {{ render_item(item) }}
        {% endfor %}
    </div>

    {% macro render_item(item) %}
    <div class="v-unit">
        <img src="{{ item['poster'] }}" class="bg-blur">
        <img src="{{ item['poster'] }}" class="main-poster">
        
        <div class="ui-data">
            <span style="background:{{ item['badge_color'] }}; padding:4px 10px; border-radius:5px; font-size:10px; font-weight:bold; text-transform:uppercase;">{{ item['badge_text'] }}</span>
            <h2 style="margin: 10px 0; color: #fff; font-size: 25px; font-weight: 800; line-height: 1.2;">{{ item['title'] }}</h2>
            <p style="color: #ccc; font-size: 13px;">Scroll down for more or click download below.</p>
        </div>
        
        <div class="sidebar">
            {% for l in item['links'] %}
            <a href="{{ l['url'] }}" target="_blank" class="btn-dl">📥 {{ l['label'] }}</a>
            {% endfor %}
        </div>
    </div>
    {% endmacro %}
</body>
</html>
'''

# ৩. এডমিন ড্যাশবোর্ড
ADMIN_HTML = '''
<!DOCTYPE html>
<html>
<head><meta name="viewport" content="width=device-width, initial-scale=1">
<style>
    body { font-family: sans-serif; background: #f0f2f5; padding: 20px; color: #333; }
    .box { background: #fff; padding: 25px; border-radius: 15px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); margin-bottom: 25px; max-width: 700px; margin: auto; }
    input, select { width: 100%; padding: 12px; margin: 8px 0; border: 1px solid #ddd; border-radius: 8px; box-sizing: border-box; }
    .btn-main { background: #000; color: #fff; border: none; padding: 15px; width: 100%; border-radius: 8px; font-weight: bold; cursor: pointer; }
    .btn-green { background: #28a745; }
    .row { display: flex; justify-content: space-between; align-items: center; padding: 12px 0; border-bottom: 1px solid #eee; }
    .search-adm { padding: 10px; margin-bottom: 15px; width: 100%; border: 2px solid #000; border-radius: 10px; }
</style>
</head>
<body>
    <div class="container">
        <div class="box">
            <h3>⚙️ Site Settings</h3>
            <form method="POST" action="/admin/site_name">
                <input name="site_name" value="{{ site_name }}" placeholder="Site Name">
                <button class="btn-main">Update Site Name</button>
            </form>
        </div>

        <div class="box">
            <h3>{% if edit_item %}📝 Edit{% else %}🎬 Add New{% endif %}</h3>
            <form method="POST" action="{% if edit_item %}/admin/update/{{ edit_item['_id'] }}{% else %}/admin/add{% endif %}">
                <input name="title" placeholder="Title" value="{{ edit_item['title'] if edit_item }}" required>
                <input name="poster" placeholder="Poster URL" value="{{ edit_item['poster'] if edit_item }}" required>
                <div style="display:flex; gap:10px;">
                    <input name="badge_text" placeholder="Badge (New, 4K)" value="{{ edit_item['badge_text'] if edit_item }}" style="flex:2;">
                    <input name="badge_color" type="color" value="{{ edit_item['badge_color'] if edit_item else '#ff0050' }}" style="flex:1; height:45px; border:none; background:none;">
                </div>
                <select name="category">
                    <option value="movie" {{ 'selected' if edit_item and edit_item['category']=='movie' }}>Movie</option>
                    <option value="drama" {{ 'selected' if edit_item and edit_item['category']=='drama' }}>Drama</option>
                </select>
                <div id="links">
                    {% if edit_item %}
                        {% for l in edit_item['links'] %}
                        <div style="display:flex; gap:5px; margin-bottom:5px;"><input name="labels[]" value="{{ l['label'] }}" style="width:30%;"><input name="urls[]" value="{{ l['url'] }}" style="width:70%;"></div>
                        {% endfor %}
                    {% else %}
                        <div style="display:flex; gap:5px; margin-bottom:5px;"><input name="labels[]" placeholder="Label" style="width:30%;"><input name="urls[]" placeholder="Link" style="width:70%;"></div>
                    {% endif %}
                </div>
                <button type="button" onclick="addL()" style="width:100%; padding:10px; margin-bottom:10px; cursor:pointer; border-radius:8px; border:1px dashed #333;">+ Add More Link</button>
                <button type="submit" class="btn-main btn-green">{% if edit_item %} UPDATE NOW {% else %} PUBLISH NOW {% endif %}</button>
            </form>
        </div>

        <div class="box">
            <h3>📂 All Content</h3>
            <form method="GET" action="/admin"><input name="adm_q" class="search-adm" placeholder="Search by title..." value="{{ adm_q }}"></form>
            {% for i in contents %}
            <div class="row">
                <span>{{ i['title'] }}</span>
                <div>
                    <a href="/admin/edit/{{ i['_id']|string }}" style="color:blue;">Edit</a> | 
                    <a href="/admin/delete/{{ i['_id']|string }}" style="color:red;" onclick="return confirm('Delete?')">Delete</a>
                </div>
            </div>
            {% endfor %}
            <br><a href="/" style="display:block; text-align:center; color:#888;">Go Home</a>
        </div>
    </div>
    <script>
        function addL() {
            const d = document.createElement('div'); d.style.display='flex'; d.style.gap='5px'; d.style.marginBottom='5px';
            d.innerHTML = '<input name="labels[]" placeholder="Label" style="width:30%;"> <input name="urls[]" placeholder="URL" style="width:70%;">';
            document.getElementById('links').appendChild(d);
        }
    </script>
</body>
</html>
'''

# --- BACKEND LOGIC ---

def get_site_name_db():
    c = settings_col.find_one({"key": "site_config"})
    return c['name'] if c else "MovieTok"

@app.route('/')
def home():
    q = request.args.get('q', '')
    slider = list(content_col.find().sort("_id", -1).limit(6))
    f = {"title": {"$regex": q, "$options": "i"}} if q else {}
    contents = list(content_col.find(f).sort("_id", -1))
    st = f"Search Results" if q else "🆕 New Arrivals"
    return render_template_string(INDEX_HTML, page_type='home', slider_items=slider, contents=contents, section_title=st, site_name=get_site_name_db(), q=q)

@app.route('/movies')
def movies_p():
    q = request.args.get('q', '')
    f = {'category': 'movie'}
    if q: f['title'] = {"$regex": q, "$options": "i"}
    contents = list(content_col.find(f).sort("_id", -1))
    return render_template_string(INDEX_HTML, page_type='movies', contents=contents, section_title="🎬 Blockbuster Movies", site_name=get_site_name_db(), q=q)

@app.route('/drama')
def drama_p():
    q = request.args.get('q', '')
    f = {'category': 'drama'}
    if q: f['title'] = {"$regex": q, "$options": "i"}
    contents = list(content_col.find(f).sort("_id", -1))
    return render_template_string(INDEX_HTML, page_type='drama', contents=contents, section_title="📺 Popular Drama", site_name=get_site_name_db(), q=q)

@app.route('/details/<id>')
def details_page(id):
    try:
        current_movie = content_col.find_one({"_id": ObjectId(id)})
        if not current_movie: return redirect('/')
        other_movies = list(content_col.find({"_id": {"$ne": ObjectId(id)}}).limit(15))
        return render_template_string(DETAILS_HTML, current=current_movie, others=other_movies)
    except:
        return redirect('/')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['u'] == 'admin' and request.form['p'] == '1234':
            session['is_admin'] = True
            return redirect('/admin')
    return '<body style="background:#000;color:#fff;text-align:center;padding-top:100px;"><h2>Login</h2><form method="POST"><input name="u" placeholder="User"><br><br><input name="p" type="password" placeholder="Pass"><br><br><button type="submit" style="padding:10px 25px;">Login</button></form></body>'

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
    return render_template_string(ADMIN_HTML, contents=list(content_col.find().sort("_id", -1)), site_name=get_site_name_db(), edit_item=item, adm_q="")

@app.route('/admin/add', methods=['POST'])
def add():
    ls, us = request.form.getlist('labels[]'), request.form.getlist('urls[]')
    links = [{'label':ls[i], 'url':us[i]} for i in range(len(ls)) if ls[i]]
    content_col.insert_one({'title':request.form.get('title'), 'poster':request.form.get('poster'), 'badge_text':request.form.get('badge_text'), 'badge_color':request.form.get('badge_color'), 'category':request.form.get('category'), 'links':links})
    return redirect('/admin')

@app.route('/admin/update/<id>', methods=['POST'])
def update(id):
    ls, us = request.form.getlist('labels[]'), request.form.getlist('urls[]')
    links = [{'label':ls[i], 'url':us[i]} for i in range(len(ls)) if ls[i]]
    content_col.update_one({"_id":ObjectId(id)}, {"$set": {'title':request.form.get('title'), 'poster':request.form.get('poster'), 'badge_text':request.form.get('badge_text'), 'badge_color':request.form.get('badge_color'), 'category':request.form.get('category'), 'links':links}})
    return redirect('/admin')

@app.route('/admin/site_name', methods=['POST'])
def update_sn():
    settings_col.update_one({"key": "site_config"}, {"$set": {"name": request.form.get('site_name')}})
    return redirect('/admin')

@app.route('/admin/delete/<id>')
def delete(id):
    if session.get('is_admin'): content_col.delete_one({"_id":ObjectId(id)})
    return redirect('/admin')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
