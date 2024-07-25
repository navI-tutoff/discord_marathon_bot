from main import disnake
from main import commands

from db_config import execute_query
from db_config import read_query


class Leaderboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


def setup(bot):
    bot.add_cog(Leaderboard(bot))
