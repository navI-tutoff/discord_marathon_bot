import disnake
from disnake.ext import commands


# проверяет несоответствие роли, отправляет соответствующее сообщение
async def check_missing_role(interaction: disnake.ApplicationCommandInteraction, error):
    if isinstance(error, commands.MissingRole):
        await interaction.response.send_message("У вас недостаточно прав для выполнения этой команды",
                                                ephemeral=True)
