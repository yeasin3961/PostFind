import os
from flask import Flask, render_template_string, request, redirect, url_for, session
from pymongo import MongoClient
from bson.objectid import ObjectId

# --- অ্যাপ কনফিগারেশন ---
app = Flask(__name__)
app.secret_key = "final_perfect_simple_movie_v100"

# --- ডাটাবেস কানেকশন ---
# আপনার দেওয়া MongoDB URI সরাসরি ব্যবহার করা হয়েছে
MONGO_URI = "mongodb+srv://roxiw19528:roxiw19528@cluster0.vl508y4.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client.simple_movie_db
content_col = db.contents
settings_col = db.settings

# সাইট সেটিংস ইনিশিয়ালাইজ করা (প্রথমবার রান করার জন্য)
if not settings_col.find_one({"key": "site_config"}):
    settings_col.insert_one({"key": "site_config", "name": "MovieTok Pro"})

# --- প্রিমিয়াম ডিজাইন (Responsive CSS) ---
GLOBAL_CSS = '''
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;800&display=swap');
    :root { --primary: #e50914; --bg: #000; --card: #141414; }
    body { background: var(--bg); color: #fff; font-family: 'Poppins', sans-serif; margin: 0; padding: 0; overflow-x: hidden; }
    a { text-decoration: none; color: inherit; }
    
    /* বটম নেভিগেশন (নিচে থাকবে) */
    .bottom-nav { position: fixed; bottom: 0; width: 100%; background: rgba(10, 10, 10, 0.98); backdrop-filter: blur(15px); 
                  display: flex; justify-content: space-around; padding: 12px 0; border-top: 1px solid #222; z-index: 2000; }
    .nav-link { color: #888; font-size: 13px; font-weight: 600; text-align: center; flex: 1; transition: 0.3s; }
    .nav-link.active { color: var(--primary); text-shadow: 0 0 10px var(--primary); }
    .nav-link span { display: block; font-size: 20px; margin-bottom: 2px; }

    /* অটো স্লাইডার (স্লাইড হবে) */
    .slider-wrap { width: 100%; overflow: hidden; position: relative; margin-top: 10px; }
    .slider { display: flex; transition: transform 0.6s cubic-bezier(0.25, 1, 0.5, 1); }
    .slide-item { min-width: 90%; margin: 0 5%; height: 220px; position: relative; border-radius: 15px; overflow: hidden; border: 1px solid #333; }
    @media(min-width: 768px) { .slide-item { height: 350px; min-width: 96%; margin: 0 2%; } }
    .slide-item img { width: 100%; height: 100%; object-fit: cover; opacity: 0.7; }
    .slide-info { position: absolute; bottom: 0; background: linear-gradient(transparent, #000); width: 100%; padding: 20px; font-size: 18px; font-weight: bold; }

    /* সার্চ বার */
    .search-box { padding: 15px; background: #000; position: sticky; top: 0; z-index: 1500; text-align: center; border-bottom: 1px solid #222; }
    .search-input { width: 90%; max-width: 600px; padding: 12px 20px; border-radius: 30px; border: 1px solid #333; background: #1a1a1a; color: #fff; outline: none; }

    /* গ্রিড লেআউট (রেসপনসিভ) */
    .grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; padding: 15px; margin-bottom: 90px; }
    @media(min-width: 768px) { .grid { grid-template-columns: repeat(4, 1fr); } }
    @media(min-width: 1200px) { .grid { grid-template-columns: repeat(6, 1fr); } }
    
    .card { position: relative; background: var(--card); border-radius: 10px; overflow: hidden; transition: 0.3s; border: 1px solid #222; }
    .card:hover { transform: scale(1.05); border-color: var(--primary); }
    .card img { width: 100%; height: 240px; object-fit: cover; }
    @media(min-width: 768px) { .card img { height: 300px; } }
    .card-title { padding: 8px; font-size: 13px; text-align: center; font-weight: bold; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    
    /* ব্যাজ */
    .m-badge { position: absolute; top: 8px; left: 8px; padding: 3px 8px; border-radius: 4px; font-size: 10px; font-weight: 800; z-index: 10; text-transform: uppercase; }
    .section-head { padding: 15px 20px 0; font-size: 18px; font-weight: 700; color: #eee; border-left: 4px solid var(--primary); margin-left: 15px; }

    /* ডিটেইল পেজ */
    .dt-container { padding: 20px; max-width: 1000px; margin: auto; display: flex; flex-direction: column; align-items: center; margin-bottom: 100px; }
    @media(min-width: 768px) { .dt-container { flex-direction: row; align-items: flex-start; gap: 40px; padding: 50px 20px; } }
    .dt-poster { width: 100%; max-width: 320px; border-radius: 15px; border: 2px solid #333; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }
    .dt-info { flex: 1; text-align: center; }
    @media(min-width: 768px) { .dt-info { text-align: left; } }
    .dt-title { font-size: 28px; font-weight: 800; margin: 15px 0; color: var(--primary); }
    .dl-box { background: #111; padding: 20px; border-radius: 15px; margin-top: 20px; border: 1px solid #222; width: 100%; box-sizing: border-box; }
    .btn-dl { display: block; background: var(--primary); color: #fff; padding: 15px; border-radius: 10px; font-weight: bold; text-align: center; margin-bottom: 10px; transition: 0.3s; }
    .btn-dl:hover { background: #ff1e2b; transform: scale(1.02); }
</style>
'''

