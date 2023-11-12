from Music import *
from PlaybackCM import *

# Tarea para que se reestablezca la posicion de la cola al desconectar al bot sin comandos.
@bot.event
async def on_voice_state_update(member, before, after):
    global song_position
    if before.channel is not None and after.channel is None:
        song_position = 1


# Tarea para remover los botones de todos los mensajes generados con el comando +play una vez el usuario desconecte al bot usando +leave
# Deja tambien un mensaje del bot dando las gracias por usarle.
@bot.event
async def on_voice_state_update(member, before, after):
    global music_messages
    if before.channel is not None and after.channel is None:
        for message in music_messages:
            await message.edit(content="Gracias por usarme para reproducir canciones.", view=None)
        music_messages = [] 

@bot.event
async def on_ready():
    print('El bot esta up.')


# Token de su bot
bot.run("MTA2MzQ4NzYwNjY4NTQ0MjExOQ.GibUuY.At15_v8J-HvDfCC0iW2prX-kxFYJCnKk65CLQ4")


