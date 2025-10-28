import asyncio
import os
import discord

from config import token
from discord.ext import commands

intents = discord.Intents.all()
intents.messages = True
intents.message_content = True
intents.guilds = True

bot = commands.Bot(
    command_prefix="r!",
    help_command=None,
    intents=intents,
)

async def load_cogs():
    try:
        cogs_dir = "cogs"
        for file in os.listdir(cogs_dir):
            if file.endswith(".py"):
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
    print(f"Bot conectado como {bot.user} (ID: {bot.user.id})")
    synced_commands = await sync_commands()
    

bot.run(token)
