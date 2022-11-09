import discord
from discord.ext import commands
from discord.ext.commands import Bot
import command_integration
import random
import os


def run_bot():
    # Boring setup
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True
    intents.guilds = True
    intents.presences = False

    bot = Bot("$", intents=intents)

    # Async Commands
    @bot.event
    async def on_ready():
        print(f'\n\n\t\t\t\t\t\t{bot.user} is now running!')

    @bot.command()
    async def ping(ctx):
        await ctx.send(f'Pong {ctx.author.mention}')

    @bot.command()
    async def hit(ctx, damage):
        health_left = command_integration.health_calc(damage, str(ctx.channel.name))
        await ctx.send(f"{health_left}")

    # Run the bot
    tkn = 'MTAzOTY3MDY3NzE4NTIzNzAzNA.GMKe3G.UaqGU_yHdCYEhigVY3795Hn34o0KFevUzd6dmc'
    bot.run(tkn)