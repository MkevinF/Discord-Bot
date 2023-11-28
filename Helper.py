import discord
import random
import asyncio
from discord.ext import commands


loop = asyncio.get_event_loop()
queue = asyncio.Queue()
current_song = None
search_result_global = None
vc_global = None
ctx_global = None
song_position = 1

def random_color():
    return random.randint(0, 0xFFFFFF)


class MusicContext:
    def __init__(self, ctx):
        self.ctx = ctx
        self.song_position = 1  
        self.total_played = 0



intents = discord.Intents.all()
intents.message_content = True
client = discord.Client(intents=intents)


bot = commands.Bot(command_prefix='+', description='Multi Purpose', intents=intents, help_command=None)

    