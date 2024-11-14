from datetime import datetime, timedelta
import disnake
from disnake.ext import commands
from .warns_db import warndb


bot = commands.Bot(command_prefix="!", intents=disnake.Intents.all())
moderators = {}

class Slash(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    class Moder(commands.Cog):
        cog_name = "🛡️  Модерирование "

        def __init__(self, bot):
            self.bot = bot

        @commands.slash_command(name="clear", description="Очистить сообщения в канале")
        @commands.has_permissions(manage_messages=True)
        async def clear_messages(self, inter: disnake.ApplicationCommandInteraction, amount: int):
            channel = inter.channel
            # Убедимся, что количество сообщений для удаления не меньше 1
            if amount < 1:
                await inter.response.send_message("Пожалуйста, укажите число больше 0.", ephemeral=True)
                return
            messages = await channel.history(limit=amount).flatten()
            if messages:
                await channel.purge(limit=amount)  # Удаление сообщений
                await inter.response.send_message(f"{amount} сообщений удалены успешно.", ephemeral=True)
            else:
                await inter.response.send_message("Нет сообщений для удаления.", ephemeral=True)

        @commands.slash_command(name="kick", description="Кикнуть кого-то с сервера")
        @commands.has_permissions(kick_members=True)
        async def kick(self, ctx, user: disnake.Member, reason="Нарушение правил"):
            moderators[user.id] = ctx.author.id
            await user.kick(reason=reason)
            await ctx.response.send_message(f"Пользователь кикнут", ephemeral=True)

        @commands.slash_command(name="ban", description="Забанить кого-то на сервере")
        @commands.has_permissions(ban_members=True)
        async def ban(self, ctx, user: disnake.User, reason="Нарушение правил"):
            moderators[user.id] = ctx.author.id
            await ctx.guild.ban(user, reason=reason)
            await ctx.response.send_message("Бан выдан", ephemeral=True)

        @commands.slash_command(name="mute", description="Замутить участника",
                                usage="mute <участник> <время> [причина]")
        @commands.has_permissions(moderate_members=True)
        async def mute(self, ctx, user: disnake.Member, time: int, reason="Не следил за языком"):
            expired_at = datetime.now() + timedelta(minutes=int(time))
            moderators[user.id] = ctx.author.id
            await user.timeout(reason=reason, until=expired_at)
            await ctx.response.send_message("Мут выдан", ephemeral=True)

        @commands.slash_command(name="unban", description="Разбанить кого-то на сервере")
        @commands.has_permissions(ban_members=True)
        async def unban(self, ctx, user: disnake.User, reason="Искупил вину"):
            moderators[user.id] = ctx.author.id
            await ctx.guild.unban(user, reason=reason)
            await ctx.response.send_message(f"Пользователь разбанен", ephemeral=True)

        @commands.slash_command(name="unmute", description="Размутить кого-то на сервере")
        @commands.has_permissions(moderate_members=True)
        async def unmute(self, ctx, user: disnake.Member, reason="Подобающее повоедение"):
            moderators[user.id] = ctx.author.id
            await user.timeout(until=None, reason=reason)
            await ctx.response.send_message(f"Мут снят", ephemeral=True)

    class Info(commands.Cog):
        cog_name = "📋  Информация "

        def __init__(self, bot):
            self.bot = bot

        @commands.slash_command(name="help", description="Показывает список возможных команд")
        async def help(self, ctx):
            categories = [Slash.Moder, Slash.Info, warndb]
            embed = disnake.Embed(title="Вот твой список команд:", color=disnake.Color.blue())

            for category in categories:
                cog_instance = category(self.bot)  # Create an instance of the cog
                commands_info = [f"/{command.name}: {command.description}" for command in
                                 cog_instance.get_slash_commands()]
                if commands_info:
                    embed.add_field(name=category.cog_name, value="\n".join(commands_info), inline=False)

            await ctx.send(embed=embed)


bot.add_cog(Slash(bot))


def setup(bot):
    bot.add_cog(Slash(bot))
    bot.add_cog(Slash.Moder(bot))
    bot.add_cog(Slash.Info(bot))
