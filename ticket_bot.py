import os
import asyncio
from flask import Flask
from threading import Thread
import discord
from discord.ext import commands

# 1. 렌더 웹 서비스 포트 바인딩 방지용 웹 서버
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_web)
    t.start()

# 2. 디스코드 봇 설정
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("Bot is ready and online!")

# 여기에 네가 구현할 티켓 생성이나 기타 봇 명령어 코드를 추가하면 돼!
# 예시:
# @bot.command()
# async def ping(ctx):
#     await ctx.send("Pong!")

TOKEN = os.getenv("DISCORD_TOKEN")

if __name__ == "__main__":
    if not TOKEN:
        print("ERROR: DISCORD_TOKEN is not set!")
    else:
        keep_alive()
        bot.run(TOKEN)
