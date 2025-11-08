import asyncio
import os
from typing import Any

import discord
from discord.ext import commands
from config import token

intents = discord.Intents.all()
intents.messages = True
intents.message_content = True
intents.guilds = True

class Bot(commands.Bot):
    chats_times: dict[int, Any]         
    chat_letra_atual: dict[int, str]
    chat_lyric_indices: dict[int, int]
    cogs_loaded: bool

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self.chats_times = {}
        self.chat_letra_atual = {}
        self.chat_lyric_indices = {}
        self.cogs_loaded = False

bot = Bot(
    command_prefix="l.",
    help_command=None,
    intents=intents,
)

async def load_cogs() -> None:
    cogs_dir = "cogs"
    if not os.path.isdir(cogs_dir):
        print(f"[COG] Directory '{cogs_dir}' does not exist. Ignoring.")
        return

    for file in sorted(os.listdir(cogs_dir)):
        if not file.endswith(".py"):
            continue
        name = file[:-3]
        try:
            await bot.load_extension(f"{cogs_dir}.{name}")
            print(f"[COG] ✅ '{name}' loaded.")
        except Exception as e:
            print(f"[COG] ❌ Error in '{name}': {e}")

async def sync_commands() -> list[discord.app_commands.AppCommand]:
    try:
        synced = await bot.tree.sync()
        print(f"[CMD] Synced: {len(synced)}")
        return synced
    except discord.HTTPException as e:
        print(f"[CMD] Sync failed: {e}")
        return []

@bot.event
async def on_ready() -> None:
    if bot.cogs_loaded:
        uid = getattr(bot.user, "id", "???")
        print(f"[READY] Bot already ready: {bot.user} (ID: {uid})")
        return

    uid = getattr(bot.user, "id", "???")
    print(f"[READY] Connected as {bot.user} (ID: {uid}) — loading cogs...")
    await load_cogs()
    print("[READY] Cogs loaded. Syncing commands...")
    await sync_commands()
    bot.cogs_loaded = True
    print("[READY] Setup completed.")

async def main() -> None:
    async with bot:
        await bot.start(token)

if __name__ == "__main__":
    asyncio.run(main())