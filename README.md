# Discord-Audio-Bot
Backend code for a Discord bot, meant to play audio for a Dungeons and Dragons Discord channel I created.

Requires installation of Python, ffmpeg, PyNaCl, Deno, and bgutil to function.

Before running, go into the directory you installed bgutil in, find >bgutil\bgutil-ytdlp-pot-provider\server. Open the command line at this directory and run "node build/main.js". This will help create tokens needed to run Youtube audio.

Commands:

!join - Tells the bot to join the Discord voice channel.

!leave - Tells the bot to leave the Discord voice channel.

!playmusic NAME - Bot starts playing music using a name associated with a url found in music.env.

!stopmusic - Bot immediately stops playing selected music.

!playsfx NAME - Bot starts playing sound effects using a name associated with a url found in sfx.env.

!stopsfx - Bot immediately stops playing selected sound effects.

!playbard NAME - Bot starts playing randomly selected music found in a playlist using a name found within bard.env.

!bardnext - Bot will start playing the next song in the selected playlist.

!bardshuffle - Bot will start a randomly select a song among the songs in the playlist not selected yet.

!stopbard - Bot immediately stops selected playlist.

!stop - Bot stops playing all audio.
