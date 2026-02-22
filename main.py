import os, re
from flask import Flask, render_template_string, request, redirect, url_for, session
from pymongo import MongoClient
from bson.objectid import ObjectId

# --- APP CONFIGURATION ---
app = Flask(__name__)
app.secret_key = "tik_movie_ultra_secure_999"

# --- MONGODB CONNECTION ---
# আপনার দেওয়া MongoDB URI সরাসরি ব্যবহার করা হয়েছে
MONGO_URI = "mongodb+srv://roxiw19528:roxiw19528@cluster0.vl508y4.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client.movie_database
content_col = db.contents

# --- UNIVERSAL URL PARSER LOGIC ---
def parse_video_url(url):
    """লিঙ্কটি দেখে সঠিক এমবেড ইউআরএল তৈরি করে"""
    url = url.strip()
    # YouTube Handler
    if 'youtube.com' in url or 'youtu.be' in url:
        yid = re.search(r'(?:v=|\/)([0-9A-Za-z_-]{11})', url)
        if yid: return f"https://www.youtube.com/embed/{yid.group(1)}?autoplay=1&rel=0"
    # Vimeo Handler
    elif 'vimeo.com' in url:
        vid = re.search(r'vimeo\.com\/(\d+)', url)
        if vid: return f"https://player.vimeo.com/video/{vid.group(1)}?autoplay=1"
    # Dailymotion Handler
    elif 'dailymotion.com' in url or 'dai.ly' in url:
        did = re.search(r'(?:video\/|ly\/)([0-9A-Za-z]+)', url)
        if did: return f"https://www.dailymotion.com/embed/video/{did.group(1)}?autoplay=1"
    
    return url # সরাসরি MP4 বা অন্য প্লেয়ার লিঙ্ক হলেそのまま থাকবে

# --- HTML & CSS DESIGN (GLOBAL) ---
COMMON_STYLE = '''
<style>
    body { background: #000; color: #fff; font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 0; }
    a { text-decoration: none; color: inherit; }
    
    /* Navigation Bottom */
    .nav-bottom { position: fixed; bottom: 0; width: 100%; background: #111; display: flex; justify-content: space-around; padding: 15px 0; border-top: 1px solid #333; z-index: 1000; }
    .nav-bottom a { color: #888; text-decoration: none; font-size: 14px; font-weight: bold; transition: 0.3s; }
    .nav-bottom a.active { color: #ff0050; }

    /* Poster Corner Badge */
    .card { position: relative; background: #1a1a1a; border-radius: 12px; overflow: hidden; border: 1px solid #222; }
    .corner-badge { position: absolute; top: 10px; left: 10px; padding: 4px 10px; border-radius: 5px; font-size: 11px; font-weight: bold; color: #fff; z-index: 10; text-transform: uppercase; box-shadow: 0 2px 5px rgba(0,0,0,0.5); }
    .badge-movie { background: #ff0050; }
    .badge-drama { background: #00f2ea; color: #000; }

    /* Home Slider */
    .slider { display: flex; overflow-x: auto; scroll-snap-type: x mandatory; gap: 10px; padding: 10px; scrollbar-width: none; }
    .slider::-webkit-scrollbar { display: none; }
    .slide-item { flex: 0 0 85%; height: 210px; scroll-snap-align: center; position: relative; border-radius: 15px; overflow: hidden; border: 1px solid #333; }
    .slide-item img { width: 100%; height: 100%; object-fit: cover; opacity: 0.7; }
    .slide-info { position: absolute; bottom: 0; background: linear-gradient(transparent, #000); width: 100%; padding: 20px 10px; font-size: 18px; }

    /* Grid Layout */
    .grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; padding: 12px; margin-bottom: 80px; }
    @media(min-width: 768px) { .grid { grid-template-columns: repeat(4, 1fr); } }
    .card img { width: 100%; height: 240px; object-fit: cover; }
    .card-title { padding: 10px; font-size: 13px; text-align: center; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    
    .section-title { padding: 10px 15px; font-size: 18px; font-weight: bold; color: #ff0050; border-left: 4px solid #ff0050; margin: 10px 0 5px 10px; }
</style>
'''

# --- PAGES ---

