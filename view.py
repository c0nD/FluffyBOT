import discord
import bot
from discord import ui, app_commands
from discord.ui import Modal, View


class MyView(View):
    def __init__(self, ctx):
        super().__init__(timeout=360)
        self.ctx = ctx

    @discord.ui.button(label="HIT", style=discord.ButtonStyle.green)
    async def hit_button_callback(self, interaction, button):
        await interaction.response.send_modal(AttackForum())
        self.stop()

    @discord.ui.button(label="BONUS HIT", style=discord.ButtonStyle.green)
    async def bonus_hit_button_callback(self, interaction, button):
        await interaction.response.send_message("bonus hit")
        self.stop()

    @discord.ui.button(label="KILLED", style=discord.ButtonStyle.red)
    async def killed_button_callback(self, interaction, button):
        await interaction.response.send_message("killed")
        self.stop()

    @discord.ui.button(label="BONUS KILL", style=discord.ButtonStyle.red)
    async def bonus_kill_button_callback(self, interaction, button):
        await interaction.response.send_message("bonus kill")
        self.stop()

    async def interaction_check(self, interaction) -> bool:
        if interaction.user != self.ctx.author:
            await interaction.response.send_message(f"{interaction.user.mention}, please do not try to use "
                                                    f"{self.ctx.author.mention}'s attack."
                                                    f" Wait until they have finished.", ephemeral=True)
            return False
        else:
            return True

    async def on_timeout(self):
        return


class AttackForum(Modal, title='Attacks powered by c0nD'):
    dmg = ui.TextInput(label="DAMAGE DONE")

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(f'{self.dmg} damage!')
