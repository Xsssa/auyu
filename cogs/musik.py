import asyncio
import os
import discord
import music.youtube_dl as youtube_dl
import lyricsgenius
from typing import List, Tuple
from discord.ext import commands
from typing import Optional

ffmpeg_path = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'ffmpeg/bin/ffmpeg.exe')


class Song:
    def __init__(self, title):
        self.title = title
        self.url = None

    async def get_url(self):
        if self.url is not None:
            return self.url

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': '%(id)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'default_search': 'auto',
            'source_address': '0.0.0.0',
        }

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(f"ytsearch:{self.title}", download=False)['entries'][0]
                self.url = info['formats'][0]['url']
                return self.url
            except Exception as e:
                print(f"Error while fetching song URL: {e}")
                return None

class Queue:
    def __init__(self):
        self._queue = []

    def add_song(self, song: Song):
        self._queue.append(song)

    def remove_song(self, index: int):
        self._queue.pop(index)

    def get_queue(self) -> List[Song]:
        return self._queue

class MusicPlayer:
    def __init__(self, bot, queue: Queue):
        self.bot = bot
        self.queue = queue
        self.is_playing = False
        self.voice_client = None
        self.FFMPEG_OPTIONS = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn',
            'executable': ffmpeg_path
        }
        self.YTDL_OPTIONS = {
            'format': 'bestaudio/best',
            'outtmpl': '.Ex/music download/%(extractor)s-%(id)s-%(title)s.%(ext)s',
            'restrictfilenames': True,
            'retry_max': 'auto',
            'noplaylist': True,
            'nocheckcertificate': True,
            'logtostderr': False,
            'quiet': True,
            'no_warnings': True,
            'default_search': 'auto',
            'source_address': '0.0.0.0',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'youtube_api_key': 'AIzaSyDV-QBmKAadxJKsc0qb5NsCUgDIS6S2_Ig'
        }

    async def connect_voice_channel(self, ctx):
        voice_channel = ctx.author.voice
        if not voice_channel or not voice_channel.channel:
            await ctx.send("Join voice channel dulu...")
            return False
        voice_channel = voice_channel.channel

        if not self.voice_client:
            self.voice_client = await voice_channel.connect()
        else:
            if self.voice_client.channel != voice_channel:
                await self.voice_client.move_to(voice_channel)

        return True

    async def play_music(self, ctx):
        if not self.queue.get_queue():
            await ctx.send("Antrian kosong, tambahkan lagu terlebih dahulu!")
            return

        if not self.is_playing:
            await self.connect_voice_channel(ctx)

        self.is_playing = True
        while self.queue.get_queue():
            song = self.queue.get_queue()[0]
            await ctx.send(f"Playing {song.title}")
            try:
                source = await song.get_url()
                self.voice_client.play(discord.FFmpegPCMAudio(source, **self.FFMPEG_OPTIONS), after=lambda e: self.play_music(ctx))
                self.voice_client.is_playing()

                while self.voice_client.is_playing():
                    await asyncio.sleep(1)

            except Exception as e:
                # Handle music playing errors
                print(f'Error: {e}')

            self.queue.remove_song(0)

        self.is_playing = False
        await ctx.send("Queuenya kosong.")
        await self.voice_client.disconnect()


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queue = Queue()
        self.music_player = MusicPlayer(bot, self.queue)

    @commands.hybrid_command(name="play")
    async def play (self, ctx, *, title: Optional[str]):
        await ctx.defer()
        if not await self.music_player.connect_voice_channel(ctx):
            return

        if title is None:
            # Stop playing and clear the queue
            self.queue.get_queue().clear()
            self.music_player.voice_client.stop()
            await ctx.send("Music stopped and queue cleared.")
            return

        # Search for the song and add it to the queue
        song = Song(title)
        song_url = await song.get_url()

        if song_url is None:
            await ctx.send(f"Couldn't find {title} on YouTube.")
            return

        song.source = song_url
        self.queue.add_song(song)

        if not self.music_player.is_playing:
            await self.music_player.play_music(ctx)



async def setup(bot):
    await bot.add_cog(Music(bot))