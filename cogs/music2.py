import os
import discord
from discord.ext import commands
import asyncio
import music.youtube_dl as youtube_dl



ffmpeg_path = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'ffmpeg/bin/ffmpeg.exe')

class Song:
    def __init__(self, url):
        self.url = url
        self.title = None
        self.duration = None
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
            'preferredcodec': 'mp3',  # or 'opus' for Opus codec
            'preferredquality': '192',  # audio bitrate in kbps
            }],
        'youtube_api_key': 'AIzaSyDV-QBmKAadxJKsc0qb5NsCUgDIS6S2_Ig'
    }

    async def get_info(self):
        with youtube_dl.YoutubeDL(self.YTDL_OPTIONS) as ydl:
            try:
                info = ydl.extract_info(self.url, download=False)
                return {'source': info['formats'][0]['url'], 'title': info['title']}
            except Exception:
                return None


class Queue:
    def __init__(self):
        self.songs = []
        self.now_playing = None
        self.loop = False

    def add_song(self, query):
        self.songs.append({'query': query, 'info': None})
        
    def remove_song(self, index):
        if index == 0:
            self.now_playing = None
        self.songs.pop(index)

    def set_loop(self, value):
        self.loop = value

    async def get_next_song(self):
        if self.loop and len(self.songs) > 0:
            return self.songs[0]
        elif len(self.songs) > 1:
            return self.songs[1]
        else:
            return None

    async def load_next_song(self):
            song = await self.get_next_song()
            if song:
                with youtube_dl.YoutubeDL() as ydl:
                    info = ydl.extract_info(song['query'], download=False)
                    song['info'] = {
                        'title': info['title'],
                        'url': info['url'],
                        'duration': info['duration']
                    }
                self.now_playing = song
                self.remove_song(0)

    def clear(self):
        self.songs = []
        self.now_playing = None
        self.loop = False



class MusicPlayer:
    def __init__(self, bot):
        self.queue = Queue()
        self.play_next_song = asyncio.Event()
        self.voice = None
        self.bot = bot
        self.FFMPEG_OPTIONS = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn',
            'executable': ffmpeg_path
        }

    @property

    def is_playing(self):
        return self.voice_client and self.voice_client.is_playing()

    @property
    def now_playing(self):
        return self._now_playing

    async def join_voice_channel(self, ctx):
        if self.voice and self.voice.is_connected():
            await self.voice.move_to(ctx.author.voice.channel)
        else:
            self.voice = await ctx.author.voice.channel.connect()

    async def play_song(self, ctx):
        await self.join_voice_channel(ctx)

        while True:
            await self.queue.load_next_song()

            if self.queue.now_playing is None:
                await asyncio.sleep(1)
                continue

            song = self.queue.now_playing

            source = song['source']

            def play_next(error=None):
                if error:
                    print(f"Error occurred: {error}")
                self.bot.loop.call_soon_threadsafe(self.play_next_song.set)

            self.voice.play(discord.FFmpegPCMAudio(source, **self.FFMPEG_OPTIONS), after=lambda e: self.play_next_song.set())

            await asyncio.sleep(1)

            while self.voice.is_playing():
                await asyncio.sleep(1)

            self.queue.clear()
            self.play_next_song.clear()

            if self.queue.loop:
                self.queue.songs.append(song)

            self.play_next_song.set()
            await self.play_next_song.wait()

    async def skip_song(self):
        self.voice.stop()

    async def stop_playing(self):
        self.voice.stop()
        self.queue.clear()
        self.play_next_song.set()



class MusicCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.players = {}

    async def get_player(self, ctx):
        if ctx.guild.id not in self.players:
            self.players[ctx.guild.id] = MusicPlayer(self.bot)

        player = self.players[ctx.guild.id]
            
        if not player.voice:
            player.voice = await ctx.author.voice.channel.connect()

        if not player.queue:
            player.queue = Queue()

        return player

    @commands.hybrid_command()
    async def playtwo(self, ctx, *, query: str):
        """Memainkan lagu dari query"""
        player = await self.get_player(ctx)
        player.queue.add_song(query)
        if not player.voice.is_playing and player.queue.now_playing is None:
            await player.play_next_song()
        else:
            await ctx.send(f"{query} telah ditambahkan ke antrian")



async def setup(bot):
    await bot.add_cog(MusicCog(bot))
            
