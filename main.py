import os
import disnake
from disnake.ext import commands, tasks

from cogs.marathon_views import *
from cogs.organizer import Organizer

from defines_config import REG_MARATHON_MSG_ID
from defines_config import REG_MARATHON_CHAT_ID
from defines_config import PRACTISE_CHAT_ID

# === intents ===
# intents = disnake.Intents.default()
# intents.message_content = True
intents = disnake.Intents.all()

bot = commands.InteractionBot(intents=intents)


@bot.event
async def on_ready():
    print(f"Bot {bot.user} is ready!\n")
    # await bot.change_presence(activity=disnake.Game('развитие'))

    # ===================== отслеживание кнопок =====================
    # кнопка регистрации на марафон
    main_channel = bot.get_channel(REG_MARATHON_CHAT_ID)
    if main_channel:
        message = await main_channel.fetch_message(REG_MARATHON_MSG_ID)
        if message:
            welcome_view = WelcomeMarathonButton()
            await message.edit(view=welcome_view)

    # кнопки лучших практик
    practise_channel = bot.get_channel(PRACTISE_CHAT_ID)
    if practise_channel:
        practise_buttons = read_query(f"SELECT practise_name, message_id FROM practises")
        for button in practise_buttons:
            message = await practise_channel.fetch_message(int(button[1]))
            if message:
                submit_practise = Organizer.SubmitPractiseButton()
                await message.edit(view=submit_practise)


# команда для загрузки когов
@bot.slash_command(name="load-cog",
                   default_member_permissions=disnake.Permissions(administrator=True))
@commands.is_owner()
async def load(ctx, extension):
    bot.load_extension(f'cogs.{extension}')
    await ctx.send(f'Загружен модуль {extension}', ephemeral=True)


# команда для выгрузки когов
@bot.slash_command(name="unload-cog",
                   default_member_permissions=disnake.Permissions(administrator=True))
@commands.is_owner()
async def unload(ctx, extension):
    bot.unload_extension(f'cogs.{extension}')
    await ctx.send(f'Выгружен модуль {extension}', ephemeral=True)


# команда для перезагрузки когов
@bot.slash_command(name="reload-cog",
                   default_member_permissions=disnake.Permissions(administrator=True))
@commands.is_owner()
async def reload(ctx, extension):
    bot.reload_extension(f'cogs.{extension}')
    bot.load_extension(f'cogs.{extension}')
    await ctx.send(f'Перезагружен модуль {extension}', ephemeral=True)


# считывание всех когов
for filename in os.listdir("./cogs"):
    if filename.endswith(".py"):
        bot.load_extension(f"cogs.{filename[:-3]}")

bot.run("MTI0MzgyMzAyOTE4MDY5ODY2NA.GxMCs5.y_pYr3lm5fY0x484HyMTTGbgEF48gFY3bMeY3Y")
