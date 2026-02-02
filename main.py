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
# 1. SERVER KEEP ALIVE
# ==========================================
app = Flask('')

@app.route('/')
def home():
    return "Poke Ash Agency Bot is 24/7 Live with Proxy!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# ==========================================
# 2. CONFIGURATION
# ==========================================
TOKEN = os.getenv('DISCORD_TOKEN')
PROXY_KEY = os.getenv('SCRAPER_API_KEY') # Ye key Render se aayegi

GIF_URL = "https://media.tenor.com/tC7C8f_r3iQAAAAd/anime-boy.gif"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

monitoring_list = {}

# ==========================================
# 3. PROXY SCRAPER LOGIC (Ye Block Nahi Hoga)
# ==========================================
def get_instagram_data(username):
    # Hum Picuki check karenge lekin Proxy ke through
    target_url = f"https://www.picuki.com/profile/{username}"
    
    # Agar Proxy Key nahi hai toh error do
    if not PROXY_KEY:
        return {"status": "error", "msg": "Proxy Key Missing in Render!"}

    # Request Proxy Server ke through bhejo
    proxy_url = "http://api.scraperapi.com"
    params = {
        'api_key': PROXY_KEY,
        'url': target_url
    }

    try:
        # Proxy request (Slow ho sakta hai, 5-10 sec)
        response = requests.get(proxy_url, params=params, timeout=60)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Data dhundo
            try:
                followers = soup.find("span", class_="followed_by").text.strip()
                following = soup.find("span", class_="follows").text.strip()
                pfp = soup.find("div", class_="profile-avatar").find("img")['src']
                return {"status": "active", "followers": followers, "following": following, "pfp": pfp}
            except:
                return {"status": "error", "msg": "Profile Hidden/Loading Error"}
                
        elif response.status_code == 404:
            return {"status": "banned"}
        else:
            return {"status": "error", "msg": f"Proxy Error: {response.status_code}"}
            
    except Exception as e:
        return {"status": "error", "msg": "Connection Failed"}

# ==========================================
# 4. EVENTS & COMMANDS
# ==========================================
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="Instagram via Proxy"))
    if not monitor_task.is_running():
        monitor_task.start()

@bot.command()
async def check(ctx, username: str = None):
    if not username: return await ctx.send("Usage: `!check <username>`")
    username = username.replace("@", "").lower().strip()
    
    msg = await ctx.send(f"🔎 Checking `@{username}` via Secure Proxy... (Wait 10s)")
    
    # Background mein run karo
    data = await asyncio.to_thread(get_instagram_data, username)
    
    if data['status'] == 'active':
        embed = discord.Embed(color=discord.Color.green())
        embed.set_author(name="Poke Ash Agency", icon_url=bot.user.display_avatar.url)
        embed.add_field(name="Username", value=f"@{username}", inline=False)
        embed.add_field(name="Followers", value=data['followers'], inline=True)
        embed.add_field(name="Following", value=data['following'], inline=True)
        embed.add_field(name="Status", value="✅ **Active**", inline=False)
        if data['pfp']: embed.set_thumbnail(url=data['pfp'])
        await msg.edit(content=None, embed=embed)
        
    elif data['status'] == 'banned':
        embed = discord.Embed(description=f"❌ **@{username}** is Banned.", color=discord.Color.red())
        await msg.edit(content=None, embed=embed)
    else:
        await msg.edit(content=f"⚠️ Error: {data.get('msg', 'Unknown Error')}")

@bot.command()
async def monitor(ctx, username: str = None):
    if not username: return await ctx.send("Usage: `!monitor <username>`")
    username = username.replace("@", "").lower().strip()
    
    if username in monitoring_list: return await ctx.send("⚠️ Already monitoring!")
    
    # Pehla check
    initial = await asyncio.to_thread(get_instagram_data, username)
    if initial['status'] == 'active': return await ctx.send(f"❌ `@{username}` is already Active!")
    
    await ctx.send(embed=discord.Embed(description=f"🔭 Monitoring `@{username}` (Proxy Mode)", color=discord.Color.purple()))
    monitoring_list[username] = {'channel_id': ctx.channel.id, 'user_id': ctx.author.id, 'start_time': datetime.datetime.now()}

# ==========================================
# 5. LOOP
# ==========================================
@tasks.loop(minutes=2) # Proxy limit bachane ke liye time 2 min kiya hai
async def monitor_task():
    for username in list(monitoring_list.keys()):
        try:
            data = monitoring_list[username]
            check = await asyncio.to_thread(get_instagram_data, username)
            
            if check['status'] == 'active':
                channel = bot.get_channel(data['channel_id'])
                duration = datetime.datetime.now() - data['start_time']
                
                embed = discord.Embed(color=0x9b59b6)
                embed.description = (f"**Account Unbanned** 🔓\n**{username}** ✅ | **Followers:** {check.get('followers')}")
                embed.set_image(url=GIF_URL)
                
                if channel: await channel.send(f"<@{data['user_id']}>", embed=embed)
                del monitoring_list[username]
        except: pass

keep_alive()
if TOKEN:
    bot.run(TOKEN)
    
