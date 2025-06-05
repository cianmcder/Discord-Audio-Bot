import discord
from discord.player import AudioSource
# import asyncio
# import yt_dlp

"""ytdl_options = {
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

ffmpeg_options = {
    'options': '-vn',
}

ytdl = yt_dlp.YoutubeDL(ytdl_options)"""

class CustomVoiceClient(discord.VoiceClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def add_track(self, source: AudioSource):
        self.play(source)

class PlayerUi(discord.ui.View):
    # def __init__ (self, voice_client: CustomVoiceClient, music_list: dict, sfx_list: dict):
    def __init__ (self, voice_client: CustomVoiceClient):
        self.voice_client = voice_client
        #dictionary containing name : url values
        # self.music_list = music_list
        # self.sfx_list = sfx_list

        # AudioSource of selected tracks
        self.music_selected = None
        # self.sfx_selected = None


    # convert Youtube url into AudioSource using ffmpeg
    """def url_to_audiosource(cls, url, loop = None, stream = False):
        # later, set up if-else when i can implement audio mixing
        # if self.music_selected != None and self.sfx_selected != None:
        # else if self.music_selected != None:
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)
        # else:"""
        

    # play or pause audio
    @discord.ui.button(emoji="⏯️")
    async def play_pause(self, interaction: discord.Interaction, button: discord.Button):
        if self.music_selected == None:
            await interaction.response.send_message(f"No audio selected.")
        else:
            # is the track already playing?
            if self.voice_client.is_playing():
                if self.voice_client.is_paused():
                    self.voice_client.resume()
                else:
                    self.voice_client.pause()
            # audio not playing, need to start it up
            else:
                self.voice_client.play(self.music_selected)

    # start audio over
    @discord.ui.button(emoji="🔁")
    async def replay(self):
        self.voice_client.play(self.music_selected)

    """# select audio track
    @discord.ui.select(placeholder="Select Music Track", options=self.music_list.keys())
    async def select_music(self, interaction: discord.Interaction, selected: discord.SelectOption):
        self.music_selected = url_to_audiosource(self, self.music_list[selected])

    select sfx track
    @discord.ui.select(placeholder="Select SFX Track", options=self.sfx_list.keys())
    async def select_sfx(self, interaction: discord.Interaction, selected: discord.SelectOption):
        self.sfx_Selected = self.sfx_list[selected]

    volume control; input value between 0 and 100
    might not be necessary; users can adjust volume of others in channel, so they can do the same for a bot
    @discord.ui.text_input(label="Volume", style=discord.TextStyle.short, min_length=1, max_length=3)
    async def volume(self, interaction: discord.Interaction):"""