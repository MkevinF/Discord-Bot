import discord
import asyncio
import youtube_dl
from discord.ext import commands
from queue import Queue
from discord import Embed
import random
from discord.ext.commands import has_permissions
import time
import threading

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

bot = commands.Bot(command_prefix='!', description='Multi Purpose', intents=intents)

#Saber la latencia
@bot.command()
async def ping(ctx):
    start = time.time()
    await ctx.send("Pong!")
    end = time.time()
    latency = (end - start) * 1000
    await ctx.send(f"Latencia: {latency:.2f} ms")
    
# Borra todos los mensajes    
@bot.command(name='clearall', help='Borra todos los mensajes')
@commands.has_permissions(administrator=True)
async def clearall(ctx):
    try:
        while True:
            deleted = await ctx.channel.purge(limit=100)
            if not deleted:
                break
            await asyncio.sleep(1) 
    except Exception as e:
        pass
    
    
# Borrar los mensajes indicando la cantidad a borrar EJ: !clear 5    
@bot.command(name='clear', help='Elimina una cantidad específica de mensajes')
@commands.has_permissions(administrator=True)
async def clear(ctx, amount: int):
    try:
        message = await ctx.send(f'Borrando {amount} mensajes...')
        messages = await ctx.channel.purge(limit=amount)

        await message.delete()
        
    except discord.errors.NotFound:
        pass
    except Exception as e:
        print(e)
    
# Comprobar cantidad de usuarios en el servidor
@bot.command(name='miembros', help='Muestra la cantidad total de miembros en el servidor')
async def miembros(ctx):
    guild = ctx.guild
    total_bots = sum(1 for member in guild.members if member.bot)
    human_members = guild.member_count - total_bots
    await ctx.send(f'Hay un total de {human_members} usuarios en el servidor.')
    
# Comando para banear a un usuario
@bot.command(name='ban', help='Banear a un usuario')
@commands.has_permissions(ban_members=True)
async def ban(ctx, member : discord.Member, *, reason=None):
    await member.ban(reason=reason)
    await ctx.message.delete()
    try:
        await member.send(f'Has sido baneado permanentemente del servidor por: {reason}')
    except discord.Forbidden:
        pass

# Comando para kickear a un usuario
@bot.command(name='kick', help='Kickear a un usuario')
@commands.has_permissions(kick_members=True)
async def kick(ctx, member : discord.Member, *, reason=None):
    await member.kick(reason=reason)
    await ctx.message.delete()
    try:
        await member.send(f'Has sido kickeado por: {reason}')
    except discord.Forbidden:
        pass

# Comando para mutear a un usuario
@bot.command(name='mute', help='Mutear a un usuario')
@commands.has_permissions(manage_roles=True)
async def mute(ctx, member : discord.Member, *, reason=None):
    role = discord.utils.get(ctx.guild.roles, name="Muted")
    await member.send(f'Has sido muteado permanentemente por: {reason}')
    await ctx.message.delete()
    
# Comando para dar temporalmente a un usuario
@bot.command(name='tempban', help='Banear a un usuario temporalmente')
@commands.has_permissions(ban_members=True)
async def tempban(ctx, member : discord.Member, duration: int, *, reason=None):
    await member.ban(reason=reason)
    await ctx.message.delete()
    await asyncio.sleep(duration * 60)
    await member.unban()
    try:
        await member.send(f'Has sido baneado del servidor temporalmente por {duration} minutos por: {reason}')
    except discord.Forbidden:
        pass
    
# Comando para mutear temporalmente a un usuario
@bot.command(name='tempmute', help='Silenciar a un usuario temporalmente')
@commands.has_permissions(manage_roles=True)
async def tempmute(ctx, member : discord.Member, duration: int, *, reason=None):
    mute_role = discord.utils.get(ctx.guild.roles, name='Muted')
    if not mute_role:
        mute_role = await ctx.guild.create_role(name='Muted', permissions=discord.Permissions.none())
    for channel in ctx.guild.text_channels:
        await channel.set_permissions(mute_role, send_messages=False)
    await ctx.message.delete()
    await member.add_roles(mute_role, reason=reason)
    await member.send(f'Has sido silenciado en el servidor por {duration} minutos por: {reason}')
    await asyncio.sleep(duration * 60)
    await member.remove_roles(mute_role)
    await member.send(f'Has cumplido tu condena.')
    
