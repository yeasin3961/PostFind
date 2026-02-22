import os
from flask import Flask, render_template_string, request, redirect, url_for, session
from pymongo import MongoClient
from bson.objectid import ObjectId

app = Flask(__name__)
app.secret_key = "tik_movie_pro_secure_key"

# --- MongoDB Connection ---
# আপনার দেওয়া URI সরাসরি এখানে সেট করা হলো
MONGO_URI = "mongodb+srv://roxiw19528:roxiw19528@cluster0.vl508y4.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client.movie_database
content_col = db.contents

# --- HTML TEMPLATES ---

# ১. হোমপেজ (ইউজার প্যানেল - গ্রিড এবং সার্চ)
INDEX_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MovieTok - Explore</title>
    <style>
        body { background: #000; color: #fff; font-family: sans-serif; margin: 0; }
        header { padding: 15px; background: #111; position: sticky; top: 0; z-index: 100; text-align: center; border-bottom: 1px solid #333; }
        .search-bar { width: 90%; max-width: 500px; padding: 12px; border-radius: 25px; border: 1px solid #444; background: #222; color: #fff; outline: none; }
        .container { padding: 10px; margin-bottom: 80px; }
        .grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; }
        @media(min-width: 768px) { .grid { grid-template-columns: repeat(4, 1fr); } }
        .card { background: #1a1a1a; border-radius: 12px; overflow: hidden; text-decoration: none; color: white; border: 1px solid #222; transition: 0.3s; }
        .card img { width: 100%; height: 250px; object-fit: cover; }
        .card-info { padding: 10px; text-align: center; font-size: 14px; font-weight: bold; }
        .nav-bottom { position: fixed; bottom: 0; width: 100%; background: #000; border-top: 1px solid #333; display: flex; justify-content: space-around; padding: 15px 0; z-index: 1000; }
        .nav-bottom a { color: #fff; text-decoration: none; font-size: 14px; font-weight: bold; }
        .active { color: #ff0050 !important; }
    </style>
</head>
<body>
    <header>
        <form action="/" method="GET">
            <input type="text" name="search" class="search-bar" placeholder="Search Movie or Drama..." value="{{ q }}">
        </form>
    </header>
    <div class="container">
        <div class="grid">
            {% for item in contents %}
            <a href="/watch/{{ item['_id'] }}" class="card">
                <img src="{{ item['poster'] }}" alt="Poster">
                <div class="card-info">{{ item['title'] }}</div>
            </a>
            {% endfor %}
        </div>
    </div>
    <div class="nav-bottom">
        <a href="/" class="active">Home</a>
        <a href="/login">Admin</a>
    </div>
</body>
</html>
'''

# ২. ওয়াচ পেজ (টিকটক স্টাইল ভিডিও ফিড)
WATCH_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Watching</title>
    <style>
        body, html { margin: 0; padding: 0; height: 100%; overflow: hidden; background: #000; font-family: sans-serif; }
        .feed { height: 100vh; overflow-y: scroll; scroll-snap-type: y mandatory; }
        .video-box { height: 100vh; width: 100%; scroll-snap-align: start; position: relative; display: flex; align-items: center; justify-content: center; }
        video { width: 100%; height: 100%; object-fit: contain; }
        .overlay { position: absolute; bottom: 60px; left: 15px; color: white; text-shadow: 1px 1px 5px #000; z-index: 10; pointer-events: none; }
        .sidebar { position: absolute; right: 10px; bottom: 120px; display: flex; flex-direction: column; gap: 12px; z-index: 20; }
        .link-btn { background: #ff0050; color: white; border: none; padding: 10px; border-radius: 8px; font-size: 12px; font-weight: bold; cursor: pointer; box-shadow: 0 0 10px rgba(0,0,0,0.5); }
        .close-btn { position: absolute; top: 20px; left: 20px; z-index: 100; color: white; font-size: 24px; text-decoration: none; background: rgba(0,0,0,0.5); padding: 5px 12px; border-radius: 50%; }
        .badge { background: #00f2ea; color: #000; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; text-transform: uppercase; }
    </style>
</head>
<body>
    <a href="/" class="close-btn">✕</a>
    <div class="feed">
        <!-- প্রথম ভিডিও (যেটিতে ক্লিক করা হয়েছে) -->
        {{ video_block(current) }}
        
        <!-- অন্য ভিডিওগুলো স্ক্রলে আসবে -->
        {% for item in others %}
            {{ video_block(item) }}
        {% endfor %}
    </div>

    {% macro video_block(item) %}
    <div class="video-box">
        {% if item['links'] and item['links']|length > 0 %}
        <video id="vid-{{ item['_id'] }}" src="{{ item['links'][0]['url'] }}" loop playsinline onclick="this.paused ? this.play() : this.pause()"></video>
        <div class="overlay">
            <span class="badge">{{ item['category'] }}</span>
            <h2 style="margin: 8px 0;">{{ item['title'] }}</h2>
        </div>
        <div class="sidebar">
            {% for link in item['links'] %}
            <button class="link-btn" onclick="changeVid('vid-{{ item['_id'] }}', '{{ link['url'] }}')">{{ link['label'] }}</button>
            {% endfor %}
        </div>
        {% endif %}
    </div>
    {% endmacro %}

    <script>
        function changeVid(id, url) {
            const v = document.getElementById(id);
            v.src = url;
            v.play();
        }
        // অটো প্লে সিস্টেম
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) entry.target.play();
                else { entry.target.pause(); entry.target.currentTime = 0; }
            });
        }, { threshold: 0.6 });
        document.querySelectorAll('video').forEach(v => observer.observe(v));
    </script>
</body>
</html>
'''

# ৩. এডমিন প্যানেল
ADMIN_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Admin Panel</title>
    <style>
        body { font-family: sans-serif; background: #f4f4f4; padding: 20px; }
        .box { background: white; max-width: 600px; margin: auto; padding: 20px; border-radius: 10px; box-shadow: 0 0 15px rgba(0,0,0,0.1); }
        input, select { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #ccc; border-radius: 5px; box-sizing: border-box; }
        .link-row { display: flex; gap: 10px; margin-bottom: 10px; }
        .btn { background: #28a745; color: white; border: none; padding: 12px; width: 100%; border-radius: 5px; cursor: pointer; font-size: 16px; font-weight: bold; }
        .add-btn { background: #007bff; margin-bottom: 15px; font-size: 13px; padding: 8px; }
        .item-list { margin-top: 30px; }
        .item { background: #fff; padding: 10px; border-bottom: 1px solid #eee; display: flex; justify-content: space-between; align-items: center; }
    </style>
</head>
<body>
    <div class="box">
        <a href="/logout" style="float: right;">Logout</a>
        <h2>Add Content</h2>
        <form method="POST" action="/admin/add">
            <input type="text" name="title" placeholder="Movie or Drama Name" required>
            <input type="text" name="poster" placeholder="Poster URL" required>
            <select name="category">
                <option value="movie">Movie</option>
                <option value="drama">Drama</option>
            </select>
            <div id="links">
                <label>Links (Labels & URLs):</label>
                <div class="link-row">
                    <input type="text" name="labels[]" placeholder="e.g. 1080p or Ep 01" required>
                    <input type="text" name="urls[]" placeholder="Direct MP4 URL" required>
                </div>
            </div>
            <button type="button" class="btn add-btn" onclick="addLink()">+ Add More Link</button>
            <button type="submit" class="btn">Publish Now</button>
        </form>

        <div class="item-list">
            <h3>Manage Content</h3>
            {% for item in contents %}
            <div class="item">
                <span>{{ item['title'] }} ({{ item['category'] }})</span>
                <a href="/admin/delete/{{ item['_id'] }}" style="color:red; text-decoration:none; font-weight:bold;">Delete</a>
            </div>
            {% endfor %}
        </div>
        <br><a href="/" style="display:block; text-align:center;">Back to Home</a>
    </div>

    <script>
        function addLink() {
            const div = document.createElement('div');
            div.className = 'link-row';
            div.innerHTML = '<input type="text" name="labels[]" placeholder="Label" required> <input type="text" name="urls[]" placeholder="URL" required>';
            document.getElementById('links').appendChild(div);
        }
    </script>
</body>
</html>
'''

# --- BACKEND LOGIC ---

@app.route('/')
def index():
    q = request.args.get('search', '')
    if q:
        contents = list(content_col.find({"title": {"$regex": q, "$options": "i"}}))
    else:
        contents = list(content_col.find().sort("_id", -1))
    return render_template_string(INDEX_HTML, contents=contents, q=q)

@app.route('/watch/<id>')
def watch(id):
    try:
        current = content_col.find_one({"_id": ObjectId(id)})
        if not current: return redirect(url_for('index'))
        others = list(content_col.find({"_id": {"$ne": ObjectId(id)}}).limit(15))
        return render_template_string(WATCH_HTML, current=current, others=others)
    except:
        return redirect(url_for('index'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['u'] == 'admin' and request.form['p'] == '1234':
            session['admin_on'] = True
            return redirect(url_for('admin'))
    return render_template_string('<body style="text-align:center;padding-top:100px;font-family:sans-serif;"><h2>Admin Login</h2><form method="POST"><input name="u" placeholder="User"><br><br><input type="password" name="p" placeholder="Pass"><br><br><button type="submit">Login</button></form></body>')

@app.route('/admin')
def admin():
    if not session.get('admin_on'): return redirect(url_for('login'))
    contents = list(content_col.find().sort("_id", -1))
    return render_template_string(ADMIN_HTML, contents=contents)

@app.route('/admin/add', methods=['POST'])
def add_content():
    if not session.get('admin_on'): return "No Auth"
    labels = request.form.getlist('labels[]')
    urls = request.form.getlist('urls[]')
    links = [{'label': labels[i], 'url': urls[i]} for i in range(len(labels)) if labels[i]]
    
    content_col.insert_one({
        'title': request.form.get('title'),
        'poster': request.form.get('poster'),
        'category': request.form.get('category'),
        'links': links
    })
    return redirect(url_for('admin'))

@app.route('/admin/delete/<id>')
def delete_item(id):
    if session.get('admin_on'):
        content_col.delete_one({'_id': ObjectId(id)})
    return redirect(url_for('admin'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
