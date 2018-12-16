import os

import discord
import tinydb

from cheesebot import Config, PhrasePicker, SEPicker, SEPlayer, CircularStream, MultiStream

async def setup_bgm() -> (discord.Channel, MultiStream):
    channel = None  # type: discord.Channel

    for server in client.servers:
        channel = discord.utils.find(
            lambda c: c.name.find(config['voice_channel']) >= 0 and
                      c.type is discord.ChannelType.voice,
            server.channels
        )
        if channel is not None:
            break

    if channel is None:
        return None

    voice_client = await client.join_voice_channel(channel)  # type: discord.VoiceClient
    assert isinstance(voice_client, discord.VoiceClient)

    try:
        blksize = os.stat('data/bgm/stream.raw').st_blksize
    except AttributeError:
        blksize = 4096

    audio = open('data/bgm/stream.raw', 'rb', 0)
    stream = MultiStream().add_stream(CircularStream(audio, 1000 * blksize))
    player = voice_client.create_stream_player(stream)  # type: discord.voice_client.StreamPlayer
    assert isinstance(player, discord.voice_client.StreamPlayer)
    player.start()

    return channel, stream

db = tinydb.TinyDB('data/storage.json')
phrase_picker = PhrasePicker(db.table('phrases'))
config = Config(db.table('config'))
client = discord.Client()

@client.event
async def on_ready():
    print('Logged in as {} (ID {})'.format(client.user, client.user.id))
    channel, stream = await setup_bgm()
    if channel is not None:
        print('Now playing spoopy music in {}'.format(channel.name))
        SEPlayer(stream, SEPicker('data/se')).start()
    else:
        print('Voice channel "{}" not found.'.format(config['voice_channel']))

@client.event
async def on_message(message):
    if message.content.find(client.user.mention) >= 0:
        await client.send_message(message.channel, phrase_picker.pick())

client.run(config['discord_token'])