# Comando para desbanear a un usuario
@bot.command()
async def unban(ctx, *, user: discord.User):
    await ctx.guild.unban(user)
    await ctx.message.delete()

@unban.error
async def unban_error(ctx, error):
    if isinstance(error, discord.ext.commands.BadArgument):
        user_id = int(user.split("#")[-1])
        user = discord.Object(id=user_id)
        await ctx.guild.unban(user)
        await ctx.message.delete()
        
# Comando para desmutear a un usuario
@bot.command(name='unmute', help='Desmutea a un usuario')
@commands.has_permissions(manage_roles=True)
async def unmute(ctx, member : discord.Member, *, reason=None):
    role = discord.utils.get(member.guild.roles, name="Muted")
    await member.remove_roles(role, reason=reason)
    await ctx.message.delete()
    await member.send(f'Has sido desmuteado en el servidor por la siguiente razón: {reason}')
    
# Comando para generar link
@bot.command(name='invite', help='Genera un enlace de invitación para el servidor')
async def invite(ctx):
    invite = await ctx.channel.create_invite(max_uses=2)
    await ctx.send(f'Enlace de invitación: {invite}')
        
# Tarea automatica, mutear usuarios que hagan ping a staffs por 30 minutos.
warnings = {}

async def mute(member):
    role = discord.utils.get(member.guild.roles, name="Muted")
    await member.add_roles(role)
    await member.send(f'Has sido muteado por hacer ping a staffs.')
    await asyncio.sleep(1800)
    await member.remove_roles(role)
    await member.send(f'Has sido desmuteado.')
    del warnings[member.id]

@bot.event
async def on_message(message):
    if message.mentions:
        for member in message.mentions:
            if any(role.permissions.administrator for role in member.roles):
                user = message.author
                if not any(role.permissions.administrator for role in user.roles):
                    if user.id in warnings:
                        warnings[user.id] += 1
                        if warnings[user.id] == 2:
                            await message.channel.send(f"{user.mention} Te queda solo una advertencia antes de ser muteado por 30 minutos.")
                        if warnings[user.id] >= 3:
                            await mute(user)
                            warnings[user.id] = 0
                    else:
                        warnings[user.id] = 1
    await bot.process_commands(message)
    
# Youtube
loop = asyncio.get_event_loop()
queue = asyncio.Queue()
current_song = None
search_result_global = None
vc_global = None
ctx_global = None
song_position = 1

def random_color():
    return random.randint(0, 0xFFFFFF)

@bot.command()
async def play(ctx, *, url):
    global queue, current_song, vc_global, ctx_global, search_result_global, song_position
    vc_global = ctx.voice_client
    ctx_global = ctx
    voice_channel = ctx.author.voice
    if not voice_channel:
        await ctx.send("Necesitas unirte a un canal de voz para usar este comando.")
        return
    vc = vc_global
    if vc:
        if vc.is_connected():
            if vc.channel.id != voice_channel.channel.id:
                await ctx.send(f"Necesitas estar en un {vc.channel} canal para reproducir musica.")
                return
        else:
            vc = await voice_channel.channel.connect()
    else:
        vc = await voice_channel.channel.connect()
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        if 'artist:' in url:
            search_result_global = ydl.extract_info(f"ytsearch:{url}", download=False)
        else:
            search_result_global = ydl.extract_info(f"ytsearch1:{url}", download=False)
        video_url = search_result_global['entries'][0]['url']
        
        if vc.is_paused():
            await queue.put((video_url, search_result_global["entries"][0]))
            embed = discord.Embed(title=f'Cancion en cola - Posición {song_position}', description=search_result_global["entries"][0]["title"], color=discord.Color.red())
            song_position += 1
            await ctx.send(embed=embed)
            return
        
        if vc.is_playing():
            await queue.put((video_url, search_result_global["entries"][0]))
            embed = discord.Embed(title=f'Cancion en cola - Posición {song_position}', description=search_result_global["entries"][0]["title"], color=discord.Color.red())
            song_position += 1
            await ctx.send(embed=embed)
        else:
            current_song = search_result_global["entries"][0]
            vc.play(discord.FFmpegPCMAudio(video_url, executable="C:/ffmpeg/bin/ffmpeg.exe"), after=lambda e: bot.loop.create_task(play_next_song()))
            vc.source = discord.PCMVolumeTransformer(vc.source)
            vc.source.volume = 1.0
            embed = discord.Embed(title='Reproduciendo', description=current_song["title"], color=random_color())
            await ctx.send(embed=embed)

