import disnake
from disnake import ModalInteraction

from cogs.marathon_views import *

from db_config import execute_query
from db_config import read_query

from defines_config import MAIN_COMMUNICATION_MARATHON_CHAT_ID

from errors_handling import check_missing_role


class Organizer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # создаёт команду (+ создаёт ветку команды в чате общение-марафон)
    @commands.slash_command(name="marathon-create-team", description="Создать команду",
                            default_member_permissions=disnake.Permissions(mention_everyone=True))
    @commands.has_role(ORGANIZER_ROLE_ID)
    async def create_team(self, interaction: disnake.ApplicationCommandInteraction, team_name: str):
        try:
            channel = self.bot.get_channel(MAIN_COMMUNICATION_MARATHON_CHAT_ID)
            if channel:
                team_thread = await channel.create_thread(name=team_name, type=disnake.ChannelType.private_thread)
                execute_query(
                    f"INSERT INTO teams (name, channel_id_str) VALUES (\"{team_name}\", \"{team_thread.id}\")")
                await interaction.response.send_message(f"Ветка для команды **{team_thread.mention}** создана")
            else:
                await interaction.response.send_message(f"Подходящий канал для создания веток не найден")
        except disnake.DiscordException as ex:
            await interaction.response.send_message(f"Bruh. Что-то пошло не так. Напиши разработчику\n"
                                                    f"Ошибка: {ex}", ephemeral=True)
            print(ex)

    # удаляет команду (и ветку из чата)
    @commands.slash_command(name="marathon-delete-team", description="Удалить команду",
                            default_member_permissions=disnake.Permissions(mention_everyone=True))
    @commands.has_role(ORGANIZER_ROLE_ID)
    async def delete_team(self, interaction: disnake.ApplicationCommandInteraction, team_name: str):
        try:
            received_data = read_query(f"SELECT id, channel_id_str, members_amount FROM teams "
                                       f"WHERE teams.name = \"{team_name}\"")
            if received_data:
                team_id = received_data[0][0]
                team_channel_id = int(received_data[0][1])
                members_amount = received_data[0][2]
                if team_channel_id:
                    # если участники не удалены из команды, удалим их
                    if members_amount:
                        execute_query(f"UPDATE users SET users.team_id = -1 WHERE users.team_id = {team_id}")

                    execute_query(
                        f"DELETE FROM teams WHERE teams.channel_id_str = \"{team_channel_id}\"")  # удаляем из БД
                    channel = self.bot.get_channel(team_channel_id)
                    await channel.delete()  # удаляем ветку команды
                    await interaction.response.send_message(f"Команда **{team_name}** удалена")
                else:
                    await interaction.response.send_message("Ошибка. Что-то не так с id команды в БД")
            else:
                await interaction.response.send_message(f"Команды с названием **{team_name}** не существует")

        except disnake.DiscordException as ex:
            await interaction.response.send_message(f"Bruh. Что-то пошло не так. Напиши разработчику\n"
                                                    f"Ошибка: {ex}", ephemeral=True)
            print(ex)

    # добавляет пользователя в команду (+ обновляет данные в БД)
    @commands.slash_command(name="marathon-add-user", description="Добавить участника в команду",
                            default_member_permissions=disnake.Permissions(mention_everyone=True))
    @commands.has_role(ORGANIZER_ROLE_ID)
    async def add_user(self, inter: disnake.ApplicationCommandInteraction, user_name: disnake.Member):
        try:
            # получаем id канала данной team
            team_id = read_query(f"SELECT id FROM teams WHERE teams.channel_id_str = \"{inter.channel_id}\"")
            if team_id:
                team_id = team_id[0][0]  # получаем в удобном формате
            else:
                await inter.response.send_message(f"Данная команда (team) не найдена в БД\n"
                                                  f"Вероятно, эта ветка создавалась вручную, "
                                                  f"а не с помощью `/create-team`", ephemeral=True)
                return

            # получаем id команды пользователя
            user_team_id = read_query(f"SELECT team_id FROM users WHERE users.name = \"{user_name}\"")
            if user_team_id:
                user_team_id = user_team_id[0][0]  # получаем в удобном формате
                if user_team_id is None:
                    await inter.response.send_message(f"Пользователь {user_name.mention} принимает "
                                                      f"одиночное участие в марафоне", ephemeral=True)
                    return
                elif user_team_id == team_id:
                    await inter.response.send_message(f"Пользователь {user_name.mention} уже принадлежит этой команде",
                                                      ephemeral=True)
                    return
            else:
                await inter.response.send_message(f"Пользователь {user_name.mention} "
                                                  f"не зарегистрирован (его нет в БД)", ephemeral=True)
                return

            # присваиваем юзеру team_id
            execute_query(f"UPDATE users SET users.team_id = {team_id} WHERE users.name = \"{user_name}\"")
            # увеличиваем в команде счётчик members_amount
            execute_query(
                f"UPDATE teams SET teams.members_amount = teams.members_amount + 1 WHERE teams.id = {team_id}")
            await inter.response.send_message(f"Пользователь **{user_name.mention}** добавлен в команду",
                                              ephemeral=True)
        except disnake.DiscordException as ex:
            await inter.response.send_message(f"Bruh. Что-то пошло не так. Напиши разработчику\n"
                                              f"Ошибка: {ex}", ephemeral=True)
            print(ex)

    # исключает пользователя из команды (+ обновляет данные в БД)
    @commands.slash_command(name="marathon-delete-user", description="Исключить участника из команды",
                            default_member_permissions=disnake.Permissions(mention_everyone=True))
    @commands.has_role(ORGANIZER_ROLE_ID)
    async def delete_user(self, interaction: disnake.ApplicationCommandInteraction, user_name: disnake.Member):
        try:
            # получаем id канала данной team
            team_id = read_query(f"SELECT id FROM teams WHERE teams.channel_id_str = \"{interaction.channel_id}\"")
            if team_id:
                team_id = team_id[0][0]  # получаем в удобном формате
            else:
                await interaction.response.send_message(f"Данная команда (team) не найдена в БД\n"
                                                        f"Вероятно, эта ветка создавалась вручную, "
                                                        f"а не с помощью `/create-team`", ephemeral=True)
                return

            # получаем id команды пользователя
            user_team_id = read_query(f"SELECT team_id FROM users WHERE users.name = \"{user_name}\"")
            if user_team_id:
                user_team_id = user_team_id[0][0]  # получаем в удобном формате
                if user_team_id != team_id:
                    await interaction.response.send_message(
                        f"Пользователь {user_name.mention} не принадлежит этой команде",
                        ephemeral=True)
                    return
            else:
                await interaction.response.send_message(f"Пользователь {user_name.mention} "
                                                        f"не зарегистрирован (его нет в БД)", ephemeral=True)
                return

            # присваиваем юзеру team_id = -1
            execute_query(f"UPDATE users SET users.team_id = -1 WHERE users.name = \"{user_name}\"")
            # уменьшаем в команде счётчик members_amount
            execute_query(
                f"UPDATE teams SET teams.members_amount = teams.members_amount - 1 WHERE teams.id = {team_id}")
            await interaction.response.send_message(f"Пользователь **{user_name.mention}** исключен из команды",
                                                    ephemeral=True)
        except disnake.DiscordException as ex:
            await interaction.response.send_message(f"Bruh. Что-то пошло не так. Напиши разработчику\n"
                                                    f"Ошибка: {ex}", ephemeral=True)
            print(ex)

    # TODO несрочно -> подумать, как реализовать грамотнее
    # пересчитывает очки команды (использовать после добавления/удаления участника)
    @commands.slash_command(name="marathon-recalculate-score", description="Пересчитать очки команды",
                            default_member_permissions=disnake.Permissions(mention_everyone=True))
    @commands.has_role(ORGANIZER_ROLE_ID)
    async def recalculate_score(self, interaction: disnake.ApplicationCommandInteraction):
        try:
            # получаем id канала данной team
            team_id = read_query(f"SELECT id FROM teams WHERE teams.channel_id_str = \"{interaction.channel_id}\"")
            if team_id:
                team_id = team_id[0][0]  # получаем в удобном формате
            else:
                await interaction.response.send_message(f"Данная команда (team) не найдена в БД\n"
                                                        f"Вероятно, эта ветка создавалась вручную, "
                                                        f"а не с помощью `/create-team`", ephemeral=True)
                return

            # находим количество всех отчётов участников команды
            received_data = read_query(f"SELECT COUNT(reports.id) AS reports_amount, "
                                       f"teams.members_amount "
                                       f"FROM reports "
                                       f"JOIN users ON reports.user_id = users.id "
                                       f"JOIN teams ON users.team_id = teams.id "
                                       f"WHERE teams.id = {team_id}")

            received_data_special_task = read_query(f"SELECT SUM(complete_members) AS sum_all_complete_members "
                                                    f"FROM special_tasks "
                                                    f"WHERE team_id = {team_id}")

            if received_data:
                reports_amount = received_data[0][0]
                members_amount = received_data[0][1]
                sum_complete_members = received_data_special_task[0][0]

                # обновляем очки за обычные отчёты и очки за спец. задания
                execute_query(f"UPDATE teams SET "
                              f"teams.score = {reports_amount / members_amount * 100}, "
                              f"teams.special_score = {sum_complete_members / members_amount * 100} "
                              f"WHERE teams.id = {team_id}")

                await interaction.response.send_message(f"Очки пересчитаны\n"
                                                        f"Теперь у команды:\n"
                                                        f"{reports_amount / members_amount * 100} очков за отчёты\n"
                                                        f"{sum_complete_members / members_amount * 100} очков "
                                                        f"за спец. задания", ephemeral=True)

        except disnake.DiscordException as ex:
            await interaction.response.send_message(f"Bruh. Что-то пошло не так. Напиши разработчику\n"
                                                    f"Ошибка: {ex}", ephemeral=True)
            print(ex)

    # изменяет очки команды вручную
    @commands.slash_command(name="marathon-correct-team-score", description="Скорректировать очки команды",
                            default_member_permissions=disnake.Permissions(mention_everyone=True))
    @commands.has_role(ORGANIZER_ROLE_ID)
    async def correct_team_score(self, interaction: disnake.ApplicationCommandInteraction, correcting_score: int):
        try:
            # получаем id канала данной team
            team_id = read_query(f"SELECT id FROM teams WHERE teams.channel_id_str = \"{interaction.channel_id}\"")
            if team_id:
                team_id = team_id[0][0]  # получаем в удобном формате
            else:
                await interaction.response.send_message(f"Данная команда (team) не найдена в БД\n"
                                                        f"Вероятно, эта ветка создавалась вручную, "
                                                        f"а не с помощью `/create-team`", ephemeral=True)
                return

            # обновляем количество очков
            execute_query(f"UPDATE teams SET teams.score_adjustment = teams.score_adjustment + {correcting_score} "
                          f"WHERE teams.id = {team_id}")
            await interaction.response.send_message(f"Очки команды **{interaction.channel.name}** "
                                                    f"были скорректированы на **{correcting_score}**", ephemeral=True)
        except disnake.DiscordException as ex:
            await interaction.response.send_message(f"Bruh. Что-то пошло не так. Напиши разработчику\n"
                                                    f"Ошибка: {ex}", ephemeral=True)
            print(ex)

    # ============================== лучшие практики ==============================
    # отправляет кнопку для лучших практик
    @commands.slash_command(name="marathon-best-practise", description="Опубликовать кнопку для лучших практик",
                            options=[
                                disnake.Option(
                                    name="practise_name",
                                    description="Название практики",
                                    type=disnake.OptionType.string,
                                    required=True
                                ),
                                disnake.Option(
                                    name="task_1",
                                    description="Текст задания №1",
                                    type=disnake.OptionType.string,
                                    required=True
                                ),
                                disnake.Option(
                                    name="task_2",
                                    description="Текст задания №2",
                                    type=disnake.OptionType.string,
                                    required=False
                                ),
                                disnake.Option(
                                    name="task_3",
                                    description="Текст задания №3",
                                    type=disnake.OptionType.string,
                                    required=False
                                )
                            ],
                            default_member_permissions=disnake.Permissions(mention_everyone=True))
    @commands.has_role(ORGANIZER_ROLE_ID)
    async def best_practise(self, interaction: disnake.ApplicationCommandInteraction,
                            practise_name: str, task_1: str, task_2: str = None, task_3: str = None):
        try:
            marathon_role = interaction.guild.get_role(MARATHON_ROLE_ID)

            tasks_format_text = f"# 🎯 Задания\n1. {task_1}\n"

            if task_2 is not None:
                tasks_format_text += f"2. {task_2}\n"

                if task_3 is not None:
                    tasks_format_text += f"3. {task_3}\n"

            tasks_format_text += f"\n{marathon_role.mention}"

            check_task_text_view = Organizer.CheckTaskTextButton(practise_name, tasks_format_text)
            await interaction.response.send_message("## Убедитесь в правильности написания текста ✍\n"
                                                    f"{tasks_format_text}", view=check_task_text_view, ephemeral=True)

        except disnake.DiscordException as ex:
            await interaction.response.send_message(f"Bruh. Что-то пошло не так. Напиши разработчику\n"
                                                    f"Ошибка: {ex}", ephemeral=True)
            print(ex)

    class CheckTaskTextButton(disnake.ui.View):
        def __init__(self, practise_name, tasks_format_text):
            super().__init__()
            self.practise_name = practise_name
            self.tasks_format_text = tasks_format_text

        @disnake.ui.button(label="Опубликовать задание", style=disnake.ButtonStyle.green, emoji="✅")
        async def publish_task(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
            submit_practise_view = Organizer.SubmitPractiseButton()
            message = await interaction.channel.send(self.tasks_format_text, view=submit_practise_view)
            practise_thread = await interaction.channel.create_thread(name=self.practise_name, message=message,
                                                                      auto_archive_duration=disnake.ThreadArchiveDuration.day)

            # заполняем в БД данные о практике
            execute_query(f"INSERT INTO practises (practise_name, message_id) "
                          f"VALUES (\"{self.practise_name}\", \"{practise_thread.id}\")")

            await interaction.response.defer()
            await interaction.delete_original_message()
            self.stop()

        @disnake.ui.button(label="Отменить публикацию", style=disnake.ButtonStyle.gray, emoji="❌")
        async def cancel_publish(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
            await interaction.response.defer()
            await interaction.delete_original_message()
            self.stop()

    class SubmitPractiseButton(disnake.ui.View):
        def __init__(self):
            super().__init__()

        @disnake.ui.button(label="Выполнить", style=disnake.ButtonStyle.green, emoji="📋")
        async def submit_practise(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
            user_id = read_query(f"SELECT id FROM users WHERE users.name = \"{interaction.author.name}\"")
            if user_id:
                user_id = user_id[0][0]  # получаем в удобном формате
            else:
                await interaction.response.send_message(f"Что-то пошло не так. Обратитесь к модераторам",
                                                        ephemeral=True)
                return

            input_practise_text_modal = Organizer.InputPractiseTextModal(user_id)
            await interaction.response.send_modal(input_practise_text_modal)

    class InputPractiseTextModal(disnake.ui.Modal):
        def __init__(self, user_id):
            self.user_id = user_id
            components = [
                disnake.ui.TextInput(label="Опишите проделанную работу", max_length=4000, custom_id="practise_text")
            ]
            super().__init__(title="Отчет по заданию", components=components, custom_id="practiseTextModal")

        async def callback(self, interaction: ModalInteraction):
            # получаем данные по практике из БД
            received_data = read_query(f"SELECT practise_name FROM practises "
                                       f"WHERE message_id = {interaction.message.id}")
            if received_data:
                practise_name = received_data[0][0]
            else:
                await interaction.response.send_message(f"Что-то пошло не так. Обратитесь к модераторам",
                                                        ephemeral=True)
                return

            # добавление выполнения отчета в БД
            # проверяем, есть ли ранее сданные отчеты
            is_exist_user_id = read_query(f"SELECT user_id FROM practise_reports "
                                          f"WHERE practise_reports.user_id = {self.user_id}")
            if is_exist_user_id:  # если запись в БД есть, обновляем старую запись
                is_exist_user_id = is_exist_user_id[0][0]  # получаем в удобном формате
                execute_query(f"UPDATE practise_reports SET practise_reports.done_practises = CONCAT(done_practises, "
                              f"\"{practise_name.split()[0][1:3]}, \") "
                              f"WHERE practise_reports.user_id = {is_exist_user_id}")
            else:  # если записи в БД не было, делаем вставку новой
                execute_query(f"INSERT INTO practise_reports (user_id, done_practises) "
                              f"VALUES ({self.user_id}, \"{practise_name.split()[0][1:3]}, \")")

            # отправляем отчёт в ветку
            practise_text = interaction.text_values["practise_text"]
            practise_report_embed = disnake.Embed(
                description=practise_text,
                color=0x44944b
            )
            practise_report_embed.set_author(name=interaction.author.display_name,
                                             icon_url=interaction.author.avatar.url)

            practise_thread = interaction.guild.get_thread(interaction.message.id)
            await practise_thread.send(f"Отчёт {interaction.author.mention}", embed=practise_report_embed)

            await interaction.response.defer(with_message=False)

    # ===================== обработчики ошибок =====================

    # обработчик ошибок при недостатке прав выполнения команды marathon-create-team
    @create_team.error
    async def create_team_error_handler(self, interaction: disnake.ApplicationCommandInteraction, error):
        await check_missing_role(interaction, error)

    # обработчик ошибок при недостатке прав выполнения команды marathon-delete-team
    @delete_team.error
    async def delete_team_error_handler(self, interaction: disnake.ApplicationCommandInteraction, error):
        await check_missing_role(interaction, error)

    # обработчик ошибок при недостатке прав выполнения команды marathon-delete-user
    @delete_user.error
    async def delete_user_error_handler(self, interaction: disnake.ApplicationCommandInteraction, error):
        await check_missing_role(interaction, error)

    # обработчик ошибок при недостатке прав выполнения команды marathon-add-user
    @add_user.error
    async def add_user_error_handler(self, interaction: disnake.ApplicationCommandInteraction, error):
        await check_missing_role(interaction, error)

    # обработчик ошибок при недостатке прав выполнения команды marathon-recalculate-score
    @recalculate_score.error
    async def recalculate_score_error_handler(self, interaction: disnake.ApplicationCommandInteraction, error):
        await check_missing_role(interaction, error)

    # ==============================================================


def setup(bot):
    bot.add_cog(Organizer(bot))
