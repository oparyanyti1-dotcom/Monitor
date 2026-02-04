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
def home(): return "Insta Monitor (Login Mode): ACTIVE 🟢"

def run(): server.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
def keep_alive(): Thread(target=run).start()

# ================= CONFIGURATION =================
API_ID = 35920777 
API_HASH = "99b5f89a6cf2e2f820ce41c2143c82fb" 
BOT_TOKEN = "7850428090:AAE49bQPsIjK1gXkainWR0ERWDxSjWV-X_c"

# ⚠️ APNI FAKE ID KI DETAILS YAHAN DALEIN
INSTA_USER = "disabledmonitor"
INSTA_PASS = "Zyrexx@171212"

app = Client("insta_login_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
L = instaloader.Instaloader()

# --- Login Function ---
try:
    print("Logging into Instagram...")
    L.login(INSTA_USER, INSTA_PASS)
    print("Login Successful!")
except Exception as e:
    print(f"Login Failed: {e}")

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
    except instaloader.exceptions.ProfileNotExistsException:
        return {"status": "banned"}
    except Exception as e:
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
    status_msg = await message.reply_text(f"🔍 **Direct Scan:** @{username}...")
    
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
        await status_msg.edit(f"⚠️ **Error:** {data.get('msg')}")

@app.on_message(filters.command("monitorban", prefixes="!"))
async def monitor_ban_cmd(client, message):
    if len(message.command) < 2: return
    username = message.command[1].replace("@", "")
    monitoring_ban[username] = message.chat.id
    await message.reply_text(f"🛡️ **Ban Monitor ON:** @{username}\nInterval: 5m")
    asyncio.create_task(ban_checker(client, username, message.chat.id))

@app.on_message(filters.command("monitorub", prefixes="!"))
async def monitor_unban_cmd(client, message):
    if len(message.command) < 2: return
    username = message.command[1].replace("@", "")
    monitoring_unban[username] = {'chat_id': message.chat.id, 'start_time': time.time()}
    await message.reply_text(f"⏳ **Unban Monitor ON:** @{username}\nInterval: 5m")
    asyncio.create_task(unban_checker(client, username))

@app.on_message(filters.command("stop", prefixes="!"))
async def stop_monitor(client, message):
    if len(message.command) < 2: return
    username = message.command[1].replace("@", "")
    monitoring_ban.pop(username, None)
    monitoring_unban.pop(username, None)
    await message.reply_text(f"🛑 **Monitoring Stopped:** @{username}")

# ================= BACKGROUND TASKS =================

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
            await client.send_message(info['chat_id'], f"🎉 **UNBANNED DETECTED!**\n\n✅ **User:** @{username}\n⏱️ **Time:** {time_taken}\n━━━━━━━━━━━━━━━━━━━━\n✨ @DisabledMM")
            monitoring_unban.pop(username, None)
            break

print("Professional Monitor Bot Starting...")
keep_alive()
app.run()
