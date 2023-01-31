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
import linecache
import jsonpickle
from ast import literal_eval
from collections import namedtuple
from apscheduler.schedulers.background import BackgroundScheduler
from types import SimpleNamespace
from datetime import datetime
from discord import Intents, MemberCacheFlags, Embed, app_commands
from discord.ext import commands
from discord.ext.commands import Bot
from discord.ui import Button, View

# FINALS
guild_id = 1036888929850359840
admin_roles = []
valid_channels = ['avatar', 'living_abyss', 'dragon']
split_threshold = 3
guilds = {
    "toasted": None,
    "pearl": None,
    "burnt": None,
    "royal": None,
    "spring": None,
    "fall": None,
    "onion": None,

    "toasted_sandbox": None,
    "pearl_sandbox": None,
    "burnt_sandbox": None,
    "royal_sandbox": None,
    "spring_sandbox": None,
    "fall_sandbox": None,
    "onion_sandbox": None,

    "dev": None
}

ping_roles = {
    "avatar": 1047787785895038986,
    "living_abyss": 1047787857357590538,
    "dragon": 1042512104059568138
}

sweeper_roles = {
    "avatar": 1061881832280424529,
    "living_abyss": 1061881839419150376,
    "dragon": 1061881749098999808
}

sweeper_requirements = {
    "onion": {
        "avatar": 75_000_000,
        "living_abyss": 100_000_000,
        "dragon": 5_000_000
    },
    "fall": {
        "avatar": 70_000_000,
        "living_abyss": 85_000_000,
        "dragon": 5_000_000
    },
    "spring": {
        "avatar": 55_000_000,
        "living_abyss": 50_000_000,
        "dragon": 5_000_000
    },
    "burnt": {
        "avatar": -1,
        "living_abyss": 55_000_000,
        "dragon": 5_000_000
    },
    "other": {
        "avatar": 5_000_000,
        "living_abyss": 5_000_000,
        "dragon": 5_000_000
    }
}

split_exempt = ["onion", "burnt", "toasted", "royal", "pearl", "onion_sandbox", "toasted_sandbox", 
                "pearl_sandbox", "burnt_sandbox", "royal_sandbox", "spring_sandbox", "fall_sandbox",]

