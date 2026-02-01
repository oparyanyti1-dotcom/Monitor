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
# 1. KEEP ALIVE SERVER (For Render)
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
# YE LINE TOKEN KO RENDER KI SETTINGS SE LEGI (SAFE HAI)
TOKEN = os.environ.get('MTQ2NzQ2NDAzODQwNDMyOTU1NA.GAV2Pu.FIVwroH1uFGNKI3Znu85OHB9_wYM-JFn7d4RYA') 

# You can change this to any GIF you want
GIF_URL = "https://media.tenor.com/tC7C8f_r3iQAAAAd/anime-boy.gif"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"
}

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

monitoring_list = {}

# ==========================================
# 3. LOGIC
# ==========================================
def get_instagram_data(username):
    url = f"https://www.picuki.com/profile/{username}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            try:
                followers = soup.find("span", class_="followed_by").text.strip()
                following = soup.find("span", class_="follows").text.strip()
                pfp = soup.find("div", class_="profile-avatar").find("img")['src']
            except:
                followers = "0"; following = "0"; pfp = ""
            return {"status": "active", "followers": followers, "following": following, "pfp": pfp}
        elif response.status_code == 404:
            return {"status": "banned"}
        else:
            return {"status": "error"}
    except:
        return {"status": "error"}

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    # Sets the status to "Watching Poke Ash Agency"
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="Poke Ash Agency"))
    monitor_task.start()

@bot.command()
async def check(ctx, username: str = None):
    if not username: return await ctx.send("Usage: `!check <username>`")
    username = username.replace("@", "").lower().strip()
    msg = await ctx.send(f"🔎 **Poke Ash Agency** is checking `@{username}`...")
    
    data = await asyncio.to_thread(get_instagram_data, username)
    
    if data['status'] == 'active':
        embed = discord.Embed(color=discord.Color.green())
        embed.set_author(name="Poke Ash Agency", icon_url=bot.user.display_avatar.url)
        embed.add_field(name="Username", value=f"@{username}", inline=False)
        embed.add_field(name="Followers", value=data['followers'], inline=True)
        embed.add_field(name="Following", value=data['following'], inline=True)
        embed.add_field(name="Status", value="✅ **Active**", inline=False)
        embed.set_thumbnail(url=data['pfp'])
        await msg.edit(content=None, embed=embed)
    elif data['status'] == 'banned':
        embed = discord.Embed(description=f"❌ **@{username}** is Banned.", color=discord.Color.red())
        embed.set_footer(text="Poke Ash Agency Check")
        await msg.edit(content=None, embed=embed)
    else:
        await msg.edit(content="⚠️ Connection Error. Try again.")

@bot.command()
async def monitor(ctx, username: str = None):
    if not username: return await ctx.send("Usage: `!monitor <username>`")
    username = username.replace("@", "").lower().strip()
    
    if username in monitoring_list: return await ctx.send(f"⚠️ **Poke Ash Agency** is already monitoring `@{username}`")
    
    initial = await asyncio.to_thread(get_instagram_data, username)
    if initial['status'] == 'active': return await ctx.send(f"❌ `@{username}` is already active!")
    
    embed = discord.Embed(description=f"🔭 **Poke Ash Agency** started monitoring `@{username}`", color=discord.Color.purple())
    await ctx.send(embed=embed)
    
    monitoring_list[username] = {'channel_id': ctx.channel.id, 'user_id': ctx.author.id, 'start_time': datetime.datetime.now()}

@tasks.loop(seconds=20)
async def monitor_task():
    for username in list(monitoring_list.keys()):
        data = monitoring_list[username]
        check = await asyncio.to_thread(get_instagram_data, username)
        
        if check['status'] == 'active':
            channel = bot.get_channel(data['channel_id'])
            duration = datetime.datetime.now() - data['start_time']
            hours, remainder = divmod(duration.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            
            # --- THE EXACT EMBED STYLE ---
            embed = discord.Embed(color=0x9b59b6)
            embed.set_author(name="Poke Ash Agency", icon_url=bot.user.display_avatar.url)
            
            # The Description Format
            embed.description = (
                f"**Monitoring Status:** Account Unbanned |\n"
                f"**{username}** 🔰✅ | **Followers:** {check['followers']} |\n"
                f"**Time taken:** {duration.days}d {hours}h {minutes}m {seconds}s"
            )
            
            embed.set_image(url=GIF_URL)
            embed.set_footer(text="Poke Ash Agency", icon_url=check['pfp'])
            
            if channel: 
                await channel.send(f"<@{data['user_id']}>", embed=embed)
            
            del monitoring_list[username]

monitor_task.before_loop(bot.wait_until_ready)

keep_alive()
bot.run(TOKEN)

