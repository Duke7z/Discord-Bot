import sqlite3
import disnake
import asyncio
from disnake.ext import commands
from .slashcommands import Slash
from .warns_db import warndb

bot = commands.Bot(command_prefix="!", intents=disnake.Intents.all())
db = sqlite3.connect("amod.db")
cursor = db.cursor()

class AutoMod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.warns_db_cog = bot.get_cog('warndb')
        
    async def amod(self, ctx, user: disnake.Member):
        target = user
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS amod (
            user_id INTEGER,
            automod_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
            """
        )
        cursor.execute("SELECT MAX(automod_id) FROM amod WHERE user_id=?", (target.id,))
        result = cursor.fetchone()
        max_automods = result[0]  # Извлекаем значение из первого элемента кортежа
        if max_automods is None:
            automod_id = 1
        else:
            automod_id = max_automods + 1
        cursor.execute("INSERT INTO amod (user_id, automod_id) VALUES (?, ?)",
                       (target.id, automod_id))
        db.commit()
        if automod_id == 1:
            await Slash.Moder.mute(bot, ctx, user, time=60, reason="Банворд")
        elif automod_id == 2:
            await asyncio.gather(
                Slash.Moder.mute(bot, ctx, user, time=180, reason="Банворд"),
                self.warns_db_cog.warn(ctx, user, time=10080, reason="Банворд")
            )
        elif automod_id == 3:
            cursor.execute("DELETE FROM amod WHERE user_id=?", (user.id,))
            db.commit()
            await Slash.Moder.ban(bot, ctx, user, reason="Неоднократное использование банвордов")


def setup(bot):
    bot.add_cog(AutoMod(bot))