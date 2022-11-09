from discord import Intents, MemberCacheFlags
from discord.ext.commands import Bot
import boss
import re


def run_bot():
    # Boring setup
    bot = Bot("$", member_cache_flags=MemberCacheFlags.all(), intents=Intents.all())
    boss_dict = {}
    valid_channels = ['aod', 'tla', 'rvd']

    # Async Commands
    @bot.event
    async def on_ready():
        print(f'\n\n\t\t\t\t\t\t{bot.user} is now running!')

    # STAFF COMMANDS
    @bot.command()
    async def create_boss(ctx):
        if str(ctx.channel.name).lower() in valid_channels:
            new_boss = boss.Boss(ctx.channel.name, 1)
            res = bool(boss_dict.get(ctx.channel.id))
            if not res:
                boss_dict[ctx.channel.id] = new_boss
                await ctx.send(f"Created Boss in {ctx.channel.name}.")
                await ctx.send(f"{boss_dict}")
            else:
                await ctx.send("Cannot create two bosses at once. If you want to reset the boss, please call "
                               "`$delete_boss` first.")

    @bot.command()
    async def delete_boss(ctx):
        if str(ctx.channel.name).lower() in valid_channels:
            curr_boss = boss_dict[ctx.channel.id]
            await ctx.send(f"Deleting lv.{curr_boss.level} {str(ctx.channel.name).upper()} boss.")
            del boss_dict[ctx.channel.id]

    @bot.command()
    async def insert_boss(ctx, level, health):
        if str(ctx.channel.name).lower() in valid_channels:
            level = sanitize_int(level)
            health = sanitize_int(health)
            new_boss = boss.Boss(ctx.channel.name, level)
            # If you accidentally set the hp too high
            if health > new_boss.level_hp[new_boss.level]:
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
            await ctx.send("A boss has not been set up in this channel. Please contact staff if you think this is a mistake.")
            return
        if str(ctx.channel.name).lower() in valid_channels:
            curr_boss = boss_dict[ctx.channel.id]
            damage = sanitize_int(damage)
            if damage > curr_boss.level_hp[curr_boss.level] or damage > curr_boss.hp:
                await ctx.send("Please double check that you input the correct number for damage. If you killed the boss"
                               " please use the `$killed` command before calling `$hit` if you just swept this boss. If"
                               " neither of these are the case, please contact your staff to get them to reset the boss"
                               " at it's current level and hp.")
                return
            curr_boss.take_damage(damage, ctx.message.author.id)
            await ctx.send(f"{ctx.message.author.mention} did {damage} to the {str(ctx.channel.name).upper()}. "
                           f"HP: {curr_boss.hp:,}/{curr_boss.level_hp[curr_boss.level]:,}")

    @bot.command()
    async def killed(ctx):
        res = bool(boss_dict.get(ctx.channel.id))
        if not res:
            await ctx.send("A boss has not been set up in this channel. Please contact staff if you think this is a mistake.")
            return
        if str(ctx.channel.name).lower() in valid_channels:
            curr_boss = boss_dict[ctx.channel.id]
            curr_boss.killed()
            await ctx.send(f"New Boss HP: {curr_boss.hp:,}/{curr_boss.hp:,}")

    @bot.command()
    async def hp(ctx):
        res = bool(boss_dict.get(ctx.channel.id))
        if not res:
            await ctx.send("A boss has not been set up in this channel. Please contact staff if you think this is a mistake.")
            return
        if str(ctx.channel.name).lower() in valid_channels:
            curr_boss = boss_dict[ctx.channel.id]
            await ctx.send(f"Current HP of lv.{curr_boss.level} {str(ctx.channel.name).upper()}: "
                           f"{curr_boss.hp:,}/{curr_boss.level_hp[curr_boss.level]:,}")

    # Run the bot
    tkn = 'MTAzOTY3MDY3NzE4NTIzNzAzNA.GMKe3G.UaqGU_yHdCYEhigVY3795Hn34o0KFevUzd6dmc'
    bot.run(tkn)

def sanitize_int(num):
    re.sub('\D', '', str(num))
    num = int(num)
    return num