async def play_next_song():
    global queue, current_song, vc_global, ctx_global, search_result_global, color
    if queue.qsize() > 0:
        next_song_url, current_song = await queue.get()
        vc_global.stop()
        for song in search_result_global["entries"]:
            if song['url'] == next_song_url:
                current_song = song
                break
        vc_global.play(discord.FFmpegPCMAudio(next_song_url, executable="C:/ffmpeg/bin/ffmpeg.exe"), after=lambda e: bot.loop.create_task(play_next_song()))
        vc_global.source = discord.PCMVolumeTransformer(vc_global.source)
        vc_global.source.volume = 1.0
        embed = discord.Embed(title='Reproduciendo', description=current_song["title"], color=random_color())
        await ctx_global.send(embed=embed)

# Comandos para ontrolar el reproductor de musica (Youtube):

# Pausar
@bot.command(name='pause')
async def pause(ctx):
    if ctx.author.voice is None or ctx.author.voice.channel is None:
        embed = discord.Embed(description='No estas en un canal de voz.', color=discord.Color.gold())
        return await ctx.send(embed=embed)
    vc = ctx.guild.voice_client
    if vc and vc.is_playing():
        vc.pause()
        embed = discord.Embed(description='Pausando la cancion.', color=discord.Color.gold())
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(description='No hay canción reproduciendose.', color=discord.Color.gold())
        await ctx.send(embed=embed)

# Resumir
@bot.command(name='resume')
async def resume(ctx):
    if ctx.author.voice is None or ctx.author.voice.channel is None:
        embed = discord.Embed(description='No estas en un canal de voz.', color=discord.Color.gold())
        return await ctx.send(embed=embed)
    vc = ctx.guild.voice_client
    if vc and vc.is_paused():
        vc.resume()
        embed = discord.Embed(description='Resumiendo la canción.', color=discord.Color.gold())
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(description='No hay canción en pausa.', color=discord.Color.gold())
        await ctx.send(embed=embed)

# Saltar canción
@bot.command(name='skip')
async def skip(ctx):
    if ctx.author.voice is None or ctx.author.voice.channel is None:
        embed = discord.Embed(description='No estas en un canal de voz.', color=discord.Color.gold())
        return await ctx.send(embed=embed)
    vc = ctx.guild.voice_client
    if vc and vc.is_playing():
        message = await ctx.send('¿Desea saltar a la siguiente canción? 🤖')
        await message.add_reaction('✅')
        await message.add_reaction('❌')
        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ['✅', '❌']
        try:
            reaction, user = await bot.wait_for('reaction_add', timeout=30.0, check=check)
        except asyncio.TimeoutError:
            embed = discord.Embed(description='Tiempo agotado para saltar la canción.', color=discord.Color.gold())
            await ctx.send(embed=embed)
        else:
            if str(reaction.emoji) == '✅':
                vc.stop()
                embed = discord.Embed(description='Saltando la canción.', color=discord.Color.gold())
                await ctx.send(embed=embed)
            elif str(reaction.emoji) == '❌':
                embed = discord.Embed(description='No se saltó la canción.', color=discord.Color.gold())
                await ctx.send(embed=embed)
    else:
        embed = discord.Embed(description='No hay canción reproduciendose.', color=discord.Color.gold())
        await ctx.send(embed=embed)

