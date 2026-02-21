import os
import sqlite3
import logging
from pyrogram import Client, filters
from flask import Flask
from threading import Thread

# লগিং সেটআপ
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- কনফিগারেশন ---
API_ID = int(os.environ.get("API_ID", "29904834"))
API_HASH = os.environ.get("API_HASH", "8b4fd9ef578af114502feeafa2d31938")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8488533482:AAFqGM4nyXF2NYg3BNfbCyc0CikJFBPsrKg")
CHANNEL_ID = int(os.environ.get("CHANNEL_ID", "-1003814445874"))

# --- ডাটাবেস সেটআপ (SQLite) ---
db = sqlite3.connect("files.db", check_same_thread=False)
cursor = db.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS files (name TEXT, link TEXT)''')
db.commit()

# --- Flask Server (For Render/Koyeb) ---
app = Flask(__name__)
@app.route('/')
def home(): return "Bot is Alive!"

def run_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

# --- টেলিগ্রাম বট ---
bot = Client("file_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@bot.on_message(filters.command("start") & filters.private)
async def start(client, message):
    await message.reply_text(f"হ্যালো {message.from_user.mention}!\nআমি ফাইল ফাইন্ডার বট। প্রথমে /index কমান্ড দিয়ে ফাইলগুলো লোড করে নিন (শুধু এডমিনের জন্য)। তারপর যেকোনো ফাইলের নাম লিখে সার্চ করুন।")

# --- ইনডেক্সিং কমান্ড (চ্যানেলের সব ফাইল ডাটাবেসে সেভ করবে) ---
@bot.on_message(filters.command("index") & filters.private)
async def index_files(client, message):
    await message.reply_text("চ্যানেলের ফাইলগুলো ইনডেক্স করা শুরু হচ্ছে... কিছুটা সময় লাগতে পারে।")
    
    count = 0
    async for msg in client.get_chat_history(CHANNEL_ID):
        file_name = None
        if msg.document: file_name = msg.document.file_name
        elif msg.video: file_name = msg.video.file_name or "Video"
        elif msg.audio: file_name = msg.audio.file_name or "Audio"

        if file_name:
            # ফাইল লিঙ্ক তৈরি
            clean_id = str(CHANNEL_ID).replace("-100", "")
            file_link = f"https://t.me/c/{clean_id}/{msg.id}"
            
            # ডাটাবেসে সেভ করা
            cursor.execute("INSERT INTO files (name, link) VALUES (?, ?)", (file_name.lower(), file_link))
            count += 1
    
    db.commit()
    await message.reply_text(f"সফলভাবে {count}টি ফাইল ইনডেক্স করা হয়েছে! এখন সার্চ করতে পারেন।")

# --- সার্চ লজিক ---
@bot.on_message(filters.text & filters.private)
async def search(client, message):
    query = message.text.lower()
    if len(query) < 3:
        return await message.reply_text("দয়া করে কমপক্ষে ৩ অক্ষরের নাম লিখুন।")

    cursor.execute("SELECT * FROM files WHERE name LIKE ?", ('%' + query + '%',))
    results = cursor.fetchall()

    if not results:
        await message.reply_text("দুঃখিত! এই নামে কোনো ফাইল পাওয়া যায়নি।")
    else:
        reply = "আপনার জন্য প্রাপ্ত ফাইলসমূহ:\n\n"
        for name, link in results[:15]: # সর্বোচ্চ ১৫টি রেজাল্ট দেখাবে
            reply += f"📂 `{name}`\n🔗 [ডাউনলোড লিঙ্ক]({link})\n\n"
        await message.reply_text(reply, disable_web_page_preview=True)

if __name__ == "__main__":
    Thread(target=run_flask).start()
    print("বটটি চালু হয়েছে...")
    bot.run()
