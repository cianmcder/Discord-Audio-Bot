import asyncio
import subprocess
import sys
import threading

import discord
import yt_dlp

# installed bgutil locally to bypass Youtube's requirement for PO tokens
# C:\Program Files\bgutil\bgutil-ytdlp-pot-provider\server
# from CMD line above run "node build/main.js"

FFMPEG_EXECUTABLE = r"C:\ffmpeg\bin\ffmpeg.exe"

YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
    
    'extractor_args': {
        'youtube': {
            'player_client': ['mweb'],
        }
    },

    'remote_components': ['ejs:github'],
}

ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)

async def youtubedl(url: str):
    """Retrieve metadata without downloading the entire track."""
    loop = asyncio.get_running_loop()
    data = await loop.run_in_executor(
        None,
        lambda: ytdl.extract_info(url, download=False),
    )
    return {
        "url": url,
        "title": data.get("title", "Unknown title"),
    }

class YtDlpAudioSource(discord.AudioSource):
    """Stream yt-dlp stdout through FFmpeg into Discord PCM frames."""

    def __init__(self, url: str):
        self._lock = threading.Lock()
        self._closed = False

        command = [
            sys.executable,
            "-m", "yt_dlp",
            "--no-playlist",
            "--no-warnings",
            "--no-progress",
            "--quiet",
            "--remote-components", "ejs:github",
            "--extractor-args", "youtube:player_client=mweb",
            "-f", "bestaudio/best",
            "-o", "-",
            url,
        ]

        # Audio bytes go to stdout; diagnostic messages remain visible
        # in the bot console through stderr.
        self._ytdlp = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=None,
            bufsize=0,
        )

        try:
            self._ffmpeg = discord.FFmpegPCMAudio(
                self._ytdlp.stdout,
                pipe=True,
                executable=FFMPEG_EXECUTABLE,
                options="-vn",
            )
        except Exception:
            self._terminate_ytdlp()
            raise

    def read(self) -> bytes:
        if self._closed:
            return b""
        return self._ffmpeg.read()

    def is_opus(self) -> bool:
        return False

    def cleanup(self):
        with self._lock:
            if self._closed:
                return
            self._closed = True

        # Stop FFmpeg first so it no longer consumes the pipe.
        try:
            self._ffmpeg.cleanup()
        except Exception:
            pass

        self._terminate_ytdlp()

    def _terminate_ytdlp(self):
        process = getattr(self, "_ytdlp", None)
        if process is None:
            return

        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()

        if process.stdout is not None:
            try:
                process.stdout.close()
            except Exception:
                pass

def make_youtube_source(url: str) -> YtDlpAudioSource:
    """Create a live streaming audio source from a YouTube URL."""
    return YtDlpAudioSource(url)