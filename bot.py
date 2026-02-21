import os
import sqlite3
import logging
import sys
from pyrogram import Client, filters
from flask import Flask
from threading import Thread

# লগিং সেটআপ (রেন্ডার লগে এরর দেখার জন্য)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# --- কনফিগারেশন ---
# এখানে আমরা os.environ.get ব্যবহার করব যাতে রেন্ডারের ড্যাশবোর্ড থেকে কন্ট্রোল করা যায়
API_ID = int(os.environ.get("API_ID", 29904834))
API_HASH = os.environ.get("API_HASH", "8b4fd9ef578af114502feeafa2d31938")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8488533482:AAFDhuByABx0-7DgUfQFsCNWzaso_Km_YRc")
CHANNEL_ID = int(os.environ.get("CHANNEL_ID", -1003814445874))

# --- ডাটাবেস সেটআপ ---
def init_db():
    conn = sqlite3.connect("files.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS files (name TEXT, link TEXT)''')
    conn.commit()
    return conn

db_conn = init_db()

# --- Flask Web Server (Render-এর পোর্ট চেক পাস করার জন্য) ---
app = Flask(__name__)

@app.route('/')
def health_check():
    return "Bot is Running Perfectly!", 200

def run_flask():
    # Render নিজে থেকেই একটি PORT এনভায়রনমেন্ট ভেরিয়েবল দেয়
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# --- টেলিগ্রাম বট ---
# 'workdir' হিসেবে /tmp ব্যবহার করা হয়েছে যাতে ফাইল রাইট পারমিশন নিয়ে সমস্যা না হয়
bot = Client(
    "file_finder_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    in_memory=True # সেশন ফাইল সেভ না করে মেমোরিতে রাখবে
)

@bot.on_message(filters.command("start") & filters.private)
async def start_handler(client, message):
    await message.reply_text(f"হ্যালো {message.from_user.mention}!\nআমি রেডি। সার্চ করতে মুভির নাম লিখুন। নতুন মুভি যোগ করলে /index দিন।")

@bot.on_message(filters.command("index") & filters.private)
async def index_handler(client, message):
    msg_wait = await message.reply_text("ইনডেক্সিং শুরু হচ্ছে...")
    try:
        cursor = db_conn.cursor()
        cursor.execute("DELETE FROM files") # পুরাতন ডাটা ক্লিয়ার করা
        
        count = 0
        async for msg in client.get_chat_history(CHANNEL_ID):
            file_name = None
            if msg.document: file_name = msg.document.file_name
            elif msg.video: file_name = msg.video.file_name or "Video"
            
            if file_name:
                clean_id = str(CHANNEL_ID).replace("-100", "")
                link = f"https://t.me/c/{clean_id}/{msg.id}"
                cursor.execute("INSERT INTO files (name, link) VALUES (?, ?)", (file_name.lower(), link))
                count += 1
        
        db_conn.commit()
        await msg_wait.edit(f"সফলভাবে {count}টি ফাইল ইনডেক্স করা হয়েছে!")
    except Exception as e:
        logger.error(f"Index Error: {e}")
        await msg_wait.edit(f"ভুল হয়েছে: {e}")

@bot.on_message(filters.text & filters.private)
async def search_handler(client, message):
    query = message.text.lower()
    if len(query) < 3: return
    
    cursor = db_conn.cursor()
    cursor.execute("SELECT * FROM files WHERE name LIKE ?", ('%' + query + '%',))
    results = cursor.fetchall()

    if not results:
        await message.reply_text("কিছু পাওয়া যায়নি।")
    else:
        out = "\n".join([f"📂 `{n}`\n🔗 [Link]({l})\n" for n, l in results[:10]])
        await message.reply_text(out, disable_web_page_preview=True)

# --- মেইন রানার ---
if __name__ == "__main__":
    try:
        # ১. আগে Flask সার্ভার চালু করুন আলাদা থ্রেডে
        flask_thread = Thread(target=run_flask)
        flask_thread.daemon = True
        flask_thread.start()
        logger.info("Flask server started.")

        # ২. তারপর বট রান করুন
        logger.info("Bot is starting...")
        bot.run()
    except Exception as e:
        logger.critical(f"Fatal Error: {e}")
        sys.exit(1)
