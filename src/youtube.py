import asyncio
import yt_dlp

# installed bgutil locally to bypass Youtube's requirement for PO tokens
# C:\Program Files\bgutil\bgutil-ytdlp-pot-provider\server
# from CMD line above run "node build/main.js"

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

async def youtubedl(url : str):
    """ Uses url to retrieve mp3 from Youtube """
    loop = asyncio.get_event_loop()
    
    data = await loop.run_in_executor(None, lambda : ytdl.extract_info(url, download = False))
    
    return {
        "url": data["url"],
        "headers": data.get("http_headers", {}),
        "title": data.get("title", "Unknown title"),
    }
    
    
