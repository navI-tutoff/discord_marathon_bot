# import disnake
# from disnake.ext import commands
#
# from marathon_views import WelcomeMarathonButton
#
# from defines_config import ORGANIZER_ROLE_ID
# from defines_config import REG_MARATHON_CHAT_ID
#
# from errors_handling import check_missing_role
#
#
# class Marathon(commands.Cog):
#     def __init__(self, bot):
#         self.bot = bot
#
#     # команда для запуска кнопки старта марафона
#     @commands.slash_command(name="marathon-start",
#                             default_member_permissions=disnake.Permissions(mention_everyone=True))
#     @commands.has_role(ORGANIZER_ROLE_ID)
#     async def start_marathon(self, interaction: disnake.ApplicationCommandInteraction):
#         marathon_channel = self.bot.get_channel(REG_MARATHON_CHAT_ID)
#
#         welcome_view = WelcomeMarathonButton()  # форма для начала регистрации
#         await marathon_channel.send("## Регистрируйтесь на марафон правильного отдыха!\n"
#                                     "За две недели марафона вы:\n"
#                                     "- текст\n"
#                                     "- текст",
#                                     view=welcome_view)
#         await interaction.send("Отправили старт марафона")
#         await welcome_view.wait()
#
#     # обработчик ошибок при недостатке прав выполнения команды marathon-start
#     @start_marathon.error
#     async def start_marathon_error_handler(self, interaction: disnake.ApplicationCommandInteraction, error):
#         await check_missing_role(interaction, error)
#
#
# def setup(bot):
#     bot.add_cog(Marathon(bot))
