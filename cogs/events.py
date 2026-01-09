"""
Events cog.

Handles music embed detection, lyric fetching and timed lyric sending.
"""

import datetime
import re
from datetime import timezone
from typing import Optional

import discord
import httpx
from discord.ext import commands, tasks


class Events(commands.Cog):
    """React to music embeds and send synced lyrics to channels."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.client = httpx.AsyncClient()

        self.chats_times = bot.chats_times
        self.chat_letra_atual = bot.chat_letra_atual
        self.chat_lyric_indices = bot.chat_lyric_indices

        self.send_lyrics_loop.start()

    def get_embed_track_info(
        self, embed: discord.Embed
    ) -> tuple[Optional[str], Optional[str]]:
        """Extract artist and track from a music embed description."""
        match = re.search(
            r"playing \[\*\*(.+?)\*\*\s+\*\*by\*\*\s+\*\*(.+?)\*\*\]",
            embed.description or "",
        )
        if not match:
            return None, None

        # artist, track
        return match.group(2), match.group(1)

    async def get_track_cover_url(
        self, artist: str, track: str
    ) -> Optional[str]:
        """Fetch cover art URL using MusicBrainz and Cover Art Archive."""
        url = "https://musicbrainz.org/ws/2/recording"
        params = {
            "query": f'recording:"{track}" AND artist:"{artist}"',
            "fmt": "json",
            "limit": 1,
        }

        response = await self.client.get(
            url,
            params=params,
            headers={"User-Agent": "RaquisonMusicFetcher/1.0"},
            timeout=30,
        )

        if response.status_code != 200:
            return None

        data = response.json()
        recordings = data.get("recordings")
        if not recordings:
            return None

        releases = recordings[0].get("releases")
        if not releases:
            return None

        mbid = releases[0].get("id")
        if not mbid:
            return None

        return f"https://coverartarchive.org/release/{mbid}/front-250"

    async def get_track_lyrics(self, artist: str, track: str) -> str:
        """Fetch synced lyrics from LRCLIB."""
        url = "https://lrclib.net/api/search"
        params = {"track_name": track, "artist_name": artist}

        response = await self.client.get(
            url,
            params=params,
            headers={"User-Agent": "RaquisonMusicFetcher/1.0"},
            timeout=30,
        )

        if response.status_code != 200:
            return ""

        try:
            data = response.json()
        except ValueError:
            return ""

        if not data:
            return ""

        return data[0].get("syncedLyrics", "") or ""

    def parse_lyrics(self, raw_lyrics: str) -> list[tuple[float, str]]:
        """Parse LRC lyrics into timestamped lines."""
        pattern = r"\[(\d{2}:\d{2}\.\d{2})\]\s*(.*)"
        parsed: list[tuple[float, str]] = []

        for line in raw_lyrics.splitlines():
            match = re.match(pattern, line)
            if not match:
                continue

            minutes, rest = match.group(1).split(":")
            seconds, ms = rest.split(".")
            timestamp = (
                int(minutes) * 60
                + int(seconds)
                + int(ms) / 100
            )
            parsed.append((timestamp, match.group(2)))

        parsed.sort(key=lambda x: x[0])
        return parsed

    @tasks.loop(seconds=0.5)
    async def send_lyrics_loop(self):
        """Send lyrics line-by-line based on playback time."""
        now = datetime.datetime.now(timezone.utc)

        for channel_id, start_time in list(self.chats_times.items()):
            lyrics = self.chat_letra_atual.get(channel_id)
            if not lyrics:
                continue

            parsed_lyrics = self.parse_lyrics(lyrics)
            index = self.chat_lyric_indices.get(channel_id, 0)

            while (
                index < len(parsed_lyrics)
                and (now - start_time).total_seconds()
                >= parsed_lyrics[index][0]
            ):
                channel = self.bot.get_channel(channel_id)
                if channel and parsed_lyrics[index][1].strip():
                    await channel.send(parsed_lyrics[index][1])
                index += 1

            self.chat_lyric_indices[channel_id] = index

            if index >= len(parsed_lyrics):
                channel = self.bot.get_channel(channel_id)
                if channel:
                    await channel.send("Finished sending lyrics.")

                self.chats_times.pop(channel_id, None)
                self.chat_letra_atual.pop(channel_id, None)
                self.chat_lyric_indices.pop(channel_id, None)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Listen for music embeds and start lyric fetching."""
        if not message.author.bot:
            return

        if message.author.id not in {
            412347257233604609,
            411916947773587456,
        }:
            return

        if not message.embeds:
            return

        embed = message.embeds[0]
        if not embed.description:
            return

        desc = embed.description
        channel_id = message.channel.id

        stop_phrases = {
            "There are no more tracks",
            "Thank you for using our service!",
        }

        if any(phrase in desc for phrase in stop_phrases):
            if channel_id in self.chat_letra_atual:
                channel = self.bot.get_channel(channel_id)
                if channel:
                    await channel.send("Finished sending lyrics.")

                self.chats_times.pop(channel_id, None)
                self.chat_letra_atual.pop(channel_id, None)
                self.chat_lyric_indices.pop(channel_id, None)
            return

        if "Started playing" not in desc:
            return

        artist, track = self.get_embed_track_info(embed)
        if not artist or not track:
            return

        status_embed = discord.Embed(
            description=(
                f"Getting lyrics for **{track}** by **{artist}**..."
            ),
            color=discord.Color.green(),
        )

        cover_url = await self.get_track_cover_url(artist, track)
        if cover_url:
            status_embed.set_image(url=cover_url)

        await message.reply(embed=status_embed)

        self.chats_times[channel_id] = message.created_at
        self.chat_letra_atual[channel_id] = await self.get_track_lyrics(
            artist, track
        )
        self.chat_lyric_indices[channel_id] = 0

        if not self.chat_letra_atual[channel_id]:
            error_embed = discord.Embed(
                description=(
                    f"Lyrics not found for **{track}** by **{artist}**."
                ),
                color=discord.Color.red(),
            )
            if cover_url:
                error_embed.set_image(url=cover_url)

            await message.reply(embed=error_embed)


async def setup(bot: commands.Bot):
    """Load the Events cog."""
    await bot.add_cog(Events(bot))
