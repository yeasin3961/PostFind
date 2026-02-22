import os
from flask import Flask, render_template, request, redirect, url_for, session, render_template_string
from pymongo import MongoClient
from bson.objectid import ObjectId

app = Flask(__name__)
app.secret_key = "super_secret_tiktok_key"

# --- MongoDB Connection ---
# Render/Koyeb এর Environment Variable থেকে MONGO_URI নেবে
MONGO_URI = os.environ.get("MONGO_URI", "mongodb+srv://roxiw19528:roxiw19528@cluster0.vl508y4.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
client = MongoClient(MONGO_URI)
db = client.tiktok_db
videos_col = db.videos

# --- HTML Templates (Single File এ রাখার জন্য String হিসেবে ডিফাইন করা) ---

HTML_TEMPLATES = {
    'index.html': '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>TikTok Clone</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body { margin: 0; background: #000; font-family: sans-serif; }
                .video-container { height: 100vh; overflow-y: scroll; scroll-snap-type: y mandatory; }
                .video-card { height: 100vh; width: 100%; scroll-snap-align: start; position: relative; display: flex; align-items: center; justify-content: center; }
                video { width: 100%; height: 100%; object-fit: cover; }
                .info { position: absolute; bottom: 80px; left: 20px; color: white; text-shadow: 1px 1px 5px #000; }
                .nav { position: fixed; bottom: 0; width: 100%; background: rgba(0,0,0,0.8); display: flex; justify-content: space-around; padding: 15px; z-index: 10; }
                .nav a { color: white; text-decoration: none; font-weight: bold; }
            </style>
        </head>
        <body>
            <div class="video-container">
                {% for video in videos %}
                <div class="video-card">
                    <video src="{{ video.url }}" loop playsinline onclick="this.paused ? this.play() : this.pause()"></video>
                    <div class="info">
                        <h3>@user</h3>
                        <p>{{ video.caption }}</p>
                    </div>
                </div>
                {% endfor %}
            </div>
            <div class="nav">
                <a href="/">Home</a>
                <a href="/upload">Upload</a>
                <a href="/login">Admin</a>
            </div>
            <script>
                document.addEventListener('click', function() {
                    const vids = document.querySelectorAll('video');
                    vids[0].play();
                }, {once: true});
            </script>
        </body>
        </html>
    ''',
    'upload.html': '''
        <!DOCTYPE html>
        <html>
        <head><title>Upload Video</title><style>body{padding:20px; font-family:sans-serif;}</style></head>
        <body>
            <h2>Upload Video (Direct MP4 URL)</h2>
            <form method="POST">
                <input type="text" name="video_url" placeholder="Video URL (mp4)" required style="width:100%; padding:10px;"><br><br>
                <textarea name="caption" placeholder="Caption" style="width:100%; padding:10px;"></textarea><br><br>
                <button type="submit" style="padding:10px 20px; background:red; color:white; border:none;">Post Video</button>
            </form>
            <br><a href="/">Back to Feed</a>
        </body>
        </html>
    ''',
    'login.html': '''
        <!DOCTYPE html>
        <html>
        <head><title>Admin Login</title></head>
        <body style="text-align:center; padding-top:50px;">
            <h2>Admin Login</h2>
            <form method="POST">
                <input type="text" name="username" placeholder="Username" required><br><br>
                <input type="password" name="password" placeholder="Password" required><br><br>
                <button type="submit">Login</button>
            </form>
        </body>
        </html>
    ''',
    'admin.html': '''
        <!DOCTYPE html>
        <html>
        <head><title>Admin Panel</title><style>table{width:100%; border-collapse:collapse;} td,th{border:1px solid #ddd; padding:8px;}</style></head>
        <body style="padding:20px;">
            <h2>Admin Management</h2>
            <table>
                <tr><th>Caption</th><th>Action</th></tr>
                {% for video in videos %}
                <tr>
                    <td>{{ video.caption }}</td>
                    <td><a href="/delete/{{ video._id }}" style="color:red;">Delete</a></td>
                </tr>
                {% endfor %}
            </table>
            <br><a href="/">Logout & Back</a>
        </body>
        </html>
    '''
}

# --- Routes ---

@app.route('/')
def index():
    videos = list(videos_col.find().sort("_id", -1))
    return render_template_string(HTML_TEMPLATES['index.html'], videos=videos)

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        video_data = {
            'url': request.form.get('video_url'),
            'caption': request.form.get('caption')
        }
        videos_col.insert_one(video_data)
        return redirect(url_for('index'))
    return render_template_string(HTML_TEMPLATES['upload.html'])

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Default Admin Credentials: admin / 1234
        if request.form['username'] == 'admin' and request.form['password'] == '1234':
            session['admin'] = True
            return redirect(url_for('admin'))
    return render_template_string(HTML_TEMPLATES['login.html'])

@app.route('/admin')
def admin():
    if not session.get('admin'): return redirect(url_for('login'))
    videos = list(videos_col.find())
    return render_template_string(HTML_TEMPLATES['admin.html'], videos=videos)

@app.route('/delete/<id>')
def delete_video(id):
    if session.get('admin'):
        videos_col.delete_one({'_id': ObjectId(id)})
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
