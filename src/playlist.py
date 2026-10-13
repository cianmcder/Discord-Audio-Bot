import asyncio
import random
import threading

import discord
import yt_dlp

from youtube import (make_youtube_source)

PLAYLIST_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': False,
    'quiet': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
    "extract_flat": "in_playlist",
    "ignoreerrors": True,
    "skip_download": True,

    'extractor_args': {
        'youtube': {
            'player_client': ['mweb'],
        }
    },

    'remote_components': ['ejs:github'],
}

playlist_ytdl = yt_dlp.YoutubeDL(PLAYLIST_OPTIONS)

async def get_playlist_entries(url: str) -> list[dict]:
    """Read playlist metadata without downloading the audio."""
    loop = asyncio.get_running_loop()
    data = await loop.run_in_executor(
        None,
        lambda: playlist_ytdl.extract_info(url, download=False),
    )

    if not data:
        raise RuntimeError("yt-dlp could not read the playlist.")

    entries = []
    for entry in data.get("entries") or []:
        if not entry:
            continue

        video_id = entry.get("id")
        video_url = (
            f"https://www.youtube.com/watch?v={video_id}"
            if video_id
            else entry.get("url") or entry.get("webpage_url")
        )

        if not video_url or not video_url.startswith("http"):
            continue

        entries.append({
            "id": video_id or video_url,
            "url": video_url,
            "title": entry.get("title") or video_id or "Unknown title",
        })

    if not entries:
        raise RuntimeError(
            "No playlist entries found. Check the playlist URL and access."
        )

    return entries


class PlaylistAudioSource(discord.AudioSource):
    """
    A continuous source that plays shuffled playlist entries.

    Each track uses the existing yt-dlp -> FFmpeg streaming source.
    Entries are shuffled without replacement within each cycle.
    """

    def __init__(self, entries: list[dict]):
        if not entries:
            raise ValueError("The playlist contains no entries.")

        self._entries = list(entries)
        self._remaining = []
        self._last_id = None
        self._current = None
        self._current_entry = None
        self._lock = threading.RLock()
        self._closed = False
        self._skip_requested = threading.Event()
        self._shuffle_cycle()

    @property
    def closed(self) -> bool:
        with self._lock:
            return self._closed

    @property
    def current_title(self) -> str | None:
        with self._lock:
            return (self._current_entry or {}).get("title")

    def _shuffle_cycle(self):
        self._remaining = list(self._entries)
        random.shuffle(self._remaining)

        # Avoid repeating the last song immediately across cycle boundaries
        # whenever there is more than one entry.
        if (
            len(self._remaining) > 1
            and self._remaining[-1]["id"] == self._last_id
        ):
            self._remaining[0], self._remaining[-1] = (
                self._remaining[-1],
                self._remaining[0],
            )

    def _next_entry(self) -> dict:
        if not self._remaining:
            self._shuffle_cycle()

        entry = self._remaining.pop()
        self._last_id = entry["id"]
        return entry

    def _start_next_track(self) -> bool:
        # Skip entries that fail to initialize, but avoid looping forever
        # if every entry fails to start.
        for _ in range(len(self._entries)):
            with self._lock:
                if self._closed:
                    return False
                entry = self._next_entry()

            try:
                source = make_youtube_source(entry["url"])
            except Exception as exc:
                print(
                    f"Could not start playlist track "
                    f"'{entry['title']}': {exc}"
                )
                continue

            with self._lock:
                if self._closed:
                    source.cleanup()
                    return False

                self._current = source
                self._current_entry = entry
                self._skip_requested.clear()

            print(f"Playlist track: {entry['title']}")
            return True

        print("Playlist stopped: no track could be started.")
        return False

    def read(self) -> bytes:
        while True:
            with self._lock:
                if self._closed:
                    return b""
                current = self._current

            if current is None:
                if not self._start_next_track():
                    return b""
                continue

            frame = current.read()

            # A skip closes the current source, causing read() to return EOF.
            if frame:
                return frame

            current.cleanup()
            with self._lock:
                if self._current is current:
                    self._current = None
                    self._current_entry = None
                if self._closed:
                    return b""

            # EOF or skip: the loop starts the next unplayed entry.
            # At cycle end, _next_entry() reshuffles automatically.

    def skip_next(self) -> bool:
        with self._lock:
            if self._closed:
                return False
            current = self._current
            self._skip_requested.set()

        # Terminating FFmpeg unblocks the worker reading this track.
        if current is not None:
            current.cleanup()
        return True

    def shuffle_remaining(self):
        with self._lock:
            if not self._closed:
                random.shuffle(self._remaining)

    def is_opus(self) -> bool:
        return False

    def cleanup(self):
        with self._lock:
            if self._closed:
                return
            self._closed = True
            current = self._current
            self._current = None
            self._current_entry = None

        if current is not None:
            current.cleanup()