import sqlite3
import disnake
from disnake.ext import commands
from disnake import ButtonStyle
from disnake.ui import View, Button, Select

bot = commands.Bot(command_prefix="!", help_command=None, intents=disnake.Intents.all())
db = sqlite3.connect("anketa.db")
dbm = sqlite3.connect("anketam.db")
cursorm = dbm.cursor()
cursor = db.cursor()

class ModalsViewButton(View):
  def __init__(self):

    super().__init__()

    self.add_item(Button(style=ButtonStyle.green, label="Отправить заявку", custom_id="create"))
    self.add_item(Button(style=ButtonStyle.red, label="Удалить", custom_id="delete"))

class ModalsViewSelect(View):
  def __init__(self):
    super().__init__()
    self.add_item(Select(
      placeholder="Выберите раздел модерации.",options=[
        disnake.SelectOption(label="Ивентер", value="events"),
        disnake.SelectOption(label="Следящий", value="spectator"),
        disnake.SelectOption(label="Репортёр", value="reporter"),
      ],
      custom_id="action_dropdown"
    ))


class Moderators(disnake.ui.Modal, commands.Cog):
  def __init__(self, bot, channel_id=None, select_option=None):
    self.bot = bot
    self.channel_id = channel_id
    self.selected_option = select_option
    components = [
      disnake.ui.TextInput(
        label="Как Вас зовут?",
        placeholder="Введите Ваше имя",
        custom_id="Имя",
      ),
      disnake.ui.TextInput(
        label="Сколько Вам лет?",
        placeholder="Введите Ваш возраст",
        custom_id="Возраст",
        max_length="2",
      ),
      disnake.ui.TextInput(
        label="Имеется ли у Вас опыт в модерировании?",
        placeholder="Напишите если имеется, то какой",
        custom_id="Опыт",
        style=disnake.TextInputStyle.paragraph
      ),
      disnake.ui.TextInput(
        label="Почему Вы хотите стать модератором?",
        placeholder="Введите причину",
        custom_id="Причина",
        style=disnake.TextInputStyle.paragraph
      ),
      disnake.ui.TextInput(
        label="Расскажите о себе",
        placeholder="Введите информацию о себе(хобби, чем занимаетесь)",
        custom_id="О себе",
        style=disnake.TextInputStyle.paragraph
      ),
    ]

    super().__init__(
      title="Заявка на модератора",
      components=components
    )

  @commands.Cog.listener()
  @bot.event
  async def on_ready(self):
    channel = self.bot.get_channel(1174038662393114634)
    if channel:
      messages = await channel.history(limit=1).flatten()
      if not messages:
        view = ModalsViewSelect()
        embed = disnake.Embed(title="Заявка на модератора <a:emoji_32:1101701242083885056> ", description="""<a:emoji_37:1101701313894547476> **Набираем модераторов в наш коллектив!<a:emoji_37:1101701313894547476>** 
        
    <a:emoji_33:1101701255279153172> Всегда хотел быть главным и наводить порядки? 
    Тогда для тебя роль **Следящего** <:emoji_19:1101699513888026725>  
    
    <a:emoji_33:1101701255279153172> Или если тебе больше по душе проводить мероприятия и общаться с людьми? 
    Выбирай **Ивентера** <a:emoji_38:1101701340662616174> 
    
    <a:emoji_33:1101701255279153172> Ну, а если вообще твой конёк это красивое оформление, красноречие и умение интересно преподнести информацию. 
    Ждём в **Репортёрах** <:reporter:1174043432717664417> 
    
    Выберите из списка раздел который Вам интересен.

    """, color=disnake.Color.purple())
        embed.add_field(
          name="__Анкету заполнить Вы можете только на одну позицию__",
          value="После заполнения с вами свяжется администратор.",
          inline=False
        )

        await channel.send(embed=embed, view=view)
      else:
        print("Сообщение уже существует.")
    else:
      print("Канал не найден.")

  @commands.Cog.listener()
  @bot.event
  async def on_dropdown(self, inter):
    if isinstance(inter, disnake.MessageInteraction):
      data = inter.data
      custom_id = data.get("custom_id")
      if custom_id == "action_dropdown":
        self.selected_option = data.get("values")[0]
        cursorm.execute(
          """
          CREATE TABLE IF NOT EXISTS anketam (
          user_id INTEGER PRIMARY KEY,
          message_id INTEGER,
          FOREIGN KEY (user_id) REFERENCES users (user_id)
          )
          """
        )
        user_id = inter.author.id
        cursorm.execute("SELECT user_id FROM anketam WHERE user_id=?", (user_id,))
        result = cursorm.fetchone()
        if result:
            await inter.response.send_message("Вы уже отправили свою анкету.", ephemeral=True)
        else:
            modal = Moderators(bot, select_option=self.selected_option)
            await inter.response.send_modal(modal=modal)

  async def callback(self, inter: disnake.Interaction):
    embed = disnake.Embed(title=f"Заявка на {self.selected_option}", color=disnake.Color.purple())
    for key, value in inter.text_values.items():
        embed.add_field(name=key.capitalize(), value=value, inline=False)
    embed.add_field(
      name="Пользователь:",
      value=f"{inter.author.mention}",
    )
    await inter.response.send_message('Анкета отправлена! Ожидайте ответа администратора...', ephemeral=True)
    guild = inter.guild  # Замените на ID вашего канала
    channel = guild.get_channel(1174039059623067689)
    if channel:
      sent = await channel.send(embed=embed)
      cursorm.execute("INSERT INTO anketam (user_id, message_id) VALUES (?, ?)", (inter.author.id, sent.id,))
      dbm.commit()
    else:
      print("Log channel not found!")
    
  @commands.slash_command(name="del", description="Удалить заявку")
  @commands.has_permissions(administrator=True)
  async def delete(self, ctx, user: disnake.User):
    cursorm.execute("SELECT message_id FROM anketam WHERE user_id=?", (user.id,))
    result = cursorm.fetchone()
    if result:
      message_id = result[0]
      channel = ctx.guild.get_channel(1174039059623067689)
      message = await channel.fetch_message(message_id)
      cursorm.execute("DELETE FROM anketam WHERE user_id=?", (user.id,))
      dbm.commit()
      await message.delete()
      await ctx.response.send_message("Анкета успешно удалена.", ephemeral=True)
    else:
      await ctx.response.send_message("Анкета не найдена.", ephemeral=True)


