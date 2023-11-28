import yt_dlp as youtube_dl
from Buttons import *
import re


# Mostrar la canción actual y la siguiente canción. SNS = Show next song or mostrar siguiente canción.

@bot.command(name='sns', help='Muestra la canción actual y la siguiente: +sns')
async def sns(ctx):
    global queue, current_song

    if ctx.author.voice is not None:
        vc = ctx.author.voice.channel
    else:
        embed = discord.Embed(description='No estás en un canal de voz.', color=discord.Color.gold())
        await ctx.send(embed=embed)
        return

    queue_list = list(queue._queue)

    embed = discord.Embed(title="💿 Ahora suena", color=random_color())

    if current_song:
        embed.set_thumbnail(url=current_song["thumbnail"])
        title = current_song.get('title', 'No hay ninguna canción reproduciéndose.')
        url = current_song.get('webpage_url', '')
        if url:
            embed.add_field(name="🔊 Canción Actual 🔊", value=f"[{title[:100]}]({url[:100]})", inline=False)
        else:
            embed.add_field(name="🔊 Canción Actual 🔊", value=title, inline=False)
    else:
        embed.add_field(name="🔊 Canción Actual 🔊", value="No hay ninguna canción reproduciéndose.", inline=False)

    if not queue.empty() and len(queue_list) > 0:  # Cambiado de 1 a 0 aquí
        next_song = queue_list[0]['info']  # Cambiado de 1 a 0 aquí
        embed.add_field(name="🎶 Siguiente Canción 🎶", value=f"{next_song['title']}", inline=False)
    else:
        embed.add_field(name="🎶 No hay siguiente canción. ¡Agrega una! 🎶", value=f"", inline=False)

    embed.set_footer(text="Usa +skip para saltar la canción")

    msg = await ctx.send(embed=embed)

    await msg.add_reaction("❌")

    def check(reaction, user):
        return (
            user == ctx.author
            and reaction.message.id == msg.id
            and str(reaction.emoji) == "❌"
        )

    try:
        reaction, user = await bot.wait_for("reaction_add", check=check, timeout=60.0)
    except asyncio.TimeoutError:
        pass
    else:
        if str(reaction.emoji) == "❌":
            await msg.delete()







# Contenedor de mensajes generados por el comando +play
music_messages = []






# Sistema para reproducir cancion desde youtube usando el comando +play 
@bot.command(name='play', help='Reproducir canciones mediante link o nombre de la canción y artista: +play')
async def play(ctx, *, url):
    global queue, current_song, vc_global, ctx_global, search_result_global, song_position, music_messages
    vc_global = ctx.voice_client
    ctx_global = ctx

    if not hasattr(ctx, 'music') or not ctx.music:
        ctx.music = MusicContext(ctx)

    voice_channel = ctx.author.voice
    if not voice_channel:
        await ctx.send("Necesitas unirte a un canal de voz para usar este comando.")
        return
    vc = vc_global
    if vc:
        if vc.is_connected():
            if vc.channel.id != voice_channel.channel.id:
                await ctx.send(f"Necesitas estar en el canal {vc.channel} para reproducir música.")
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
            'preferredquality': 'best',
        }]
    }
    
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        try:
            if 'artist:' in url:
                search_result_global = ydl.extract_info(f"ytsearch:{url}", download=False)
            else:
                search_result_global = ydl.extract_info(f"ytsearch1:{url}", download=False)
        except youtube_dl.utils.DownloadError as e:
            await ctx.send("Lo siento, no pude obtener la información de la canción.")
            return
        video_url = search_result_global['entries'][0]['url']
        

        if vc.is_paused() or vc.is_playing():
            await queue.put({"url": video_url, "info": search_result_global["entries"][0]})
            queue_size = queue.qsize()
            song_position = ctx.music.total_played + queue_size
            embed = discord.Embed(title=f'Canción en cola - Posición {song_position}', description=search_result_global["entries"][0]["title"], color=discord.Color.red())
            ctx.music.total_played += 1
            await ctx.send(embed=embed)
            return
        
        else:
            current_song = search_result_global["entries"][0]
            ffmpeg_options = {
                'options': '-vn',
                'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
            }
            vc.play(discord.FFmpegPCMAudio(video_url, executable="C:/ffmpeg/bin/ffmpeg.exe", **ffmpeg_options), after=lambda e: bot.loop.create_task(play_next_song(ctx, view)))
            vc.source = discord.PCMVolumeTransformer(vc.source)
            vc.source.volume = 1.0
            embed = discord.Embed(title='🎶 Reproduciendo', description=current_song["title"], color=random_color())
            embed.set_thumbnail(url=current_song["thumbnail"])
            title = current_song["title"]
            webpage_url = current_song["webpage_url"]
            

            song_name = re.split(r'-|\(|\[', title, 1)[1].strip() if "-" in title else title
            video_link = f"[{song_name}]({webpage_url})"
            queue_size = queue.qsize() # Esto mostrará la cantidad de canciones que hay en la cola.
            embed.description = f"**Canción:** {video_link}\n**Cola:** {queue_size}"
            

            user = ctx.author
            user_name = str(user)
            user_avatar = user.avatar.url
            embed.set_footer(text=f"Solicitado por: {user_name}", icon_url=user_avatar)

    

    view = MusicView()
    view.pause_button.set_callback(view.pause_resume)
    view.stop_button.set_callback(lambda interaction: view.stop(interaction, ctx_global))
    view.queue_button.set_callback(lambda interaction: view.show_queue(interaction, current_song))
    view.skip_button.set_callback(view.skip)
    view.pause_button.custom_id = "pause"
    
    
    message = await ctx.send(embed=embed, view=view)
    music_messages.append(message)






#Lógica para reproducir la siguiente canción.
async def play_next_song(ctx, view):
    global queue, current_song, vc_global, ctx_global, search_result_global, music_messages, song_position, current_song_info
    if not vc_global or not vc_global.is_connected():
        return
    
    try:
        if queue.qsize() > 0:
            next_song = await queue.get()
            next_song_url = next_song["url"]
            current_song = next_song["info"]
            vc_global.stop()
            ffmpeg_options = {
                'options': '-vn',
                'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
            }
            for song in search_result_global["entries"]:
                if song['url'] == next_song_url:
                    current_song = song
                    break

            vc_global.play(discord.FFmpegPCMAudio(next_song_url, executable="C:/ffmpeg/bin/ffmpeg.exe", **ffmpeg_options), after=lambda e: bot.loop.create_task(play_next_song(ctx, view)))
            vc_global.source = discord.PCMVolumeTransformer(vc_global.source)
            vc_global.source.volume = 1.0
            embed = discord.Embed(title='🎶 Reproduciendo', description=current_song["title"], color=random_color())
            embed.set_thumbnail(url=current_song["thumbnail"])
            title = current_song["title"]
            webpage_url = current_song["webpage_url"]

            song_name = re.split(r'-|\(|\[', title, 1)[1].strip() if "-" in title else title
            video_link = f"[{song_name}]({webpage_url})"
            queue_size = queue.qsize()
            embed.description = f"**Canción:** {video_link}\n**Cola:** {queue_size}"
            
            user = ctx_global.author
            user_name = str(user)
            user_avatar = user.avatar.url
            embed.set_footer(text=f"Solicitado por: {user_name}", icon_url=user_avatar)

            message = await ctx_global.send(embed=embed, view=view)
            music_messages.append(message)
    except discord.errors.InteractionFailed as e:
        pass
