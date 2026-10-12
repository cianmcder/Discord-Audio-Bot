import discord
from discord.ext import commands
from dotenv import dotenv_values
from dotenv import load_dotenv
import os

# from player import CustomVoiceClient
# from player import PlayerUi
from youtube import youtubedl

FFMPEG_PATH = "C:\\ffmpeg\\bin"

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}

intents = discord.Intents.default()
intents.voice_states = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

load_dotenv("tokens.env")

# REMINDER: Commands must be issued via the chat within the Voice Channel
# (click the "Open Chat" bubble icon next to the voice channel)

# installed bgutil locally to bypass Youtube's requirement for PO tokens
# C:\Program Files\bgutil\bgutil-ytdlp-pot-provider\server
# from CMD line above run "node build/main.js"

@bot.command()
async def join(ctx: commands.Context):
    """ Joins the current voice channel. """
    if ctx.author.voice is None:
        return await ctx.send(
            "This command will not work unless you're in a voice channel."
        )

    channel = ctx.author.voice.channel

    if ctx.voice_client is not None:
        await ctx.voice_client.move_to(channel)
        return await ctx.send(f"Audio bot moved to channel {channel.name}")

    try:
        await channel.connect()
        return await ctx.send(
            f"Audio bot connected to channel {channel.name}"
        )
    except Exception as e:
        print(f"Failed to connect to voice: {e}")
        return await ctx.send(f"Failed to connect to {channel.name}: {e}")

@bot.command()
async def leave(ctx: commands.Context):
    """ Leaves the voice channel """
    await ctx.send(f"Audio bot leaving channel {ctx.author.voice.channel.name}")
    return await ctx.voice_client.disconnect(force=True)

@bot.command()
async def playmusic(ctx: commands.Context, file: str):
    """ Plays audio url as defined in music.env """
    if ctx.author.voice is None:
        return await ctx.send("You must connect to a voice channel first.")
    await play(ctx, file, True)

@bot.command()
async def playsfx(ctx: commands.Context, file: str):
    """ Plays audio url as defined in sfx.env """
    if ctx.author.voice is None:
        return await ctx.send("You must connect to a voice channel first.")
    await play(ctx, file, False)

@bot.command()
async def stop(ctx: commands.Context):
    """ Stops playing current audio """
    if ctx.author.voice is None:
        return await ctx.send("You must connect to a voice channel first.")
    ctx.voice_client.stop()
    return await ctx.send("Ended audio.")

# define as code shared between playmusic and playsfx; remove bloat
async def play(ctx : commands.Context, file : str, music: bool):
    # create dict object and populates with .env
    if music:
        dict = dotenv_values("music.env")
    else:
        dict = dotenv_values("sfx.env")

    if not dict:
        return await ctx.send("Audio library is empty: Nothing to play.")
    url = dict.get(file)
    if url is None or isYoutubeUrl(url) is False:
        return await ctx.send(f"Could not retrieve Youtube url using name: {file}")

    stream = await youtubedl(url)
    
    vc = ctx.voice_client
    if vc is None or not vc.is_connected():
        return await ctx.send("The bot is not connected to a voice channel.")
    if vc.is_playing():
        vc.stop()
    
    source = discord.FFmpegPCMAudio(
        stream["url"],
        before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
        options="-vn",
        **{
            "executable": r"C:\ffmpeg\bin\ffmpeg.exe",
            "stderr": None,
        },
    )
    
    # Pass the headers extracted by yt-dlp to FFmpeg.
    headers = stream["headers"]
    if headers:
        header_string = "".join(
            f"{key}: {value}\r\n"
            for key, value in headers.items()
        )
        source = discord.FFmpegPCMAudio(
            stream["url"],
            before_options=(
                "-reconnect 1 -reconnect_streamed 1 "
                "-reconnect_delay_max 5 "
                f'-headers "{header_string}"'
            ),
            options="-vn",
            executable=r"C:\ffmpeg\bin\ffmpeg.exe",
        )
    
    def after_playback(error):
        if error:
            print(f"Discord audio playback error: {error}")

    vc.play(
        discord.PCMVolumeTransformer(source, volume=0.5),
        after=after_playback,
    )

    await ctx.send(f"Starting playback: {stream['title']}")
    
    # vc.stop()
    # vc.play(discord.FFmpegPCMAudio(stream, **FFMPEG_OPTIONS))
    await ctx.send(f"Now Playing: {file}")

def isYoutubeUrl(url : str):
    if url.startswith("https://www.youtube.com/watch?v="):
        return True
    return False

bot.run(os.environ['BOT_TOKEN'])