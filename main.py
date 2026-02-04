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
def home(): return "Insta API Debug Mode: ACTIVE 🟢"

def run(): server.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
def keep_alive(): Thread(target=run).start()

# ================= CONFIGURATION =================
API_ID = 35920777 
API_HASH = "99b5f89a6cf2e2f820ce41c2143c82fb" 
BOT_TOKEN = "7850428090:AAE49bQPsIjK1gXkainWR0ERWDxSjWV-X_c" 
RAPID_API_KEY = "cd2d64a77cmshcf7b10058add59ap13b975jsn91cf86d53b12"

app = Client("insta_debug_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- Powerful API Fetcher ---
def get_insta_details(username):
    # Hum ek different stable endpoint use kar rahe hain
    url = f"https://instagram-scraper-api2.p.rapidapi.com/v1/info"
    headers = {
        "x-rapidapi-key": RAPID_API_KEY,
        "x-rapidapi-host": "instagram-scraper-api2.p.rapidapi.com"
    }
    try:
        response = requests.get(url, headers=headers, params={"username_or_id_or_url": username}, timeout=20)
        
        # DEBUG: Print status in console
        print(f"API Status: {response.status_code}")
        
        if response.status_code == 401 or response.status_code == 403:
            return {"status": "error", "msg": "Invalid RapidAPI Key! Check your subscription."}
        
        res_data = response.json()
        if response.status_code == 200 and "data" in res_data:
            user = res_data["data"]
            return {
                "status": "active",
                "username": user.get("username"),
                "followers": user.get("follower_count", 0),
                "following": user.get("following_count", 0)
            }
        return {"status": "banned", "msg": "Account not found or Banned."}
    except Exception as e:
        return {"status": "error", "msg": str(e)}

@app.on_message(filters.command("check", prefixes="!"))
async def check_user(client, message):
    if len(message.command) < 2:
        await message.reply_text("✨ **Usage:** `!check [username]`")
        return
    
    username = message.command[1].replace("@", "")
    status_msg = await message.reply_text(f"🚀 **Testing Connection for** @{username}...")
    
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
        error_reason = data.get("msg", "Unknown API Error")
        await status_msg.edit(f"❌ **Failed:** {error_reason}\n\nCheck if your RapidAPI key is active.")

print("Bot is starting...")
keep_alive()
app.run()
