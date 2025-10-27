import discord
from discord.ext import commands, tasks
import httpx
import re
import io
import datetime
from datetime import timezone

class Events(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.client = httpx.AsyncClient()
        self.chats_times = {}
        self.chat_letra_atual = {}
        self.chat_lyric_indices = {}
        self.send_lyrics_loop.start()

    def get_embed_track_info(self, embed: discord.Embed):
        match = re.search(r'playing \[\*\*(.+?)\*\*\s+\*\*by\*\*\s+\*\*(.+?)\*\*\]', embed.description)
        if match:
            print(f"Extraindo info do embed: {match.group(2)} por {match.group(1)}")
            return match.group(2), match.group(1) # artist, track
        return None, None

    async def get_track_lyrics(self, artist: str, track: str) -> str:
        print(f"Buscando letra de {track} por {artist}...")
        url = "https://lrclib.net/api/search"
        params = {"track_name": track, "artist_name": artist}
        response = await self.client.get(url, params=params, headers={"User-Agent": "RaquisonMusicFetcher/1.0"}, timeout=30)
        print(f"Status da requisição: {response.status_code}")
        

        if response.status_code == 200:
            try:
                dados = response.json()
                if dados:
                    letra = dados[0].get("syncedLyrics", "")
                    print(letra)
                    print(f"Letra encontrada com {len(letra.splitlines())} linhas")
                    return letra or ""
                else:
                    print(f"Nenhum dado retornado pelo API para {track}")
            except Exception as e:
                print(f"Erro ao processar JSON: {e}")

        print(f"Letra não encontrada para {track}")
        return ""

    def parse_lyrics(self, raw_lyrics: str):
        pattern = r'\[(\d{2}:\d{2}\.\d{2})\]\s*(.*)'
        parsed = []
        for line in raw_lyrics.splitlines():
            match = re.match(pattern, line)
            if match:
                minutes, rest = match.group(1).split(':')
                seconds, ms = rest.split('.')
                timestamp = int(minutes)*60 + int(seconds) + int(ms)/100
                text = match.group(2)
                parsed.append((timestamp, text))
        parsed.sort(key=lambda x: x[0])
        print(f"Parse completo: {len(parsed)} linhas com timestamps")
        return parsed

    @tasks.loop(seconds=0.5)
    async def send_lyrics_loop(self):
        now = datetime.datetime.now(timezone.utc)
        for channel_id, start_time in list(self.chats_times.items()):
            lyrics = self.chat_letra_atual.get(channel_id)
            if not lyrics:
                continue

            parsed_lyrics = self.parse_lyrics(lyrics)
            index = self.chat_lyric_indices.get(channel_id, 0)

            while index < len(parsed_lyrics) and (now - start_time).total_seconds() >= parsed_lyrics[index][0]:
                channel = self.bot.get_channel(channel_id)
                if channel:
                    print(f"[{(now - start_time).total_seconds():.2f}s] Enviando linha para canal {channel_id}: {parsed_lyrics[index][1]}")
                    if parsed_lyrics[index][1].strip():
                        await channel.send(parsed_lyrics[index][1])
                index += 1

            self.chat_lyric_indices[channel_id] = index
            if index >= len(parsed_lyrics):
                print(f"Todas as linhas enviadas para canal {channel_id}, removendo dados")
                self.chats_times.pop(channel_id)
                self.chat_letra_atual.pop(channel_id)
                self.chat_lyric_indices.pop(channel_id, None)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot and message.author.id == 412347257233604609:
            if message.embeds:
                embed = message.embeds[0]
                if embed.description and "Started playing" in embed.description:
                    print(f"Embed detectado em {message.channel.id}")
                    artist, track = self.get_embed_track_info(embed)
                    if artist and track:
                        self.chats_times[message.channel.id] = message.created_at
                        self.chat_letra_atual[message.channel.id] = await self.get_track_lyrics(artist, track)
                        self.chat_lyric_indices[message.channel.id] = 0

async def setup(bot: commands.Bot):
    await bot.add_cog(Events(bot))