# --- টেমপ্লেটস ---

# ১. হোম, মুভি ও ড্রামা পেজ
INDEX_HTML = GLOBAL_CSS + '''
<!DOCTYPE html>
<html>
<head><meta name="viewport" content="width=device-width, initial-scale=1"><title>{{ site_name }}</title></head>
<body>
    <div style="padding: 20px; text-align: center; font-size: 26px; font-weight: 900; color: var(--primary); text-transform: uppercase; letter-spacing: 1px;">{{ site_name }}</div>
    
    <div class="search-box">
        <form action="{{ request.path }}" method="GET">
            <input type="text" name="q" class="search-input" placeholder="Search movies or drama..." value="{{ q }}">
        </form>
    </div>

    {% if page_type == 'home' and not q %}
    <div class="slider-wrap">
        <div class="slider" id="mainSlider">
            {% for s in slider_items %}
            <a href="/details/{{ s['_id']|string }}" class="slide-item">
                <div class="m-badge" style="background: {{ s['badge_color'] }}; color: #fff;">{{ s['badge_text'] }}</div>
                <img src="{{ s['poster'] }}">
                <div class="slide-info"><b>{{ s['title'] }}</b></div>
            </a>
            {% endfor %}
        </div>
    </div>
    <script>
        let cur = 0; const sld = document.getElementById('mainSlider');
        const total = {{ slider_items|length }};
        if(total > 0) {
            setInterval(() => {
                cur = (cur + 1) % total;
                sld.style.transform = `translateX(-${cur * 100}%)`;
            }, 4500);
        }
    </script>
    {% endif %}

    <div class="section-head">{{ section_title }}</div>
    <div class="grid">
        {% for item in contents %}
        <a href="/details/{{ item['_id']|string }}" class="card">
            <div class="m-badge" style="background: {{ item['badge_color'] }}; color: #fff;">{{ item['badge_text'] }}</div>
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

# ২. ডিটেইলস পেজ
DETAILS_HTML = GLOBAL_CSS + '''
<!DOCTYPE html>
<html>
<head><meta name="viewport" content="width=device-width, initial-scale=1"><title>{{ item['title'] }}</title></head>
<body>
    <div class="dt-container">
        <img src="{{ item['poster'] }}" class="dt-poster">
        <div class="dt-info">
            <span class="m-badge" style="position:static; background: {{ item['badge_color'] }}; padding: 5px 12px; display:inline-block;">{{ item['badge_text'] }}</span>
            <h1 class="dt-title">{{ item['title'] }}</h1>
            <p style="color: #888;">Category: {{ item['category']|capitalize }}</p>
            
            <div class="dl-box">
                <h3 style="margin-top: 0; color: #ccc;">Download Links</h3>
                {% for l in item['links'] %}
                <a href="{{ l['url'] }}" target="_blank" class="btn-dl">📥 {{ l['label'] }}</a>
                {% endfor %}
            </div>
            <br><a href="/" style="color: #666; font-weight: bold;">← Back to Home</a>
        </div>
    </div>
    
    <div class="bottom-nav">
        <a href="/" class="nav-link"><span>🏠</span>Home</a>
        <a href="/movies" class="nav-link"><span>🎬</span>Movies</a>
        <a href="/drama" class="nav-link"><span>📺</span>Drama</a>
    </div>
