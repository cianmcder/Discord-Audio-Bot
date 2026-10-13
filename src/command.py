import os

import discord
from discord.ext import commands
from dotenv import dotenv_values, load_dotenv

from audio_mixer import LayeredAudioSource
from youtube import make_youtube_source, youtubedl

FFMPEG_EXECUTABLE = r"C:\ffmpeg\bin\ffmpeg.exe"

intents = discord.Intents.default()
intents.voice_states = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

load_dotenv("tokens.env")

# One mixer per Discord server (guild).
mixers: dict[int, LayeredAudioSource] = {}


def get_mixer(vc: discord.VoiceClient) -> LayeredAudioSource:
    guild_id = vc.guild.id
    mixer = mixers.get(guild_id)
    if mixer is None or mixer.closed:
        mixer = LayeredAudioSource()
        mixers[guild_id] = mixer
    return mixer


def start_mixer_if_needed(vc: discord.VoiceClient,
                          mixer: LayeredAudioSource) -> None:
    # The mixer is the one and only source played by the voice client.
    if not vc.is_playing() and not vc.is_paused():
        vc.play(
            mixer,
            after=lambda error: print(f"Discord mixer playback error: {error}")
            if error else None,
        )

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
    """Stop all layers and disconnect."""
    vc = ctx.voice_client
    if vc is None:
        return await ctx.send("The bot is not connected to a voice channel.")

    mixer = mixers.get(ctx.guild.id) if ctx.guild else None
    if mixer is not None:
        mixer.stop_all()
    channel_name = vc.channel.name if vc.channel else "the voice channel"
    await vc.disconnect(force=True)
    return await ctx.send(f"Audio bot left {channel_name}.")


@bot.command()
async def playmusic(ctx: commands.Context, file: str):
    """Start or replace background music from music.env."""
    await play_layer(ctx, file, "music.env", "music", 0.45)


@bot.command()
async def playsfx(ctx: commands.Context, file: str):
    """Play a sound effect over any current background music."""
    await play_layer(ctx, file, "sfx.env", "sfx", 0.85)


async def play_layer(ctx: commands.Context, file: str,
                     env_file: str, layer_name: str, volume: float):
    if ctx.author.voice is None:
        return await ctx.send("You must be in a voice channel first.")

    vc = ctx.voice_client
    if vc is None or not vc.is_connected():
        return await ctx.send("Use !join first to connect the bot to voice.")

    library = dotenv_values(env_file)
    if not library:
        return await ctx.send(f"Audio library is empty: {env_file}")

    url = library.get(file)
    if not url or not is_youtube_url(url):
        return await ctx.send(f"Could not retrieve a YouTube URL for: {file}")

    try:
        stream = await youtubedl(url)

        print("Stream title:", stream.get("title"))

        source = make_youtube_source(url)
        mixer = get_mixer(vc)
        # Replaces only this layer. Music and SFX can coexist.
        mixer.add(layer_name, source, volume=volume)
        start_mixer_if_needed(vc, mixer)

        title = stream.get("title", file)
        if layer_name == "music":
            await ctx.send(f"Background music: {title}")
        else:
            await ctx.send(f"Playing sound effect: {title}")
    except Exception as exc:
        print(f"Could not start {layer_name} '{file}': {exc}")
        await ctx.send(f"Could not play {file}: {exc}")


@bot.command()
async def stopmusic(ctx: commands.Context):
    """Stop only the background music layer."""
    return await stop_layer(ctx, "music", "Background music stopped.")


@bot.command()
async def stopsfx(ctx: commands.Context):
    """Stop only the current sound-effect layer."""
    return await stop_layer(ctx, "sfx", "Sound effect stopped.")


async def stop_layer(ctx: commands.Context, layer_name: str, message: str):
    if ctx.author.voice is None:
        return await ctx.send("You must be in a voice channel first.")
    mixer = mixers.get(ctx.guild.id) if ctx.guild else None
    if mixer is None or not mixer.remove(layer_name):
        return await ctx.send(f"No {layer_name} audio is currently playing.")
    return await ctx.send(message)


@bot.command()
async def stop(ctx: commands.Context):
    """Stop all audio layers but keep the bot connected."""
    if ctx.author.voice is None:
        return await ctx.send("You must be in a voice channel first.")
    mixer = mixers.get(ctx.guild.id) if ctx.guild else None
    if mixer is not None:
        mixer.stop_all()
    return await ctx.send("All audio layers stopped.")


def is_youtube_url(url: str) -> bool:
    return url.startswith("https://www.youtube.com/watch?v=")


bot.run(os.environ["BOT_TOKEN"])
