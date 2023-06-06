import os
import discord
import asyncio

from discord.ext import commands
from discord.ext.commands import Bot



intents = discord.Intents.all()
bot = Bot(commands.when_mentioned_or("/"), intents=intents, help_command=None)
intents.message_content = True

hidup = True
mati = False
bot.sync_command = hidup

@bot.event
async def on_ready():
    print("Bot is ready!")
    if bot.sync_command:
        print("menyinkronkan command")
        await bot.tree.sync()
    else:
        print("Opsi sinkronisasi perintah dinonaktifkan.")



async def load_cog():
    for cog in os.listdir("cogs"):
        if cog.endswith(".py"):
            try:
                await bot.load_extension("cogs.{}".format(cog[:-3]))
                print("Loaded cog: {}".format(cog))
            except Exception as e:
                print(e)


if __name__ == "__main__":
    asyncio.run(load_cog())
    bot.run("MTEwNDUxOTIwNTAyNzU3Nzg5OQ.G787g_.JjSWA25vNBwMsJbEeNAgkIDby7xIEYtsgzzWrE")