</body>
</html>
'''

# ৩. এডমিন প্যানেল
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
    <div class="box">
        <h3>⚙️ Site Settings</h3>
        <form method="POST" action="/admin/site_name">
            <input name="site_name" value="{{ site_name }}">
            <button class="btn-main">Update Site Name</button>
        </form>
    </div>

    <div class="box">
        <h3>{% if edit_item %}📝 Edit Item{% else %}🎬 Add New{% endif %}</h3>
        <form method="POST" action="{% if edit_item %}/admin/update/{{ edit_item['_id'] }}{% else %}/admin/add{% endif %}">
            <input name="title" placeholder="Title" value="{{ edit_item['title'] if edit_item }}" required>
            <input name="poster" placeholder="Poster URL" value="{{ edit_item['poster'] if edit_item }}" required>
            <div style="display:flex; gap:10px;">
                <input name="badge_text" placeholder="Badge (New, 4K)" value="{{ edit_item['badge_text'] if edit_item }}" style="flex:2;">
                <input name="badge_color" type="color" value="{{ edit_item['badge_color'] if edit_item else '#e50914' }}" style="flex:1; height:45px;">
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
            <button type="button" onclick="addL()" style="width:100%; padding:10px; margin-bottom:10px; cursor:pointer;">+ Add Link</button>
            <button type="submit" class="btn-main btn-green">{% if edit_item %} SAVE CHANGES {% else %} PUBLISH NOW {% endif %}</button>
        </form>
    </div>

    <div class="box">
        <h3>📂 All Contents</h3>
        <form method="GET" action="/admin"><input name="adm_q" class="search-adm" placeholder="Search to edit/delete..." value="{{ adm_q }}"></form>
        {% for i in contents %}
        <div class="row">
            <span>{{ i['title'] }} ({{ i['category'] }})</span>
            <div>
                <a href="/admin/edit/{{ i['_id']|string }}" style="color:blue;">Edit</a> | 
                <a href="/admin/delete/{{ i['_id']|string }}" style="color:red;">Delete</a>
            </div>
        </div>
        {% endfor %}
        <br><a href="/" style="display:block; text-align:center; color:#888;">Logout & Go Home</a>
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

# --- ব্যাকেন্ড লজিক (BACKEND LOGIC) ---

def get_site_name_db():
    c = settings_col.find_one({"key": "site_config"})
    return c['name'] if c else "MovieTok"

@app.route('/')
def home():
    q = request.args.get('q', '')
    slider = list(content_col.find().sort("_id", -1).limit(6))
    f = {"title": {"$regex": q, "$options": "i"}} if q else {}
    contents = list(content_col.find(f).sort("_id", -1))
    st = f"Search Results" if q else "🆕 New Uploads"
    return render_template_string(INDEX_HTML, page_type='home', slider_items=slider, contents=contents, section_title=st, site_name=get_site_name_db(), q=q)

@app.route('/movies')
def movies_cat():
    q = request.args.get('q', '')
    f = {'category': 'movie'}
    if q: f['title'] = {"$regex": q, "$options": "i"}
    contents = list(content_col.find(f).sort("_id", -1))
    return render_template_string(INDEX_HTML, page_type='movies', contents=contents, section_title="🎬 Blockbuster Movies", site_name=get_site_name_db(), q=q)

@app.route('/drama')
def drama_cat():
    q = request.args.get('q', '')
    f = {'category': 'drama'}
    if q: f['title'] = {"$regex": q, "$options": "i"}
    contents = list(content_col.find(f).sort("_id", -1))
    return render_template_string(INDEX_HTML, page_type='drama', contents=contents, section_title="📺 Popular Drama", site_name=get_site_name_db(), q=q)

@app.route('/details/<id>')
def details_p(id):
    try:
        item = content_col.find_one({"_id": ObjectId(id)})
        if not item: return redirect('/')
        return render_template_string(DETAILS_HTML, item=item, site_name=get_site_name_db())
    except:
        return redirect('/')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['u'] == 'admin' and request.form['p'] == '1234':
            session['is_admin'] = True
            return redirect('/admin')
    return '<body style="background:#000;color:#fff;text-align:center;padding-top:100px;font-family:sans-serif;"><h2>Admin Login</h2><form method="POST"><input name="u" placeholder="User"><br><br><input name="p" type="password" placeholder="Pass"><br><br><button type="submit" style="padding:10px 25px; background:#e50914; color:#fff; border:none;">Login</button></form></body>'

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
    content_col.insert_one({
        'title':request.form.get('title'), 'poster':request.form.get('poster'),
        'badge_text':request.form.get('badge_text'), 'badge_color':request.form.get('badge_color'),
        'category':request.form.get('category'), 'links':links
    })
    return redirect('/admin')

@app.route('/admin/update/<id>', methods=['POST'])
def update(id):
    ls, us = request.form.getlist('labels[]'), request.form.getlist('urls[]')
    links = [{'label':ls[i], 'url':us[i]} for i in range(len(ls)) if ls[i]]
    content_col.update_one({"_id":ObjectId(id)}, {"$set": {
        'title':request.form.get('title'), 'poster':request.form.get('poster'),
        'badge_text':request.form.get('badge_text'), 'badge_color':request.form.get('badge_color'),
        'category':request.form.get('category'), 'links':links
    }})
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
