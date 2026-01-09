import asyncio
import os
from typing import Any

import discord
from discord.ext import commands

try:
    from config import TOKEN  # real file (private, ignored by git)
except ImportError:
    try:
        from config.example import TOKEN  # using actions
    except ImportError:
        raise ImportError("config.y/config.example.py not found!")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True


class Bot(commands.Bot):
    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)

        self.chats_times: dict[int, Any] = {}
        self.chat_letra_atual: dict[int, str] = {}
        self.chat_lyric_indices: dict[int, int] = {}

        self.cogs_loaded: bool = False


bot = Bot(
    command_prefix="l.",
    help_command=None,
    intents=intents,
)


async def load_cogs() -> None:
    cogs_dir = "cogs"

    if not os.path.isdir(cogs_dir):
        print(f"[COG] Directory '{cogs_dir}' does not exist. Skipping.")
        return

    for filename in sorted(os.listdir(cogs_dir)):
        if filename.endswith(".py"):
            cog_name = filename[:-3]
            try:
                await bot.load_extension(f"{cogs_dir}.{cog_name}")
                print(f"[COG] ✔ Loaded: '{cog_name}'")
            except Exception as e:
                print(f"[COG] ✖ Error loading '{cog_name}': {e}")


async def sync_commands():
    try:
        synced = await bot.tree.sync()
        print(f"[CMD] Synced {len(synced)} commands.")
        return synced
    except discord.HTTPException as e:
        print(f"[CMD] Sync failed: {e}")
        return []


@bot.event
async def on_ready():
    uid = getattr(bot.user, "id", "???")

    if bot.cogs_loaded:
        print(f"[READY] Bot was already initialized: {bot.user} (ID: {uid})")
        return

    print(f"[READY] Logged in as {bot.user} (ID: {uid})")
    print("[READY] Loading extensions...")

    await load_cogs()

    print("[READY] Extensions loaded. Syncing commands...")
    await sync_commands()

    bot.cogs_loaded = True
    print("[READY] Initialization complete.")


async def main() -> None:
    async with bot:
        await bot.start(TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
