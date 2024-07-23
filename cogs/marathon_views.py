import disnake

from datetime import datetime

from db_config import execute_query
from db_config import read_query

from defines_config import MARATHON_ROLE_ID
from defines_config import MARATHON_START_DATE

from disnake.ext import commands

from defines_config import ORGANIZER_ROLE_ID
from defines_config import REG_MARATHON_CHAT_ID

from errors_handling import check_missing_role


class Marathon(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # команда для запуска кнопки старта марафона
    @commands.slash_command(name="marathon-start",
                            default_member_permissions=disnake.Permissions(mention_everyone=True))
    @commands.has_role(ORGANIZER_ROLE_ID)
    async def start_marathon(self, interaction: disnake.ApplicationCommandInteraction):
        marathon_channel = self.bot.get_channel(REG_MARATHON_CHAT_ID)

        welcome_view = WelcomeMarathonButton()  # форма для начала регистрации
        await marathon_channel.send("## Регистрируйтесь на марафон правильного отдыха!\n"
                                    "За две недели марафона вы:\n"
                                    "- текст\n"
                                    "- текст",
                                    view=welcome_view)
        await interaction.send("Отправили старт марафона")
        # await welcome_view.wait()

    # обработчик ошибок при недостатке прав выполнения команды marathon-start
    @start_marathon.error
    async def start_marathon_error_handler(self, interaction: disnake.ApplicationCommandInteraction, error):
        await check_missing_role(interaction, error)


# TODO несрочно | сделать грамотное отражение времени (в дискорде чтоб дата показывалась)
# https://www.youtube.com/watch?v=5cl_2xAyG0w&list=PLcsmHdQZxRKB7b8zKb2-aq9j3y7pZkQmP&index=7
def get_time_until_start():
    now = datetime.now()
    remaining_time = MARATHON_START_DATE - now

    if remaining_time.total_seconds() < 0:
        return "`Марафон уже начался!`"

    days, remainder = divmod(remaining_time.total_seconds(), 86400)
    hours, remainder = divmod(remainder, 3600)

    string = f"Марафон начнётся "
    if days % 10 == 1:
        string += f"`через {int(days)} день "
    elif days % 10 in [2, 3, 4]:
        string += f"`через {int(days)} дня "
    else:
        string += f"`через {int(days)} дней "

    if hours % 10 == 1:
        string += f"{int(hours)} час`"
    elif hours % 10 in [2, 3, 4]:
        string += f"{int(hours)} часа`"
    else:
        string += f"{int(hours)} часов`"

    return string


# view встречающее на марафоне
class WelcomeMarathonButton(disnake.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.value = None  # true - регистрация; false - задать вопрос (мб исправить это потом)
        # TODO сделать кнопку «задать вопрос»

    @disnake.ui.button(label="Марафон отдыха", style=disnake.ButtonStyle.blurple, emoji="⛵")
    async def welcomeMarathonButton(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        self.value = True

        time_until_start = get_time_until_start()
        received_user_data = read_query(f"SELECT * FROM users WHERE users.name = \"{inter.author.name}\"")
        if received_user_data:
            extra_reg_view = ExtraRegMarathonButton()
            await inter.response.send_message(f"## Марафон отдыха\n"
                                              f"{time_until_start}", view=extra_reg_view,
                                              ephemeral=True)
        else:
            reg_view = RegMarathonButton()
            await inter.response.send_message(f"## Марафон отдыха\n"
                                              f"{time_until_start}", view=reg_view,
                                              ephemeral=True)


# шаблон для перехода на view выбора формата участия
async def choice_format_pattern(inter: disnake.MessageInteraction):
    choice_format_view = ChoiceFormatMarathonButton()
    choice_format_embed = disnake.Embed(
        title="Выберите формат участия на весь марафон",
        description="текст текст текст\n"
                    "текст текст текст\n"
                    "текст текст текст\n"
                    "текст текст текст\n"
                    "текст текст текст\n"
                    "текст текст текст\n",
        color=0x7aefb0
    )
    await inter.response.edit_message("", view=choice_format_view, embed=choice_format_embed)


# view повторной регистрации
class ExtraRegMarathonButton(disnake.ui.View):
    def __init__(self):
        super().__init__()

    @disnake.ui.button(label="Заполнить регистрацию заново", style=disnake.ButtonStyle.red, emoji="🖊")
    async def extraRegMarathonButton(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        # удаляем из БД участника
        execute_query(f"DELETE FROM users WHERE users.name = \"{inter.author.name}\"")
        # при нажатии на кнопку удаляем роль сразу
        guild = inter.user.guild
        role = guild.get_role(MARATHON_ROLE_ID)
        await inter.author.remove_roles(role)

        await choice_format_pattern(inter)
        self.stop()


# view регистрации
class RegMarathonButton(disnake.ui.View):
    def __init__(self):
        super().__init__()

    @disnake.ui.button(label="Регистрация на марафон", style=disnake.ButtonStyle.green, emoji="🖊")
    async def regMarathonButton(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await choice_format_pattern(inter)
        self.stop()


# TODO если марафон начался -> только соло участие
# view выбора формата марафона (команда/соло)
class ChoiceFormatMarathonButton(disnake.ui.View):
    def __init__(self):
        super().__init__()

    @disnake.ui.button(label="Участвовать в команде", style=disnake.ButtonStyle.green, emoji="🏆")
    async def team_button(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        choice_timezone_view = TimezonesDropdownView()
        choice_format_embed = disnake.Embed(
            title="Выберите свой часовой пояс",
            description="Постараемся подобрать участников команды так, "
                        "чтобы с ними было удобно общаться в чате и "
                        "планировать созвоны.",
            color=0xd1782c
        )
        await inter.response.edit_message("", view=choice_timezone_view, embed=choice_format_embed)
        self.stop()

    @disnake.ui.button(label="Свободное участие", style=disnake.ButtonStyle.blurple, emoji="📚")
    async def solo_button(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        successful_reg_embed = disnake.Embed(
            title="Теперь вы участник марафона!",
            description="Следите за новостями марафона в **LINK**. Вам придёт уведомление, "
                        "когда выйдет первый пост с заданиями в **LINK**. Пока напишите о целях на марафон "
                        "и пообщайтесь с участниками в **LINK**",
            color=0x7aefb0
        )
        execute_query(f"INSERT INTO users (name, team_id, is_leader) VALUES (\"{inter.author.name}\", NULL, 0);")
        await inter.response.edit_message("", view=None, embed=successful_reg_embed)
        self.stop()


# подготовка dropdown menu для часовых поясов
class TimezonesDropdown(disnake.ui.StringSelect):
    def __init__(self):
        options = [
            disnake.SelectOption(label="GMT-10 ~ Гонолулу", emoji="🕙"),
            disnake.SelectOption(label="GMT-9 ~ Анкоридж, Фэрбенкс", emoji="🕘"),
            disnake.SelectOption(label="GMT-8 ~ Лос-Анджелес, Сан-Франциско, Ванкувер", emoji="🕗"),
            disnake.SelectOption(label="GMT-7 ~ Финикс, Денвер, Солт-Лейк-Сити", emoji="🕖"),
            disnake.SelectOption(label="GMT-6 ~ Мехико, Чикаго, Хьюстон", emoji="🕕"),
            disnake.SelectOption(label="GMT-5 ~ Нью-Йорк, Торонто, Монреаль", emoji="🕔"),
            disnake.SelectOption(label="GMT-4 ~ Каракас, Сантьяго, Гавана", emoji="🕓"),
            disnake.SelectOption(label="GMT-3 ~ Буэнос-Айрес, Монтевидео, Сан-Паулу", emoji="🕒"),
            disnake.SelectOption(label="GMT-2 ~ Средний Атлантик", emoji="🕑"),
            disnake.SelectOption(label="GMT-1 ~ Азорские острова, Кабо-Верде", emoji="🕐"),
            disnake.SelectOption(label="GMT-0 ~ Лондон, Лиссабон, Дублин", emoji="🕛"),
            disnake.SelectOption(label="GMT+1 ~ Берлин, Париж", emoji="🕐"),
            disnake.SelectOption(label="GMT+2 ~ Калининград, Киев, Варшава", emoji="🕑"),
            disnake.SelectOption(label="GMT+3 ~ Москва, Санкт-Петербург", emoji="🕒"),
            disnake.SelectOption(label="GMT+4 ~ Дубай, Баку, Абу-Даби", emoji="🕓"),
            disnake.SelectOption(label="GMT+5 ~ Екатеринбург, Ташкент, Алматы", emoji="🕔"),
            disnake.SelectOption(label="GMT+6 ~ Омск", emoji="🕕"),
            disnake.SelectOption(label="GMT+7 ~ Новосибирск, Бангкок, Красноярск", emoji="🕖"),
            disnake.SelectOption(label="GMT+8 ~ Иркутск, Улан-Удэ", emoji="🕗"),
            disnake.SelectOption(label="GMT+9 ~ Чита, Токио, Сеул", emoji="🕘"),
            disnake.SelectOption(label="GMT+10 ~ Владивосток, Сидней", emoji="🕙"),
            disnake.SelectOption(label="GMT+11 ~ Сахалин", emoji="🕚"),
            disnake.SelectOption(label="GMT+12 ~ Камчатка, Окленд", emoji="🕛")
        ]

        super().__init__(
            placeholder="Часовой пояс",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, inter: disnake.MessageInteraction):
        # TODO кажется, можно сделать взятие GMT без костылей split -> использовать в SelectOption параметр value
        # типа disnake.SelectOption(label="GMT+12 ~ Камчатка, Окленд", value="12", emoji="🕛"), но это не точно
        choice_leader_position_view = ChoiceLeaderPositionMarathonButton(int(self.values[0].split()[0][3:6]))
        choice_leader_position_embed = disnake.Embed(
            title="Вы можете стать лидером своей команды",
            description="Текст текст текст",
            color=0x5999c3
        )
        await inter.response.edit_message("", view=choice_leader_position_view,
                                          embed=choice_leader_position_embed)


# view выбора часовых поясов
class TimezonesDropdownView(disnake.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(TimezonesDropdown())


# view выбора лидерской позиции (лидер/участник), затем конец регистрации
class ChoiceLeaderPositionMarathonButton(disnake.ui.View):
    def __init__(self, timezone):
        super().__init__()
        self.timezone = timezone
        self.successful_reg_embed = disnake.Embed(
            title="Успешная регистрация на марафоне",
            description="Вам придет уведомление, когда мы создадим чат вашей команды. "
                        "Следите за новостями марафона в LINK. Напишите о целях на марафон и пообщайтесь с "
                        "другими участниками в LINK",
            color=0x7aefb0
        )

    async def give_role(self, inter: disnake.MessageInteraction):
        guild = inter.user.guild
        role = guild.get_role(MARATHON_ROLE_ID)
        await inter.author.add_roles(role)  # важно, чтобы роль бота в списке ролей была выше марафонской роли

    @disnake.ui.button(label="Хочу быть лидером команды", style=disnake.ButtonStyle.green, emoji="👨‍🏫")
    async def leader_button(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        execute_query(f"INSERT INTO users (name, team_id, timezone, is_leader) "
                      f"VALUES (\"{inter.author.name}\", -1, {self.timezone}, 1);")
        await self.give_role(inter)

        await inter.response.edit_message("", view=None, embed=self.successful_reg_embed)
        self.stop()

    @disnake.ui.button(label="Хочу быть участником команды", style=disnake.ButtonStyle.green, emoji="🙍‍♂️")
    async def member_button(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        execute_query(f"INSERT INTO users (name, team_id, timezone, is_leader) "
                      f"VALUES (\"{inter.author.name}\", -1, {self.timezone}, 0);")
        await self.give_role(inter)

        await inter.response.edit_message("", view=None, embed=self.successful_reg_embed)
        self.stop()

def setup(bot):
    bot.add_cog(Marathon(bot))
