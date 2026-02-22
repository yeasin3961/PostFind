import os
from flask import Flask, render_template_string, request, redirect, url_for, session
from pymongo import MongoClient
from bson.objectid import ObjectId

app = Flask(__name__)
app.secret_key = "movie_tiktok_pro_key"

# --- MongoDB Connection ---
MONGO_URI = os.environ.get("MONGO_URI", "mongodb+srv://admin:password@cluster.mongodb.net/test")
client = MongoClient(MONGO_URI)
db = client.movie_db
content_col = db.contents

# --- HTML Templates ---

HTML_TEMPLATES = {
    # হোমপেজ: সার্চ বার এবং মুভি গ্রিড
    'index.html': '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>MovieHome - Search & Explore</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body { background: #121212; color: white; font-family: sans-serif; margin: 0; padding: 10px; }
                .search-container { margin-bottom: 20px; text-align: center; }
                input[type="text"] { width: 80%; padding: 12px; border-radius: 25px; border: none; outline: none; }
                .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 15px; }
                .card { background: #1e1e1e; border-radius: 10px; overflow: hidden; text-decoration: none; color: white; transition: 0.3s; }
                .card img { width: 100%; height: 200px; object-fit: cover; }
                .card-info { padding: 8px; font-size: 14px; text-align: center; }
                .nav-btn { position: fixed; bottom: 20px; right: 20px; background: #ff0050; color: white; padding: 10px 20px; border-radius: 20px; text-decoration: none; font-weight: bold; }
            </style>
        </head>
        <body>
            <div class="search-container">
                <form action="/" method="GET">
                    <input type="text" name="search" placeholder="Search movies or dramas..." value="{{ search_query }}">
                </form>
            </div>
            
            <div class="grid">
                {% for item in contents %}
                <a href="/watch/{{ item._id }}" class="card">
                    <img src="{{ item.poster }}" alt="{{ item.title }}">
                    <div class="card-info">{{ item.title }}</div>
                </a>
                {% endfor %}
            </div>

            <a href="/login" class="nav-btn">Admin</a>
        </body>
        </html>
    ''',

    # ডিটেইলস পেজ: টিকটক স্টাইল ভার্টিক্যাল স্ক্রল
    'watch.html': '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Watching - {{ current_item.title }}</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body { margin: 0; background: #000; font-family: sans-serif; color: white; }
                .feed-container { height: 100vh; overflow-y: scroll; scroll-snap-type: y mandatory; }
                .tiktok-card { height: 100vh; width: 100%; scroll-snap-align: start; position: relative; 
                               background-size: cover; background-position: center; display: flex; flex-direction: column; justify-content: flex-end; }
                .overlay { background: linear-gradient(transparent, rgba(0,0,0,0.9)); padding: 25px; padding-bottom: 50px; }
                .btn-group { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 15px; }
                .link-btn { background: #ff0050; color: white; padding: 10px 18px; border-radius: 5px; text-decoration: none; font-size: 14px; font-weight: bold; }
                .back-btn { position: absolute; top: 20px; left: 20px; color: white; text-decoration: none; font-size: 20px; background: rgba(0,0,0,0.5); padding: 5px 15px; border-radius: 50%; }
                .badge { background: #00f2ea; color: black; padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }
            </style>
        </head>
        <body>
            <a href="/" class="back-btn">✕</a>
            <div class="feed-container">
                {# প্রথমে যে মুভিতে ক্লিক করা হয়েছে সেটি দেখাবে #}
                <div class="tiktok-card" style="background-image: url('{{ current_item.poster }}');">
                    <div class="overlay">
                        <span class="badge">{{ current_item.category | capitalize }}</span>
                        <h2>{{ current_item.title }}</h2>
                        <div class="btn-group">
                            {% for link in current_item.links %}
                            <a href="{{ link.url }}" class="link-btn" target="_blank">{{ link.label }}</a>
                            {% endfor %}
                        </div>
                    </div>
                </div>

                {# এরপর অন্যান্য মুভিগুলো টিকটক স্ক্রলের মতো আসবে #}
                {% for item in others %}
                <div class="tiktok-card" style="background-image: url('{{ item.poster }}');">
                    <div class="overlay">
                        <span class="badge">{{ item.category | capitalize }}</span>
                        <h2>{{ item.title }}</h2>
                        <div class="btn-group">
                            {% for link in item.links %}
                            <a href="{{ link.url }}" class="link-btn" target="_blank">{{ link.label }}</a>
                            {% endfor %}
                        </div>
                    </div>
                </div>
                {% endfor %}
            </div>
        </body>
        </html>
    ''',

    # অ্যাডমিন এবং লগইন টেমপ্লেট আগের মতোই থাকবে (সংক্ষিপ্ত রাখা হলো)
    'admin.html': '''...পূর্বের অ্যাডমিন কোড এখানে...''', 
    'login.html': '''...পূর্বের লগইন কোড এখানে...'''
}

# --- Routes ---

@app.route('/')
def index():
    query = request.args.get('search', '')
    if query:
        # সার্চ ফিল্টার
        contents = list(content_col.find({"title": {"$regex": query, "$options": "i"}}))
    else:
        contents = list(content_col.find().sort("_id", -1))
    return render_template_string(HTML_TEMPLATES['index.html'], contents=contents, search_query=query)

@app.route('/watch/<id>')
def watch(id):
    current_item = content_col.find_one({"_id": ObjectId(id)})
    # বর্তমান আইটেম বাদে অন্যগুলো স্ক্রলের জন্য আনা
    others = list(content_col.find({"_id": {"$ne": ObjectId(id)}}).limit(10))
    return render_template_string(HTML_TEMPLATES['watch.html'], current_item=current_item, others=others)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['user'] == 'admin' and request.form['pass'] == '1234':
            session['admin'] = True
            return redirect(url_for('admin'))
    return render_template_string('''<body style="text-align:center;padding-top:100px;"><h2>Admin Login</h2><form method="POST"><input name="user" placeholder="User"><br><br><input type="password" name="pass" placeholder="Pass"><br><br><button>Login</button></form></body>''')

@app.route('/admin')
def admin():
    if not session.get('admin'): return redirect(url_for('login'))
    contents = list(content_col.find().sort("_id", -1))
    # অ্যাডমিন প্যানেলের ফুল HTML এখানে বসাবেন (আগের উত্তরে দেওয়া আছে)
    return render_template_string(ADMIN_PAGE_HTML, contents=contents) # ADMIN_PAGE_HTML হলো আগের অ্যাডমিন প্যানেল কোড

@app.route('/admin/add', methods=['POST'])
def add_content():
    if not session.get('admin'): return "Unauthorized"
    labels = request.form.getlist('link_label[]')
    urls = request.form.getlist('link_url[]')
    links = [{'label': labels[i], 'url': urls[i]} for i in range(len(labels)) if labels[i]]
    data = {
        'title': request.form.get('title'),
        'poster': request.form.get('poster'),
        'category': request.form.get('category'),
        'links': links
    }
    content_col.insert_one(data)
    return redirect(url_for('admin'))

@app.route('/delete/<id>')
def delete_item(id):
    if session.get('admin'): content_col.delete_one({'_id': ObjectId(id)})
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
