from main import disnake
from main import commands

from db_config import execute_query
from db_config import read_query

from defines_config import MAIN_COMMUNICATION_MARATHON_CHAT_ID

from datetime import timedelta


class Reports(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if (message.channel.type != disnake.ChannelType.private_thread or
                message.channel.parent_id != MAIN_COMMUNICATION_MARATHON_CHAT_ID):
            return  # не слушаем сообщение, если оно не в канале главного общего чата марафона (или его ветках)

        print(1)

        try:
            if message.content.split()[0].lower() in ["отчет", "отчёт"]:
                received_data = read_query(f"SELECT id, team_id FROM users "
                                           f"WHERE users.name = \"{message.author.name}\"")
                if received_data:  # если пользователь зарегистрирован
                    user_id = received_data[0][0]
                    team_id = received_data[0][1]

                    # получаем timezone у пользователя
                    user_timezone = read_query(f"SELECT timezone FROM users "
                                               f"WHERE users.name = \"{message.author.name}\"")

                    adjust_user_time = 0
                    if user_timezone:
                        adjust_user_time = user_timezone[0][0]

                    # получаем время отчета, основываясь на времени сообщения + регулируем по личному timezone пользователя
                    message_time = message.created_at + timedelta(hours=adjust_user_time)

                    # получаем все отчёты у этого пользователя
                    received_data = read_query(f"SELECT user_local_time FROM reports "
                                               f"WHERE reports.user_id = {user_id}")
                    is_find_today_report = 0

                    if received_data:
                        for row in received_data:
                            # если дата текущего отчета == дате прошлого отчета => find_today is True
                            if message_time.date() == row[0].date():
                                is_find_today_report = 1
                                break

                    if is_find_today_report == 0:
                        # добавляем запись об отчёте в БД
                        execute_query(f"INSERT INTO reports (user_id, user_local_time) "
                                      f"VALUES (\"{user_id}\", \"{message_time.strftime('%Y-%m-%d %H:%M:%S')}\")")
                        # добавляем очки команде
                        execute_query(f"UPDATE teams SET teams.score = teams.score + 100 / teams.members_amount "
                                      f"WHERE id = {team_id}")
                        await message.add_reaction("✅")
                    else:
                        await message.add_reaction("❌")
        except Exception as ex:
            print(f"- Report's system exception:", ex)


def setup(bot):
    bot.add_cog(Reports(bot))
