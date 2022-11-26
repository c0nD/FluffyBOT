import attrs
import boss
import cattrs
import discord
import json
import pytz
import re
import view
import csv, io
import sys, traceback
import pandas as pd
from apscheduler.schedulers.background import BackgroundScheduler
from types import SimpleNamespace
from datetime import datetime
from discord import Intents, MemberCacheFlags, Embed, app_commands
from discord.ext import commands
from discord.ext.commands import Bot
from discord.ui import Button, View

# FINALS
guild_ids = [1036888929850359840]
admin_roles = []
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
    @bot.tree.command(name="admin_hit", description="HIT THE BOSS TO FIX THE HP -- WILL NOT REGISTER AS A HIT.")
    @app_commands.describe(damage="Enter the exact amount to deal to the boss.")
    @commands.guild_only()
    async def admin_hit(interaction: discord.Interaction, damage: str):
        await interaction.response.send_message("Attempting to hit...")  # Deferring so I can followup later
        res = bool(boss_dict.get(interaction.channel_id))
        if not res:
            await interaction.followup.send(
                "A boss has not been set up in this channel. If this is a mistake: please contact c0nD.")
            await interaction.delete_original_response()
            return
        if str(interaction.channel.name).lower() in valid_channels:
            curr_boss = boss_dict[interaction.channel_id]
            damage = sanitize_int(damage)
            if damage > curr_boss.hp_list[curr_boss.level] or damage >= curr_boss.hp or damage < 0:
                await interaction.followup.send(
                    "Please double check that you input the exact, correct number for damage (will not accept comma"
                    " separated numbers or numbers ending with 'm' (123.4m). If you want to kill the boss, please"
                    " use `/admin_kill` instead. If there is some other error: please contact c0nD.")
                await interaction.delete_original_response()
                return
            curr_boss.admin_hit(damage)

            # Embed
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
            embed = discord.Embed(color=clr, title=f"lv.{curr_boss.level} {str(interaction.channel.name).upper()}",
                                  description=f"**_ADMIN_ did {damage:,} damage"
                                              f" to the {str(interaction.channel.name).upper()}**")
            embed.add_field(name="> __New Health__",
                            value=f"**HP: *{curr_boss.hp:,}/{curr_boss.hp_list[curr_boss.level]:,}***",
                            inline=True)
            embed.set_author(name=interaction.user.display_name,
                             icon_url=interaction.user.display_avatar.url)
            embed.set_footer(text=f"•CRK/KR TIME: {ct}•")
            await interaction.followup.send(embed=embed)
            await interaction.delete_original_response()

    @bot.tree.command(name="admin_kill", description="KILL THE BOSS TO FIX THE LEVEL -- WILL NOT REGISTER AS A HIT.")
    @commands.guild_only()
    async def admin_kill(interaction: discord.Interaction):
        res = bool(boss_dict.get(interaction.channel_id))
        if not res:
            await interaction.response.send_message(
                "A boss has not been set up in this channel. If this is a mistake, please contact c0nD ")
            return
        if str(interaction.channel.name).lower() in valid_channels:
            curr_boss = boss_dict[interaction.channel_id]
            curr_boss.admin_kill()
            allowed_mentions = discord.AllowedMentions(everyone=True)
            await interaction.response.send_message(f"**_ADMIN_ has killed the boss. New Boss:**",
                                                    allowed_mentions=allowed_mentions)
            embed = get_hp_embed(interaction, curr_boss)
            await interaction.followup.send(embed=embed)

    @bot.tree.command(name="admin_revive", description="REVIVE THE BOSS TO FIX THE LEVEL -- WILL NOT REGISTER AS A HIT")
    @commands.guild_only()
    async def admin_revive(interaction: discord.Interaction):
        res = bool(boss_dict.get(interaction.channel_id))
        if not res:
            await interaction.response.send_message(
                "A boss has not been set up in this channel. If this is a mistake, please contact c0nD ")
            return
        if str(interaction.channel.name).lower() in valid_channels:
            curr_boss = boss_dict[interaction.channel_id]
            if curr_boss.level == 1:
                await interaction.response.send_message("**Cannot revive boss. No levels to be revived to.**")
                return
            curr_boss.admin_revive()
            allowed_mentions = discord.AllowedMentions(everyone=True)
            await interaction.response.send_message(f"**_ADMIN_ has revived the boss. New Boss:**",
                                                    allowed_mentions=allowed_mentions)
            embed = get_hp_embed(interaction, curr_boss)
            await interaction.followup.send(embed=embed)

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
                embed = get_hp_embed(interaction, new_boss)
                await interaction.followup.send(embed=embed)
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
                                                     f" {str(interaction.channel.name).upper()}`**")
                del boss_dict[interaction.channel_id]
            except Exception as e:
                await interaction.response.send_message(f"Cannot delete a boss that does not exist. Please create "
                                                        f"a boss before trying to call `/delete_boss`.")

    @bot.tree.command(name="insert_boss", description="Insert a boss with stats. (PLEASE USE IN LAST CASE SCENARIO)")
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
                await interaction.response.send_message(f"**Inserted `lv.{new_boss.level}"
                                                        f" {interaction.channel.name.upper()}` Boss**.")
                embed = get_hp_embed(interaction, new_boss)
                await interaction.followup.send(embed=embed)
            else:
                await interaction.response.send_message("Cannot create two bosses at once. If you want to reset "
                                                        "the boss, please call `/delete_boss` first.")
        else:
            await interaction.response.send_message("Cannot create boss in this channel. Please try"
                                                    " this command again in a valid channel.")

    # USER COMMANDS
    @bot.tree.command(name="hit", description="Uses 1 ticket to hit the boss.")
    @app_commands.describe(damage="Enter the exact amount of damage dealt to the boss.")
    @commands.guild_only()
    async def hit(interaction: discord.Interaction, damage: str):
        await interaction.response.send_message("Attempting to hit...")  # Deferring so I can followup later
        res = bool(boss_dict.get(interaction.channel_id))
        if not res:
            await interaction.followup.send(
                "A boss has not been set up in this channel. Please contact staff if you think this is a mistake.")
            await interaction.delete_original_response()
            return
        if str(interaction.channel.name).lower() in valid_channels:
            curr_boss = boss_dict[interaction.channel_id]
            damage = sanitize_int(damage)
            if damage > curr_boss.hp_list[curr_boss.level] or damage >= curr_boss.hp or damage < 0:
                await interaction.followup.send(
                    "Please double check that you input the exact, correct number for damage (will not accept comma"
                    " separated numbers or numbers ending with 'm' (123.4m). If you killed the boss"
                    " please use the `/killed` command before calling `/hit` if you just swept this boss. If"
                    " neither of these are the case, please contact your staff to get them to reset the boss"
                    " at it's current level and hp.")
                await interaction.delete_original_response()
                return
            if interaction.user.id in curr_boss.current_users_hit:
                curr_boss.take_damage(damage, interaction.user.id, True, False)
            else:
                curr_boss.take_damage(damage, interaction.user.id, True, True)
                curr_boss.current_users_hit.append(interaction.user.id)
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
            embed = discord.Embed(color=clr, title=f"lv.{curr_boss.level} {str(interaction.channel.name).upper()}",
                                  description=f"**{interaction.user.mention} did {damage:,} damage"
                                              f" to the {str(interaction.channel.name).upper()}**")
            embed.add_field(name="> __New Health__",
                            value=f"**HP: *{curr_boss.hp:,}/{curr_boss.hp_list[curr_boss.level]:,}***",
                            inline=True)
            embed.set_author(name=interaction.user.display_name,
                             icon_url=interaction.user.display_avatar.url)
            embed.set_footer(text=f"•CRK/KR TIME: {ct}•")
            await interaction.followup.send(embed=embed)
            await interaction.delete_original_response()

    # Hit command for when you don't want it to subtract a ticket
    @bot.tree.command(name="bonus_hit", description="Hit the boss *without* using a ticket (aka Continued hit).")
    @app_commands.describe(damage="Enter the exact amount of damage dealt to the boss.")
    @commands.guild_only()
    async def bonus_hit(interaction: discord.Interaction, damage: str):
        await interaction.response.send_message("Attempting to hit...")  # Deferring so I can followup later
        res = bool(boss_dict.get(interaction.channel_id))
        if not res:
            await interaction.followup.send(
                "A boss has not been set up in this channel. Please contact staff if you think this is a mistake.")
            await interaction.delete_original_response()
            return
        if str(interaction.channel.name).lower() in valid_channels:
            curr_boss = boss_dict[interaction.channel_id]
            damage = sanitize_int(damage)
            if damage > curr_boss.hp_list[curr_boss.level] or damage >= curr_boss.hp or damage < 0:
                await interaction.followup.send(
                    "Please double check that you input the exact, correct number for damage (will not accept comma"
                    " separated numbers or numbers ending with 'm' (123.4m). If you killed the boss"
                    " please use the `/killed` command before calling `/hit` if you just swept this boss. If"
                    " neither of these are the case, please contact your staff to get them to reset the boss"
                    " at it's current level and hp.")
                await interaction.delete_original_response()
                return
            if interaction.user.id in curr_boss.current_users_hit:
                curr_boss.take_damage(damage, interaction.user.id, False, False)
            else:
                curr_boss.take_damage(damage, interaction.user.id, False, True)
                curr_boss.current_users_hit.append(interaction.user.id)
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
            embed = discord.Embed(color=clr, title=f"lv.{curr_boss.level} {str(interaction.channel.name).upper()}",
                                  description=f"**{interaction.user.mention} did {damage:,} damage"
                                              f" to the {str(interaction.channel.name).upper()}**")
            embed.add_field(name="> __New Health__",
                            value=f"**HP: *{curr_boss.hp:,}/{curr_boss.hp_list[curr_boss.level]:,}***",
                            inline=True)
            embed.set_author(name=interaction.user.display_name,
                             icon_url=interaction.user.display_avatar.url)
            embed.set_footer(text=f"•CRK/KR TIME: {ct}•")
            await interaction.followup.send(embed=embed)
            await interaction.delete_original_response()

    @bot.tree.command(name="killed", description="Uses a ticket and kills the boss.")
    @commands.guild_only()
    async def killed(interaction: discord.Interaction):
        res = bool(boss_dict.get(interaction.channel_id))
        if not res:
            await interaction.response.send_message(
                "A boss has not been set up in this channel. Please contact staff if you think this is a mistake.")
            return
        if str(interaction.channel.name).lower() in valid_channels:
            curr_boss = boss_dict[interaction.channel_id]
            curr_boss.take_damage(curr_boss.hp, interaction.user.id, True, True)
            curr_boss.killed()
            allowed_mentions = discord.AllowedMentions(everyone=True)
            ping = discord.utils.get(interaction.guild.roles, id=ping_roles[interaction.channel.name])
            await interaction.response.send_message(f"**{ping.mention} has been swept. New Boss:**",
                                                    allowed_mentions=allowed_mentions)
            embed = get_hp_embed(interaction, curr_boss)
            await interaction.followup.send(embed=embed)

    # Killed command for when you don't want it to subtract a ticket
    @bot.tree.command(name="bonus_kill", description="Kill the boss *without* using a ticket (aka solo'd).")
    @commands.guild_only()
    async def bonus_kill(interaction: discord.Interaction):
        res = bool(boss_dict.get(interaction.channel_id))
        if not res:
            await interaction.response.send_message(
                "A boss has not been set up in this channel. Please contact staff if you think this is a mistake.")
            return
        if str(interaction.channel.name).lower() in valid_channels:
            curr_boss = boss_dict[interaction.channel_id]
            curr_boss.take_damage(curr_boss.hp, interaction.user.id, False, True)
            curr_boss.killed()
            allowed_mentions = discord.AllowedMentions(everyone=True)
            ping = discord.utils.get(interaction.guild.roles, id=ping_roles[interaction.channel.name])
            await interaction.response.send_message(f"**{ping.mention} has been swept. New Boss:**",
                                                    allowed_mentions=allowed_mentions)
            embed = get_hp_embed(interaction, curr_boss)
            await interaction.followup.send(embed=embed)

    @bot.tree.command(name="hp", description="Check the HP of the boss.")
    @commands.guild_only()
    async def hp(interaction: discord.Interaction):
        res = bool(boss_dict.get(interaction.channel_id))
        if not res:
            await interaction.response.send_message(
                "A boss has not been set up in this channel. Please contact staff if you think this is a mistake.")
            return
        if str(interaction.channel.name).lower() in valid_channels:
            curr_boss = boss_dict[interaction.channel_id]
            embed = get_hp_embed(interaction, curr_boss)
            await interaction.response.send_message(embed=embed)

    @bot.tree.command(name="boss_help", description="Help understand how to use Fluffy!")
    @commands.guild_only()
    async def boss_help(interaction: discord.Interaction):
        embed = discord.Embed(title="Documentation",
                              description="Please click on the link above to view the documentation for all"
                                          " possible commands.",
                              url="https://www.onioncult.com/bot-help/",
                              color=0x6c25be)
        await interaction.response.send_message(embed=embed)

    # Reading / Writing to json
    def __write_json():
        json_object = json.dumps(cattrs.unstructure(boss_dict), indent=4)
        with open("data.json", "w") as outfile:
            outfile.write(json_object)
        print("Saved to json file.")

    async def __convert_csv():
        for key in boss_dict:
            for i in boss_dict[key].hits:
                user = await bot.get_user(i.user_id)
                i.username = user.name

        __write_json()

        df = pd.read_json(r'data.json')
        df.to_csv(r'data.csv', index=None)

    @bot.tree.command(name="send_csv", description="Loads the current data.json into the boss_dictionary")
    @commands.guild_only()
    async def send_csv(interaction: discord.Interaction):
        await interaction.response.send_message("Converting data to csv file...")
        await __convert_csv()
        await interaction.followup.send(file=discord.File('data.csv'))

    # Setting up scheduler to save data
    scheduler = BackgroundScheduler()
    scheduler.add_job(__write_json, 'interval', seconds=600)
    scheduler.start()

    # Run the bot
    tkn = 'MTAzOTY3MDY3NzE4NTIzNzAzNA.GBXmNr.m2gHuFoBsFFngVnge1k54XInzNZ78T_PuvQBZw'
    bot.run(tkn)


def sanitize_int(num):
    try:
        if num[-1].lower() == 'm':
            return -1
        re.sub('\D', '', str(num))
        num = int(num)
        return num
    except Exception as e:
        return -1


def get_hp_embed(interaction: discord.Interaction, curr_boss):
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
    embed = discord.Embed(title=f"lv.{curr_boss.level} {str(interaction.channel.name).upper()}", color=clr)
    embed.add_field(name="> __Health__",
                    value=f"**HP: *{curr_boss.hp:,}/{curr_boss.hp_list[curr_boss.level]:,}***",
                    inline=True)
    embed.set_author(name=interaction.user.display_name,
                     icon_url=interaction.user.display_avatar.url)
    embed.set_footer(text=f"•CRK/KR TIME: {ct}•")
    return embed