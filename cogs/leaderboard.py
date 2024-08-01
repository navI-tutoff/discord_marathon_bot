from main import disnake, commands, tasks

from datetime import datetime

from db_config import pymysql, execute_query, read_query

from defines_config import LEADERBOARD_CHAT_ID, LEADERBOARD_MSG_ID


class Leaderboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.leaderboard.add_exception_type(disnake.DiscordException)
        self.leaderboard.add_exception_type(pymysql.err.DatabaseError)
        self.leaderboard.start()

    def cog_unload(self):
        self.leaderboard.cancel()

    def get_embed(self, teams_info: [[]]):
        description = ("## 🏆 Таблица лидеров\n\n"
                       "### Лидирующая троица 🏅\n")
        counter = 1
        teams_info.sort(key=lambda x: x[1], reverse=True)

        for team in teams_info:
            if counter == 11:
                description += "### Отстающие\n"
            elif counter == 4:
                description += "### Догоняющие\n"
            # elif counter == 1:
            #     description += "🥇 "
            # elif counter == 2:
            #     description += "🥈 "
            # elif counter == 3:
            #     description += "🥉 "

            # TODO сделать красивое форматирование
            description += f"{counter}. {team[0]}: {team[1]}\n"
            counter += 1

        description += (f"\n\n Обновлено "
                        f"{disnake.utils.format_dt(datetime.now(), style='R')}")
        embed = disnake.Embed(
            description=description,
            color=0xffcc4d
        )

        return embed

    @tasks.loop(seconds=300.0)
    async def leaderboard(self):
        try:
            leaderboard_channel = self.bot.get_channel(LEADERBOARD_CHAT_ID)
            leaderboard_message = await leaderboard_channel.fetch_message(LEADERBOARD_MSG_ID)

            leaderboard_info = read_query(f"SELECT * FROM teams")
            if leaderboard_info:
                teams_info = []
                for team in leaderboard_info:
                    name = team[1]
                    score = team[2] + team[3] + team[4]

                    teams_info.append([name, score])

                # await leaderboard_channel.send(embed=self.get_embed(teams_info))
                await leaderboard_message.edit(embed=self.get_embed(teams_info))

        except disnake.DiscordException as ex:
            print("Bruh. Что-то пошло не так в разделе Leaderboard")
            print(ex)

    @leaderboard.before_loop
    async def before_leaderboard(self):
        await self.bot.wait_until_ready()

    # TODO сделать перезапуск в случае падения


def setup(bot):
    bot.add_cog(Leaderboard(bot))
