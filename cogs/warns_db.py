import disnake
from disnake.ext import commands
import sqlite3
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

bot = commands.Bot(command_prefix="!", help_command=None, intents=disnake.Intents.all())
db = sqlite3.connect("warns.db")
cursor = db.cursor()
scheduler = AsyncIOScheduler()
moderators = {}

class warndb(commands.Cog):
    cog_name = "❗ Варны"
    def __init__(self, bot):
        self.bot = bot

    async def remove_warn(self, user_id, warn_id, expires_at):
        print(f"Removing warn for user {user_id}, warn_id {warn_id}")  # Отладочный вывод
        user = self.bot.get_user(user_id)
        cursor.execute("SELECT reason, moder_id FROM warns WHERE user_id=? AND warn_id=?", (user_id, warn_id))
        result = cursor.fetchone()
        if result:
            reason = result[0]
            moderator_id = result[1]
            moderator = self.bot.get_user(moderator_id)
            embed = disnake.Embed(
                title="🌦️ | Варн истёк",
                description=f"У пользователя {user.name}({user.mention}) истёк варн.",
                color=disnake.Color.brand_green(),
            )
            embed.add_field(
                name=f"Модератор",
                value=f"{moderator.name}({moderator.mention})",
                inline=False
            )
            embed.add_field(
                name=f"Причина выдачи",
                value=f"{reason}",
                inline=False
            )
            embed.add_field(
                name=f"Номер варна",
                value=f"{warn_id}",
                inline=False
            )
            embed.set_footer(
                text=f"ID участника: {user.id}",
                icon_url=user.display_avatar
            )
            log_channel = self.bot.get_channel(1101567459737215047)  # Здесь используйте self.bot для доступа к вашему боту
            if log_channel:
                await log_channel.send(embed=embed)
            else:
                print("Log channel not found!")
        cursor.execute("DELETE FROM warns WHERE user_id=? AND warn_id=?", (user_id, warn_id))
        db.commit()
        job_id = f"unwarn_{user_id}_{warn_id}"
        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)
        else:
            pass

    async def setup_timers(self):
        cursor.execute("SELECT user_id, warn_id, expires_at, timer_id FROM warns")
        results = cursor.fetchall()
        for user_id, warn_id, expires_at, timer_id in results:
            if expires_at:
                expires_at_datetime = datetime.fromisoformat(expires_at)
                if expires_at_datetime >= datetime.now():
                    interval = expires_at_datetime - datetime.now()
                    trigger = IntervalTrigger(seconds=interval.total_seconds())
                    await self.remove_warn(user_id, warn_id, expires_at)
                    scheduler.add_job(self.remove_warn, trigger=trigger, id=timer_id,
                                          kwargs={'user_id': user_id, 'warn_id': warn_id, 'expires_at': expires_at})

    @commands.Cog.listener()
    async def on_ready(self):
        cursor.execute("SELECT user_id, warn_id, reason, expires_at, timer_id, task_id FROM warns")
        results = cursor.fetchall()

        for user_id, warn_id, reason, expires_at, timer_id, task_id in results:
            if expires_at:
                expires_at_datetime = datetime.fromisoformat(expires_at)
                if expires_at_datetime >= datetime.now():
                    interval = expires_at_datetime - datetime.now()
                    trigger = IntervalTrigger(seconds=interval.total_seconds())
                    scheduler.add_job(self.remove_warn, trigger=trigger, id=timer_id,
                                      kwargs={'user_id': user_id, 'warn_id': warn_id, 'expires_at': expires_at})
                elif expires_at_datetime <= datetime.now():
                # Таймер завершился, удаляем варн
                    await self.remove_warn(user_id, warn_id, expires_at)
        scheduler.start()

    @commands.slash_command(name="warn", description="Выдать кому-то предупреждение на сервере")
    @commands.has_permissions(moderate_members=True)
    async def warn(self, ctx, user: disnake.Member, time: str, reason="Нарушил правила сервера"):
        target = user
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS warns (
            user_id INTEGER,
            moder_id INTEGER,
            warns INTEGER,
            warn_id INTEGER PRIMARY KEY,
            reason TEXT,
            expires_at TEXT,
            timer_id TEXT,
            task_id TEXT, -- Объявление столбца для идентификации задачи
            FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
            """
        )
        cursor.execute("SELECT MAX(warn_id) FROM warns")
        result = cursor.fetchone()
        max_warn_id = result[0]

        if max_warn_id is None:
            warn_id = 1
        else:
            warn_id = max_warn_id + 1

        timer_id = f"unwarn_{target.id}_{warn_id}"
        task_id = f"task_{target.id}_{warn_id}"
        trigger = IntervalTrigger(minutes=int(time))
        expires_at = datetime.now() + timedelta(minutes=int(time))
        scheduler.add_job(self.remove_warn, trigger=trigger, id=timer_id,
                          kwargs={'user_id': target.id, 'warn_id': warn_id, 'expires_at': expires_at})
        cursor.execute(
            "INSERT INTO warns (user_id, moder_id, warn_id, reason, expires_at, timer_id, task_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (target.id, ctx.author.id, warn_id, reason, expires_at, timer_id, task_id))
        db.commit()

        log_channel = self.bot.get_channel(1101567459737215047)
        if log_channel:
            embed = disnake.Embed(
                title="🎟️ | Выдача варна",
                description=f"Пользователю {user.name}({user.mention}) был выдан варн.",
                color=disnake.Color.dark_orange(),
            )
            embed.add_field(
                name=f"Модератор",
                value=f"{ctx.author.name}({ctx.author.mention})",
                inline=False
            )
            embed.add_field(
                name=f"Причина",
                value=f"{reason}",
                inline=False
            )
            embed.add_field(
                name=f"Номер варна",
                value=f"{warn_id}",
                inline=False
            )
            embed.add_field(
                name=f"Длительность",
                value=f"{expires_at.strftime('%d.%m.%Y %H:%M')}",
                inline=False
            )
            embed.set_footer(
                text=f"ID участника: {user.id}",
                icon_url=user.display_avatar
            )
            await log_channel.send(embed=embed)
        await ctx.send(f"Варн выдан", ephemeral=True)


    @commands.slash_command(name="unwarn", description="Снять кому-то предупреждение на сервере")
    @commands.has_permissions(moderate_members=True)
    async def unwarn(self, ctx, user: disnake.Member, warn_id: int):
        target = user
        user_id = target.id
        cursor.execute("SELECT reason, expires_at FROM warns WHERE user_id=? AND warn_id=?", (target.id, warn_id))
        result = cursor.fetchone()
        if result:
            reason, expires_at = result
            expires_at_datetime = datetime.fromisoformat(expires_at)
            if expires_at_datetime >= datetime.now():
                cursor.execute("DELETE FROM warns WHERE user_id=? AND warn_id=?", (target.id, warn_id))
                db.commit()
                log_channel = self.bot.get_channel(1101567459737215047)  # Замените на ID канала для логов
                if log_channel:
                    embed = disnake.Embed(
                        title="🚬 | Снятие варна",
                        description=f"У пользователя {user.name}({user.mention}) был снят варн.",
                        color=disnake.Color.brand_green(),
                    )
                    embed.add_field(
                        name=f"Модератор",
                        value=f"{ctx.author.name}({ctx.author.mention})",
                        inline=False
                    )
                    embed.add_field(
                        name=f"Причина выдачи",
                        value=f"{reason}",
                        inline=False
                    )
                    embed.add_field(
                        name=f"Номер варна",
                        value=f"{warn_id}",
                        inline=False
                    )
                    embed.set_footer(
                        text=f"ID участника: {user.id}",
                        icon_url=user.display_avatar
                    )
                    await log_channel.send(embed=embed)
                    scheduler.remove_job(f"unwarn_{user_id}_{warn_id}")
                await ctx.send("Варн снят.", ephemeral=True)
            else:
                await ctx.send("Невозможно снять варн. Варн истек или у вас недостаточно прав.", ephemeral=True)
        else:
            await ctx.send("Варн с указанным идентификатором не найден.", ephemeral=True)


    @commands.slash_command(name="warns", description="Показать возможные предупреждения")
    async def warns(self, ctx, user: disnake.Member = None):
        if user is None:
            user = ctx.author
        # Получите информацию о варнах пользователя
        cursor.execute("SELECT warns, warn_id, reason, expires_at FROM warns WHERE user_id=?", (user.id,))
        results = cursor.fetchall()
        if user == ctx.author:
            if not results:
                embed = disnake.Embed(
                    title="У вас нет предупреждений",
                    color=disnake.Color.green()  # Вы можете выбрать цвет по вашему усмотрению
                )
                await ctx.send(embed=embed, ephemeral=True)
            else:
                embed = disnake.Embed(
                    title="Список ваших предупреждений",
                    color=disnake.Color.red()  # Вы можете выбрать цвет по вашему усмотрению
                )
                for index, (warns, warn_id, reason, expires_at) in enumerate(results, 1):
                    if expires_at:
                        expires_at_datetime = datetime.fromisoformat(expires_at)
                        if expires_at_datetime >= datetime.now():
                            embed.add_field(
                                name=f"Предупреждение с id: {warn_id}",
                                value=f"Причина: {reason}\nИстекает: {expires_at_datetime.strftime('%d.%m.%Y в %H:%M')}",
                                inline=False
                            )

                    else:
                        embed.add_field(
                            name=f"Предупреждение {warn_id}",
                            value=f"Причина: {reason}\nБез срока истечения",
                            inline=False
                        )
                    await ctx.send(embed=embed, ephemeral=True)
        if user != ctx.author:
            if ctx.author.guild_permissions.moderate_members:
                if not results:
                    embed = disnake.Embed(
                        title=f"У пользователя {user.display_name} нет предупреждений",
                        color=disnake.Color.green()  # Вы можете выбрать цвет по вашему усмотрению
                    )
                    await ctx.send(embed=embed, ephemeral=True)
                else:
                    embed = disnake.Embed(
                        title=f"Список предупреждений у пользователя {user.display_name}",
                        color=disnake.Color.red()  # Вы можете выбрать цвет по вашему усмотрению
                    )
                    for index, (warns, warn_id, reason, expires_at) in enumerate(results, 1):
                        if expires_at:
                            expires_at_datetime = datetime.fromisoformat(expires_at)
                            if expires_at_datetime >= datetime.now():
                                embed.add_field(
                                    name=f"Предупреждение с id: {warn_id}",
                                    value=f"Причина: {reason}\nИстекает: {expires_at_datetime.strftime('%d.%m.%Y в %H:%M')}",
                                    inline=False
                                )
                        else:
                            embed.add_field(
                                name=f"Предупреждение с id: {warn_id}",
                                value=f"Причина: {reason}\nБез срока истечения",
                                inline=False
                            )
                    await ctx.send(embed=embed, ephemeral=True)
            else:
                embed = disnake.Embed(
                    title="У вас недостаточно прав для просмотра чужих предупреждений.",
                    color=disnake.Color.red()  # Вы можете выбрать цвет по вашему усмотрению
                )
                await ctx.send(embed=embed, ephemeral=True)







def setup(bot):
    bot.add_cog(warndb(bot))