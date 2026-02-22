import os
from flask import Flask, render_template_string, request, redirect, url_for, session
from pymongo import MongoClient
from bson.objectid import ObjectId

# --- অ্যাপ কনফিগারেশন ---
app = Flask(__name__)
app.secret_key = "simple_movie_download_portal_999"

# --- ডাটাবেস কানেকশন ---
# আপনার দেওয়া MongoDB URI
MONGO_URI = "mongodb+srv://roxiw19528:roxiw19528@cluster0.vl508y4.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client.simple_movie_db
content_col = db.contents
settings_col = db.settings

# সাইট সেটিংস ইনিশিয়ালাইজ করা
if not settings_col.find_one({"key": "site_config"}):
    settings_col.insert_one({"key": "site_config", "name": "MovieDownload Pro"})

# --- প্রিমিয়াম ডার্ক ডিজাইন (CSS) ---
GLOBAL_CSS = '''
<style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap');
    :root { --primary: #e50914; --bg: #141414; --card: #1f1f1f; --text: #ffffff; }
    body { background: var(--bg); color: var(--text); font-family: 'Roboto', sans-serif; margin: 0; padding: 0; }
    a { text-decoration: none; color: inherit; }
    
    /* Header & Navigation */
    header { background: #000; padding: 15px 5%; display: flex; justify-content: space-between; align-items: center; position: sticky; top: 0; z-index: 1000; border-bottom: 1px solid #333; }
    .logo { font-size: 24px; font-weight: bold; color: var(--primary); text-transform: uppercase; }
    nav a { margin-left: 20px; font-weight: 500; font-size: 15px; color: #ccc; transition: 0.3s; }
    nav a:hover, nav a.active { color: #fff; }

    /* Search Bar */
    .search-section { padding: 20px 5%; text-align: center; background: #000; }
    .search-input { width: 80%; max-width: 600px; padding: 12px 20px; border-radius: 5px; border: 1px solid #333; background: #222; color: #fff; outline: none; }

    /* Movie Grid */
    .container { padding: 20px 5%; margin-bottom: 50px; }
    .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 20px; }
    .card { background: var(--card); border-radius: 8px; overflow: hidden; transition: 0.3s; position: relative; border: 1px solid #222; }
    .card:hover { transform: translateY(-5px); border-color: var(--primary); }
    .card img { width: 100%; height: 240px; object-fit: cover; }
    .card-info { padding: 10px; text-align: center; }
    .card-title { font-size: 14px; font-weight: bold; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    
    /* Badge Styles */
    .badge { position: absolute; top: 10px; left: 10px; padding: 3px 8px; border-radius: 4px; font-size: 10px; font-weight: bold; text-transform: uppercase; z-index: 10; }

    /* Details Page */
    .details-container { padding: 30px 5%; display: flex; flex-wrap: wrap; gap: 30px; }
    .details-poster { width: 100%; max-width: 300px; border-radius: 10px; border: 2px solid #333; }
    .details-info { flex: 1; min-width: 300px; }
    .details-title { font-size: 32px; font-weight: bold; margin-bottom: 10px; color: var(--primary); }
    .download-section { margin-top: 30px; background: #1a1a1a; padding: 20px; border-radius: 10px; }
    .dl-btn { display: inline-block; background: var(--primary); color: #fff; padding: 12px 25px; border-radius: 5px; font-weight: bold; margin: 10px 10px 0 0; transition: 0.3s; }
    .dl-btn:hover { background: #b20710; }

    /* Admin Panel Styles */
    .admin-box { background: #fff; color: #333; padding: 25px; border-radius: 10px; max-width: 800px; margin: 30px auto; box-shadow: 0 5px 15px rgba(0,0,0,0.2); }
    .admin-box h3 { border-bottom: 2px solid #eee; padding-bottom: 10px; }
    input, select { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #ddd; border-radius: 5px; box-sizing: border-box; }
    .btn-action { background: #000; color: #fff; border: none; padding: 12px 25px; border-radius: 5px; cursor: pointer; font-weight: bold; }
</style>
'''

# --- টেমপ্লেটস (HTML Templates) ---

