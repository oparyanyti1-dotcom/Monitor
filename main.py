import asyncio
import os
import requests
import re
from pyrogram import Client, filters
from threading import Thread
from flask import Flask

# ================= SERVER KEEPER =================
server = Flask(__name__)
@server.route('/')
def home(): return "Theory Bot: Status + Count Mode 🟢"

def run():
    port = int(os.environ.get("PORT", 8080))
    server.run(host="0.0.0.0", port=port)

def keep_alive():
    Thread(target=run).start()

# ================= CONFIGURATION =================
API_ID = 35920777 
API_HASH = "99b5f89a6cf2e2f820ce41c2143c82fb" 
BOT_TOKEN = "7850428090:AAE49bQPsIjK1gXkainWR0ERWDxSjWV-X_c"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
}

app = Client("theory_count_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- Data Fetcher (Bina Login Wala Logic) ---
def fetch_insta_data(username):
    url = f"https://www.instagram.com/{username}/"
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        
        if response.status_code == 200:
            # Followers/Following nikalne ki koshish (Meta Tags se)
            # Note: Ye tabhi kaam karega jab Instagram Login Wall na dikhaye
            content = response.text
            meta_desc = re.search(r'<meta content="([^"]+)" name="description"', content)
            
            if meta_desc:
                desc_text = meta_desc.group(1) # Example: "100 Followers, 50 Following..."
                return {"status": "active", "data": desc_text}
            else:
                return {"status": "partial", "reason": "Instagram ne Login Wall (Popup) dikha di hai. Counts nahi dikh rahe."}
        
        elif response.status_code == 404:
            return {"status": "banned", "reason": "Account ya toh ban ho gaya hai ya username galat hai (404 Error)."}
        
        elif response.status_code == 429:
            return {"status": "error", "reason": "Too Many Requests (429). Instagram ne IP block kar diya hai. 1-2 ghante wait karo."}
        
        else:
            return {"status": "error", "reason": f"Server Error: {response.status_code}"}
            
    except Exception as e:
        return {"status": "error", "reason": f"Connection Failed: {str(e)}"}

# ================= COMMANDS =================

@app.on_message(filters.command("check", prefixes="!"))
async def check_cmd(client, message):
    if len(message.command) < 2:
        await message.reply_text("✨ **Usage:** `!check [username]`")
        return
    
    username = message.command[1].replace("@", "")
    msg = await message.reply_text(f"🔍 **Theory Scan:** @{username}...")
    
    res = fetch_insta_data(username)
    
    if res["status"] == "active":
        await msg.edit(f"👤 **INSTAGRAM PROFILE**\n━━━━━━━━━━━━━━━━━━━━\n✅ **Status:** Active\n📊 **Info:** {res['data']}\n━━━━━━━━━━━━━━━━━━━━\n✨ @DisabledMM")
    
    elif res["status"] == "partial":
        await msg.edit(f"✅ **Status:** Active\n⚠️ **Notice:** {res['reason']}\n\n*Tip: Followers dekhne ke liye session login zaroori hai.*")
    
    else:
        await msg.edit(f"❌ **Failed!**\n━━━━━━━━━━━━━━━━━━━━\n🧐 **Kyu nahi aaya?**\n{res['reason']}\n━━━━━━━━━━━━━━━━━━━━")

print("Theory Bot with Error Reporting Starting...")
keep_alive()
app.run()
