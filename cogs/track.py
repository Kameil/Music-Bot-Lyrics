"""
Track cog.

Provides a slash command to search tracks using Last.fm
and fetch cover art using MusicBrainz.
"""

import asyncio
import traceback
from typing import Optional

import discord
import httpx
import musicbrainzngs
from discord import app_commands
from discord.ext import commands
from musicbrainzngs import NetworkError, ResponseError

from config import LAST_FM_API_KEY

musicbrainzngs.set_useragent("Stihovi-track-search", "1.0")


class Track(commands.Cog):
    """Track search commands using Last.fm and MusicBrainz."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.client = httpx.AsyncClient()

    async def get_cover_url(
        self, artist: str, track: str
    ) -> Optional[str]:
        """Fetch track cover art URL using MusicBrainz."""
        try:
            result = await asyncio.to_thread(
                musicbrainzngs.search_recordings,
                artist=artist,
                recording=track,
                limit=1,
            )
        except (NetworkError, ResponseError) as exc:
            print(f"MusicBrainz search failed: {exc}")
            return None
        except Exception:  # fallback safety
            traceback.print_exc()
            return None

        recordings = result.get("recording-list")
        if not recordings:
            return None

        recording = recordings[0]
        releases = recording.get("release-list")
        if not releases:
            return None

        release_id = releases[0].get("id")
        if not release_id:
            return None

        try:
            art = await asyncio.to_thread(
                musicbrainzngs.get_image_list, release_id
            )
        except ResponseError:
            # very common when no cover art exists
            return None
        except (NetworkError, KeyError, IndexError) as exc:
            print(f"Cover art fetch failed: {exc}")
            return None

        images = art.get("images")
        if not images:
            return None

        return images[0].get("image")

    async def last_fm_get_track(
        self, artist: str, track: str
    ) -> Optional[dict]:
        """Search for a track using the Last.fm API."""
        url = "http://ws.audioscrobbler.com/2.0/"
        params = {
            "method": "track.search",
            "api_key": LAST_FM_API_KEY,
            "artist": artist,
            "track": track,
            "format": "json",
        }

        response = await self.client.get(
            url,
            params=params,
            headers={"User-Agent": "RaquisonMusicFetcher/1.0"},
            timeout=30,
        )

        response.raise_for_status()
        data = response.json()

        results = data.get("results", {})
        matches = results.get("trackmatches", {})
        tracks = matches.get("track")

        if tracks:
            return tracks[0]

        return None

    @app_commands.command(name="track", description="Search for a track")
    async def track_search(
        self,
        inter: discord.Interaction,
        artist: str,
        track: str,
    ):
        """Slash command to search for a track."""
        await inter.response.defer()

        try:
            track_info = await self.last_fm_get_track(artist, track)
        except (httpx.HTTPError, ValueError) as exc:
            await inter.followup.send(f"Request failed: {exc}")
            return

        if not track_info:
            await inter.followup.send("Track not found.")
            return

        embed = discord.Embed(
            title="Track Found",
            color=discord.Color.blue(),
        )
        embed.add_field(
            name="Name",
            value=track_info.get("name", "N/A"),
            inline=False,
        )
        embed.add_field(
            name="Artist",
            value=track_info.get("artist", "N/A"),
            inline=False,
        )
        embed.add_field(
            name="Listeners",
            value=track_info.get("listeners", "N/A"),
            inline=False,
        )
        embed.add_field(
            name="URL",
            value=track_info.get("url", "N/A"),
            inline=False,
        )

        cover_url = await self.get_cover_url(artist, track)
        if cover_url:
            embed.set_thumbnail(url=cover_url)

        await inter.followup.send(embed=embed)


async def setup(bot: commands.Bot):
    """Load the Track cog."""
    await bot.add_cog(Track(bot))