class Tournament(disnake.ui.Modal, commands.Cog):


  def __init__(self, bot, channel_id=None):
    self.bot = bot
    self.channel_id = channel_id
    self.messid = {}
    components = [
      disnake.ui.TextInput(
        label="Название команды",
        placeholder="Введите название вашей команды",
        custom_id="Название"
      ),
      disnake.ui.TextInput(
        label="Лого команды",
        placeholder="imgur.com/yapix.ru",
        custom_id="Лого",
        required=False
      ),
      disnake.ui.TextInput(
        label="AVG MMR команды",
        placeholder="Средний ммр всей команды",
        custom_id="AVG MMR",
      ),
      disnake.ui.TextInput(
        label="Стим аккаунт капитана",
        placeholder="Ссылка на стим аккаунт",
        custom_id="Стим ак"
      ),
      disnake.ui.TextInput(
        label="Дискорды игроков команды с запасным",
        placeholder="Введите ники (запасной)",
        custom_id="Остальные",
        style=disnake.TextInputStyle.paragraph
      ),

    ]

    super().__init__(
      title="Заявка на турнир",
      components=components
    )

  @commands.Cog.listener()
  @bot.event
  async def on_ready(self):
    channel = self.bot.get_channel(1169318339160592444)
    if channel:
      messages = await channel.history(limit=1).flatten()
      if not messages:
          view = ModalsViewButton()
          embed = disnake.Embed(title="Отправить заявку", description="""**Добро пожаловать.** 
Ты Капитан команды и хочешь записать свою команду на турнир? 
Нажми на зеленую кнопку **"Отправить заявку"** и заполни необходимые поля.

""", color=disnake.Color.blurple())
          embed.add_field(
            name="__Анкету заполняет только капитан команды__",
            value="После заполнения с вами свяжется администратор.",
            inline=False
          )
          embed.add_field(
            name="Правила турнира можете прочитать ниже:",
            value="https://docs.google.com/document/d/1kUzDFNoLNGLLooCRSYveHUuGpDsNgPABC-T33jJIKNk/edit?usp=sharing",
            inline=False
            )

          await channel.send(embed=embed, view=view)
      else:
          print("Сообщение уже существует.")
    else:
      print("Канал не найден.")

  @commands.Cog.listener()
  @bot.event
  async def on_button_click(self, inter):
    if isinstance(inter, disnake.MessageInteraction):
      data = inter.data
      custom_id = data.get("custom_id")
      if custom_id == "create":
        cursor.execute(
          """
          CREATE TABLE IF NOT EXISTS anketa (
          user_id INTEGER PRIMARY KEY,
          message_id INTEGER,
          FOREIGN KEY (user_id) REFERENCES users (user_id)
          )
          """
        )
        user_id = inter.author.id
        cursor.execute("SELECT user_id FROM anketa WHERE user_id=?", (user_id,))
        result = cursor.fetchone()
        if result:
          await inter.response.send_message("Вы уже отправили свою анкету.", ephemeral=True)
        else:
          modal = Tournament(bot)
          await inter.response.send_modal(modal=modal)
      elif custom_id == "delete":
        user = inter.author
        cursor.execute("SELECT message_id FROM anketa WHERE user_id=?", (user.id,))
        result = cursor.fetchone()
        if result:
          message_id = result[0]
          channel = inter.guild.get_channel(1110215626422763560)
          message = await channel.fetch_message(message_id)
          cursor.execute("DELETE FROM anketa WHERE user_id=?", (user.id,))
          db.commit()
          await message.delete()
          await inter.response.send_message("Анкета успешно удалена.", ephemeral=True)
        else:
          await inter.response.send_message("Анкета не найдена.", ephemeral=True)


  async def callback(self, inter: disnake.Interaction):
    embed = disnake.Embed(title="Заявка на турнир", color=disnake.Color.dark_gold())
    for key, value in inter.text_values.items():
      embed.add_field(name=key.capitalize(), value=value, inline=False)
    embed.add_field(
      name="Капитан:",
      value=f"{inter.author.mention}",
    )
    await inter.response.send_message('Анкета отправлена! Ожидайте ответа администратора...', ephemeral=True)
    guild = inter.guild  # Замените на ID вашего канала
    channel = guild.get_channel(1110215626422763560)
    if channel:
      sent = await channel.send(embed=embed)
      cursor.execute("INSERT INTO anketa (user_id, message_id) VALUES (?, ?)", (inter.author.id, sent.id,))
      db.commit()
    else:
      print("Log channel not found!")



def setup(bot):
  bot.add_cog(Tournament(bot))
  bot.add_cog(Moderators(bot))