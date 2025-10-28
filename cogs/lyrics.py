from discord.ext import commands
from discord import app_commands
import httpx        
import discord


class lyrics(commands.Cog): 
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.chats_times = bot.chats_times
        self.chat_letra_atual = bot.chat_letra_atual
        self.chat_lyric_indices = bot.chat_lyric_indices
        self.client = httpx.AsyncClient()

    @app_commands.command(name="stop", description="Stop sending lyrics in this channel")
    async def stop(self, inter: discord.Interaction):
        channel_id = inter.channel.id
        if channel_id in self.chats_times:
            self.chats_times.pop(channel_id)
            self.chat_letra_atual.pop(channel_id)
            self.chat_lyric_indices.pop(channel_id, None)
            embed = discord.Embed(
                description="Stopped sending lyrics in this channel.",
                color=discord.Color.blue()
                
            )
            embed.set_footer(text="requested by " + str(inter.user))
            await inter.response.send_message(embed=embed)
        else:
            await inter.response.send_message("No lyrics are being sent in this channel.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(lyrics(bot))