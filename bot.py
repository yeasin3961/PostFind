import os
import asyncio
import logging
from pyrogram import Client, filters
from flask import Flask
from threading import Thread

# লগিং সেটআপ (যাতে সমস্যা ধরা যায়)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- কনফিগারেশন ---
API_ID = int(os.environ.get("API_ID", "29904834"))
API_HASH = os.environ.get("API_HASH", "8b4fd9ef578af114502feeafa2d31938")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8488533482:AAFDhuByABx0-7DgUfQFsCNWzaso_Km_YRc")
CHANNEL_ID = int(os.environ.get("CHANNEL_ID", "-1003814445874"))

# --- Flask Server (Render/Koyeb এর জন্য বাধ্যতামূলক) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is Running!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# --- টেলিগ্রাম বট ---
bot = Client(
    "file_finder_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

@bot.on_message(filters.command("start") & filters.private)
async def start(client, message):
    logger.info(f"Start command received from {message.from_user.id}")
    await message.reply_text(
        f"হ্যালো {message.from_user.mention}!\n"
        "আমি ফাইল ফাইন্ডার বট। আপনি যে ফাইলটি খুঁজছেন তার নাম লিখে আমাকে মেসেজ দিন।"
    )

@bot.on_message(filters.text & filters.private)
async def search_files(client, message):
    query = message.text
    if len(query) < 3:
        return await message.reply_text("দয়া করে অন্তত ৩ অক্ষরের নাম লিখুন।")
    
    sent_msg = await message.reply_text("খোঁজা হচ্ছে...")
    
    results = []
    try:
        # সার্চ করার লজিক
        async for msg in client.search_messages(CHANNEL_ID, query=query):
            if msg.document or msg.video or msg.audio:
                file_name = ""
                if msg.document: file_name = msg.document.file_name
                elif msg.video: file_name = msg.video.file_name or "Video"
                elif msg.audio: file_name = msg.audio.file_name or "Audio"
                
                # ফাইল লিঙ্ক (চ্যানেল পাবলিক হলে কাজ করবে)
                file_link = f"https://t.me/c/{str(CHANNEL_ID).replace('-100', '')}/{msg.id}"
                results.append(f"📂 `{file_name}`\n🔗 [Get File]({file_link})")
        
        if not results:
            await sent_msg.edit("দুঃখিত! কোনো ফাইল পাওয়া যায়নি।")
        else:
            output = "\n\n".join(results[:15]) # ১০-১৫টি রেজাল্ট দেখাবে
            await sent_msg.edit(output, disable_web_page_preview=True)
            
    except Exception as e:
        logger.error(f"Error: {e}")
        await sent_msg.edit(f"একটি সমস্যা হয়েছে: {e}")

# --- রান করার মেইন ফাংশন ---
if __name__ == "__main__":
    # Flask সার্ভার স্টার্ট
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()
    
    logger.info("Bot is starting...")
    bot.run()
