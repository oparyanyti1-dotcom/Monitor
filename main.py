import asyncio
import time
import os
import instaloader
from pyrogram import Client, filters
from threading import Thread
from flask import Flask

# ================= SERVER KEEPER (Render Alive) =================
server = Flask(__name__)
@server.route('/')
def home(): return "Insta Monitor Service: ONLINE 🟢"

def run(): server.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
def keep_alive(): Thread(target=run).start()

# ================= CONFIGURATION =================

API_ID = 35920777 
API_HASH = "99b5f89a6cf2e2f820ce41c2143c82fb" 
BOT_TOKEN = "YAHAN_BOTFATHER_TOKEN_DALO" # BotFather wala token yahan bharein

# Aapki Image se nikali gayi details
INSTA_USER = "disabledmonitor" 
SESSION_ID = "80140188832%3AxuAndowMEdkSTh%3A13%3AAYjHT4M6C7FBMqZUPks1fwBrnl44iCtPC_TpCTeYVq"

app = Client("insta_session_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
L = instaloader.Instaloader()

# --- Load Session Logic ---
print("Authenticating with Instagram Session...")
L.context._session.cookies.set("sessionid", SESSION_ID)
print("Session Loaded Successfully! ✅")

# --- Helper: Time Formatter ---
def get_time_taken(seconds):
    days, seconds = divmod(int(seconds), 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    parts = []
    if days > 0: parts.append(f"{days}d")
    if hours > 0: parts.append(f"{hours}h")
    if minutes > 0: parts.append(f"{minutes}m")
    parts.append(f"{int(seconds)}s")
    return " ".join(parts)

# --- Data Fetcher ---
def get_insta_details(username):
    try:
        profile = instaloader.Profile.from_username(L.context, username)
        return {
            "status": "active",
            "username": profile.username,
            "followers": profile.followers,
            "following": profile.followees
        }
    except Exception as e:
        if "404" in str(e): return {"status": "banned"}
        return {"status": "error", "msg": str(e)}

# ================= COMMANDS =================

monitoring_ban = {}
monitoring_unban = {}

@app.on_message(filters.command("check", prefixes="!"))
async def check_user(client, message):
    if len(message.command) < 2:
        await message.reply_text("✨ **Usage:** `!check [username]`")
        return
    username = message.command[1].replace("@", "")
    status_msg = await message.reply_text(f"🔍 **Scanning:** @{username}...")
    
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
    elif data["status"] == "banned":
        await status_msg.edit(f"❌ **Alert:** @{username} is **Banned** or **Invalid**.")
    else:
        await status_msg.edit(f"⚠️ **Instagram Alert:** Request blocked (429). Thodi der baad try karein.")

@app.on_message(filters.command("monitorban", prefixes="!"))
async def monitor_ban_cmd(client, message):
    if len(message.command) < 2: return
    username = message.command[1].replace("@", "")
    monitoring_ban[username] = message.chat.id
    await message.reply_text(f"🛡️ **Surveillance Active (Ban):** @{username}\nInterval: 5m")
    asyncio.create_task(ban_checker(client, username, message.chat.id))

@app.on_message(filters.command("monitorub", prefixes="!"))
async def monitor_unban_cmd(client, message):
    if len(message.command) < 2: return
    username = message.command[1].replace("@", "")
    monitoring_unban[username] = {'chat_id': message.chat.id, 'start_time': time.time()}
    await message.reply_text(f"⏳ **Surveillance Active (Unban):** @{username}\nInterval: 5m")
    asyncio.create_task(unban_checker(client, username))

@app.on_message(filters.command("stop", prefixes="!"))
async def stop_monitor(client, message):
    if len(message.command) < 2: return
    username = message.command[1].replace("@", "")
    monitoring_ban.pop(username, None)
    monitoring_unban.pop(username, None)
    await message.reply_text(f"🛑 **Monitoring Stopped:** @{username}")

# ================= BACKGROUND LOGIC =================

async def ban_checker(client, username, chat_id):
    while username in monitoring_ban:
        await asyncio.sleep(300)
        data = get_insta_details(username)
        if data["status"] == "banned":
            await client.send_message(chat_id, f"🚨 **ACCOUNT REMOVED!**\n\n👤 **User:** @{username}\n━━━━━━━━━━━━━━━━━━━━\n✨ @DisabledMM")
            monitoring_ban.pop(username, None)
            break

async def unban_checker(client, username):
    while username in monitoring_unban:
        await asyncio.sleep(300)
        data = get_insta_details(username)
        if data["status"] == "active":
            info = monitoring_unban[username]
            time_taken = get_time_taken(time.time() - info['start_time'])
            await client.send_message(info['chat_id'], f"🎉 **RECOVERY DETECTED!**\n\n✅ **User:** @{username} is back.\n⏱️ **Time:** {time_taken}\n━━━━━━━━━━━━━━━━━━━━\n✨ @DisabledMM")
            monitoring_unban.pop(username, None)
            break

print("Bot is ready...")
keep_alive()
app.run()
