import asyncio
import yt_dlp

YTDL_OPTIONS = {
    'format': 'bestaudio',
    'noplaylist': True,
    'quiet': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
}

ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)

async def youtubedl(url : str):
    """ Uses url to retrieve mp3 from Youtube """
    loop = asyncio.get_event_loop()
    data = await loop.run_in_executor(None, lambda : ytdl.extract_info(url, download = False))
    audio_url = data['url']
    return audio_url
