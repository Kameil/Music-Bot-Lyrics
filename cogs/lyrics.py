"""
Lyrics cog.

Provides commands to manage lyric sending in channels.
"""

import discord
import httpx
from discord import app_commands
from discord.ext import commands


class Lyrics(commands.Cog):
    """Commands related to lyric control and management."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.chats_times = bot.chats_times
        self.chat_letra_atual = bot.chat_letra_atual
        self.chat_lyric_indices = bot.chat_lyric_indices
        self.client = httpx.AsyncClient()

    @app_commands.command(
        name="stop",
        description="Stop sending lyrics in this channel",
    )
    async def stop(self, inter: discord.Interaction):
        """Stop sending lyrics in the current channel."""
        member = inter.user
        channel = inter.channel

        if not isinstance(member, discord.Member) or channel is None:
            await inter.response.send_message(
                "This command can only be used in a server.",
                ephemeral=True,
            )
            return

        is_admin = channel.permissions_for(member).administrator
        in_voice = member.voice and member.voice.channel

        if not (is_admin or in_voice):
            await inter.response.send_message(
                "You need to be an admin or be in a voice channel to use this command.",
                ephemeral=True,
            )
            return

        channel_id = channel.id

        if channel_id not in self.chats_times:
            await inter.response.send_message(
                "No lyrics are being sent in this channel.",
                ephemeral=True,
            )
            return

        self.chats_times.pop(channel_id, None)
        self.chat_letra_atual.pop(channel_id, None)
        self.chat_lyric_indices.pop(channel_id, None)

        embed = discord.Embed(
            description="Stopped sending lyrics in this channel.",
            color=discord.Color.blue(),
        )
        embed.set_footer(text=f"requested by {member}")

        await inter.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    """Load the Lyrics cog."""
    await bot.add_cog(Lyrics(bot))
