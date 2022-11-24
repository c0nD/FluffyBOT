import attrs
import boss
import cattrs
import discord
import json
import pytz
import re
import view
import csv
import sys, traceback
from apscheduler.schedulers.background import BackgroundScheduler
from types import SimpleNamespace
from datetime import datetime
from discord import Intents, MemberCacheFlags, Embed, app_commands
from discord.ext import commands
from discord.ext.commands import Bot
from discord.ui import Button, View

# FINALS
guild_ids = [1036888929850359840]
valid_channels = ['aod', 'tla', 'rvd']
guilds = {
    "toasted": None,
    "pearl": None,
    "burnt": None,
    "royal": None,
    "spring": None,
    "fall": None,
    "onion": None
}

ping_roles = {
    "aod": 1040927294123937852,
    "tla": 1040927394288115753,
    "rvd": 1040927439343341620
}


def run_bot():
    # Boring setup
    bot = Bot("$", member_cache_flags=MemberCacheFlags.all(), intents=Intents.all())

    @bot.event
    async def on_ready():
        print(f'\n\n\t\t\t\t\t\t{bot.user} is now running!')
        try:
            synced = await bot.tree.sync()
            print(f"Synced {len(synced)} command(s)")
        except Exception as e:
            print(e)

    bot.remove_command("help")
    boss_dict = {}

    @bot.event
    async def on_command_error(ctx, exception):
        exc_class = exception.__class__
        if exc_class in (commands.CommandNotFound, commands.NotOwner):
            return

        exc_table = {
            commands.MissingRequiredArgument: f"The required arguments are missing for this command!",
            commands.NoPrivateMessage: f"This command cannot be used in PM's!",
            commands.BadArgument: f"A bad argument was passed, please check if your arguments are correct!",
        }

        if exc_class in exc_table.keys():
            await ctx.send(exc_table[exc_class])
            await help(ctx)
        else:
            # All other Errors not returned come here. And we can just print the default TraceBack.
            print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
            traceback.print_exception(type(exception), exception, exception.__traceback__, file=sys.stderr)

    # STAFF COMMANDS
    @bot.tree.command(name="create_boss", description="Add a boss to this channel.")
    @app_commands.describe(guild="Enter the guild this boss belongs to (ie. Onion, Spring, etc).")
    @commands.guild_only()
    async def create_boss(interaction: discord.Interaction, guild: str):
        guild = guild.lower()
        if guild not in guilds:
            await interaction.response.send_message("Invalid guild. Type `$help` for more information.")
            return
        elif guilds[guild] is None:
            guilds[guild] = boss.Guild()
        if str(interaction.channel.name).lower() in valid_channels:
            new_boss = boss.Boss(interaction.channel.name, 1, guild)
            res = bool(boss_dict.get(interaction.channel_id))
            if not res:
                boss_dict[interaction.channel_id] = new_boss
                await interaction.response.send_message(f"**Created `{str(interaction.channel.name).upper()}` "
                                                        f"Boss for `{guild.capitalize()}`.**")
            else:
                await interaction.response.send_message(
                    "Cannot create two bosses at once. If you want to reset the boss, please call "
                    "`/delete_boss` first.")
        else:
            await interaction.response.send_message(
                "Attempting to create a boss in a channel not designated to create bosses in.")

    @bot.tree.command(name="delete_boss", description="Delete the boss out of the current channel."
                                                      " Use carefully.")
    @commands.guild_only()
    async def delete_boss(interaction: discord.Interaction):
        if str(interaction.channel.name).lower() in valid_channels:
            try:
                curr_boss = boss_dict[interaction.channel_id]
                await interaction.response.send_message(f"**Deleting `lv.{curr_boss.level}"
                                                     f" {str(interaction.channel.name).upper()}` boss.**")
                del boss_dict[interaction.channel_id]
            except Exception as e:
                await interaction.response.send_message(f"Cannot delete a boss that does not exist. Please create "
                                                        f"a boss before trying to call `/delete_boss`.")

    @bot.tree.command(name="insert_boss", description="Insert a boss (stat inclusive) to this channel.")
    @app_commands.describe(guild="Enter the guild this boss belongs to (ie. Onion, Spring, etc).",
                           level="Enter the level of the boss to be inserted.",
                           health="Enter the health of the boss to be inserted.")
    @commands.guild_only()
    async def insert_boss(interaction: discord.Interaction, guild: str,
                          level: str, health: str):
        if str(interaction.channel.name).lower() in valid_channels:
            level = sanitize_int(level)
            health = sanitize_int(health)
            guild = guild.lower()
            if guild not in guilds:
                await interaction.response.send_message("Invalid guild. Type `/boss_help` for more information.")
                return
            elif guilds[guild] is None:
                guilds[guild] = boss.Guild()

            new_boss = boss.Boss(interaction.channel.name, level, guild)
            # If you accidentally set the hp too high
            if health > new_boss.hp_list[new_boss.level]:
                res = bool(boss_dict.get(interaction.channel_id))
                if res:
                    del boss_dict[interaction.channel_id]
                    await interaction.response.send_message("HP was set higher than boss level allows for."
                                                            " Please try again with valid HP.")
                    return
            else:
                new_boss.set_hp(health)

            res = bool(boss_dict.get(interaction.channel_id))
            if not res:
                boss_dict[interaction.channel_id] = new_boss
                await interaction.response.send_message(f"**Inserted `{interaction.channel.name}` Boss**.")
            else:
                await interaction.response.send_message("Cannot create two bosses at once. If you want to reset "
                                                        "the boss, please call `/delete_boss` first.")
        else:
            await interaction.response.send_message("Cannot create boss in this channel. Please try"
                                                    " this command again in a valid channel.")

    # USER COMMANDS
    @bot.command()
    @commands.guild_only()
    async def hit(ctx, damage):
        res = bool(boss_dict.get(ctx.channel.id))
        if not res:
            await ctx.send(
                "A boss has not been set up in this channel. Please contact staff if you think this is a mistake.")
            return
        if str(ctx.channel.name).lower() in valid_channels:
            curr_boss = boss_dict[ctx.channel.id]
            damage = sanitize_int(damage)
            if damage > curr_boss.hp_list[curr_boss.level] or damage >= curr_boss.hp or damage < 0:
                await ctx.send(
                    "Please double check that you input the correct number for damage. If you killed the boss"
                    " please use the `$killed` command before calling `$hit` if you just swept this boss. If"
                    " neither of these are the case, please contact your staff to get them to reset the boss"
                    " at it's current level and hp.")
                return
            if ctx.message.author.id in curr_boss.current_users_hit:
                curr_boss.take_damage(damage, ctx.message.author.id, True, False)
            else:
                curr_boss.take_damage(damage, ctx.message.author.id, True, True)
                curr_boss.current_users_hit.append(ctx.message.author.id)
            name = curr_boss.name
            tz = pytz.timezone("Asia/Seoul")
            unformatted_time = datetime.now(tz)
            ct = unformatted_time.strftime("%H:%M:%S")
            if name == 'rvd':
                clr = 0xFF6060
            elif name == 'aod':
                clr = 0xB900A2
            else:
                clr = 0x58C7CF
            embed = discord.Embed(color=clr, title=f"lv.{curr_boss.level} {str(ctx.channel.name).upper()}",
                                  description=f"**{ctx.author.mention} did {damage:,} damage"
                                              f" to the {str(ctx.channel.name).upper()}**")
            embed.add_field(name="> __New Health__",
                            value=f"**HP: *{curr_boss.hp:,}/{curr_boss.hp_list[curr_boss.level]:,}***",
                            inline=True)
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
            embed.set_footer(text=f"•CRK/KR TIME: {ct}•")
            await ctx.send(embed=embed)

    # Hit command for when you don't want it to subtract a ticket
    @bot.command(aliases=["resume_hit"])
    @commands.guild_only()
    async def bonus_hit(ctx, damage):
        res = bool(boss_dict.get(ctx.channel.id))
        if not res:
            await ctx.send(
                "A boss has not been set up in this channel. Please contact staff if you think this is a mistake.")
            return
        if str(ctx.channel.name).lower() in valid_channels:
            curr_boss = boss_dict[ctx.channel.id]
            damage = sanitize_int(damage)
            if damage > curr_boss.hp_list[curr_boss.level] or damage >= curr_boss.hp or damage < 0:
                await ctx.send(
                    "Please double check that you input the correct number for damage. If you killed the boss"
                    " please use the `$killed` command before calling `$hit` if you just swept this boss. If"
                    " neither of these are the case, please contact your staff to get them to reset the boss"
                    " at it's current level and hp.")
                return
            if ctx.message.author.id in curr_boss.current_users_hit:
                curr_boss.take_damage(damage, ctx.message.author.id, False, False)
            else:
                curr_boss.take_damage(damage, ctx.message.author.id, False, True)
                curr_boss.current_users_hit.append(ctx.message.author.id)
            name = curr_boss.name
            tz = pytz.timezone("Asia/Seoul")
            unformatted_time = datetime.now(tz)
            ct = unformatted_time.strftime("%H:%M:%S")
            if name == 'rvd':
                clr = 0xFF6060
            elif name == 'aod':
                clr = 0xB900A2
            else:
                clr = 0x58C7CF
            embed = discord.Embed(title=f"lv.{curr_boss.level} {str(ctx.channel.name).upper()}",
                                  description=f"**{ctx.author.mention} did {damage:,} damage"
                                              f" to the {str(ctx.channel.name).upper()}**",
                                  color=clr)
            embed.add_field(name="> __New Health__",
                            value=f"**HP: *{curr_boss.hp:,}/{curr_boss.hp_list[curr_boss.level]:,}***",
                            inline=True)
            embed.set_author(name=ctx.author.display_name,
                             icon_url=ctx.author.display_avatar.url)  # interaction.user.display_avatar.url interaction.user.display_name
            embed.set_footer(text=f"•CRK/KR TIME: {ct}•")
            await ctx.send(embed=embed)

    @bot.command()
    @commands.guild_only()
    async def killed(ctx):
        res = bool(boss_dict.get(ctx.channel.id))
        if not res:
            await ctx.send(
                "A boss has not been set up in this channel. Please contact staff if you think this is a mistake.")
            return
        if str(ctx.channel.name).lower() in valid_channels:
            curr_boss = boss_dict[ctx.channel.id]
            curr_boss.take_damage(curr_boss.hp, ctx.message.author.id, True, True)
            curr_boss.killed()
            allowed_mentions = discord.AllowedMentions(everyone=True)
            ping = discord.utils.get(ctx.guild.roles, id=ping_roles[ctx.channel.name])
            await ctx.send(f"{ping.mention} has been swept. New Boss:", allowed_mentions=allowed_mentions)
            await hp(ctx)

    # Killed command for when you don't want it to subtract a ticket
    @bot.command()
    @commands.guild_only()
    async def bonus_kill(ctx):
        res = bool(boss_dict.get(ctx.channel.id))
        if not res:
            await ctx.send(
                "A boss has not been set up in this channel. Please contact staff if you think this is a mistake.")
            return
        if str(ctx.channel.name).lower() in valid_channels:
            curr_boss = boss_dict[ctx.channel.id]
            curr_boss.take_damage(curr_boss.hp, ctx.message.author.id, False, True)
            curr_boss.killed()
            ping = discord.utils.get(ctx.guild.roles, id=ping_roles[ctx.channel.name])
            await ctx.send(f"{ping.mention} has been bonus killed by {ctx.message.author.mention}. Next Boss:")
            await hp(ctx)

    @bot.command()
    @commands.guild_only()
    async def hp(ctx):
        res = bool(boss_dict.get(ctx.channel.id))
        if not res:
            await ctx.send(
                "A boss has not been set up in this channel. Please contact staff if you think this is a mistake.")
            return
        if str(ctx.channel.name).lower() in valid_channels:
            curr_boss = boss_dict[ctx.channel.id]
            name = curr_boss.name
            tz = pytz.timezone("Asia/Seoul")
            unformatted_time = datetime.now(tz)
            ct = unformatted_time.strftime("%H:%M:%S")
            if name == 'rvd':
                clr = 0xFF6060
            elif name == 'aod':
                clr = 0xB900A2
            else:
                clr = 0x58C7CF
            embed = discord.Embed(title=f"lv.{curr_boss.level} {str(ctx.channel.name).upper()}", color=clr)
            embed.add_field(name="> __Health__",
                            value=f"**HP: *{curr_boss.hp:,}/{curr_boss.hp_list[curr_boss.level]:,}***",
                            inline=True)
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
            embed.set_footer(text=f"•CRK/KR TIME: {ct}•")
            await ctx.send(embed=embed)

    @bot.command()
    @commands.guild_only()
    async def help(ctx):
        embed = discord.Embed(title="Documentation",
                              description="Please click on the link above to view the documentation for all"
                                          " possible commands.",
                              url="https://www.onioncult.com/bot-help/",
                              color=0x6c25be)
        await ctx.send(embed=embed)

    @bot.command()
    @commands.guild_only()
    async def print_dict(ctx):
        for key in boss_dict:
            boss_json = cattrs.unstructure(boss_dict[key])
            await ctx.send(boss_json)

    # Reading / Writing to json
    def __write_json():
        print("Execute")
        json_object = json.dumps(cattrs.unstructure(boss_dict), indent=4)
        with open("data.json", "w") as outfile:
            outfile.write(json_object)

    def __read_json():
        pass

    @bot.command()
    @commands.guild_only()
    async def send_data(ctx):
        for i in boss_dict:
            for j in boss_dict[i].hits:
                if j.user_id != -1:
                    user = await bot.fetch_user(j.user_id)
                    j.username = user.name

                    await ctx.send(j)

    # Setting up scheduler to save data
    scheduler = BackgroundScheduler()
    scheduler.add_job(__write_json, 'interval', seconds=600)
    scheduler.start()

    # Run the bot
    tkn = 'MTAzOTY3MDY3NzE4NTIzNzAzNA.GBXmNr.m2gHuFoBsFFngVnge1k54XInzNZ78T_PuvQBZw'
    bot.run(tkn)


def sanitize_int(num):
    re.sub('\D', '', str(num))
    num = int(num)
    return num