# ১. কমন হেডার ও ফুটার পার্ট
HEADER_HTML = '''
<header>
    <a href="/" class="logo">{{ site_name }}</a>
    <nav>
        <a href="/" class="{{ 'active' if page_type == 'home' }}">🏠 Home</a>
        <a href="/movies" class="{{ 'active' if page_type == 'movies' }}">🎬 Movies</a>
        <a href="/drama" class="{{ 'active' if page_type == 'drama' }}">📺 Drama</a>
    </nav>
</header>
<div class="search-section">
    <form action="{{ request.path }}" method="GET">
        <input type="text" name="q" class="search-input" placeholder="Search for movies or drama..." value="{{ q }}">
    </form>
</div>
'''

# ২. হোমপেজ / ক্যাটাগরি গ্রিড
INDEX_HTML = GLOBAL_CSS + HEADER_HTML + '''
<div class="container">
    <h2 style="margin-bottom: 20px; color: #ccc;">{{ section_title }}</h2>
    <div class="grid">
        {% for item in contents %}
        <div class="card">
            <a href="/details/{{ item['_id']|string }}">
                <div class="badge" style="background: {{ item['badge_color'] }}; color: #fff;">{{ item['badge_text'] }}</div>
                <img src="{{ item['poster'] }}" alt="{{ item['title'] }}">
                <div class="card-info">
                    <div class="card-title">{{ item['title'] }}</div>
                </div>
            </a>
        </div>
        {% else %}
        <p>No content found.</p>
        {% endfor %}
    </div>
</div>
'''

# ৩. মুভি ডিটেইলস পেজ (সিম্পল ডাউনলোড ভিউ)
DETAILS_HTML = GLOBAL_CSS + HEADER_HTML + '''
<div class="details-container">
    <img src="{{ item['poster'] }}" class="details-poster">
    <div class="details-info">
        <span class="badge" style="position:relative; background: {{ item['badge_color'] }}; top:0; left:0; display:inline-block; margin-bottom:10px;">{{ item['badge_text'] }}</span>
        <div class="details-title">{{ item['title'] }}</div>
        <p style="color: #aaa; line-height: 1.6;">Category: {{ item['category']|capitalize }}</p>
        <div class="download-section">
            <h3 style="margin-top:0;">Download Links:</h3>
            {% for l in item['links'] %}
            <a href="{{ l['url'] }}" target="_blank" class="dl-btn">⬇️ {{ l['label'] }}</a>
            {% endfor %}
        </div>
        <br><a href="/" style="color: #666;">← Back to Gallery</a>
    </div>
</div>
'''

# ৪. এডমিন ড্যাশবোর্ড
ADMIN_HTML = '''
<!DOCTYPE html>
<html>
<head><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Admin Dashboard</title>
''' + GLOBAL_CSS + '''
</head>
<body style="background: #f4f4f4; color: #333;">
    <div class="admin-box">
        <a href="/logout" style="float:right;">Logout</a>
        <h3>⚙️ Site Settings</h3>
        <form method="POST" action="/admin/site_name">
            <input name="site_name" value="{{ site_name }}" placeholder="Website Name">
            <button class="btn-action">Update Name</button>
        </form>
    </div>

    <div class="admin-box">
        <h3>{% if edit_item %}📝 Edit Movie/Drama {% else %}🎬 Add New Content {% endif %}</h3>
        <form method="POST" action="{% if edit_item %}/admin/update/{{ edit_item['_id'] }}{% else %}/admin/add{% endif %}">
            <input name="title" placeholder="Title" value="{{ edit_item['title'] if edit_item }}" required>
            <input name="poster" placeholder="Poster Image URL" value="{{ edit_item['poster'] if edit_item }}" required>
            <div style="display:flex; gap:10px;">
                <input name="badge_text" placeholder="Badge Text (e.g. 4K, New)" value="{{ edit_item['badge_text'] if edit_item }}" style="flex:2;">
                <input name="badge_color" type="color" value="{{ edit_item['badge_color'] if edit_item else '#e50914' }}" style="flex:1; height:45px;">
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
                        <input name="urls[]" value="{{ l['url'] }}" placeholder="URL" style="width:70%;">
                    </div>
                    {% endfor %}
                {% else %}
                    <div style="display:flex; gap:5px; margin-bottom:5px;">
                        <input name="labels[]" placeholder="Label (e.g. 1080p)" style="width:30%;">
                        <input name="urls[]" placeholder="Link URL" style="width:70%;">
                    </div>
                {% endif %}
            </div>
            <button type="button" onclick="addLink()" style="margin-bottom:15px; cursor:pointer;">+ Add Link</button>
            <button type="submit" class="btn-action" style="background:#28a745; width:100%;">{% if edit_item %} SAVE CHANGES {% else %} PUBLISH NOW {% endif %}</button>
        </form>
    </div>

    <div class="admin-box">
        <h3>📂 Manage All Content</h3>
        <form method="GET" action="/admin"><input name="adm_q" placeholder="Search by name to manage..." value="{{ adm_q }}"></form>
        {% for i in contents %}
        <div style="display:flex; justify-content:space-between; padding:10px 0; border-bottom:1px solid #eee;">
            <span>{{ i['title'] }} ({{ i['category']|capitalize }})</span>
            <div>
                <a href="/admin/edit/{{ i['_id']|string }}" style="color:blue;">Edit</a> | 
                <a href="/admin/delete/{{ i['_id']|string }}" style="color:red;" onclick="return confirm('Delete?')">Delete</a>
            </div>
        </div>
        {% endfor %}
        <br><a href="/" style="display:block; text-align:center;">View Website</a>
    </div>
    <script>
        function addLink() {
            const d = document.createElement('div'); d.style.display='flex'; d.style.gap='5px'; d.style.marginBottom='5px';
            d.innerHTML = '<input name="labels[]" placeholder="Label" style="width:30%;"> <input name="urls[]" placeholder="URL" style="width:70%;">';
            document.getElementById('link-fields').appendChild(d);
        }
    </script>
</body>
</html>
'''

