import os
from flask import Flask, render_template_string, request, redirect, url_for, session
from pymongo import MongoClient
from bson.objectid import ObjectId

app = Flask(__name__)
app.secret_key = "full_tiktok_movie_system_99"

# --- MongoDB Connection ---
# Render/Koyeb Environment Variable থেকে MONGO_URI নিবে
MONGO_URI = os.environ.get("MONGO_URI", "mongodb+srv://roxiw19528:roxiw19528@cluster0.vl508y4.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
client = MongoClient(MONGO_URI)
db = client.movie_tok_db
content_col = db.contents

# --- HTML TEMPLATES ---

HTML_LAYOUT = {
    # হোমপেজ: সার্চ এবং পোস্টার গ্রিড
    'index': '''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>MovieTok - Home</title>
            <style>
                body { background: #000; color: #fff; font-family: 'Segoe UI', sans-serif; margin: 0; padding: 0; }
                header { padding: 15px; text-align: center; background: #111; position: sticky; top: 0; z-index: 100; }
                .search-bar { width: 90%; max-width: 500px; padding: 12px 20px; border-radius: 25px; border: none; background: #222; color: white; font-size: 16px; outline: none; border: 1px solid #333; }
                .container { padding: 15px; margin-bottom: 70px; }
                .grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; }
                @media(min-width: 768px) { .grid { grid-template-columns: repeat(4, 1fr); } }
                .card { background: #1a1a1a; border-radius: 12px; overflow: hidden; text-decoration: none; color: white; transition: 0.3s; border: 1px solid #222; }
                .card img { width: 100%; height: 240px; object-fit: cover; }
                .card-info { padding: 10px; font-size: 14px; font-weight: bold; text-align: center; }
                .nav-bottom { position: fixed; bottom: 0; width: 100%; background: #111; display: flex; justify-content: space-around; padding: 15px 0; border-top: 1px solid #222; }
                .nav-bottom a { color: white; text-decoration: none; font-size: 14px; opacity: 0.8; }
                .active { color: #ff0050 !important; font-weight: bold; opacity: 1 !important; }
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
                    <a href="/watch/{{ item._id }}" class="card">
                        <img src="{{ item.poster }}" alt="Poster">
                        <div class="card-info">{{ item.title }}</div>
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
    ''',

    # ওয়াচ পেজ: টিকটক ভার্টিক্যাল ভিডিও ফিড
    'watch': '''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Watching - {{ current.title }}</title>
            <style>
                body, html { margin: 0; padding: 0; height: 100%; overflow: hidden; background: #000; font-family: sans-serif; }
                .video-feed { height: 100vh; overflow-y: scroll; scroll-snap-type: y mandatory; }
                .section { height: 100vh; width: 100%; scroll-snap-align: start; position: relative; display: flex; align-items: center; justify-content: center; }
                video { width: 100%; height: 100%; object-fit: contain; }
                .back-btn { position: absolute; top: 20px; left: 20px; z-index: 100; color: white; text-decoration: none; font-size: 25px; background: rgba(0,0,0,0.5); padding: 5px 15px; border-radius: 50%; }
                .info-overlay { position: absolute; bottom: 40px; left: 15px; color: white; text-shadow: 1px 1px 5px #000; pointer-events: none; z-index: 10; }
                .side-bar { position: absolute; right: 10px; bottom: 100px; display: flex; flex-direction: column; gap: 15px; z-index: 20; }
                .quality-btn { background: #ff0050; color: white; border: none; padding: 10px 12px; border-radius: 8px; font-size: 12px; font-weight: bold; cursor: pointer; box-shadow: 0 0 10px rgba(0,0,0,0.5); }
                .badge { background: #00f2ea; color: #000; padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }
            </style>
        </head>
        <body>
            <a href="/" class="back-btn">✕</a>
            <div class="video-feed">
                <!-- Selected Content First -->
                {{ video_card(current) }}
                
                <!-- Other Content for Scroll -->
                {% for item in others %}
                    {{ video_card(item) }}
                {% endfor %}
            </div>

            {% macro video_card(item) %}
            <div class="section">
                <video id="v-{{ item._id }}" src="{{ item.links[0].url }}" loop playsinline onclick="togglePlay(this)"></video>
                <div class="info-overlay">
                    <span class="badge">{{ item.category | capitalize }}</span>
                    <h2>{{ item.title }}</h2>
                </div>
                <div class="side-bar">
                    {% for link in item.links %}
                    <button class="quality-btn" onclick="changeVideo('v-{{ item._id }}', '{{ link.url }}')">{{ link.label }}</button>
                    {% endfor %}
                </div>
            </div>
            {% endmacro %}

            <script>
                function togglePlay(vid) {
                    if(vid.paused) vid.play();
                    else vid.pause();
                }
                function changeVideo(id, url) {
                    const v = document.getElementById(id);
                    v.src = url;
                    v.play();
                }
                // Auto Play Observer
                const options = { threshold: 0.6 };
                const observer = new IntersectionObserver((entries) => {
                    entries.forEach(e => {
                        if(e.isIntersecting) e.target.play();
                        else { e.target.pause(); e.target.currentTime = 0; }
                    });
                }, options);
                document.querySelectorAll('video').forEach(v => observer.observe(v));
            </script>
        </body>
        </html>
    ''',

    # অ্যাডমিন প্যানেল
    'admin': '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Admin Panel</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body { font-family: sans-serif; padding: 20px; background: #f0f0f0; }
                .box { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.1); max-width: 600px; margin: auto; }
                input, select { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #ccc; border-radius: 5px; box-sizing: border-box; }
                .row { display: flex; gap: 10px; margin-bottom: 5px; }
                .btn { background: #007bff; color: white; border: none; padding: 12px; cursor: pointer; width: 100%; border-radius: 5px; font-size: 16px; }
                .add-link { background: #28a745; margin-bottom: 10px; }
                .list { margin-top: 20px; }
                .item { background: #fff; padding: 10px; margin-bottom: 5px; display: flex; justify-content: space-between; align-items: center; border-radius: 5px; }
            </style>
        </head>
        <body>
            <div class="box">
                <h2>Add Movie/Drama</h2>
                <form method="POST" action="/admin/add">
                    <input type="text" name="title" placeholder="Movie/Drama Name" required>
                    <input type="text" name="poster" placeholder="Poster Image URL" required>
                    <select name="category" id="cat">
                        <option value="movie">Movie (Quality System)</option>
                        <option value="drama">Drama (Episode System)</option>
                    </select>
                    <div id="links-area">
                        <div class="row">
                            <input type="text" name="labels[]" placeholder="Label (1080p / Ep 01)">
                            <input type="text" name="urls[]" placeholder="Direct Video Link (.mp4)">
                        </div>
                    </div>
                    <button type="button" class="btn add-link" onclick="addMore()">+ Add More Links</button>
                    <button type="submit" class="btn">Publish Content</button>
                </form>
                <br><a href="/" style="display:block; text-align:center;">Back to Home</a>
            </div>

            <div class="box list">
                <h3>Managed Content</h3>
                {% for i in contents %}
                <div class="item">
                    <span>{{ i.title }} ({{ i.category }})</span>
                    <a href="/delete/{{ i._id }}" style="color:red; text-decoration:none;">Delete</a>
                </div>
                {% endfor %}
            </div>

            <script>
                function addMore() {
                    const container = document.getElementById('links-area');
                    const div = document.createElement('div');
                    div.className = 'row';
                    div.innerHTML = '<input type="text" name="labels[]" placeholder="Label"> <input type="text" name="urls[]" placeholder="Direct Video Link">';
                    container.appendChild(div);
                }
            </script>
        </body>
        </html>
    '''
}

# --- ROUTES ---

@app.route('/')
def index():
    q = request.args.get('search', '')
    if q:
        contents = list(content_col.find({"title": {"$regex": q, "$options": "i"}}))
    else:
        contents = list(content_col.find().sort("_id", -1))
    return render_template_string(HTML_LAYOUT['index'], contents=contents, q=q)

@app.route('/watch/<id>')
def watch(id):
    current = content_col.find_one({"_id": ObjectId(id)})
    others = list(content_col.find({"_id": {"$ne": ObjectId(id)}}).limit(15))
    return render_template_string(HTML_LAYOUT['watch'], current=current, others=others)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['u'] == 'admin' and request.form['p'] == '1234':
            session['admin'] = True
            return redirect(url_for('admin'))
    return render_template_string('<body style="text-align:center;padding-top:100px;font-family:sans-serif;"><h2>Admin Login</h2><form method="POST"> <input name="u" placeholder="User"><br><br><input type="password" name="p" placeholder="Pass"><br><br><button type="submit">Login</button></form></body>')

@app.route('/admin')
def admin():
    if not session.get('admin'): return redirect(url_for('login'))
    contents = list(content_col.find().sort("_id", -1))
    return render_template_string(HTML_LAYOUT['admin'], contents=contents)

@app.route('/admin/add', methods=['POST'])
def add():
    if not session.get('admin'): return "Unauthorized"
    labels = request.form.getlist('labels[]')
    urls = request.form.getlist('urls[]')
    links = []
    for i in range(len(labels)):
        if labels[i] and urls[i]:
            links.append({'label': labels[i], 'url': urls[i]})
    
    content_col.insert_one({
        'title': request.form.get('title'),
        'poster': request.form.get('poster'),
        'category': request.form.get('category'),
        'links': links
    })
    return redirect(url_for('admin'))

@app.route('/delete/<id>')
def delete(id):
    if session.get('admin'):
        content_col.delete_one({'_id': ObjectId(id)})
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
