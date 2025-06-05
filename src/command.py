import discord
from discord.ext import commands
from dotenv import load_dotenv
import os

from player import CustomVoiceClient
from player import PlayerUi

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

load_dotenv("tokens.env")
# token = discord.Object(os.environ['BOT_TOKEN'])
guild = discord.Object(os.environ['GUILD'])

@bot.command()
async def join(ctx: commands.Context):
    """ Joins the current voice channel. """
    if ctx.author.voice is None:
        return await ctx.send("This command will not work unless you're in a voice channel.")
    name = ctx.author.voice.channel.name
    await ctx.author.voice.channel.connect()
    await ctx.send(f"Audio bot connected to channel {name}")

@bot.command()
async def leave(ctx: commands.Context):
    """ Leaves the voice channel """
    await ctx.voice_client.disconnect()

@bot.command()
async def playmusic(ctx: commands.Context, file: str):
    """ Plays audio file located in /music folder """
    if ctx.author.voice is None:
        return await ctx.send("You must connect to a voice channel first.")
    if ctx.voice.client is None:
        # allows use of CustomVoiceClient class 
        voice_client = await ctx.author.voice.channel.connect(cls=CustomVoiceClient)
        voice_client.add_track(discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(f"music/{file}.mp3")))
        await ctx.send(embed=discord.Embed(title=f"Now Playing: {file}"), view=PlayerUi(voice_client))
    else:
        ctx.voice_client.add_track(discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(f"music/{file}.mp3")))

@bot.command()
async def playsfx(ctx: commands.Context, file: str):
    """ Plays audio file located in /sfx folder """
    if ctx.author.voice is None:
        return await ctx.send("You must connect to a voice channel first.")
    if ctx.voice.client is None:
        voice_client = await ctx.author.voice.channel.connect(cls=CustomVoiceClient)
        voice_client.add_track(discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(f"sfx/{file}.mp3")))
        await ctx.send(embed=discord.Embed(title=f"Now Playing: {file}"), view=PlayerUi(voice_client))
    else:
        ctx.voice_client.add_track(discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(f"sfx/{file}.mp3")))

# bot.run(token)
# client.run(os.environ['BOT_TOKEN'])
bot.run(os.environ['BOT_TOKEN'])