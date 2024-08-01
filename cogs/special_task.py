from main import disnake
from main import commands

from db_config import execute_query, read_query

from errors_handling import check_missing_role

from defines_config import MAIN_COMMUNICATION_MARATHON_CHAT_ID, LEADER_ROLE_ID

import asyncio


class UserCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    '''
    важно понимать, что привилегии использовать эту команду настраиваются прямо в дискорде
    в разделе определённого чата. Например, у роли "Лидер" есть возможность "использовать команды приложения"
    '''
    @commands.has_role(LEADER_ROLE_ID)
    @commands.slash_command(name="marathon-start-special-task", description="Запустить спец.задание")
    async def special_task(self, interaction: disnake.ApplicationCommandInteraction):
        if (isinstance(interaction.channel, disnake.Thread) and
                interaction.channel.parent_id == MAIN_COMMUNICATION_MARATHON_CHAT_ID and
                interaction.channel.name != "Комната Лидеров"):
            themes_view = SpecialTaskThemesDropdownView()  # выбор темы созвона
            await interaction.response.send_message(view=themes_view,
                                                    ephemeral=True)
        else:
            await interaction.response.send_message("Запускать спец.задание можно только в чате вашей команды",
                                                    ephemeral=True)

    # обработчик ошибок при недостатке прав выполнения команды marathon-start-special-task
    @special_task.error
    async def special_task_error_handler(self, interaction: disnake.ApplicationCommandInteraction, error):
        await check_missing_role(interaction, error)


class SpecialTaskThemesDropdown(disnake.ui.StringSelect):
    def __init__(self):
        self.task_1 = "Тема 1"
        self.task_2 = "Тема 2"
        self.task_3 = "Тема 3"
        options = [
            disnake.SelectOption(label=self.task_1, value="1", emoji="🎨"),
            disnake.SelectOption(label=self.task_2, value="2", emoji="🧶"),
            disnake.SelectOption(label=self.task_3, value="3", emoji="⚽"),
        ]

        super().__init__(
            placeholder="Тема созвона",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: disnake.MessageInteraction):
        # описание embed в зависимости от выбранной темы
        special_task_embed = None
        task_name = None
        if self.values[0] == "1":
            task_name = self.task_1
            special_task_embed = disnake.Embed(
                title="⛵ Восстановление сил дома: ТЕМА 1",
                description="bla bla\n"
                            "1. asd\n"
                            "2. qwe\n"
                            "3. rty\n",
                color=0x1e1f22
            )
        elif self.values[0] == "2":
            task_name = self.task_2
            special_task_embed = disnake.Embed(
                title="⛵ Восстановление сил дома: ТЕМА 2",
                description="bla bla\n"
                            "1. asd\n"
                            "2. qwe\n"
                            "3. rty\n",
                color=0x1e1f22
            )
        elif self.values[0] == "3":
            task_name = self.task_3
            special_task_embed = disnake.Embed(
                title="⛵ Восстановление сил дома: ТЕМА 3",
                description="bla bla\n"
                            "1. asd\n"
                            "2. qwe\n"
                            "3. rty\n",
                color=0x1e1f22
            )

        confirm_theme_button_view = ConfirmThemeButton(special_task_embed, task_name)  # view подтверждения
        await interaction.response.edit_message("", view=confirm_theme_button_view,
                                                embed=special_task_embed)


class SpecialTaskThemesDropdownView(disnake.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(SpecialTaskThemesDropdown())


class ConfirmThemeButton(disnake.ui.View):
    def __init__(self, embed, task_name):
        super().__init__()
        self.embed = embed
        self.task_name = task_name

    @disnake.ui.button(label="Начать спец. задание", style=disnake.ButtonStyle.blurple, emoji="🚀")
    async def confirmThemeButton(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        await interaction.response.edit_message(content="## Вы запустили спец. задание", embed=None, view=None)

        special_task_view = SpecialTaskButton(interaction, self.embed, self.task_name)
        await special_task_view.start_task()


class SpecialTaskButton(disnake.ui.View):
    def __init__(self, interaction, embed, task_name):
        super().__init__()
        self.pass_members = set()
        self.interaction = interaction
        self.embed = embed
        self.task_name = task_name

    async def start_task(self):
        # получаем id канала данной team
        team_id = read_query(f"SELECT id FROM teams WHERE teams.channel_id_str = \"{self.interaction.channel_id}\"")
        if team_id:
            team_id = team_id[0][0]  # получаем в удобном формате
        else:
            await self.interaction.response.send_message(f"Что-то пошло не так. Обратитесь к разработчику",
                                                         ephemeral=True)
            return

        time_for_special_task = 15
        special_task_view = SpecialTaskButton(self.interaction, self.embed, self.task_name)
        message = await self.interaction.channel.send(f"## Спец. задание. У вас `{time_for_special_task} секунд`",
                                                      view=special_task_view, embed=self.embed)

        for remaining_seconds in range(time_for_special_task - 1, 0, -1):
            await asyncio.sleep(1)
            await message.edit(content=f"## Спец. задание. У вас осталось `{remaining_seconds} секунд`",
                               view=special_task_view, embed=self.embed)

        # выключаем кнопку после таймера
        non_clickable_button = NonClickableSpecialTaskButton()
        await message.edit(content=f"## Спец. задание завершено. "
                                   f"Отмечено `{len(special_task_view.pass_members)} участников`",
                           view=non_clickable_button, embed=self.embed)

        # добавляем спец отчет команды в БД
        execute_query(f"INSERT INTO special_tasks (name, team_id, complete_members) "
                      f"VALUES (\"{self.task_name}\", {team_id}, {len(special_task_view.pass_members)})")

        # добавляем очки в БД
        execute_query(f"UPDATE teams SET teams.special_score = teams.special_score + "
                      f"{len(special_task_view.pass_members)} / teams.members_amount * 100 "
                      f"WHERE teams.id = {team_id}")

    @disnake.ui.button(label="Сдать отчет за спец. задание", style=disnake.ButtonStyle.blurple, emoji="📝")
    async def specialTaskButton(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        # TODO сделать проверку, принадлежит ли участник команде, в которой отправлена кнопка (p.s. хотя зачем?)
        if interaction.user.id in self.pass_members:
            await interaction.response.send_message("Вы уже отметились в спец. задании",
                                                    ephemeral=True)
            return

        self.pass_members.add(interaction.user.id)

        member_pass_embed = disnake.Embed(
            description="Отчет принят",
            color=0x77ecc0
        )
        member_pass_embed.set_author(name=interaction.author.display_name,
                                     icon_url=interaction.author.avatar.url)
        await interaction.response.send_message(embed=member_pass_embed)


class NonClickableSpecialTaskButton(disnake.ui.View):
    def __init__(self):
        super().__init__()

    @disnake.ui.button(label="Спец. задание завершено", disabled=True,
                       style=disnake.ButtonStyle.blurple, emoji="📝")
    async def specialTaskButton(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        pass


def setup(bot):
    bot.add_cog(UserCommands(bot))