# ১. হোমপেজ, মুভি ও ড্রামা পেজ
INDEX_PAGE = COMMON_STYLE + '''
<!DOCTYPE html>
<html>
<head><meta name="viewport" content="width=device-width, initial-scale=1"><title>MovieTok</title></head>
<body>
    <div style="padding: 15px; text-align: center; font-size: 22px; color: #ff0050; font-weight: bold;">MovieTok</div>
    
    {% if page_type == 'home' %}
        <div class="section-title">Latest Featured</div>
        <div class="slider">
            {% for s in slider_items %}
            <a href="/watch/{{ s['_id'] }}" class="slide-item">
                <div class="corner-badge {{ 'badge-movie' if s['category']=='movie' else 'badge-drama' }}">{{ s['category'] }}</div>
                <img src="{{ s['poster'] }}">
                <div class="slide-info"><b>{{ s['title'] }}</b></div>
            </a>
            {% endfor %}
        </div>
        <div class="section-title">Newest Uploads</div>
    {% else %}
        <div class="section-title">{{ page_type | capitalize }} Collection</div>
    {% endif %}

    <div class="grid">
        {% for item in contents %}
        <a href="/watch/{{ item['_id'] }}" class="card">
            <div class="corner-badge {{ 'badge-movie' if item['category']=='movie' else 'badge-drama' }}">{{ item['category'] }}</div>
            <img src="{{ item['poster'] }}">
            <div class="card-title">{{ item['title'] }}</div>
        </a>
        {% endfor %}
    </div>

    <div class="nav-bottom">
        <a href="/" class="{{ 'active' if page_type=='home' }}">Home</a>
        <a href="/movies" class="{{ 'active' if page_type=='movies' }}">Movies</a>
        <a href="/drama" class="{{ 'active' if page_type=='drama' }}">Drama</a>
    </div>
</body>
</html>
'''

# ২. ডিটেইলস পেজ (টিকটক ভার্টিক্যাল ফিড)
WATCH_PAGE = '''
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body, html { margin: 0; padding: 0; height: 100%; overflow: hidden; background: #000; font-family: sans-serif; color: white; }
        .feed { height: 100vh; overflow-y: scroll; scroll-snap-type: y mandatory; scrollbar-width: none; }
        .v-item { height: 100vh; width: 100%; scroll-snap-align: start; position: relative; display: flex; align-items: center; justify-content: center; }
        iframe, video { width: 100%; height: 100%; border: none; background: #000; }
        .ui { position: absolute; bottom: 85px; left: 15px; z-index: 10; pointer-events: none; text-shadow: 1px 1px 5px #000; }
        .sidebar { position: absolute; right: 10px; bottom: 120px; display: flex; flex-direction: column; gap: 12px; z-index: 20; }
        .q-btn { background: #ff0050; border: none; padding: 12px 10px; border-radius: 10px; color: white; font-weight: bold; cursor: pointer; font-size: 11px; min-width: 60px; box-shadow: 0 0 10px #000; }
        .back-btn { position: absolute; top: 20px; left: 20px; z-index: 100; font-size: 24px; color: white; background: rgba(0,0,0,0.4); padding: 5px 15px; border-radius: 50%; text-decoration: none; }
    </style>
</head>
<body>
    <a href="/" class="back-btn">✕</a>
    <div class="feed">
        {{ video_block(current_item) }}
        {% for item in other_items %}
            {{ video_block(item) }}
        {% endfor %}
    </div>

    {% macro video_block(item) %}
    <div class="v-item">
        {% set final_url = get_embed(item['links'][0]['url']) %}
        
        {% if 'embed' in final_url or 'player' in final_url %}
            <iframe id="frame-{{ item['_id'] }}" src="{{ final_url }}" allow="autoplay; fullscreen"></iframe>
        {% else %}
            <video id="vid-{{ item['_id'] }}" src="{{ final_url }}" loop playsinline muted autoplay onclick="this.paused ? this.play() : this.pause()"></video>
        {% endif %}
        
        <div class="ui">
            <span style="background:cyan; color:#000; padding:2px 8px; border-radius:4px; font-weight:bold; font-size:10px;">{{ item['category']|upper }}</span>
            <h2 style="margin: 8px 0;">{{ item['title'] }}</h2>
        </div>
        
        <div class="sidebar">
            {% for link in item['links'] %}
            <button class="q-btn" onclick="updatePlayer('{{ item['_id'] }}', '{{ link['url'] }}')">{{ link['label'] }}</button>
            {% endfor %}
        </div>
    </div>
    {% endmacro %}

    <script>
        function updatePlayer(itemId, rawUrl) {
            const frame = document.getElementById('frame-'+itemId);
            const vid = document.getElementById('vid-'+itemId);
            let embedUrl = rawUrl;
            
            // Client side YouTube parser
            if(rawUrl.includes('youtube.com') || rawUrl.includes('youtu.be')) {
                let yid = rawUrl.match(/(?:v=|\\/)([0-9A-Za-z_-]{11})/);
                if(yid) embedUrl = "https://www.youtube.com/embed/" + yid[1] + "?autoplay=1";
            }

            if(frame) frame.src = embedUrl;
            if(vid) { vid.src = embedUrl; vid.play(); }
        }

        // Auto-play for native videos on scroll
        const obs = new IntersectionObserver((entries) => {
            entries.forEach(e => {
                if(e.target.tagName === 'VIDEO') {
                    if(e.isIntersecting) e.target.play();
                    else { e.target.pause(); e.target.currentTime = 0; }
                }
            });
        }, { threshold: 0.6 });
        document.querySelectorAll('video').forEach(v => obs.observe(v));
    </script>
</body>
</html>
'''

