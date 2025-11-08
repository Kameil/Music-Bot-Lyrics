import discord
from discord import app_commands
from discord.ext import commands
from config import last_fm_API_key
import httpx
import musicbrainzngs
import asyncio
import traceback
from musicbrainzngs import ResponseError, NetworkError 

musicbrainzngs.set_useragent("Stihovi-track-search", "1.0")

class track(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.client = httpx.AsyncClient()

    async def get_cover_url(self, artist, track):
        # 1. search for recording (now in a separate thread)
        try:
            # use asyncio.to_thread for blocking call
            result = await asyncio.to_thread(
                musicbrainzngs.search_recordings,
                artist=artist,
                recording=track,
                limit=1,
            )
        except Exception as e:
            traceback.print_exc()
            print(f"Returning None due to error in musicbrainzngs search: {e}")
            return None

        # the verification logic remains the same
        if not result.get("recording-list"):
            return None
        
        recording = result["recording-list"][0]
        if "release-list" not in recording or not recording["release-list"]:
            return None

        release_id = recording["release-list"][0]["id"]

        # 2. get cover from Cover Art Archive (also in a thread)
        try:
            # use asyncio.to_thread for the second blocking call
            art = await asyncio.to_thread(
                musicbrainzngs.get_image_list,
                release_id
            )
            
            # security check before accessing keys
            if art.get("images"):
                return art["images"][0].get("image")
            return None
            
        except ResponseError:
            # common error if release doesn't have art (e.g., 404)
            return None
        except (NetworkError, KeyError, IndexError) as e:
            # handle other possible errors (network, malformed JSON, etc.)
            print(f"Error fetching cover art: {e}")
            return None

    async def last_fm_get_track(self, artist: str, track: str):
        url = "http://ws.audioscrobbler.com/2.0/"
        params = {
            "method": "track.search",
            "api_key": last_fm_API_key,
            "artist": artist,
            "track": track,
            "format": "json"
        }

        response = await self.client.get(url, params=params, headers={"User-Agent": "RaquisonMusicFetcher/1.0"}, timeout=30)
        response.raise_for_status()
        data = response.json()
        if "results" in data and "trackmatches" in data["results"] and "track" in data["results"]["trackmatches"]:
            tracks = data["results"]["trackmatches"]["track"]
            if tracks:
                return tracks[0]
        return None

    @app_commands.command(name="track", description="search track")
    async def track_search(self, inter: discord.Interaction, artist: str, track: str):
        await inter.response.defer()
        try:
            track_info = await self.last_fm_get_track(artist, track)
            if track_info:
                embed = discord.Embed(title="Track Found", color=discord.Color.blue())
                embed.add_field(name="Name", value=track_info.get("name", "N/A"), inline=False)
                embed.add_field(name="Artist", value=track_info.get("artist", "N/A"), inline=False)
                embed.add_field(name="Listeners", value=track_info.get("listeners", "N/A"), inline=False)
                embed.add_field(name="URL", value=track_info.get("url", "N/A"), inline=False)
                # embed.set_thumbnail(url=track_info.get("image", [{}])[-1].get("#text", ""))
                embed.set_thumbnail(url=await self.get_cover_url(artist, track) or "https://via.placeholder.com/150")
                await inter.followup.send(embed=embed)
            else:
                await inter.followup.send("Track not found.")
        except Exception as e:
            await inter.followup.send(f"An error occurred: {e}")

async def setup(bot: commands.Bot):
    await bot.add_cog(track(bot))