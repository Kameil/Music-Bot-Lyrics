import asyncio
import logging
import os

import discord

from config import token
from discord.ext import commands

# logging
# gambiara fudida pra tirar o logging de afc pq eu nao tava sabendo como, isso silencia TODAS as lib

intents = discord.Intents.all()
# intents.presences = True
# intents.members = True
intents.messages = True
intents.message_content = True
intents.guilds = True

# config de cache dos membros
# member_cache_flags = discord.MemberCacheFlags.none()
# member_cache_flags.joined = True

# inicialização do bot
bot = commands.Bot(
    command_prefix="r!",
    help_command=None,
    intents=intents,
    # member_cache_flags=member_cache_flags,
)

async def load_cogs():
    try:
        cogs_dir = "cogs"
        for file in os.listdir(cogs_dir):
            if file.endswith(".py") and file not in ["experimental.py", "imaginar.py"]:
                await bot.load_extension(f"{cogs_dir}.{file[:-3]}")
                print(f"Cog '{file[:-3]}' carregado com sucesso.")
    except Exception as e:
        print(f"Erro ao carregar cogs: {e}", exc_info=True)


async def sync_commands():
    try:
        synced = await bot.tree.sync()
        print(f"Comandos de barra sincronizados: {len(synced)}")
        return synced
    except discord.errors.HTTPException as e:
        print(f"Erro na sincronização de comandos: {e}")
        return []


@bot.event
async def on_ready():
    await load_cogs()
    synced_commands = await sync_commands()
    print.info(f"Bot conectado como {bot.user} (ID: {bot.user.id})")



async def main():
    try:
        await bot.start(token=token)
    except discord.errors.LoginFailure:
        print("\033[31mToken inválido. Confere o config.py!\033[0m")
    except Exception as e:
        print(f"Erro ao iniciar o bot: {e}", exc_info=True)
    finally:
        if not bot.is_closed():
            await bot.close()

if __name__ == "__main__":
    asyncio.run(main())