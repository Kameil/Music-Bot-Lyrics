import asyncio
import os
import discord
from discord.ext import commands
from config import token

intents = discord.Intents.all()
intents.messages = True
intents.message_content = True
intents.guilds = True

bot = commands.Bot(
    command_prefix="ml.",
    help_command=None,
    intents=intents,
)

bot.chats_times = {}
bot.chat_letra_atual = {}
bot.chat_lyric_indices = {}

bot.cogs_loaded = False

async def load_cogs():
    cogs_dir = "cogs"
    if not os.path.isdir(cogs_dir):
        print(f"[COG] Diretório '{cogs_dir}' não existe. Ignorando carregamento de cogs.")
        return

    for file in sorted(os.listdir(cogs_dir)):
        if not file.endswith(".py"):
            continue
        name = file[:-3]
        try:
            await bot.load_extension(f"{cogs_dir}.{name}")
            print(f"[COG] ✅ '{name}' carregado com sucesso.")
        except Exception as e:
            print(f"[COG] ❌ Erro ao carregar '{name}': {e}")

async def sync_commands():
    try:
        synced = await bot.tree.sync()
        print(f"[CMD] Comandos de barra sincronizados: {len(synced)}")
        return synced
    except discord.errors.HTTPException as e:
        print(f"[CMD] Erro na sincronização de comandos: {e}")
        return []

@bot.event
async def on_ready():
    if getattr(bot, "cogs_loaded", False):
        print(f"[READY] Bot já pronto: {bot.user} (ID: {bot.user.id})")
        return

    print(f"[READY] Conectado como {bot.user} (ID: {bot.user.id}) — carregando cogs...")
    await load_cogs()
    print("[READY] Cogs carregados. Sincronizando comandos...")
    await sync_commands()
    bot.cogs_loaded = True
    print("[READY] Setup finalizado.")

async def main():
    try:
        await bot.start(token)
    except KeyboardInterrupt:
        print("[MAIN] Interrompido pelo usuário.")
    finally:
        await bot.close()

if __name__ == "__main__":
    asyncio.run(main())
