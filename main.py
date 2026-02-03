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
def home():
    return "Instagram API Service: ACTIVE 🟢"

def run():
    server.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

def keep_alive():
    t = Thread(target=run)
    t.start()

# ================= CONFIGURATION =================

API_ID = 35920777 
API_HASH = "99b5f89a6cf2e2f820ce41c2143c82fb" 
BOT_TOKEN = "7850428090:AAE49bQPsIjK1gXkainWR0ERWDxSjWV-X_c" # BotFather wala token

# ⚠️ YAHAN APNI RAPIDAPI KEY DALEIN
RAPID_API_KEY = "cd2d64a77cmshcf7b10058add59ap13b975jsn91cf86d53b12"

CHECK_INTERVAL = 300 
monitoring_ban = {}   
monitoring_unban = {} 

app = Client("insta_pro_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- Helper: Time Formatter ---
def get_time_taken(seconds):
    days, seconds = divmod(int(seconds), 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    parts = []
    if days > 0: parts.append(f"{days}d")
    if hours > 0: parts.append(f"{hours}h")
    if minutes > 0: parts.append(f"{minutes}m")
    parts.append(f"{seconds}s")
    return " ".join(parts)

# --- Helper: Get Instagram Data (RAPID API) ---
def get_insta_details(username):
    url = "https://instagram-scraper-api2.p.rapidapi.com/v1/info"
    querystring = {"username_or_id_or_url": username}
    headers = {
        "x-rapidapi-key": RAPID_API_KEY,
        "x-rapidapi-host": "instagram-scraper-api2.p.rapidapi.com"
    }
    try:
        response = requests.get(url, headers=headers, params=querystring, timeout=15)
        res_data = response.json()
        if response.status_code == 200 and "data" in res_data:
            user_info = res_data["data"]
            return {
                "status": "active",
                "username": user_info.get("username"),
                "followers": user_info.get("follower_count"),
                "following": user_info.get("following_count")
            }
        else:
            return {"status": "banned"}
    except:
        return {"status": "error"}

# ================= PROFESSIONAL COMMANDS =================

@app.on_message(filters.command("check", prefixes="!"))
async def check_user(client, message):
    if len(message.command) < 2:
        await message.reply_text("✨ **Usage:** `!check [username]`")
        return
    username = message.command[1].replace("@", "")
    status_msg = await message.reply_text(f"🔍 **API Scanning:** @{username}...")
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
            f"✨ **Service by:** @DisabledMM"
        )
        await status_msg.edit(text)
    elif data["status"] == "banned":
        await status_msg.edit(f"❌ **Alert:** @{username} is **Banned** or **Does Not Exist**.")
    else:
        await status_msg.edit(f"⚠️ **API Error:** Could not connect to Instagram servers.")

@app.on_message(filters.command("monitorban", prefixes="!"))
async def monitor_ban(client, message):
    username = message.command[1].replace("@", "") if len(message.command) > 1 else None
    if not username: return
    monitoring_ban[username] = message.chat.id
    await message.reply_text(f"🛡️ **Surveillance Active (Ban Mode)**\nTarget: @{username}\nInterval: 5m")
    asyncio.create_task(ban_checker(client, username, message.chat.id))

@app.on_message(filters.command("monitorub", prefixes="!"))
async def monitor_unban_cmd(client, message):
    username = message.command[1].replace("@", "") if len(message.command) > 1 else None
    if not username: return
    monitoring_unban[username] = {'chat_id': message.chat.id, 'start_time': time.time()}
    await message.reply_text(f"⏳ **Surveillance Active (Unban Mode)**\nTarget: @{username}\nInterval: 5m")
    asyncio.create_task(unban_checker(client, username))

@app.on_message(filters.command("stop", prefixes="!"))
async def stop_monitor(client, message):
    username = message.command[1].replace("@", "") if len(message.command) > 1 else None
    if username in monitoring_ban: monitoring_ban.pop(username)
    if username in monitoring_unban: monitoring_unban.pop(username)
    await message.reply_text(f"🛑 **Monitoring Stopped for** @{username}")

# ================= BACKGROUND LOGIC =================

async def ban_checker(client, username, chat_id):
    while username in monitoring_ban:
        await asyncio.sleep(CHECK_INTERVAL)
        data = get_insta_details(username)
        if data["status"] == "banned":
            await client.send_message(chat_id, f"🚨 **ALERT:** @{username} has been **REMOVED** from Instagram! ❌\n\n✨ @DisabledMM")
            monitoring_ban.pop(username, None)
            break

async def unban_checker(client, username):
    while username in monitoring_unban:
        await asyncio.sleep(CHECK_INTERVAL)
        data = get_insta_details(username)
        if data["status"] == "active":
            info = monitoring_unban[username]
            time_taken = get_time_taken(time.time() - info['start_time'])
            await client.send_message(info['chat_id'], f"🎉 **RECOVERY DETECTED**\n━━━━━━━━━━━━━━━━━━━━\n✅ **@{username} IS UNBANNED!**\n⏱️ **Time Taken:** {time_taken}\n━━━━━━━━━━━━━━━━━━━━\n✨ @DisabledMM")
            monitoring_unban.pop(username, None)
            break

print("Professional Insta Monitor: ONLINE")
keep_alive()
app.run()
