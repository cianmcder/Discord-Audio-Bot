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

@bot.command()
async def join(ctx: commands.Context):
    """ Joins the current voice channel. """
    if ctx.message.author.voice.channel:
        channel = ctx.author.voice.channel
        await channel.connect()
        return await ctx.send(f"Audio bot connected to channel {channel.name}")
    else:
        return await ctx.send("This command will not work unless you're in a voice channel.")

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

    # create music dict object; replaces below block that temporarily loads .env file vars
    '''music_dict = dotenv_values("music.env")
    if music_dict is None:
        return await ctx.send("Music library is empty: No music to play.")
    url = music_dict.get(file)
    if url is None or isYoutubeUrl(url) is False:
        return await ctx.send(f"Could not retrieve Youtube url using name: {file}")

    # ctx.bot.voice_clients is always None when running. Should I specify a different object?
    if ctx.bot.voice_clients is None:
        # allows use of CustomVoiceClient class 
        vc = await ctx.author.voice.channel.connect(cls=CustomVoiceClient)
        vc.add_track(discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(f"music/{file}.mp3")))
        return await ctx.send(embed=discord.Embed(title=f"Now Playing: {file}"), view=PlayerUi(vc))
    else:
        audio_url = await youtubedl(url)
        vc = ctx.voice_client
        vc.stop()
        vc.play(discord.FFmpegPCMAudio(audio_url, **FFMPEG_OPTIONS))
        await ctx.send(f"Now Playing: {file}")'''

@bot.command()
async def playsfx(ctx: commands.Context, file: str):
    """ Plays audio url as defined in sfx.env """
    if ctx.author.voice is None:
        return await ctx.send("You must connect to a voice channel first.")

    await play(ctx, file, False)

    # temporarily load music.env during method
    """load_dotenv("sfx.env")
    url = os.getenv(file)
    if url is None or isYoutubeUrl(url) is False:
        return await ctx.send(f"Could not retrieve Youtube url using name {file}")

    # ctx.bot.voice_clients is always None when running. Should I specify a different object?
    if ctx.bot.voice.client is None:
        voice_client = await ctx.author.voice.channel.connect(cls=CustomVoiceClient)
        voice_client.add_track(discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(f"sfx/{file}.mp3")))
        return await ctx.send(embed=discord.Embed(title=f"Now Playing: {file}"), view=PlayerUi(voice_client))
    else:
        audio_url = await youtubedl(url)
        vc = ctx.voice_client
        vc.stop()
        vc.play(discord.FFmpegPCMAudio(audio_url, **FFMPEG_OPTIONS))
        await ctx.send(f"Now Playing: {file}")

    # remove variables loaded from music.env
    del os.environ["sfx.env"]"""

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

    # ctx.bot.voice_clients is always None when running. Should I specify a different object?
    '''if ctx.bot.voice_clients is None:
        # allows use of CustomVoiceClient class 
        vc = await ctx.author.voice.channel.connect(cls=CustomVoiceClient)
        vc.add_track(discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(f"music/{file}.mp3")))
        return await ctx.send(embed=discord.Embed(title=f"Now Playing: {file}"), view=PlayerUi(vc))
    else:'''
    audio_url = await youtubedl(url)
    vc = ctx.voice_client
    vc.stop()
    vc.play(discord.FFmpegPCMAudio(audio_url, **FFMPEG_OPTIONS))
    await ctx.send(f"Now Playing: {file}")

def isYoutubeUrl(url : str):
    if url.startswith("https://www.youtube.com/watch?v="):
        return True
    return False

bot.run(os.environ['BOT_TOKEN'])