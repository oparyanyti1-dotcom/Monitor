import discord
from discord.ext import commands, tasks
import requests
from bs4 import BeautifulSoup
import datetime
import asyncio
import os
from flask import Flask
from threading import Thread

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

# GIF for Embed
GIF_URL = "https://media.tenor.com/tC7C8f_r3iQAAAAd/anime-boy.gif"

# Headers to look like a Real Browser
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

monitoring_list = {}

# ==========================================
# 3. LOGIC (Switched to Imginn)
# ==========================================
def get_instagram_data(username):
    # Ab hum Imginn use karenge jo block nahi karta
    url = f"https://imginn.com/{username}/"
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        
        # Agar status 200 hai matlab page khul gaya (Active)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Data scrape karne ki koshish
            try:
                # Imginn par naam ya stats dhoondo
                if soup.find("h1"): # Profile Name
                    return {"status": "active", "followers": "Active (Count Hidden)", "pfp": ""}
                else:
                    return {"status": "error", "msg": "Page Loaded but No Profile"}
            except:
                return {"status": "active", "followers": "Active", "pfp": ""}
        
        # Agar 404 hai matlab user nahi mila (Banned)
        elif response.status_code == 404:
            return {"status": "banned"}
            
        else:
            return {"status": "error", "msg": f"Status: {response.status_code}"}
            
    except Exception as e:
        return {"status": "error", "msg": "Server Error"}

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
    msg = await ctx.send(f"🔎 Checking `@{username}` on Imginn...")
    
    data = await asyncio.to_thread(get_instagram_data, username)
    
    if data['status'] == 'active':
        embed = discord.Embed(color=discord.Color.green())
        embed.set_author(name="Poke Ash Agency", icon_url=bot.user.display_avatar.url)
        embed.add_field(name="Username", value=f"@{username}", inline=False)
        embed.add_field(name="Status", value="✅ **Active / Unbanned**", inline=False)
        embed.set_footer(text="Source: Imginn")
        await msg.edit(content=None, embed=embed)
        
    elif data['status'] == 'banned':
        embed = discord.Embed(description=f"❌ **@{username}** is Banned or Not Found.", color=discord.Color.red())
        await msg.edit(content=None, embed=embed)
        
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
@tasks.loop(seconds=45) # Time badha diya taaki block na ho
async def monitor_task():
    for username in list(monitoring_list.keys()):
        try:
            data = monitoring_list[username]
            check = await asyncio.to_thread(get_instagram_data, username)
            
            if check['status'] == 'active':
                channel = bot.get_channel(data['channel_id'])
                
                embed = discord.Embed(color=0x9b59b6)
                embed.description = (f"**Account Unbanned** 🔓\n**{username}** ✅")
                embed.set_image(url=GIF_URL)
                
                if channel: await channel.send(f"<@{data['user_id']}>", embed=embed)
                del monitoring_list[username]
        except: pass

keep_alive()
if TOKEN:
    bot.run(TOKEN)
    