def run_bot():
    # Boring setup
    bot = Bot("$", member_cache_flags=MemberCacheFlags.all(), intents=Intents.all())
    bot.boss_dict = {}

    @bot.event
    async def on_ready():
        print(f'\n\n\t\t\t\t\t\t{bot.user} is now running!')
        try:
            synced = await bot.tree.sync()
            print(f"Synced {len(synced)} command(s)")
        except Exception as e:
            print(e)

    bot.remove_command("help")


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
    @app_commands.guild_only()
    async def admin_hit(interaction: discord.Interaction, damage: str):
        await interaction.response.send_message("Attempting to hit...")  # Deferring so I can followup later
        res = bool(bot.boss_dict.get(interaction.channel_id))
        if not res:
            await interaction.edit_original_response(
                content="A boss has not been set up in this channel. If this is a mistake: please contact c0nD.")
            await interaction.delete_original_response()
            return
        if str(interaction.channel.name).lower() in valid_channels:
            curr_boss = bot.boss_dict[interaction.channel_id]
            damage = sanitize_int(damage)
            if damage > curr_boss.hp_list[curr_boss.level] or damage >= curr_boss.hp:
                await interaction.edit_original_response(
                        content="Please double check that you input a full integer value, correct number for damage"
                        " (will not accept comma separated numbers or numbers ending with 'm' (123.4m)). If you want"
                        " to kill the boss, please use `/admin_kill` instead. If there is some other error: please contact c0nD.")
                return
            curr_boss.admin_hit(damage)

            # Embed
            name = curr_boss.name
            tz = pytz.timezone("Asia/Seoul")
            unformatted_time = datetime.now(tz)
            ct = unformatted_time.strftime("%H:%M:%S")
            if name == 'dragon':
                clr = 0xFF6060
                display_name = "RVD"
            elif name == 'avatar':
                clr = 0xB900A2
                display_name = "AOD"
            else:
                clr = 0x58C7CF
                display_name = "TLA"
            
            if damage < 0 and damage != -1:
                embed = discord.Embed(color=clr, title=f"lv.{curr_boss.level} {display_name}",
                                  description=f"**`ADMIN` healed {(-1*damage):,} HP"
                                              f" for the {display_name}**")
            else:
                embed = discord.Embed(color=clr, title=f"lv.{curr_boss.level} {display_name}",
                                    description=f"**`ADMIN` did {damage:,} damage"
                                                f" to the {display_name}**")
            embed.add_field(name="> __New Health__",
                            value=f"**HP: *{curr_boss.hp:,}/{curr_boss.hp_list[curr_boss.level]:,}***",
                            inline=True)
            embed.set_author(name=interaction.user.display_name,
                             icon_url=interaction.user.display_avatar.url)
            embed.set_footer(text=f"•CRK/KR TIME: {ct}•")
            await interaction.edit_original_response(embed=embed)
            
            ping = call_sweeper(interaction, curr_boss)
            if ping != -1:
                await interaction.channel.send(f"{ping.mention}")
            

    @bot.tree.command(name="admin_kill", description="KILL THE BOSS TO FIX THE LEVEL -- WILL NOT REGISTER AS A HIT.")
    @app_commands.guild_only()
    async def admin_kill(interaction: discord.Interaction):
        await interaction.response.send_message("Attempting to kill...")  # Deferring so I can followup later
        res = bool(bot.boss_dict.get(interaction.channel_id))
        if not res:
            await interaction.followup.send(
                "A boss has not been set up in this channel. If this is a mistake, please contact c0nD ")
            return
        if str(interaction.channel.name).lower() in valid_channels:
            curr_boss = bot.boss_dict[interaction.channel_id]
            curr_boss.admin_kill()
            allowed_mentions = discord.AllowedMentions(everyone=True)
            await interaction.followup.send(f"**_ADMIN_ has killed the boss. New Boss:**",
                                                    allowed_mentions=allowed_mentions)
            embed = get_hp_embed(interaction, curr_boss)
            await interaction.followup.send(embed=embed)
        await interaction.delete_original_response()

    @bot.tree.command(name="admin_revive", description="REVIVE THE BOSS TO FIX THE LEVEL -- WILL NOT REGISTER AS A HIT")
    @app_commands.guild_only()
    async def admin_revive(interaction: discord.Interaction):
        res = bool(bot.boss_dict.get(interaction.channel_id))
        if not res:
            await interaction.response.send_message(
                "A boss has not been set up in this channel. If this is a mistake, please contact c0nD ")
            return
        if str(interaction.channel.name).lower() in valid_channels:
            curr_boss = bot.boss_dict[interaction.channel_id]
            if curr_boss.level == 1:
                await interaction.response.send_message("**Cannot revive boss. No levels to be revived to.**")
                return
            curr_boss.admin_revive()
            allowed_mentions = discord.AllowedMentions(everyone=True)
            await interaction.response.send_message(f"**_ADMIN_ has revived the boss. New Boss:**",
                                                    allowed_mentions=allowed_mentions)
            embed = get_hp_embed(interaction, curr_boss)
            await interaction.followup.send(embed=embed)
            
    @bot.tree.command(name="insert_hit", description="Inserts a hit for another user. (INSERTING A WRONG USER_ID WILL BREAK THE BOT)")
    @app_commands.describe(user_id="Enter the user's discord ID (dev mode) that you'd like to insert.")
    @app_commands.describe(damage="Enter the exact amount of damage dealt to the boss.")
    @app_commands.describe(ticket_used="Enter 'true' or 'false' whether or not a ticket should be used.")
    @app_commands.guild_only()
    async def insert_hit(interaction: discord.Interaction, user_id: str, damage: str, ticket_used: str):
        
        damage = sanitize_int(damage)
        user_id = int(user_id)
        # cause people are stupid
        if ticket_used == "yes": ticket_used = "true"
        elif ticket_used == "no": ticket_used = "false"
        ticket_used = bool(ticket_used.lower().capitalize())
        
        await interaction.response.send_message("Attempting to hit...")  # Deferring so I can followup later
        res = bool(bot.boss_dict.get(interaction.channel_id))
        if not res:
            await interaction.followup.send(
                "A boss has not been set up in this channel. Please contact staff if you think this is a mistake.")
            await interaction.delete_original_response()
            return
        if str(interaction.channel.name).lower() in valid_channels:
            curr_boss = bot.boss_dict[interaction.channel_id]
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
                curr_boss.take_damage(damage, user_id, ticket_used, False, curr_boss.level)
            else:
                curr_boss.take_damage(damage, user_id, ticket_used, True, curr_boss.level)

            name = curr_boss.name
            tz = pytz.timezone("Asia/Seoul")
            unformatted_time = datetime.now(tz)
            ct = unformatted_time.strftime("%H:%M:%S")
            if name == 'dragon':
                clr = 0xFF6060
                display_name = "RVD"
            elif name == 'avatar':
                clr = 0xB900A2
                display_name = "AOD"
            else:
                clr = 0x58C7CF
                display_name = "TLA"
            embed = discord.Embed(color=clr, title=f"lv.{curr_boss.level} {display_name}",
                                  description=f"**`ADMIN` inserted a hit for {damage:,} damage"
                                              f" to the {display_name}**")
            embed.add_field(name="> __New Health__",
                            value=f"**HP: *{curr_boss.hp:,}/{curr_boss.hp_list[curr_boss.level]:,}***",
                            inline=True)
            embed.set_author(name=interaction.user.display_name,
                             icon_url=interaction.user.display_avatar.url)
            embed.set_footer(text=f"•CRK/KR TIME: {ct}•")
            await interaction.followup.send(embed=embed)
            
            ping = call_sweeper(interaction, curr_boss)
            if ping != -1:
                await interaction.channel.send(f"{ping.mention}")
            
            await interaction.delete_original_response()
            
    @bot.tree.command(name="insert_kill", description="Inserts a kill for another user. (INSERTING A WRONG USER_ID WILL BREAK THE BOT)")
    @app_commands.describe(user_id="Enter the user's discord ID (dev mode) that you'd like to insert.")
    @app_commands.describe(ticket_used="Enter 'true' or 'false' whether or not a ticket should be used.")
    @app_commands.describe(split="Enter 'true' or 'false' whether or not the hit was split.")
    @app_commands.guild_only()
    async def insert_kill(interaction: discord.Interaction, user_id: str, ticket_used: str, split: str):
        # Sanitization of input
        user_id = int(user_id)
        # cause people are stupid
        if ticket_used == "yes": ticket_used = "true"
        elif ticket_used == "no": ticket_used = "false"
        ticket_used = bool(ticket_used.lower().capitalize())
        
        if split == "yes": split = "true"
        elif split == "no": split = "false"
        split = bool(split.lower().capitalize())
        
        # Actually hitting the boss
        await interaction.response.send_message("Attempting to kill...")  # Deferring so I can followup later
        res = bool(bot.boss_dict.get(interaction.channel_id))
        if not res:
            await interaction.followup.send(
                "A boss has not been set up in this channel. Please contact staff if you think this is a mistake.")
            return
        if str(interaction.channel.name).lower() in valid_channels:
            curr_boss = bot.boss_dict[interaction.channel_id]
            curr_boss.take_damage(curr_boss.hp, user_id, ticket_used, split, curr_boss.level)
            curr_boss.killed()
            allowed_mentions = discord.AllowedMentions(everyone=True)
            ping = discord.utils.get(interaction.guild.roles, id=ping_roles[interaction.channel.name])
            await interaction.followup.send(f"**{ping.mention} has been swept by `ADMIN`. New Boss:**",
                                                    allowed_mentions=allowed_mentions)
            embed = get_hp_embed(interaction, curr_boss)
            await interaction.followup.send(embed=embed)
        await interaction.delete_original_response()

    @bot.tree.command(name="create_boss", description="Add a boss to this channel.")
    @app_commands.describe(guild="Enter the guild this boss belongs to (ie. Onion, Spring, etc).")
    @app_commands.guild_only()
    async def create_boss(interaction: discord.Interaction, guild: str):
        guild = guild.lower()
        if guild not in guilds:
            await interaction.response.send_message("Invalid guild. Type `$help` for more information.")
            return
        elif guilds[guild] is None:
            guilds[guild] = boss.Guild()

        _name = str(interaction.channel.name).lower()
        if  _name in valid_channels:
            res = bool(bot.boss_dict.get(interaction.channel_id))
            if not res:
                new_boss = boss.Boss(interaction.channel.name, 1, guild)
                bot.boss_dict[interaction.channel_id] = new_boss
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
    @app_commands.guild_only()
    async def delete_boss(interaction: discord.Interaction):
        if str(interaction.channel.name).lower() in valid_channels:
            try:
                curr_boss = bot.boss_dict[interaction.channel_id]
                await interaction.response.send_message(f"**Deleting `lv.{curr_boss.level}"
                                                     f" {str(interaction.channel.name).upper()}`**")
                del bot.boss_dict[interaction.channel_id]
            except Exception as e:
                await interaction.response.send_message(f"Cannot delete a boss that does not exist. Please create "
                                                        f"a boss before trying to call `/delete_boss`.")

    @bot.tree.command(name="insert_boss", description="Insert a boss with stats. (PLEASE USE IN LAST CASE SCENARIO)")
    @app_commands.describe(guild="Enter the guild this boss belongs to (ie. Onion, Spring, etc).",
                           level="Enter the level of the boss to be inserted.",
                           health="Enter the health of the boss to be inserted.")
    @app_commands.guild_only()
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
                res = bool(bot.boss_dict.get(interaction.channel_id))
                if res:
                    del bot.boss_dict[interaction.channel_id]
                    await interaction.response.send_message("HP was set higher than boss level allows for."
                                                            " Please try again with valid HP.")
                    return
            else:
                new_boss.set_hp(health)

            res = bool(bot.boss_dict.get(interaction.channel_id))
            if not res:
                bot.boss_dict[interaction.channel_id] = new_boss
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

    # =========================== USER COMMANDS ===========================
    @bot.tree.command(name="hit", description="Uses 1 ticket to hit the boss.")
    @app_commands.describe(damage="Enter the exact amount of damage dealt to the boss.")
    @app_commands.guild_only()
    async def hit(interaction: discord.Interaction, damage: str):
        await interaction.response.send_message("Attempting to hit...")  # Deferring so I can followup later
        res = bool(bot.boss_dict.get(interaction.channel_id))
        if not res:
            await interaction.followup.send(
                "A boss has not been set up in this channel. Please contact staff if you think this is a mistake.")
            await interaction.delete_original_response()
            return
        if str(interaction.channel.name).lower() in valid_channels:
            curr_boss = bot.boss_dict[interaction.channel_id]
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
                curr_boss.take_damage(damage, interaction.user.id, True, False, curr_boss.level)
                curr_boss.current_users_hit.append(interaction.user.id)
            else:
                curr_boss.take_damage(damage, interaction.user.id, True, True, curr_boss.level)
                curr_boss.current_users_hit.append(interaction.user.id)
            count_hits = curr_boss.current_users_hit.count(interaction.user.id)

            # Reminding users to split hits at a certain threshold
            if count_hits >= split_threshold and curr_boss.guild not in split_exempt:
                await interaction.channel.send(f"**{interaction.user.mention}, you have {count_hits} hits on this level. Please try to split your hits.**")
            
            # Embeds
            name = curr_boss.name
            tz = pytz.timezone("Asia/Seoul")
            unformatted_time = datetime.now(tz)
            ct = unformatted_time.strftime("%H:%M:%S")
            if name == 'dragon':
                clr = 0xFF6060
                display_name = "RVD"
            elif name == 'avatar':
                clr = 0xB900A2
                display_name = "AOD"
            else:
                clr = 0x58C7CF
                display_name = "TLA"
            embed = discord.Embed(color=clr, title=f"lv.{curr_boss.level} {display_name}",
                                  description=f"**{interaction.user.mention} did {damage:,} damage"
                                              f" to the {display_name}**")
            embed.add_field(name="> __New Health__",
                            value=f"**HP: *{curr_boss.hp:,}/{curr_boss.hp_list[curr_boss.level]:,}***",
                            inline=True)
            embed.set_author(name=interaction.user.display_name,
                             icon_url=interaction.user.display_avatar.url)
            embed.set_footer(text=f"•CRK/KR TIME: {ct}•")
            await interaction.followup.send(embed=embed)
            
            ping = call_sweeper(interaction, curr_boss)
            if ping != -1:
                await interaction.channel.send(f"{ping.mention}")
            
            await interaction.delete_original_response()

    # Hit command for when you don't want it to subtract a ticket
    @bot.tree.command(name="resume_hit", description="Hit the boss *without* using a ticket (aka Continued hit).")
    @app_commands.describe(damage="Enter the exact amount of damage dealt to the boss.")
    @app_commands.guild_only()
    async def resume_hit(interaction: discord.Interaction, damage: str):
        await interaction.response.send_message("Attempting to hit...")  # Deferring so I can followup later
        res = bool(bot.boss_dict.get(interaction.channel_id))
        if not res:
            await interaction.followup.send(
                "A boss has not been set up in this channel. Please contact staff if you think this is a mistake.")
            await interaction.delete_original_response()
            return
        if str(interaction.channel.name).lower() in valid_channels:
            curr_boss = bot.boss_dict[interaction.channel_id]
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
                curr_boss.take_damage(damage, interaction.user.id, False, False, curr_boss.level)
                curr_boss.current_users_hit.append(interaction.user.id)
            else:
                curr_boss.take_damage(damage, interaction.user.id, False, True, curr_boss.level)
                curr_boss.current_users_hit.append(interaction.user.id)
                
            name = curr_boss.name
            tz = pytz.timezone("Asia/Seoul")
            unformatted_time = datetime.now(tz)
            ct = unformatted_time.strftime("%H:%M:%S")
            if name == 'dragon':
                clr = 0xFF6060
                display_name = "RVD"
            elif name == 'avatar':
                clr = 0xB900A2
                display_name = "AOD"
            else:
                clr = 0x58C7CF
                display_name = "TLA"
            embed = discord.Embed(color=clr, title=f"lv.{curr_boss.level} {display_name}",
                                  description=f"**{interaction.user.mention} did {damage:,} damage"
                                              f" to the {display_name}**")
            embed.add_field(name="> __New Health__",
                            value=f"**HP: *{curr_boss.hp:,}/{curr_boss.hp_list[curr_boss.level]:,}***",
                            inline=True)
            embed.set_author(name=interaction.user.display_name,
                             icon_url=interaction.user.display_avatar.url)
            embed.set_footer(text=f"•CRK/KR TIME: {ct}•")
            await interaction.followup.send(embed=embed)
            
            ping = call_sweeper(interaction, curr_boss)
            if ping != -1:
                await interaction.channel.send(f"{ping.mention}")
            
            await interaction.delete_original_response()

    @bot.tree.command(name="undo", description="Undoes the most recent command made by the user.")
    @app_commands.guild_only()
    async def undo(interaction: discord.Interaction):
        await interaction.response.send_message("Attempting to undo...")  # Deferring so I can followup later
        res = bool(bot.boss_dict.get(interaction.channel_id))
        if not res:
            await interaction.followup.send(
                "A boss has not been set up in this channel. Please contact staff if you think this is a mistake.")
            return
        if str(interaction.channel.name).lower() in valid_channels:
            curr_boss = bot.boss_dict[interaction.channel_id]
            error = True
            if len(curr_boss.hits) > 0:
                hit = curr_boss.hits[-1]
                # check if the last command is a kill
                if hit.boss_level == curr_boss.level - 1 and hit.user_id == interaction.user.id:
                    hit_type = "kill"
                    curr_boss.undo(-1)
                    error = False

                # find the latest command that's a hit on the current level
                idx = len(curr_boss.hits) - 1
                while error and idx >= 0 and curr_boss.hits[idx].boss_level >= curr_boss.level:
                    hit = curr_boss.hits[idx]
                    if hit.boss_level == curr_boss.level and hit.user_id == interaction.user.id:
                        hit_type = hit.damage
                        curr_boss.undo(idx)
                        error = False
                    idx -= 1

            if error:
                await interaction.followup.send(f"You can only undo hits on the current level, or kills on the last level if no other commands have been used after that.")
            else:
                name = curr_boss.name
                tz = pytz.timezone("Asia/Seoul")
                unformatted_time = datetime.now(tz)
                ct = unformatted_time.strftime("%H:%M:%S")
                if name == 'dragon':
                    clr = 0xFF6060
                    display_name = "RVD"
                elif name == 'avatar':
                    clr = 0xB900A2
                    display_name = "AOD"
                else:
                    clr = 0x58C7CF
                    display_name = "TLA"
                if hit_type == "kill":
                    embed = discord.Embed(color=clr, title=f"lv.{curr_boss.level} {display_name}",
                                        description=f"**{interaction.user.mention} undid a kill on {display_name}**")
                else:
                    embed = discord.Embed(color=clr, title=f"lv.{curr_boss.level} {display_name}",
                                        description=f"**{interaction.user.mention} undid {hit_type:,} damage on {display_name}**")
                embed.add_field(name="> __New Health__",
                                value=f"**HP: *{curr_boss.hp:,}/{curr_boss.hp_list[curr_boss.level]:,}***",
                                inline=True)
                embed.set_author(name=interaction.user.display_name,
                                icon_url=interaction.user.display_avatar.url)
                embed.set_footer(text=f"•CRK/KR TIME: {ct}•")
                await interaction.followup.send(embed=embed)

        await interaction.delete_original_response()

    @bot.tree.command(name="killed", description="Uses a ticket and kills the boss.")
    @app_commands.guild_only()
    async def killed(interaction: discord.Interaction):
        await interaction.response.send_message("Attempting to kill...")  # Deferring so I can followup later
        res = bool(bot.boss_dict.get(interaction.channel_id))
        if not res:
            await interaction.followup.send(
                "A boss has not been set up in this channel. Please contact staff if you think this is a mistake.")
            return
        if str(interaction.channel.name).lower() in valid_channels:
            curr_boss = bot.boss_dict[interaction.channel_id]
            curr_boss.take_damage(curr_boss.hp, interaction.user.id, True, True, curr_boss.level)
            curr_boss.killed()
            allowed_mentions = discord.AllowedMentions(everyone=True)
            ping = discord.utils.get(interaction.guild.roles, id=ping_roles[interaction.channel.name])
            await interaction.followup.send(f"**{ping.mention} has been swept. New Boss:**",
                                                    allowed_mentions=allowed_mentions)
            embed = get_hp_embed(interaction, curr_boss)
            await interaction.followup.send(embed=embed)
        await interaction.delete_original_response()

    # Killed command for when you don't want it to subtract a ticket
    @bot.tree.command(name="bonus_kill", description="Kill the boss *without* using a ticket (aka solo'd).")
    @app_commands.guild_only()
    async def bonus_kill(interaction: discord.Interaction):
        await interaction.response.send_message("Attempting to kill...")  # Deferring so I can followup later
        res = bool(bot.boss_dict.get(interaction.channel_id))
        if not res:
            await interaction.followup.send(
                "A boss has not been set up in this channel. Please contact staff if you think this is a mistake.")
            return
        if str(interaction.channel.name).lower() in valid_channels:
            curr_boss = bot.boss_dict[interaction.channel_id]
            curr_boss.take_damage(curr_boss.hp, interaction.user.id, False, True, curr_boss.level)
            curr_boss.killed()
            allowed_mentions = discord.AllowedMentions(everyone=True)
            ping = discord.utils.get(interaction.guild.roles, id=ping_roles[interaction.channel.name])
            await interaction.followup.send(f"**{ping.mention} has been swept. New Boss:**",
                                                    allowed_mentions=allowed_mentions)
            embed = get_hp_embed(interaction, curr_boss)
            await interaction.followup.send(embed=embed)
        await interaction.delete_original_response()

    @bot.tree.command(name="hp", description="Check the HP of the boss.")
    @app_commands.guild_only()
    async def hp(interaction: discord.Interaction):
        res = bool(bot.boss_dict.get(interaction.channel_id))
        if not res:
            await interaction.response.send_message(
                "A boss has not been set up in this channel. Please contact staff if you think this is a mistake.")
            return
        if str(interaction.channel.name).lower() in valid_channels:
            curr_boss = bot.boss_dict[interaction.channel_id]
            embed = get_hp_embed(interaction, curr_boss)
            await interaction.response.send_message(embed=embed)

    @bot.tree.command(name="boss_help", description="Help understand how to use Fluffy!")
    @app_commands.guild_only()
    async def boss_help(interaction: discord.Interaction):
        embed = discord.Embed(title="Documentation",
                              description="Please click on the link above to view the documentation for all"
                                          " possible commands.",
                              url="https://onioncult.com/documentation/standalone.html",
                              color=0x6c25be)
        await interaction.response.send_message(embed=embed)

    # ------------------------ Reading / Writing to json ------------------------
    def __write_json():
        json_object = json.dumps(cattrs.unstructure(bot.boss_dict), indent=4)
        with open("data.json", "w") as outfile:
            outfile.write(json_object)
        with open("data.txt", "w") as outfile:
            outfile.write(json_object)
        print("Saved to json file.")

    def __convert_csv(crk_guild: str = "all"):
        with open('data.json') as f:
            data = json.load(f)
        df_main = (
            pd
            .concat([pd.json_normalize(data=data[x]) for x in data], keys=data.keys())
            .droplevel(level=1)
            .reset_index(names="id")
        )
        df_main.columns = df_main.columns.str.split(".").str[-1]

        df_hits = (
            pd
            .concat([pd.json_normalize(data=data[x], record_path=["hits"]) for x in data], keys=data.keys())
            .droplevel(level=1)
            .reset_index(names="id")
        )
        df_hits.columns = df_hits.columns.str.split(".").str[-1]

        df_final = pd.merge(left=df_main, right=df_hits).drop(columns=["hits", "hp_list", "id", "level", "hp", "current_users_hit"])
        if crk_guild != "all":
            df_final = df_final[df_final["guild"] == crk_guild]
        # df_final = df_final.explode("hp_list").reset_index(drop=True)

        df_final.to_csv(fr'data_{crk_guild}.csv', index=None)
        
        return len(df_final.index)  # Returns the number of rows so that you dont send empty csv files

    @bot.tree.command(name="send_backup_csv", description="Loads the current data.json into a csv to be exported")
    @app_commands.describe(crk_guild="Enter the guild you'd like to request the csv file from. (or 'all')")
    @app_commands.guild_only()
    async def send_backup_csv(interaction: discord.Interaction, crk_guild: str):
        crk_guild = crk_guild.lower()
        await interaction.response.send_message("Converting data to csv file...")
        guild = interaction.guild
        for key in bot.boss_dict:
            for i in bot.boss_dict[key]["hits"]:
                try:
                    user = guild.get_member(i["user_id"])
                    i["username"] = user.display_name
                except:
                    i["username"] = "N/A"
        __write_json()
        if crk_guild == "all":
            for key in guilds:
                if __convert_csv(key) != 0:
                    await interaction.followup.send(file=discord.File(f'data_{key}.csv'))
        __convert_csv(crk_guild)
        await interaction.followup.send(file=discord.File(f'data_{crk_guild}.csv'))


    @bot.tree.command(name="send_csv", description="Loads the current data.json into a csv to be exported")
    @app_commands.describe(crk_guild="Enter the guild you'd like to request the csv file from. (or 'all')")
    @app_commands.guild_only()
    async def send_csv(interaction: discord.Interaction, crk_guild: str):
        crk_guild = crk_guild.lower()
        await interaction.response.send_message("Converting data to csv file...")
        guild = interaction.guild
        for key in bot.boss_dict:
            for i in bot.boss_dict[key].hits:
                try:
                    user = guild.get_member(i.user_id)
                    i.username = user.display_name
                except:
                    i.username = "N/A"
        __write_json()
        if crk_guild == "all":
            for key in guilds:
                if __convert_csv(key) != 0:
                    await interaction.followup.send(file=discord.File(f'data_{key}.csv'))
        __convert_csv(crk_guild)
        await interaction.followup.send(file=discord.File(f'data_{crk_guild}.csv'))

    @bot.tree.command(name="load_json", description="Loads the current data.json into the boss_dict (USED TO RESTORE"
                                                    " FROM A BACKUP)")
    @app_commands.guild_only()
    async def load_json(interaction: discord.Interaction):
        await interaction.response.send_message("Sending json file to dictionary...")
        with open("data.json") as outfile:
            json_string = outfile.read()
        bot.boss_dict = jsonpickle.decode(json_string)
        print(bot.boss_dict)
        await interaction.followup.send("Data loaded successfully.")


    # Setting up scheduler to save data
    scheduler = BackgroundScheduler()
    scheduler.add_job(__write_json, 'interval', seconds=600)
    scheduler.start()

    # Run the bot
    tkn = linecache.getline('tkn.txt', 1)
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
    if name == 'dragon':
        clr = 0xFF6060
        display_name = "RVD"
    elif name == 'avatar':
        clr = 0xB900A2
        display_name = "AOD"
    else:
        clr = 0x58C7CF
        display_name = "TLA"
    embed = discord.Embed(title=f"lv.{curr_boss.level} {display_name}", color=clr)
    embed.add_field(name="> __Health__",
                    value=f"**HP: *{curr_boss.hp:,}/{curr_boss.hp_list[curr_boss.level]:,}***",
                    inline=True)
    embed.set_author(name=interaction.user.display_name,
                     icon_url=interaction.user.display_avatar.url)
    embed.set_footer(text=f"•CRK/KR TIME: {ct}•")
    return embed

def call_sweeper(interaction: discord.Interaction, curr_boss):
    reqs = ["onion", "fall", "spring", "burnt"]
    if curr_boss.guild in reqs:
        guild = curr_boss.guild
    else:
        guild = "other"
    boss = curr_boss.name
    
    # If the sweeper requirement is higher than the max hp possible, return
    if curr_boss.hp_list[curr_boss.level] < sweeper_requirements[guild][boss]:
        return -1
    
    if curr_boss.hp <= sweeper_requirements[guild][boss]:
        return discord.utils.get(interaction.guild.roles, id=sweeper_roles[boss])
    
    return -1
    
