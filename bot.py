import os
import sqlite3
import logging
import asyncio
import sys
from pyrogram import Client, filters, idle
from flask import Flask
from threading import Thread

# লগিং সেটআপ
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# --- কনফিগারেশন ---
API_ID = 29904834
API_HASH = "8b4fd9ef578af114502feeafa2d31938"
BOT_TOKEN = "8488533482:AAFDhuByABx0-7DgUfQFsCNWzaso_Km_YRc"

# --- ডাটাবেস সেটআপ ---
db = sqlite3.connect("database.db", check_same_thread=False)
cursor = db.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS files (msg_id INTEGER PRIMARY KEY, name TEXT, link TEXT)''')
db.commit()

def get_setting(key):
    cursor.execute("SELECT value FROM settings WHERE key=?", (key,))
    res = cursor.fetchone()
    return res[0] if res else None

def save_setting(key, value):
    cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
    db.commit()

# --- Flask Server (Render এর জন্য) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is Running Successfully!", 200

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# --- টেলিগ্রাম বট সেটআপ ---
bot = Client(
    "file_finder_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    in_memory=True
)

# ফাইল সেভ করার ফাংশন
def save_or_update_file(msg_id, file_name, channel_id):
    if file_name:
        clean_id = str(channel_id).replace("-100", "")
        link = f"https://t.me/c/{clean_id}/{msg_id}"
        cursor.execute("INSERT OR REPLACE INTO files (msg_id, name, link) VALUES (?, ?, ?)", 
                       (msg_id, file_name.lower(), link))
        db.commit()

# --- হ্যান্ডলারসমূহ ---

@bot.on_message(filters.command("start") & filters.private)
async def start_handler(client, message):
    await message.reply_text("বট সচল আছে! মুভির নাম লিখে সার্চ করুন।\nচ্যানেল কানেক্ট করতে: `/connect -100xxxx` ব্যবহার করুন।")

@bot.on_message(filters.command("connect") & filters.private)
async def connect_handler(client, message):
    if len(message.command) < 2:
        return await message.reply_text("সঠিক নিয়ম: `/connect -100xxxxxxxxxx`")
    
    channel_id = message.command[1]
    save_setting("channel_id", channel_id)
    await message.reply_text(f"✅ চ্যানেল {channel_id} কানেক্ট হয়েছে। ব্যাকগ্রাউন্ডে ইন্ডেক্সিং শুরু হচ্ছে...")
    
    # ব্যাকগ্রাউন্ড ইন্ডেক্সিং শুরু
    asyncio.create_task(full_index(channel_id))

@bot.on_message(filters.command("verify") & filters.group)
async def verify_handler(client, message):
    save_setting("group_id", message.chat.id)
    await message.reply_text("✅ এই গ্রুপটি এখন বটের সাথে কানেক্টেড।")

# নতুন পোস্ট ও এডিট হ্যান্ডলার
@bot.on_message(filters.chat() & (filters.document | filters.video))
async def auto_save(client, message):
    channel_id = get_setting("channel_id")
    if channel_id and str(message.chat.id) == str(channel_id):
        file_name = message.document.file_name if message.document else (message.video.file_name or "Video")
        save_or_update_file(message.id, file_name, channel_id)

@bot.on_edited_message(filters.chat())
async def auto_update(client, message):
    channel_id = get_setting("channel_id")
    if channel_id and str(message.chat.id) == str(channel_id):
        file_name = None
        if message.document: file_name = message.document.file_name
        elif message.video: file_name = message.video.file_name or "Video"
        
        if file_name:
            save_or_update_file(message.id, file_name, channel_id)

# সার্চ লজিক
@bot.on_message(filters.text)
async def search_handler(client, message):
    group_id = get_setting("group_id")
    if message.chat.type != "private" and str(message.chat.id) != group_id:
        return

    query = message.text.lower()
    if len(query) < 3: return

    cursor.execute("SELECT name, link FROM files WHERE name LIKE ? LIMIT 15", ('%' + query + '%',))
    results = cursor.fetchall()

    if results:
        res_text = "🔍 আপনার জন্য প্রাপ্ত ফাইলসমূহ:\n\n"
        for name, link in results:
            res_text += f"📂 `{name}`\n🔗 [ডাউনলোড লিঙ্ক]({link})\n\n"
        await message.reply_text(res_text, disable_web_page_preview=True)
    elif message.chat.type == "private":
        await message.reply_text("দুঃখিত, কোনো ফাইল পাওয়া যায়নি।")

# ফুল ইন্ডেক্স ফাংশন
async def full_index(channel_id):
    try:
        count = 0
        async for msg in bot.get_chat_history(int(channel_id)):
            file_name = None
            if msg.document: file_name = msg.document.file_name
            elif msg.video: file_name = msg.video.file_name or "Video"
            
            if file_name:
                save_or_update_file(msg.id, file_name, channel_id)
                count += 1
        logger.info(f"Indexing complete: {count} files.")
    except Exception as e:
        logger.error(f"Indexing Error: {e}")

# --- মেইন ফাংশন (Python 3.14 এর জন্য নিরাপদ পদ্ধতি) ---
async def main():
    # ১. Flask সার্ভার চালু করা
    flask_thread = Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    logger.info("Flask server started.")

    # ২. বট চালু করা
    await bot.start()
    logger.info("Bot started successfully!")
    
    # ৩. বটকে সচল রাখা
    await idle()
    
    # ৪. বন্ধ করার সময় ডাটাবেস সেভ করা
    await bot.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
