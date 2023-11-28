from Helper import *


# Lógica para los botones.
class MusicButton(discord.ui.Button):
    def __init__(self, label, style, custom_id):
        super().__init__(label=label, style=style, custom_id=custom_id)
        self.custom_callback = None
    
    async def callback(self, interaction: discord.Interaction):
        if self.custom_callback:
            await self.custom_callback(interaction)
    
    def set_callback(self, callback):
        self.custom_callback = callback



class MusicView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.pause_button = MusicButton(label="Pause", style=discord.ButtonStyle.primary, custom_id="pause")
        self.stop_button = MusicButton(label="Stop", style=discord.ButtonStyle.danger, custom_id="stop")
        self.queue_button = MusicButton(label="SNS" , style=discord.ButtonStyle.success, custom_id="queue") #SNS significa Show Next Song
        self.skip_button = MusicButton(label="Skip", style=discord.ButtonStyle.primary, custom_id="skip")
        self.add_item(self.pause_button)
        self.add_item(self.stop_button)
        self.add_item(self.queue_button)
        self.add_item(self.skip_button)
        self.is_paused = False       
        
    
    #Botones para controlar las canciones.

    #Boton Pausa-Resumir
    async def pause_resume(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if vc:
            if self.is_paused:
                vc.resume()
                self.is_paused = False
                self.pause_button.label = "Pause"
                await interaction.response.defer()

            else:
                vc.pause()
                self.is_paused = True
                self.pause_button.label = "Resume"
                await interaction.response.defer()

        await interaction.message.edit(view=self)




    #Boton Stop
    async def stop(self, interaction: discord.Interaction, ctx: commands.Context):
        global queue, search_result_global, song_position

        vc = interaction.guild.voice_client
        if vc:
            vc.stop()
            queue = asyncio.Queue()
            search_result_global = None
            song_position = 1
            embed = discord.Embed(description='Detenido', color=discord.Color.gold())
            await ctx.send(embed=embed)
            await interaction.response.defer()




    #Boton Skip
    async def skip(self, interaction: discord.Interaction):
        global song_position
        vc = interaction.guild.voice_client
        if vc:
            vc.stop()
            song_position -= 1
            if song_position == 0:
                song_position += 1
            await interaction.response.defer()




    #Boton SNS, la función de este boton es solo para mostrar la canción actual y la siguiente canción, incluso si hay 3 canciones en la cola solo mostrará la siguiente cancion.
    async def show_queue(self, interaction: discord.Interaction, current_song):
        global queue

        await interaction.response.defer()

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

        if not queue.empty():
            next_song = queue_list[0]
            embed.add_field(name="🎶 Siguiente Canción 🎶", value=f"{next_song['info']['title']}", inline=False)
        else:
            embed.add_field(name="🎶 No hay siguiente canción. ¡Agrega una! 🎶", value=f"", inline=False)

        embed.set_footer(text="Usa +skip para saltar la canción")
        
        msg = await interaction.channel.send(embed=embed)
        
        await msg.add_reaction("❌")

        def check(reaction, user):
            return (
                user == interaction.user
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