# Parar
@bot.command(name='stop')
async def stop(ctx):
    if ctx.author.voice is None or ctx.author.voice.channel is None:
        embed = discord.Embed(description='No estas en un canal de voz.', color=discord.Color.gold())
        return await ctx.send(embed=embed)
    vc = ctx.guild.voice_client
    if vc and vc.is_connected():
        msg = await ctx.send("¿Desea detener la canción? 🤖")
        await msg.add_reaction("✅")
        await msg.add_reaction("❌")
        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["✅","❌"]
        try:
            reaction, user = await bot.wait_for('reaction_add', timeout=60.0, check=check)
        except asyncio.TimeoutError:
            await ctx.send("Tiempo de espera agotado.")
        else:
            if str(reaction.emoji) == "✅":
                vc.stop()
                embed = discord.Embed(description='Deteniendo la canción.', color=discord.Color.gold())
                await ctx.send(embed=embed)
            else:
                await ctx.send("Cancelado.")
    else:
        embed = discord.Embed(description='No estoy conectado a un canal de voz.', color=discord.Color.gold())
        await ctx.send(embed=embed)
      
 # Borrar cola o playlist     
@bot.command()
async def clearqueue(ctx):
    global queue, search_result_global, song_position
    msg = await ctx.send('¿Seguro que deseas vaciar la cola? 🤖')
    await msg.add_reaction('✅')
    await msg.add_reaction('❌')
    def check(reaction, user):
        return user == ctx.author and str(reaction.emoji) in ('✅', '❌')
    try:
        reaction, user = await bot.wait_for('reaction_add', timeout=60.0, check=check)
    except asyncio.TimeoutError:
        await ctx.send('Tiempo de espera agotado.')
        return
    if str(reaction.emoji) == '✅':
        previous_queue = queue
        queue = asyncio.Queue()
        search_result_global = None
        song_position = 1
        if previous_queue.qsize() > 1:
            # Aqui se esta removiendo todos las canciones de la cola, pero no la actual.
            current_song = previous_queue.get_nowait()
            queue.put(current_song)
            embed = discord.Embed(description='Cola vaciada.', color=discord.Color.gold())
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(description='No hay ninguna cola para vaciar.', color=discord.Color.gold())
            await ctx.send(embed=embed)
    elif str(reaction.emoji) == '👎':
        await ctx.send('Acción cancelada.')
      
# Desconectar al bot del canal de voz
@bot.command()
async def leave(ctx):
    global song_position
    if ctx.author.voice is not None:
        vc = ctx.author.voice.channel
    else:
        embed = discord.Embed(description='No estas en un canal de voz.', color=discord.Color.gold())
        await ctx.send(embed=embed)
        return
    def check(reaction, user):
        return user == ctx.author and (str(reaction.emoji) == '✅' or str(reaction.emoji) == '❌')

    msg = await ctx.send('¿Estas seguro de que deseas desconectarme? 🤖')
    await msg.add_reaction('✅')
    await msg.add_reaction('❌')
    try:
        reaction, user = await bot.wait_for('reaction_add', timeout=30.0, check=check)
    except asyncio.TimeoutError:
        embed = discord.Embed(description='Tiempo agotado.', color=discord.Color.gold())
        await ctx.send(embed=embed)
        return
    if str(reaction.emoji) == '✅':
        song_position = 1
        await vc.guild.voice_client.disconnect()
        embed = discord.Embed(description='Desconectando...', color=discord.Color.gold())
        await ctx.send(embed=embed)
    elif str(reaction.emoji) == '❌':
        embed = discord.Embed(description='Cancelado.', color=discord.Color.gold())
        await ctx.send(embed=embed)


@bot.event
async def on_ready():
    print('Now, the bot is connected.')

bot.run("")
