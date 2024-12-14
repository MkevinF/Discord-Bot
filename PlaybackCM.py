from Helper import *


# Pausar -- pause
@bot.command(name='pause', help='Pausa la canción actual en el canal de voz: +pause')
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



# Resumir -- +resume
@bot.command(name='resume', help='Reanuda la reproducción de la canción pausada: +resume')
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



# Saltar canción confirmando la accion con el cotejo. +skip
@bot.command(name='skip', help='Salta a la siguiente canción en la cola de reproducción: +skip')
async def skip(ctx):
    global song_position
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
                song_position -= 1
                if song_position == 0:
                    song_position += 1
                    
                embed = discord.Embed(description='Saltando la canción.', color=discord.Color.gold())
                await ctx.send(embed=embed)
            elif str(reaction.emoji) == '❌':
                embed = discord.Embed(description='No se saltó la canción.', color=discord.Color.gold())
                await ctx.send(embed=embed)
    else:
        embed = discord.Embed(description='No hay canción reproduciendose.', color=discord.Color.gold())
        await ctx.send(embed=embed)



# Parar confirmando la accion con el cotejo. +stop
@bot.command(name='stop', help='Detiene la canción actual: +stop')
async def stop(ctx):
    global queue, search_result_global, song_position
    if ctx.author.voice is None or ctx.author.voice.channel is None:
        embed = discord.Embed(description='No estás en un canal de voz.', color=discord.Color.gold())
        return await ctx.send(embed=embed)
    vc = ctx.guild.voice_client
    if vc and vc.is_connected():
        if vc.is_playing():
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
                    queue = asyncio.Queue()
                    search_result_global = None
                    song_position = 1
                    embed = discord.Embed(description='Deteniendo...', color=discord.Color.gold())
                    await ctx.send(embed=embed)
                else:
                    await ctx.send("Cancelado.")
        else:
            embed = discord.Embed(description='No hay ninguna canción reproduciéndose para detener.', color=discord.Color.gold())
            await ctx.send(embed=embed)
    else:
        embed = discord.Embed(description='No estoy conectado a un canal de voz.', color=discord.Color.gold())
        await ctx.send(embed=embed)
      
      
      
 # Borrar cola o playlist confirmando la accion con el cotejo. +clearqueue
@bot.command(name='clearqueue', help='Vacia la cola de reproducción: +clearqueue')
async def clearqueue(ctx):
    global queue, search_result_global, song_position

    if queue.qsize() == 0:
        embed = discord.Embed(description='No hay ninguna cola para vaciar.', color=discord.Color.gold())
        await ctx.send(embed=embed)
        return

    embed = discord.Embed(description='¿Estás seguro que deseas vaciar la cola? 🤖', color=discord.Color.gold())
    msg = await ctx.send(embed=embed)
    
    await msg.add_reaction('✅')
    await msg.add_reaction('❌')

    def check(reaction, user):
        return user == ctx.author and str(reaction.emoji) in ('✅', '❌') and reaction.message.id == msg.id

    try:
        reaction, user = await bot.wait_for('reaction_add', timeout=60.0, check=check)
    except asyncio.TimeoutError:
        await ctx.send('Tiempo de espera alcanzado.')
        return

    if str(reaction.emoji) == '✅':
        previous_queue = queue
        queue = asyncio.Queue()
        search_result_global = None
        song_position = 1

        if not previous_queue.empty():
            current_song = await previous_queue.get()
            queue.put_nowait(current_song)

        embed = discord.Embed(description='La cola ha sido vaciada.', color=discord.Color.gold())
        await ctx.send(embed=embed)
    elif str(reaction.emoji) == '❌':
        await ctx.send('Acción cancelada.')
        
      
      
# Desconectar al bot del canal de voz confirmando la accion con el cotejo. +leave
@bot.command(name='leave', help='Desconecta al bot del canal de voz actual: +leave')
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



@bot.command(name='help')
async def custom_help(ctx):
    embed = discord.Embed(title='Comandos del Bot', color=0x42F56C)

    # Añade el comando 'play' primero
    embed.add_field(name=f"**play**", value=bot.get_command('play').help, inline=False)

    for command in bot.commands:
        if command.name not in ('play', 'help'):
            embed.add_field(name=f"**{command.name}**", value=command.help, inline=False)

    await ctx.send(embed=embed)
