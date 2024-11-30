import discord
from discord.ext import commands
import yt_dlp
import asyncio
import requests
import secrets
import os
import webserver


DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
music_queue = []
bot = commands.Bot(command_prefix='$',intents=intents)


async def play_next(ctx):
    """Reproduce la siguiente canción en la cola."""
    if len(music_queue) > 0:
        url = music_queue.pop(0)
        player = await YTDLSource.from_url(url, loop=bot.loop, stream=True)
        ctx.voice_client.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop))
    else:
        await ctx.voice_client.disconnect()


# Configuración de yt-dlp
yt_dlp.utils.bug_reports_message = lambda: ''
ytdl_format_options = {
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
    'quiet': True,
    'noplaylist': True,
}
ffmpeg_options = {
    'executable': r'C:\ffmpeg\bin\ffmpeg.exe',
    'options': '-vn -nostdin -loglevel panic',
}
ytdl = yt_dlp.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        if 'entries' in data:
            data = data['entries'][0]
        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)
@bot.command()
async def viktor(ctx):
    """Reproduce el audio de 'VIKTOOOOOR' en el canal de voz."""
    # Obtén el canal de voz del usuario que invoca el comando
    if ctx.author.voice is None or ctx.author.voice.channel is None:
        await ctx.send("¡Necesitas estar en un canal de voz para invocar a VIKTOOOOOR!")
        return

    channel = ctx.author.voice.channel

    # Conéctate al canal si no estás conectado ya
    if ctx.voice_client is None:
        vc = await channel.connect()
    else:
        vc = ctx.voice_client
        if vc.channel != channel:
            await vc.move_to(channel)

    # Envía el mensaje
    await ctx.send("VIKTOOOOOR")

    # Reproduce el audio del video
    url = "https://www.youtube.com/shorts/eYaFVNi1k7M"
    async with ctx.typing():
        player = await YTDLSource.from_url(url, loop=bot.loop, stream=True)
        vc.play(player, after=lambda e: print(f"Player error: {e}") if e else None)

    # Espera a que termine de reproducirse
    while vc.is_playing():
        await asyncio.sleep(1)

    # Desconecta al bot del canal después de la reproducción
    await vc.disconnect()

@bot.command()
async def skip(ctx):
    """Salta a la siguiente canción en la cola."""
    if ctx.voice_client is None or not ctx.voice_client.is_playing():
        await ctx.send("No hay ninguna canción reproduciéndose.")
        return

    ctx.voice_client.stop()
    await ctx.send("⏭ Saltando a la siguiente canción...")

@bot.command()
async def queue(ctx):
    """Muestra la cola de reproducción."""
    if len(music_queue) == 0:
        await ctx.send("La cola está vacía.")
    else:
        queue_list = "\n".join([f"{idx+1}. {url}" for idx, url in enumerate(music_queue)])
        await ctx.send(f"**Canciones en cola:**\n{queue_list}")
@bot.command()
async def play(ctx, url):
    """Agrega una canción a la cola y la reproduce si no hay otra sonando."""
    # Verifica que el usuario esté en un canal de voz
    if ctx.author.voice is None or ctx.author.voice.channel is None:
        await ctx.send("¡Necesitas estar en un canal de voz para usar este comando!")
        return

    channel = ctx.author.voice.channel

    # Conecta al bot si no está conectado ya
    if ctx.voice_client is None:
        await channel.connect()
    elif ctx.voice_client.channel != channel:
        await ctx.voice_client.move_to(channel)

    # Agrega la canción a la cola
    music_queue.append(url)
    await ctx.send(f"¡Agregada a la cola! Canciones en cola: {len(music_queue)}")

    # Si no se está reproduciendo nada, inicia la reproducción
    if not ctx.voice_client.is_playing():
        await play_next(ctx)
@bot.command()
async def stop(ctx):
    """Detiene la reproducción y desconecta al bot del canal de voz."""
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("⏹️ Música detenida y desconexión del canal de voz.")
    else:
        await ctx.send("No estoy conectado a ningún canal de voz.")




@bot.event
async def on_ready():
    print(f"Ya estamos andando {bot.user}")


webserver.keep_alive()
bot.run(DISCORD_TOKEN)