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
# 2. CONFIGURATION & TOKEN
# ==========================================
# Render settings se Token uthayega
TOKEN = os.getenv('DISCORD_TOKEN')

GIF_URL = "https://media.tenor.com/tC7C8f_r3iQAAAAd/anime-boy.gif"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"
}

# Intents Setup (Zaroori hai)
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

monitoring_list = {}

# ==========================================
# 3. LOGIC (Scraping)
# ==========================================
def get_instagram_data(username):
    url = f"https://www.picuki.com/profile/{username}"
    try:
        # Request bhej kar dekho
        response = requests.get(url, headers=HEADERS, timeout=10)
        
        # Agar page khul gaya (Status 200)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            try:
                followers = soup.find("span", class_="followed_by").text.strip()
                following = soup.find("span", class_="follows").text.strip()
                pfp = soup.find("div", class_="profile-avatar").find("img")['src']
            except:
                # Agar details na mile par page active hai
                followers = "Hidden"; following = "Hidden"; pfp = ""
            return {"status": "active", "followers": followers, "following": following, "pfp": pfp}
            
        # Agar page nahi mila (Status 404 - Matlab Banned)
        elif response.status_code == 404:
            return {"status": "banned"}
            
        # Koi aur error
        else:
            return {"status": "error"}
    except:
        return {"status": "error"}

# ==========================================
# 4. BOT EVENTS
# ==========================================
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="Poke Ash Agency"))
    if not monitor_task.is_running():
        monitor_task.start()

# ==========================================
# 5. COMMANDS
# ==========================================
@bot.command()
async def check(ctx, username: str = None):
    if not username: return await ctx.send("Usage: `!check <username>`")
    
    username = username.replace("@", "").lower().strip()
    status_msg = await ctx.send(f"🔎 Checking `@{username}`...")
    
    # Background mein check karo taaki bot freeze na ho
    data = await asyncio.to_thread(get_instagram_data, username)
    
    if data['status'] == 'active':
        embed = discord.Embed(color=discord.Color.green())
        embed.set_author(name="Poke Ash Agency Check", icon_url=bot.user.display_avatar.url)
        embed.add_field(name="Username", value=f"@{username}", inline=False)
        embed.add_field(name="Followers", value=data['followers'], inline=True)
        embed.add_field(name="Following", value=data['following'], inline=True)
        embed.add_field(name="Status", value="✅ **Active**", inline=False)
        if data['pfp']: embed.set_thumbnail(url=data['pfp'])
        await status_msg.edit(content=None, embed=embed)
        
    elif data['status'] == 'banned':
        embed = discord.Embed(description=f"❌ **@{username}** is Banned or Not Found.", color=discord.Color.red())
        await status_msg.edit(content=None, embed=embed)
        
    else:
        await status_msg.edit(content="⚠️ Error fetching data. Try again.")

@bot.command()
async def monitor(ctx, username: str = None):
    if not username: return await ctx.send("Usage: `!monitor <username>`")
    
    username = username.replace("@", "").lower().strip()
    
    if username in monitoring_list:
        return await ctx.send(f"⚠️ Already monitoring `@{username}`")
    
    # Pehle check karo ki wo active toh nahi hai
    initial_check = await asyncio.to_thread(get_instagram_data, username)
    if initial_check['status'] == 'active':
        return await ctx.send(f"❌ `@{username}` is already Active!")
    
    embed = discord.Embed(description=f"🔭 **Poke Ash Agency** started monitoring `@{username}`", color=discord.Color.purple())
    await ctx.send(embed=embed)
    
    # List mein add karo
    monitoring_list[username] = {
        'channel_id': ctx.channel.id, 
        'user_id': ctx.author.id, 
        'start_time': datetime.datetime.now()
    }

@bot.command()
async def status(ctx):
    if not monitoring_list:
        return await ctx.send("💤 Not monitoring any accounts.")
    msg = "**Currently Monitoring:**\n"
    for user in monitoring_list:
        msg += f"• `@{user}`\n"
    await ctx.send(msg)

# ==========================================
# 6. MONITORING LOOP
# ==========================================
@tasks.loop(seconds=20)
async def monitor_task():
    # List ki copy banao taaki loop ke dauran error na aaye
    for username in list(monitoring_list.keys()):
        try:
            user_data = monitoring_list[username]
            current_status = await asyncio.to_thread(get_instagram_data, username)
            
            # Agar Account Unban (Active) ho gaya
            if current_status['status'] == 'active':
                channel = bot.get_channel(user_data['channel_id'])
                
                # Time calculate karo
                duration = datetime.datetime.now() - user_data['start_time']
                hours, remainder = divmod(duration.seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                
                # Embed banao
                embed = discord.Embed(color=0x9b59b6)
                embed.set_author(name="Poke Ash Agency", icon_url=bot.user.display_avatar.url)
                embed.description = (
                    f"**Monitoring Status:** Account Unbanned 🔓\n"
                    f"**{username}** 🔰✅ | **Followers:** {current_status['followers']} |\n"
                    f"**Time taken:** {duration.days}d {hours}h {minutes}m {seconds}s"
                )
                embed.set_image(url=GIF_URL)
                if current_status['pfp']: 
                    embed.set_footer(text="Poke Ash Agency", icon_url=current_status['pfp'])
                
                if channel:
                    await channel.send(f"<@{user_data['user_id']}>", embed=embed)
                
                # List se remove karo
                del monitoring_list[username]
                
        except Exception as e:
            print(f"Error checking {username}: {e}")

# ==========================================
# 7. RUN
# ==========================================
keep_alive()

if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ ERROR: Token not found in Environment Variables!")
    
