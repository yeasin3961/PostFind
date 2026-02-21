import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from flask import Flask
from threading import Thread

# --- কনফিগারেশন (Environment Variables থেকে আসবে) ---
API_ID = int(os.environ.get("API_ID", "29904834")) # আপনার API ID
API_HASH = os.environ.get("API_HASH", "8b4fd9ef578af114502feeafa2d31938") # আপনার API Hash
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8488533482:AAFDhuByABx0-7DgUfQFsCNWzaso_Km_YRc") # BotFather থেকে পাওয়া টোকেন
CHANNEL_ID = int(os.environ.get("CHANNEL_ID", "-1003814445874")) # যে চ্যানেল থেকে ফাইল খুঁজবে

# --- Flask Server (Render/Koyeb এর জন্য জরুরি) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is Running!"

def run_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

# --- টেলিগ্রাম বট লজিক ---
bot = Client(
    "file_finder_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

@bot.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text(
        f"হ্যালো {message.from_user.mention}!\n"
        "আমি ফাইল ফাইন্ডার বট। আপনি যে ফাইলটি খুঁজছেন তার নাম লিখে আমাকে মেসেজ দিন।"
    )

@bot.on_message(filters.text & filters.private)
async def search_files(client, message):
    query = message.text
    sent_msg = await message.reply_text("খোঁজা হচ্ছে... দয়া করে অপেক্ষা করুন।")
    
    results = []
    # চ্যানেলে ফাইল সার্চ করা (ভিডিও, ডকুমেন্ট বা অডিও)
    async for msg in client.search_messages(CHANNEL_ID, query=query):
        if msg.document or msg.video or msg.audio:
            file_name = ""
            if msg.document: file_name = msg.document.file_name
            elif msg.video: file_name = msg.video.file_name or "Video File"
            elif msg.audio: file_name = msg.audio.file_name or "Audio File"
            
            # ফাইলের লিঙ্ক বা মেসেজ লিঙ্ক তৈরি
            file_link = f"https://t.me/c/{str(CHANNEL_ID)[4:]}/{msg.id}"
            results.append(f"📂 **{file_name}**\n🔗 [ফাইলটি দেখুন]({file_link})")

    if not results:
        await sent_msg.edit("দুঃখিত! আপনার দেওয়া নামে কোনো ফাইল খুঁজে পাওয়া যায়নি।")
    else:
        output = "\n\n".join(results[:10]) # প্রথম ১০টি রেজাল্ট দেখাবে
        await sent_msg.edit(f"আপনার জন্য প্রাপ্ত ফাইলগুলো নিচে দেওয়া হলো:\n\n{output}", disable_web_page_preview=True)

# --- বট স্টার্ট করা ---
if __name__ == "__main__":
    # Flask সার্ভার আলাদা থ্রেডে চালানো
    Thread(target=run_flask).start()
    
    print("Bot is starting...")
    bot.run()
