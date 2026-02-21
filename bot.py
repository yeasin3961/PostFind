import asyncio
import os
import sqlite3
import logging
import sys
from threading import Thread
from flask import Flask

# --- Python 3.14 এর ইভেন্ট লুপ এরর ফিক্স ---
try:
    asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

# এখন পাইগ্রাম ইমপোর্ট করুন
from pyrogram import Client, filters, idle
from pyrogram.types import Message

# লগিং সেটআপ
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# --- কনফিগারেশন (আপনার দেওয়া তথ্য) ---
API_ID = 29904834
API_HASH = "8b4fd9ef578af114502feeafa2d31938"
BOT_TOKEN = "8488533482:AAFDhuByABx0-7DgUfQFsCNWzaso_Km_YRc"

# --- ডাটাবেস সেটআপ (SQLite) ---
db = sqlite3.connect("database.db", check_same_thread=False)
cursor = db.cursor()
# সেটিংস এবং ফাইল টেবিল তৈরি
cursor.execute('CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)')
cursor.execute('CREATE TABLE IF NOT EXISTS files (msg_id INTEGER PRIMARY KEY, name TEXT, link TEXT)')
db.commit()

def get_setting(key):
    cursor.execute("SELECT value FROM settings WHERE key=?", (key,))
    res = cursor.fetchone()
    return res[0] if res else None

def save_setting(key, value):
    cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
    db.commit()

# --- Flask Web Server (Render/Koyeb এর জন্য) ---
app = Flask(__name__)
@app.route('/')
def home(): 
    return "Bot is Running Successfully!", 200

def run_flask():
    # রেন্ডার পোর্টের জন্য অটো কনফিগারেশন
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# --- টেলিগ্রাম বট ক্লায়েন্ট ---
bot = Client(
    "file_sync_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    in_memory=True
)

# ফাইল সেভ বা আপডেট করার ফাংশন
def save_or_update_file(msg_id, name, channel_id):
    if name:
        clean_id = str(channel_id).replace("-100", "")
        link = f"https://t.me/c/{clean_id}/{msg_id}"
        cursor.execute("INSERT OR REPLACE INTO files (msg_id, name, link) VALUES (?, ?, ?)", 
                       (msg_id, name.lower(), link))
        db.commit()

# --- হ্যান্ডলারসমূহ ---

@bot.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):
    await message.reply_text(
        "👋 স্বাগতম!\n\n"
        "আমি একটি অটোমেটিক ফাইল ফাইন্ডার বট।\n\n"
        "🛠 **কিভাবে সেটআপ করবেন?**\n"
        "১. `/connect -100xxxx` (আপনার চ্যানেলের আইডি দিন)\n"
        "২. গ্রুপে গিয়ে `/verify` দিন।\n"
        "৩. এখন থেকে চ্যানেলের সব পোস্ট অটো সেভ হবে এবং এডিট করলেও আপডেট হয়ে যাবে।"
    )

@bot.on_message(filters.command("connect") & filters.private)
async def connect_cmd(client, message):
    if len(message.command) < 2:
        return await message.reply_text("ব্যবহার করুন: `/connect -100123456789` (চ্যানেল আইডি)")
    
    channel_id = message.command[1]
    save_setting("channel_id", channel_id)
    await message.reply_text(f"✅ চ্যানেল কানেক্ট হয়েছে। ব্যাকগ্রাউন্ডে আগের সব ফাইল সেভ করা শুরু হচ্ছে...")
    
    # ব্যাকগ্রাউন্ডে ইনডেক্সিং শুরু
    asyncio.create_task(index_all_files(channel_id))

@bot.on_message(filters.command("verify") & filters.group)
async def verify_cmd(client, message):
    save_setting("group_id", message.chat.id)
    await message.reply_text(f"✅ এই গ্রুপটি বটের সাথে কানেক্ট হয়েছে।\nID: `{message.chat.id}`")

# চ্যানেলের নতুন পোস্ট সেভ করার হ্যান্ডলার
@bot.on_message(filters.chat() & (filters.document | filters.video))
async def handle_new_post(client, message):
    channel_id = get_setting("channel_id")
    if channel_id and str(message.chat.id) == str(channel_id):
        name = message.document.file_name if message.document else (message.video.file_name or "Video File")
        save_or_update_file(message.id, name, channel_id)
        logger.info(f"Auto Saved: {name}")

# চ্যানেলের পোস্ট এডিট করলে আপডেট করার হ্যান্ডলার
@bot.on_edited_message(filters.chat())
async def handle_edited_post(client, message):
    channel_id = get_setting("channel_id")
    if channel_id and str(message.chat.id) == str(channel_id):
        name = None
        if message.document: name = message.document.file_name
        elif message.video: name = message.video.file_name or "Video File"
        
        if name:
            save_or_update_file(message.id, name, channel_id)
            logger.info(f"Auto Updated (Edited): {name}")

# সার্চ লজিক
@bot.on_message(filters.text)
async def search_files(client, message):
    group_id = get_setting("group_id")
    # শুধু প্রাইভেট অথবা কানেক্ট করা গ্রুপে কাজ করবে
    if message.chat.type != "private" and str(message.chat.id) != group_id:
        return

    query = message.text.lower()
    if len(query) < 2: return

    cursor.execute("SELECT name, link FROM files WHERE name LIKE ? LIMIT 15", ('%' + query + '%',))
    results = cursor.fetchall()

    if results:
        res_text = f"🔍 আপনার খোঁজা রেজাল্ট:\n\n"
        for name, link in results:
            res_text += f"📂 `{name}`\n🔗 [ফাইল লিঙ্ক]({link})\n\n"
        await message.reply_text(res_text, disable_web_page_preview=True)
    elif message.chat.type == "private":
        await message.reply_text("দুঃখিত, কোনো ফাইল পাওয়া যায়নি!")

# ইনডেক্সিং ফাংশন (পুরাতন পোস্টের জন্য)
async def index_all_files(channel_id):
    try:
        count = 0
        async for msg in bot.get_chat_history(int(channel_id)):
            name = None
            if msg.document: name = msg.document.file_name
            elif msg.video: name = msg.video.file_name or "Video"
            
            if name:
                save_or_update_file(msg.id, name, channel_id)
                count += 1
        logger.info(f"Indexing Complete. {count} files saved.")
    except Exception as e:
        logger.error(f"Index Error: {e}")

# --- মেইন রানার ফাংশন ---
async def main():
    # ১. Flask সার্ভার চালু করা
    flask_thread = Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    logger.info("Flask server started.")

    # ২. বট স্টার্ট করা
    await bot.start()
    logger.info("Bot is active now!")
    
    # ৩. বট সচল রাখা
    await idle()
    
    # ৪. বন্ধ করার সময়
    await bot.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