# ৩. এডমিন প্যানেল
ADMIN_PAGE = '''
<!DOCTYPE html>
<html>
<head><meta name="viewport" content="width=device-width, initial-scale=1">
<style>
    body { font-family: sans-serif; padding: 20px; background: #eee; }
    .box { max-width: 600px; margin: auto; background: #fff; padding: 20px; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
    input, select { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #ddd; border-radius: 5px; box-sizing: border-box; }
    .link-row { display: flex; gap: 5px; margin-bottom: 5px; }
    .btn { background: #28a745; color: white; border: none; padding: 12px; cursor: pointer; width: 100%; border-radius: 5px; font-weight: bold; }
    .add-link { background: #007bff; margin-bottom: 15px; padding: 8px; font-size: 13px; }
    .item-list { margin-top: 20px; }
    .item { display: flex; justify-content: space-between; padding: 10px; border-bottom: 1px solid #eee; }
</style>
</head>
<body>
    <div class="box">
        <h2>Add Movie or Drama</h2>
        <form method="POST" action="/admin/add">
            <input name="title" placeholder="Title Name" required>
            <input name="poster" placeholder="Poster Image URL" required>
            <select name="category">
                <option value="movie">Movie</option><option value="drama">Drama</option>
            </select>
            <div id="links-container">
                <div class="link-row">
                    <input name="labels[]" placeholder="Label (e.g. 1080p / Ep 01)" style="width:40%;">
                    <input name="urls[]" placeholder="Video URL (YouTube/MP4)" style="width:60%;">
                </div>
            </div>
            <button type="button" class="btn add-link" onclick="addL()">+ Add More Quality/Episode</button>
            <button type="submit" class="btn">PUBLISH CONTENT</button>
        </form>
        <hr>
        <div class="item-list">
            <h3>Manage Uploads</h3>
            {% for i in contents %}
            <div class="item">
                <span>{{ i.title }} [{{ i.category }}]</span>
                <a href="/admin/delete/{{ i._id }}" style="color:red; font-weight:bold;">Delete</a>
            </div>
            {% endfor %}
        </div>
        <br><a href="/" style="display:block; text-align:center;">Back to Home</a>
    </div>
    <script>
        function addL() {
            const div = document.createElement('div'); div.className='link-row';
            div.innerHTML = '<input name="labels[]" placeholder="Label" style="width:40%;"> <input name="urls[]" placeholder="URL" style="width:60%;">';
            document.getElementById('links-container').appendChild(div);
        }
    </script>
</body>
</html>
'''

# --- BACKEND ROUTES & LOGIC ---

@app.context_processor
def utility_processor():
    return dict(get_embed=parse_video_url)

@app.route('/')
def home():
    slider_items = list(content_col.find().sort("_id", -1).limit(6))
    contents = list(content_col.find().sort("_id", -1))
    return render_template_string(INDEX_PAGE, page_type='home', slider_items=slider_items, contents=contents)

@app.route('/movies')
def movies_cat():
    contents = list(content_col.find({'category': 'movie'}).sort("_id", -1))
    return render_template_string(INDEX_PAGE, page_type='movies', contents=contents)

@app.route('/drama')
def drama_cat():
    contents = list(content_col.find({'category': 'drama'}).sort("_id", -1))
    return render_template_string(INDEX_PAGE, page_type='drama', contents=contents)

@app.route('/watch/<id>')
def watch(id):
    try:
        current = content_col.find_one({"_id": ObjectId(id)})
        others = list(content_col.find({"_id": {"$ne": ObjectId(id)}}).limit(20))
        return render_template_string(WATCH_PAGE, current_item=current, other_items=others)
    except:
        return redirect(url_for('home'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['u'] == 'admin' and request.form['p'] == '1234':
            session['is_admin'] = True
            return redirect(url_for('admin'))
    return '''<body style="background:#000;color:#fff;text-align:center;padding-top:100px;font-family:sans-serif;">
              <h2>Admin Login</h2><form method="POST"><input name="u" placeholder="User"><br><br>
              <input name="p" type="password" placeholder="Pass"><br><br>
              <button type="submit">Login</button></form></body>'''

@app.route('/admin')
def admin():
    if not session.get('is_admin'): return redirect(url_for('login'))
    contents = list(content_col.find().sort("_id", -1))
    return render_template_string(ADMIN_PAGE, contents=contents)

@app.route('/admin/add', methods=['POST'])
def add_content():
    if not session.get('is_admin'): return "No Auth"
    labels = request.form.getlist('labels[]')
    urls = request.form.getlist('urls[]')
    links = [{'label': labels[i], 'url': urls[i]} for i in range(len(labels)) if labels[i] and urls[i]]
    
    content_col.insert_one({
        'title': request.form.get('title'),
        'poster': request.form.get('poster'),
        'category': request.form.get('category'),
        'links': links
    })
    return redirect(url_for('admin'))

@app.route('/admin/delete/<id>')
def delete_content(id):
    if session.get('is_admin'):
        content_col.delete_one({'_id': ObjectId(id)})
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