# --- ব্যাকেন্ড লজিক (BACKEND LOGIC) ---

def get_site_name():
    c = settings_col.find_one({"key": "site_config"})
    return c['name'] if c else "MovieTok"

@app.route('/')
def home():
    q = request.args.get('q', '')
    f = {"title": {"$regex": q, "$options": "i"}} if q else {}
    contents = list(content_col.find(f).sort("_id", -1))
    st = f"Search Results for '{q}'" if q else "🔥 New Uploads"
    return render_template_string(INDEX_HTML, page_type='home', contents=contents, section_title=st, site_name=get_site_name(), q=q)

@app.route('/movies')
def movies_p():
    q = request.args.get('q', '')
    f = {'category': 'movie'}
    if q: f['title'] = {"$regex": q, "$options": "i"}
    contents = list(content_col.find(f).sort("_id", -1))
    return render_template_string(INDEX_HTML, page_type='movies', contents=contents, section_title="🎬 Movies", site_name=get_site_name(), q=q)

@app.route('/drama')
def drama_p():
    q = request.args.get('q', '')
    f = {'category': 'drama'}
    if q: f['title'] = {"$regex": q, "$options": "i"}
    contents = list(content_col.find(f).sort("_id", -1))
    return render_template_string(INDEX_HTML, page_type='drama', contents=contents, section_title="📺 Drama", site_name=get_site_name(), q=q)

@app.route('/details/<id>')
def details(id):
    try:
        item = content_col.find_one({"_id": ObjectId(id)})
        return render_template_string(DETAILS_HTML, item=item, site_name=get_site_name(), q="", page_type="details")
    except: return redirect('/')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['u'] == 'admin' and request.form['p'] == '1234':
            session['admin'] = True
            return redirect('/admin')
    return '<body style="background:#000;color:#fff;text-align:center;padding-top:100px;"><h2>Admin Login</h2><form method="POST"><input name="u" placeholder="User"><br><br><input name="p" type="password" placeholder="Pass"><br><br><button type="submit">Login</button></form></body>'

@app.route('/admin')
def admin():
    if not session.get('admin'): return redirect('/login')
    q = request.args.get('adm_q', '')
    f = {"title": {"$regex": q, "$options": "i"}} if q else {}
    contents = list(content_col.find(f).sort("_id", -1))
    return render_template_string(ADMIN_HTML, contents=contents, site_name=get_site_name(), edit_item=None, adm_q=q)

@app.route('/admin/edit/<id>')
def edit_p(id):
    if not session.get('admin'): return redirect('/login')
    item = content_col.find_one({"_id": ObjectId(id)})
    return render_template_string(ADMIN_HTML, contents=list(content_col.find().sort("_id", -1)), site_name=get_site_name(), edit_item=item, adm_q="")

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
    if session.get('admin'): content_col.delete_one({"_id":ObjectId(id)})
    return redirect('/admin')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
