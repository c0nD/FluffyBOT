import discord
from discord import Intents, MemberCacheFlags, Embed
from discord.ext.commands import Bot
import boss
import re
from datetime import datetime
import json
import attrs
import cattrs
import pytz


def run_bot():
    # Boring setup
    bot = Bot("$", member_cache_flags=MemberCacheFlags.all(), intents=Intents.all())
    bot.remove_command("help")
    boss_dict = {}
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

    # Async Commands
    @bot.event
    async def on_ready():
        print(f'\n\n\t\t\t\t\t\t{bot.user} is now running!')

    # STAFF COMMANDS
    @bot.command()
    async def create_boss(ctx, guild):
        guild = guild.lower()
        if guild not in guilds:
            await ctx.send("Invalid guild. Type `$help` for more information.")
            return
        elif guilds[guild] is None:
            guilds[guild] = boss.Guild()
            await ctx.send((guilds[guild]))
        if str(ctx.channel.name).lower() in valid_channels:
            new_boss = boss.Boss(ctx.channel.name, 1, guild)
            res = bool(boss_dict.get(ctx.channel.id))
            if not res:
                boss_dict[ctx.channel.id] = new_boss
                await ctx.send(f"Created Boss in {ctx.channel.name}.")
                await ctx.send(f"{boss_dict}")
            else:
                await ctx.send("Cannot create two bosses at once. If you want to reset the boss, please call "
                               "`$delete_boss` first.")
        else:
            await ctx.send("Attempting to create a boss in a channel not designated to create bosses in.")

    @bot.command()
    async def delete_boss(ctx):
        if str(ctx.channel.name).lower() in valid_channels:
            try:
                curr_boss = boss_dict[ctx.channel.id]
                await ctx.send(f"Deleting lv.{curr_boss.level} {str(ctx.channel.name).upper()} boss.")
                del boss_dict[ctx.channel.id]
            except:
                await ctx.send(f"Cannot delete a boss that does not exist. Please create a boss before "
                               f"trying to call `$delete`")

    @bot.command()
    async def insert_boss(ctx, guild, level, health):
        if str(ctx.channel.name).lower() in valid_channels:
            level = sanitize_int(level)
            health = sanitize_int(health)
            guild = guild.lower()
            if guild not in guilds:
                await ctx.send("Invalid guild. Type `$help` for more information.")
                return
            elif guilds[guild] is None:
                guilds[guild] = boss.Guild()
                ctx.send((guilds[guild]))

            new_boss = boss.Boss(ctx.channel.name, level, guild)
            # If you accidentally set the hp too high
            if health > new_boss.hp_list[new_boss.level]:
                res = bool(boss_dict.get(ctx.channel.id))
                if res:
                    del boss_dict[ctx.channel.id]
                    await ctx.send("HP was set higher than boss level allows for. Please try again with valid HP.")
                    return
            else:
                new_boss.set_hp(health)

            res = bool(boss_dict.get(ctx.channel.id))
            if not res:
                boss_dict[ctx.channel.id] = new_boss
                await ctx.send(f"Created Boss in {ctx.channel.name}.")
                await ctx.send(f"{boss_dict}")
            else:
                await ctx.send("Cannot create two bosses at once. If you want to reset the boss, please call "
                               "`$delete_boss` first.")

    # USER COMMANDS
    @bot.command()
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
            curr_boss.take_damage(damage, ctx.message.author.id, True)
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
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
            embed.set_footer(text=f"•CRK TIME: {ct}•")
            await ctx.send(embed=embed)

    # Hit command for when you don't want it to subtract a ticket
    @bot.command()
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
            curr_boss.take_damage(damage, ctx.message.author.id, False)
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
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
            embed.set_footer(text=f"•CRK: {ct}•")
            await ctx.send(embed=embed)

    @bot.command()
    async def killed(ctx):
        res = bool(boss_dict.get(ctx.channel.id))
        if not res:
            await ctx.send(
                "A boss has not been set up in this channel. Please contact staff if you think this is a mistake.")
            return
        if str(ctx.channel.name).lower() in valid_channels:
            curr_boss = boss_dict[ctx.channel.id]
            curr_boss.take_damage(curr_boss.hp, ctx.message.author.id, True)
            curr_boss.killed()
            allowed_mentions = discord.AllowedMentions(everyone=True)
            ping = discord.utils.get(ctx.guild.roles, id=ping_roles[ctx.channel.name])
            await ctx.send(f"{ping.mention} has been swept. New Boss:", allowed_mentions=allowed_mentions)
            await hp(ctx)

    # Killed command for when you don't want it to subtract a ticket
    @bot.command()
    async def bonus_kill(ctx):
        res = bool(boss_dict.get(ctx.channel.id))
        if not res:
            await ctx.send(
                "A boss has not been set up in this channel. Please contact staff if you think this is a mistake.")
            return
        if str(ctx.channel.name).lower() in valid_channels:
            curr_boss = boss_dict[ctx.channel.id]
            curr_boss.take_damage(curr_boss.hp, ctx.message.author.id, False)
            curr_boss.killed()
            ping = discord.utils.get(ctx.guild.roles, id=ping_roles[ctx.channel.name])
            await ctx.send(f"{ping.mention} has been bonus killed by {ctx.message.author.mention}. Next Boss:")
            await hp(ctx)

    @bot.command()
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
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
            embed.set_footer(text=f"•CRK: {ct}•")
            await ctx.send(embed=embed)

    @bot.command()
    async def help(ctx):
        embed = discord.Embed(title="Documentation",
                              description="Please click on the link above to view the documentation for all"
                                          " possible commands.",
                              url="https://www.onioncult.com/bot-help/",
                              color=0x6c25be)
        await ctx.send(embed=embed)

    @bot.command()
    async def print_dict(ctx):
        await ctx.send(boss_dict)
        for key in boss_dict:
            boss_json = cattrs.unstructure(boss_dict[key])

            await ctx.send(boss_json)















    # Run the bot
    tkn = 'MTAzOTY3MDY3NzE4NTIzNzAzNA.GMKe3G.UaqGU_yHdCYEhigVY3795Hn34o0KFevUzd6dmc'
    bot.run(tkn)


def sanitize_int(num):
    re.sub('\D', '', str(num))
    num = int(num)
    return num
