import discord
from discord import app_commands
from dotenv import load_dotenv
import os
import yt_dlp
import asyncio

import command

# setup file taken from 'https://blog.stackademic.com/how-to-create-a-music-bot-using-discord-py-and-slash-commands-e3c0a0f92e53'

# Setup Youtube DL library
ytdl_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',  # bind to ipv4 since ipv6 addresses cause issues sometimes
}

#setup FFmpeg
ffmpeg_options = {
    'options': '-vn',
}

ytdl = yt_dlp.YoutubeDL(ytdl_options)

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
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


# from 'https://blog.stackademic.com/how-to-create-a-music-bot-using-discord-py-and-slash-commands-e3c0a0f92e53'
# creates a list of commands used to interact with bot, set up in other .py files

# load .env attributes
load_dotenv("tokens.env")
MY_GUILD = discord.Object(os.environ['GUILD'])

# custom subclasss of discord client used to implement command tree
class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.current_voice_channel = None

    async def setup_hook(self):
        # This copies the global commands over to your guild.
        self.tree.copy_global_to(guild=MY_GUILD)
        await self.tree.sync(guild=MY_GUILD)

intents = discord.Intents.default()
client = MyClient(intents=intents)

# joins voice channel
@client.tree.command()
async def join(interaction: discord.Interaction):
    """ Joins the current voice channel"""
    if(interaction.user.voice):
        name = interaction.user.voice.channel.name
        await interaction.response.send_message(f"Joining voice channel {name}....")
        client.current_voice_channel = await interaction.user.voice.channel.connect()
    else:
        await interaction.response.send_message("You must be in a voice channel to use this command")

# leaves voice channel
@client.tree.command()
async def leave(interaction: discord.Interaction):
    """ Leaves the voice channel """
    name = interaction.user.voice.channel.name
    await interaction.response.send_message(f"Leaving voice channel {name}...")
    client.current_voice_channel = await interaction.user.voice.channel.leave()

# play audio, send to command or command_sfx depending on input
@client.tree.command()
async def play(interaction: discord.Interaction, music: bool, mood: int):
    """ Plays audio """
    url = command.retrieve(music, mood)

    if url == "":
        print(f"URL for given mood does not exist")
    else:
        # NOTE: implement code that determines whether to play on music or sfx track
        await interaction.response.send_message(f"Attempting to play {url}")
        player = await YTDLSource.from_url(url, stream=True)
        guild = interaction.guild
        guild.voice_client.play(player, after=lambda e: print(f'Player error: {e}') if e else None)

# pauses audio already playing
@client.tree.command()
async def pause(interaction: discord.Interaction, music: bool):
    """ Pauses the current audio """
    if(client.current_voice_channel):
        if(client.current_voice_channel.is_paused()):
            await interaction.response.send_message(f"Audio is already paused")
            return
        client.current_voice_channel.pause()
        await interaction.response.send_message(f"Audio paused")
    else:
        await interaction.response.send_message("Not currently in a voice channel")

# resuming audio
@client.tree.command()
async def resume(interaction: discord.Interaction, music: bool):
    """ Resumes the current audio """
    if(client.current_voice_channel):
        if(client.current_voice_channel.is_paused()):
            await interaction.response.send_message(f"Resuming audio")
            client.current_voice_channel.resume()
        else:
            await interaction.response.send_message(f"Audio is not currently paused")
    else:
        await interaction.response.send_message("Not currently in a voice channel")

# end currently selected audio
@client.tree.command()
async def stop(interaction: discord.Interaction, music: bool):
    """ Leaves the current voice channel"""
    if(client.current_voice_channel):
        await client.current_voice_channel.disconnect()
        await interaction.response.send_message("Bye bye")
        client.current_voice_channel = None
    else:
        await interaction.response.send_message("Not currently in a voice channel")

client.run(os.environ['BOT_TOKEN'])