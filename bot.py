import os
import sqlite3
import logging
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from flask import Flask
from threading import Thread

# লগিং সেটআপ
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- কনফিগারেশন ---
API_ID = 29904834
API_HASH = "8b4fd9ef578af114502feeafa2d31938"
BOT_TOKEN = "8488533482:AAFDhuByABx0-7DgUfQFsCNWzaso_Km_YRc"

# --- ডাটাবেস সেটআপ (SQLite) ---
db = sqlite3.connect("database.db", check_same_thread=False)
cursor = db.cursor()

# সেটিংস টেবিল
cursor.execute('''CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)''')
# ফাইল টেবিল (msg_id রাখা হয়েছে যাতে এডিট করলে খুঁজে পাওয়া যায়)
cursor.execute('''CREATE TABLE IF NOT EXISTS files (msg_id INTEGER PRIMARY KEY, name TEXT, link TEXT)''')
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
def home(): return "Bot is Online and Syncing!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# --- টেলিগ্রাম বট সেটআপ ---
bot = Client("file_manager_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ফাইল সেভ করার কমন ফাংশন
def save_or_update_file(msg_id, file_name, channel_id):
    if file_name:
        clean_id = str(channel_id).replace("-100", "")
        link = f"https://t.me/c/{clean_id}/{msg_id}"
        cursor.execute("INSERT OR REPLACE INTO files (msg_id, name, link) VALUES (?, ?, ?)", 
                       (msg_id, file_name.lower(), link))
        db.commit()

# ব্যাকগ্রাউন্ডে চ্যানেলের আগের সব পোস্ট ইনডেক্স করা
async def full_channel_index(channel_id):
    logger.info(f"Indexing started for: {channel_id}")
    count = 0
    try:
        async for msg in bot.get_chat_history(int(channel_id)):
            file_name = None
            if msg.document: file_name = msg.document.file_name
            elif msg.video: file_name = msg.video.file_name or "Video"
            
            if file_name:
                save_or_update_file(msg.id, file_name, channel_id)
                count += 1
        logger.info(f"Indexing finished. {count} files indexed.")
    except Exception as e:
        logger.error(f"Indexing Error: {e}")

# ১. চ্যানেল কানেক্ট করা
@bot.on_message(filters.command("connect") & filters.private)
async def connect_channel(client, message):
    if len(message.command) < 2:
        return await message.reply_text("ব্যবহার: `/connect -100xxxxxxx`")
    
    channel_id = message.command[1]
    save_setting("channel_id", channel_id)
    await message.reply_text("✅ চ্যানেল কানেক্ট হয়েছে। আগের সব পোস্ট ব্যাকগ্রাউন্ডে সেভ হচ্ছে...")
    asyncio.create_task(full_channel_index(channel_id))

# ২. গ্রুপ ভেরিফাই করা
@bot.on_message(filters.command("verify") & filters.group)
async def verify_group(client, message):
    save_setting("group_id", message.chat.id)
    await message.reply_text(f"✅ গ্রুপ কানেক্ট হয়েছে!\nID: `{message.chat.id}`")

# ৩. চ্যানেলে নতুন পোস্ট করলে অটো সেভ
@bot.on_message(filters.chat(int(get_setting("channel_id") or 0)) & (filters.document | filters.video))
async def auto_save_new(client, message):
    channel_id = get_setting("channel_id")
    file_name = message.document.file_name if message.document else (message.video.file_name or "Video")
    save_or_update_file(message.id, file_name, channel_id)
    logger.info(f"New file saved: {file_name}")

# ৪. চ্যানেলের পুরাতন পোস্ট এডিট করলে অটো আপডেট (মেইন ফিচার)
@bot.on_edited_message(filters.chat(int(get_setting("channel_id") or 0)))
async def auto_update_edit(client, message):
    channel_id = get_setting("channel_id")
    file_name = None
    if message.document: file_name = message.document.file_name
    elif message.video: file_name = message.video.file_name or "Video"
    
    if file_name:
        save_or_update_file(message.id, file_name, channel_id)
        logger.info(f"File updated after edit: {file_name}")

# ৫. স্টার্ট কমান্ড
@bot.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text("বট সচল আছে। মুভির নাম লিখে সার্চ করুন।")

# ৬. সার্চ লজিক
@bot.on_message(filters.text)
async def search(client, message):
    group_id = get_setting("group_id")
    if message.chat.type != "private" and str(message.chat.id) != group_id:
        return

    query = message.text.lower()
    if len(query) < 3: return

    cursor.execute("SELECT name, link FROM files WHERE name LIKE ?", ('%' + query + '%',))
    results = cursor.fetchall()

    if results:
        res_text = f"🔍 আপনার জন্য রেজাল্ট:\n\n"
        for name, link in results[:15]:
            res_text += f"📂 `{name}`\n🔗 [ফাইলটি দেখুন]({link})\n\n"
        await message.reply_text(res_text, disable_web_page_preview=True)
    elif message.chat.type == "private":
        await message.reply_text("দুঃখিত, কোনো ফাইল পাওয়া যায়নি।")

# --- বট স্টার্ট ---
if __name__ == "__main__":
    # Flask থ্রেড শুরু
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()
    
    print("Bot is Running...")
    bot.run()
