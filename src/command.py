import discord
from discord.ext import commands
from dotenv import load_dotenv
import os

from player import CustomVoiceClient
from player import PlayerUi

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
    return await ctx.voice_client.disconnect(force=True)

@bot.command()
async def playmusic(ctx: commands.Context, file: str):
    """ Plays audio file located in /music folder """
    if ctx.author.voice is None:
        return await ctx.send("You must connect to a voice channel first.")
    if ctx.bot.voice.client is None:
        # allows use of CustomVoiceClient class 
        voice_client = await ctx.author.voice.channel.connect(cls=CustomVoiceClient)
        voice_client.add_track(discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(f"music/{file}.mp3")))
        return await ctx.send(embed=discord.Embed(title=f"Now Playing: {file}"), view=PlayerUi(voice_client))
    else:
        return ctx.voice_client.add_track(discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(f"music/{file}.mp3")))

@bot.command()
async def playsfx(ctx: commands.Context, file: str):
    """ Plays audio file located in /sfx folder """
    if ctx.author.voice is None:
        return await ctx.send("You must connect to a voice channel first.")
    if ctx.bot.voice.client is None:
        voice_client = await ctx.author.voice.channel.connect(cls=CustomVoiceClient)
        voice_client.add_track(discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(f"sfx/{file}.mp3")))
        return await ctx.send(embed=discord.Embed(title=f"Now Playing: {file}"), view=PlayerUi(voice_client))
    else:
        return ctx.voice_client.add_track(discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(f"sfx/{file}.mp3")))

bot.run(os.environ['BOT_TOKEN'])