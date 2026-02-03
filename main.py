import asyncio
import time
import os
import instaloader
from pyrogram import Client, filters
from threading import Thread
from flask import Flask

# ================= SERVER KEEPER =================
server = Flask(__name__)

@server.route('/')
def home():
    return "Instagram Monitor Service: ACTIVE 🟢"

def run():
    server.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

def keep_alive():
    t = Thread(target=run)
    t.start()

# ================= CONFIGURATION =================

API_ID = 35920777
API_HASH = "99b5f89a6cf2e2f820ce41c2143c82fb"
BOT_TOKEN = "7850428090:AAE49bQPsIjK1gXkainWR0ERWDxSjWV-X_c" # BotFather wala token yahan daalein

CHECK_INTERVAL = 300 

monitoring_ban = {}   
monitoring_unban = {} 

app = Client("insta_monitor_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
L = instaloader.Instaloader()

# --- Helper: Time Formatter ---
def get_time_taken(seconds):
    days = int(seconds // 86400)
    seconds %= 86400
    hours = int(seconds // 3600)
    seconds %= 3600
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    
    parts = []
    if days > 0: parts.append(f"{days}d")
    if hours > 0: parts.append(f"{hours}h")
    if minutes > 0: parts.append(f"{minutes}m")
    parts.append(f"{seconds}s")
    return " ".join(parts)

# --- Helper: Get Instagram Data ---
def get_insta_details(username):
    try:
        # User-Agent simulation for better results
        profile = instaloader.Profile.from_node(L.context, L.context.get_json(f"users/web_profile_info/?username={username}", target=username)['data']['user'])
        return {
            "status": "active",
            "username": profile.username,
            "followers": profile.followers,
            "following": profile.followees
        }
    except:
        return {"status": "banned"}

# ================= PROFESSIONAL COMMANDS =================

# 1. CHECK COMMAND
@app.on_message(filters.command("check", prefixes="!"))
async def check_user(client, message):
    if len(message.command) < 2:
        await message.reply_text("✨ **Usage:** `!check [username]`")
        return

    username = message.command[1].replace("@", "")
    status_msg = await message.reply_text(f"🔍 **Scanning Database for** @{username}...")
    
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
    else:
        await status_msg.edit(f"❌ **Alert:** @{username} is either **Banned** or the **Username is Invalid**.")

# 2. MONITOR BAN
@app.on_message(filters.command("monitorban", prefixes="!"))
async def monitor_ban(client, message):
    if len(message.command) < 2:
        await message.reply_text("✨ **Usage:** `!monitorban [username]`")
        return

    username = message.command[1].replace("@", "")
    data = get_insta_details(username)
    
    if data["status"] == "banned":
        await message.reply_text("⚠️ **Error:** This account is already unavailable.")
        return

    monitoring_ban[username] = message.chat.id
    await message.reply_text(
        f"🛡️ **Surveillance Active (Ban Mode)**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 **Target:** @{username}\n"
        f"⏱️ **Interval:** Every 5 Minutes\n"
        f"📢 **Notification:** On Profile Removal\n"
        f"━━━━━━━━━━━━━━━━━━━━"
    )
    asyncio.create_task(ban_checker(client, username, message.chat.id))

# 3. MONITOR UNBAN
@app.on_message(filters.command("monitorub", prefixes="!"))
async def monitor_unban_cmd(client, message):
    if len(message.command) < 2:
        await message.reply_text("✨ **Usage:** `!monitorub [username]`")
        return

    username = message.command[1].replace("@", "")
    data = get_insta_details(username)
    
    if data["status"] == "active":
        await message.reply_text("✅ **Notice:** Profile is currently active.")
        return

    monitoring_unban[username] = {'chat_id': message.chat.id, 'start_time': time.time()}
    await message.reply_text(
        f"⏳ **Surveillance Active (Unban Mode)**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 **Target:** @{username}\n"
        f"⏱️ **Interval:** Every 5 Minutes\n"
        f"📢 **Notification:** On Account Recovery\n"
        f"━━━━━━━━━━━━━━━━━━━━"
    )
    asyncio.create_task(unban_checker(client, username))

# 4. STOP
@app.on_message(filters.command("stop", prefixes="!"))
async def stop_monitor(client, message):
    if len(message.command) < 2:
        await message.reply_text("✨ **Usage:** `!stop [username]`")
        return
        
    username = message.command[1].replace("@", "")
    found = False
    
    if username in monitoring_ban:
        del monitoring_ban[username]
        found = True
    if username in monitoring_unban:
        del monitoring_unban[username]
        found = True
        
    if found:
        await message.reply_text(f"🛑 **Surveillance Terminated for** @{username}")
    else:
        await message.reply_text("⚠️ **Notice:** No active monitoring found for this user.")

# ================= BACKGROUND LOGIC =================

async def ban_checker(client, username, chat_id):
    while username in monitoring_ban:
        await asyncio.sleep(CHECK_INTERVAL)
        data = get_insta_details(username)
        if data["status"] == "banned":
            await client.send_message(
                chat_id, 
                f"🚨 **URGENT NOTIFICATION**\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"❌ **ACCOUNT REMOVED!**\n\n"
                f"👤 **Target:** @{username}\n"
                f"📊 **Status:** No longer found on Instagram.\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"✨ @DisabledMM"
            )
            monitoring_ban.pop(username, None)
            break

async def unban_checker(client, username):
    while username in monitoring_unban:
        await asyncio.sleep(CHECK_INTERVAL)
        data = get_insta_details(username)
        if data["status"] == "active":
            info = monitoring_unban[username]
            time_taken = get_time_taken(time.time() - info['start_time'])
            
            await client.send_message(
                info['chat_id'], 
                f"🎉 **RECOVERY DETECTED**\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"✅ **@{username} IS UNBANNED!**\n\n"
                f"📈 **Followers:** {data['followers']:,}\n"
                f"📉 **Following:** {data['following']:,}\n"
                f"⏱️ **Recovery Time:** {time_taken}\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"✨ @DisabledMM"
            )
            monitoring_unban.pop(username, None)
            break

print("Instagram Monitoring Bot: ONLINE")
keep_alive()
app.run()
