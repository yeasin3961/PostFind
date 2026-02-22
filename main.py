import os
from flask import Flask, render_template_string, request, redirect, url_for, session
from pymongo import MongoClient
from bson.objectid import ObjectId

app = Flask(__name__)
app.secret_key = "ultimate_tiktok_secret_key_101"

# --- MongoDB Connection ---
# আপনার দেওয়া URI এখানে যুক্ত করা হয়েছে
MONGO_URI = "mongodb+srv://roxiw19528:roxiw19528@cluster0.vl508y4.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client.movie_database
content_col = db.contents

# --- HTML TEMPLATES ---

# ১. ইউজার হোমপেজ (সার্চ এবং গ্রিড লেআউট)
INDEX_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MovieTok - Stream</title>
    <style>
        body { background: #000; color: #fff; font-family: sans-serif; margin: 0; }
        header { padding: 15px; background: #111; position: sticky; top: 0; z-index: 100; text-align: center; border-bottom: 1px solid #333; }
        .search-bar { width: 90%; max-width: 500px; padding: 12px; border-radius: 25px; border: 1px solid #444; background: #222; color: #fff; outline: none; }
        .grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; padding: 10px; margin-bottom: 80px; }
        @media(min-width: 768px) { .grid { grid-template-columns: repeat(4, 1fr); } }
        .card { background: #1a1a1a; border-radius: 10px; overflow: hidden; text-decoration: none; color: white; border: 1px solid #222; transition: 0.3s; }
        .card img { width: 100%; height: 230px; object-fit: cover; }
        .card-info { padding: 10px; text-align: center; font-size: 14px; font-weight: bold; }
        .nav-bottom { position: fixed; bottom: 0; width: 100%; background: #000; border-top: 1px solid #333; display: flex; justify-content: space-around; padding: 15px 0; z-index: 1000; }
        .nav-bottom a { color: #fff; text-decoration: none; font-size: 14px; font-weight: bold; }
        .nav-bottom a.active { color: #ff0050; }
    </style>
</head>
<body>
    <header>
        <form action="/" method="GET">
            <input type="text" name="search" class="search-bar" placeholder="Search Movie or Drama..." value="{{ q }}">
        </form>
    </header>
    <div class="grid">
        {% for item in contents %}
        <a href="/watch/{{ item._id }}" class="card">
            <img src="{{ item.poster }}" alt="Poster">
            <div class="card-info">{{ item.title }}</div>
        </a>
        {% endfor %}
    </div>
    <div class="nav-bottom">
        <a href="/" class="active">Home</a>
        <a href="/login">Admin Panel</a>
    </div>
</body>
</html>
'''

# ২. ভিডিও ওয়াচ পেজ (টিকটক স্টাইল ভার্টিক্যাল স্ক্রল)
WATCH_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Watching - {{ current.title }}</title>
    <style>
        body, html { margin: 0; padding: 0; height: 100%; overflow: hidden; background: #000; font-family: sans-serif; }
        .feed { height: 100vh; overflow-y: scroll; scroll-snap-type: y mandatory; }
        .video-box { height: 100vh; width: 100%; scroll-snap-align: start; position: relative; display: flex; align-items: center; justify-content: center; }
        video { width: 100%; height: 100%; object-fit: contain; background: #000; }
        .overlay { position: absolute; bottom: 60px; left: 15px; color: white; text-shadow: 1px 1px 5px #000; z-index: 10; pointer-events: none; }
        .sidebar { position: absolute; right: 10px; bottom: 120px; display: flex; flex-direction: column; gap: 12px; z-index: 20; }
        .link-btn { background: #ff0050; color: white; border: none; padding: 10px; border-radius: 8px; font-size: 12px; font-weight: bold; cursor: pointer; box-shadow: 0 0 10px rgba(0,0,0,0.5); }
        .close-btn { position: absolute; top: 20px; left: 20px; z-index: 100; color: white; font-size: 24px; text-decoration: none; background: rgba(0,0,0,0.5); padding: 5px 15px; border-radius: 50%; }
        .badge { background: #00f2ea; color: #000; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; text-transform: uppercase; }
    </style>
</head>
<body>
    <a href="/" class="close-btn">✕</a>
    <div class="feed">
        <!-- Selected Video -->
        {{ video_element(current) }}
        
        <!-- Other Videos -->
        {% for item in others %}
            {{ video_element(item) }}
        {% endfor %}
    </div>

    {% macro video_element(item) %}
    <div class="video-box">
        <video id="vid-{{ item._id }}" src="{{ item.links[0].url }}" loop playsinline onclick="this.paused ? this.play() : this.pause()"></video>
        <div class="overlay">
            <span class="badge">{{ item.category }}</span>
            <h2 style="margin: 8px 0;">{{ item.title }}</h2>
        </div>
        <div class="sidebar">
            {% for link in item.links %}
            <button class="link-btn" onclick="changeSource('vid-{{ item._id }}', '{{ link.url }}')">{{ link.label }}</button>
            {% endfor %}
        </div>
    </div>
    {% endmacro %}

    <script>
        function changeSource(vidId, newUrl) {
            const v = document.getElementById(vidId);
            v.src = newUrl;
            v.play();
        }
        // Auto Play on Scroll
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

# ৩. অ্যাডমিন প্যানেল (কন্টেন্ট ম্যানেজমেন্ট)
ADMIN_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Admin Panel</title>
    <style>
        body { font-family: sans-serif; background: #f4f4f4; padding: 20px; }
        .admin-box { background: white; max-width: 600px; margin: auto; padding: 20px; border-radius: 10px; box-shadow: 0 0 15px rgba(0,0,0,0.1); }
        input, select { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #ccc; border-radius: 5px; box-sizing: border-box; }
        .link-group { display: flex; gap: 10px; margin-bottom: 10px; }
        .btn { background: #28a745; color: white; border: none; padding: 12px; width: 100%; border-radius: 5px; cursor: pointer; font-size: 16px; font-weight: bold; }
        .add-more { background: #007bff; margin-bottom: 15px; font-size: 13px; padding: 8px; }
        .list-box { margin-top: 30px; }
        .list-item { background: #fff; padding: 10px; border-bottom: 1px solid #eee; display: flex; justify-content: space-between; align-items: center; }
        .del-btn { color: red; text-decoration: none; font-weight: bold; }
    </style>
</head>
<body>
    <div class="admin-box">
        <a href="/logout" style="float: right;">Logout</a>
        <h2>Add Movie/Drama</h2>
        <form method="POST" action="/admin/add">
            <input type="text" name="title" placeholder="Name (e.g. Iron Man)" required>
            <input type="text" name="poster" placeholder="Poster Image URL" required>
            <select name="category">
                <option value="movie">Movie</option>
                <option value="drama">Drama</option>
            </select>
            <div id="links-container">
                <label style="font-size: 13px; font-weight: bold;">Video Links / Quality / Episodes:</label>
                <div class="link-group">
                    <input type="text" name="link_label[]" placeholder="Label (1080p / Ep 01)" required>
                    <input type="text" name="link_url[]" placeholder="Direct MP4 Link" required>
                </div>
            </div>
            <button type="button" class="btn add-more" onclick="addLinkField()">+ Add More Link</button>
            <button type="submit" class="btn">Publish Content</button>
        </form>

        <div class="list-box">
            <h3>Uploaded Content</h3>
            {% for item in contents %}
            <div class="list-item">
                <span>{{ item.title }} ({{ item.category }})</span>
                <a href="/admin/delete/{{ item._id }}" class="del-btn" onclick="return confirm('Delete this?')">Delete</a>
            </div>
            {% endfor %}
        </div>
    </div>

    <script>
        function addLinkField() {
            const container = document.getElementById('links-container');
            const div = document.createElement('div');
            div.className = 'link-group';
            div.innerHTML = '<input type="text" name="link_label[]" placeholder="Label" required> <input type="text" name="link_url[]" placeholder="Video URL" required>';
            container.appendChild(div);
        }
    </script>
</body>
</html>
'''

# --- ROUTES & LOGIC ---

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
    current = content_col.find_one({"_id": ObjectId(id)})
    others = list(content_col.find({"_id": {"$ne": ObjectId(id)}}).limit(20))
    return render_template_string(WATCH_HTML, current=current, others=others)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Admin User: admin | Pass: 1234
        if request.form['u'] == 'admin' and request.form['p'] == '1234':
            session['logged_in'] = True
            return redirect(url_for('admin'))
    return render_template_string('<body style="text-align:center;padding-top:100px;background:#f4f4f4;font-family:sans-serif;"><h2>Admin Login</h2><form method="POST"><input name="u" placeholder="Username" style="padding:10px;"><br><br><input type="password" name="p" placeholder="Password" style="padding:10px;"><br><br><button type="submit" style="padding:10px 20px; background:green; color:white; border:none; border-radius:5px;">Login</button></form></body>')

@app.route('/admin')
def admin():
    if not session.get('logged_in'): return redirect(url_for('login'))
    contents = list(content_col.find().sort("_id", -1))
    return render_template_string(ADMIN_HTML, contents=contents)

@app.route('/admin/add', methods=['POST'])
def add_item():
    if not session.get('logged_in'): return "Unauthorized"
    labels = request.form.getlist('link_label[]')
    urls = request.form.getlist('link_url[]')
    links = [{'label': labels[i], 'url': urls[i]} for i in range(len(labels)) if labels[i] and urls[i]]
    
    content_col.insert_one({
        'title': request.form.get('title'),
        'poster': request.form.get('poster'),
        'category': request.form.get('category'),
        'links': links
    })
    return redirect(url_for('admin'))

@app.route('/admin/delete/<id>')
def delete_item(id):
    if session.get('logged_in'):
        content_col.delete_one({'_id': ObjectId(id)})
    return redirect(url_for('admin'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    # Local এ রান করতে চাইলে
    app.run(host='0.0.0.0', port=5000, debug=True)
