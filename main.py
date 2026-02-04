import asyncio
import time
import os
import requests
from pyrogram import Client, filters
from threading import Thread
from flask import Flask

# ================= SERVER KEEPER =================
server = Flask(__name__)
@server.route('/')
def home(): return "Insta Fast API: ACTIVE 🟢"

def run(): server.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
def keep_alive(): Thread(target=run).start()

# ================= CONFIGURATION =================
API_ID = 35920777 
API_HASH = "99b5f89a6cf2e2f820ce41c2143c82fb" 
BOT_TOKEN = "7850428090:AAE49bQPsIjK1gXkainWR0ERWDxSjWV-X_c" 
RAPID_API_KEY = "cd2d64a77cmshcf7b10058add59ap13b975jsn91cf86d53b12"

# Ye values is specific API ke liye set kar di hain
API_HOST = "instagram-api-fast-reliable-data-scraper.p.rapidapi.com"
API_URL = "https://instagram-api-fast-reliable-data-scraper.p.rapidapi.com/v1/info"

app = Client("insta_fast_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

def get_insta_details(username):
    headers = {
        "x-rapidapi-key": RAPID_API_KEY,
        "x-rapidapi-host": API_HOST
    }
    # Is API mein parameter ka naam 'username_or_id_or_url' hota hai
    params = {"username_or_id_or_url": username}
    
    try:
        response = requests.get(API_URL, headers=headers, params=params, timeout=20)
        res_data = response.json()
        
        if response.status_code == 200 and res_data.get("data"):
            user = res_data["data"]
            return {
                "status": "active",
                "username": user.get("username", username),
                "followers": user.get("follower_count", 0),
                "following": user.get("following_count", 0)
            }
        elif response.status_code == 429:
            return {"status": "error", "msg": "Limit Exhausted! Free plan khatam."}
        else:
            return {"status": "banned", "msg": "Profile not found or API error."}
    except Exception as e:
        return {"status": "error", "msg": "Connection Timeout"}

# ================= COMMANDS =================

@app.on_message(filters.command("check", prefixes="!"))
async def check_user(client, message):
    if len(message.command) < 2:
        await message.reply_text("✨ **Usage:** `!check [username]`")
        return
    
    username = message.command[1].replace("@", "")
    status_msg = await message.reply_text(f"🔍 **Fast Scan:** @{username}...")
    
    data = get_insta_details(username)
    
    if data["status"] == "active":
        text = (
            f"👤 **INSTAGRAM PROFILE DATA**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"✨ **Username:** @{data['username']}\n"
            f"📈 **Followers:** {data['followers']:,}\n"
            f"📉 **Following:** {data['following']:,}\n"
            f"📊 **Status:** `Active` ✅\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"✨ @DisabledMM"
        )
        await status_msg.edit(text)
    else:
        await status_msg.edit(f"❌ **Error:** {data.get('msg')}")

# Monitor commands (Ban/Unban) bhi isi logic par kaam karenge
# ... [Baaki monitor commands pichle code jaise hi rahenge] ...

print("Bot started with MediaCrawlers API...")
keep_alive()
app.run()
