import discord
from discord.ext import commands, tasks
import requests
from bs4 import BeautifulSoup
import datetime
import asyncio
import os
from flask import Flask
from threading import Thread
import random

# ==========================================
# 1. KEEP ALIVE SERVER
# ==========================================
app = Flask('')

@app.route('/')
def home():
    return "Poke Ash Agency Bot is Online!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# ==========================================
# 2. CONFIGURATION
# ==========================================
TOKEN = os.getenv('DISCORD_TOKEN')

GIF_URL = "https://media.tenor.com/tC7C8f_r3iQAAAAd/anime-boy.gif"

# ✅ NEW: Anti-Block Headers (Bot ko Insaan dikhane ke liye)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Referer": "https://www.google.com/"
}

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

monitoring_list = {}

# ==========================================
# 3. LOGIC (Smart Scraper)
# ==========================================
def get_instagram_data(username):
    url = f"https://www.picuki.com/profile/{username}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        
        # Agar Block Page aa jaye
        if "Just a moment" in response.text or "Attention Required" in response.text:
            return {"status": "error", "msg": "Blocked by Website"}

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Check karein ki profile mili ya nahi
            if soup.find("span", class_="followed_by"):
                followers = soup.find("span", class_="followed_by").text.strip()
                return {"status": "active", "followers": followers, "pfp": ""}
            else:
                # Page khula par profile nahi mili (Matlab Hidden/Error)
                return {"status": "error", "msg": "Profile Hidden/Private"}
        
        elif response.status_code == 404:
            return {"status": "banned"}
        else:
            return {"status": "error", "msg": f"Status Code {response.status_code}"}
    except Exception as e:
        return {"status": "error", "msg": "Connection Error"}

# ==========================================
# 4. EVENTS & COMMANDS
# ==========================================
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="Poke Ash Agency"))
    if not monitor_task.is_running():
        monitor_task.start()

@bot.command()
async def check(ctx, username: str = None):
    if not username: return await ctx.send("Usage: `!check <username>`")
    username = username.replace("@", "").lower().strip()
    msg = await ctx.send(f"🔎 Checking `@{username}`...")
    
    data = await asyncio.to_thread(get_instagram_data, username)
    
    if data['status'] == 'active':
        embed = discord.Embed(color=discord.Color.green())
        embed.set_author(name="Poke Ash Agency", icon_url=bot.user.display_avatar.url)
        embed.add_field(name="Username", value=f"@{username}", inline=False)
        embed.add_field(name="Followers", value=data.get('followers', 'N/A'), inline=True)
        embed.add_field(name="Status", value="✅ **Active**", inline=False)
        await msg.edit(content=None, embed=embed)
    elif data['status'] == 'banned':
        await msg.edit(content=None, embed=discord.Embed(description=f"❌ **@{username}** is Banned.", color=discord.Color.red()))
    else:
        await msg.edit(content=f"⚠️ Error: {data.get('msg', 'Unknown Error')}")

@bot.command()
async def monitor(ctx, username: str = None):
    if not username: return await ctx.send("Usage: `!monitor <username>`")
    username = username.replace("@", "").lower().strip()
    
    if username in monitoring_list: return await ctx.send("⚠️ Already monitoring!")
    
    initial = await asyncio.to_thread(get_instagram_data, username)
    if initial['status'] == 'active': return await ctx.send(f"❌ `@{username}` is already Active!")
    
    await ctx.send(embed=discord.Embed(description=f"🔭 Monitoring `@{username}`", color=discord.Color.purple()))
    monitoring_list[username] = {'channel_id': ctx.channel.id, 'user_id': ctx.author.id, 'start_time': datetime.datetime.now()}

# ==========================================
# 5. LOOP
# ==========================================
@tasks.loop(seconds=30)
async def monitor_task():
    for username in list(monitoring_list.keys()):
        try:
            data = monitoring_list[username]
            check = await asyncio.to_thread(get_instagram_data, username)
            
            if check['status'] == 'active':
                channel = bot.get_channel(data['channel_id'])
                
                embed = discord.Embed(color=0x9b59b6)
                embed.description = (f"**Account Unbanned** 🔓\n**{username}** ✅ | **Followers:** {check.get('followers', '0')}")
                embed.set_image(url=GIF_URL)
                
                if channel: await channel.send(f"<@{data['user_id']}>", embed=embed)
                del monitoring_list[username]
        except: pass

keep_alive()
if TOKEN:
    bot.run(TOKEN)
    
