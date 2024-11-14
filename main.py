import os
import sqlite3
import disnake 
from disnake.ext import commands
from cogs.AutoMod import AutoMod



bot = commands.Bot(command_prefix="!", help_command=None, intents=disnake.Intents.all(), test_guilds=[1100921385230028890])  #server id
db = sqlite3.connect("amod.db")
cursor = db.cursor()
banned_words = ["Нигер","нига","нага","негр","черножопый","черномазый","фагот","пидр","пидор","пидорас","педик",
                "гомик","глиномес","хохол","кацап","москаль","русня","хач","жид","чурка","даун","аутист","ретатрд",
                "вирджин","девтсвенник","симп","ницел","cunt","шлюха","куколд" ]


@commands.Cog.listener()
async def on_ready(self):
    # При подключении бота к серверу, ищем и инициализируем канал
    self.channel = self.bot.get_channel(self.channel_id)

@bot.command()
@commands.is_owner()
async def load(ctx, extension):
    bot.load_extension(f"cogs.{extension}")

@bot.command()
@commands.is_owner()
async def unload(ctx, extension):
    bot.unload_extension(f"cogs.{extension}")

@bot.command()
@commands.is_owner()
async def reload(ctx, extension):
    bot.reload_extension(f"cogs.{extension}")

for filename in os.listdir("cogs"):
    if filename.endswith(".db"):
        pass

for filename in os.listdir("cogs"):
    if filename.endswith(".py"):
        bot.load_extension(f"cogs.{filename[:-3]}")

@bot.event
async def on_message(message):
    await bot.process_commands(message)
    for content in message.content.split():
        for censored_word in banned_words:
            if content.lower() == censored_word:
                await message.delete()
                auto_mod = AutoMod(bot)  # Создание экземпляра класса AutoMod
                await auto_mod.amod(await bot.get_context(message), user=message.author)

async def on_ready(self):
    print(f"Bot {self.bot.user} is ready to work!")

bot.run("MTE2MjQzNDAzNTc4ODgyMDUwMQ.GwPup5.z2HmEEDOFZx2rtW_scr6D3o5QZIAhrwFDcGBvg")
