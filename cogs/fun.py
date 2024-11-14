import disnake
from disnake.ext import commands
bot = commands.Bot(command_prefix="!", intents=disnake.Intents.all())


class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

def setup(bot):
    bot.add_cog(Fun(bot))