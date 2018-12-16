import asyncio
from os import stat

from discord import Channel, ChannelType, Client, VoiceClient, utils
from discord.voice_client import StreamPlayer
from tinydb import TinyDB, Query

from . import CircularStream, Config, PhrasePicker, SEPicker, SEPlayer, MultiStream

class CheeseBot():
    def __init__(self, data_path: str):
        db = TinyDB('{}/storage.json'.format(data_path))
        phrase_picker = PhrasePicker(db.table('phrases'))
        self.__config = Config(db.table('config'))
        self.__client = client = Client()

        @client.event
        async def on_ready():
            print('Logged in as {} (ID {})'.format(client.user, client.user.id))
            channel, stream = await self.setup_bgm(data_path)
            if channel is not None:
                print('Now playing spoopy music in {}'.format(channel.name))
                SEPlayer(stream, SEPicker('{}/se'.format(data_path))).start()
            else:
                print('Voice channel "{}" not found.'.format(self.__config['voice_channel']))

        @client.event
        async def on_message(message):
            if message.content.find(client.user.mention) >= 0:
                await client.send_message(message.channel, phrase_picker.pick())

    async def setup_bgm(self, data_path: str) -> (Channel, MultiStream):
        channel = None  # type: discord.Channel

        for server in self.__client.servers:
            channel = utils.find(
                lambda c: c.name.find(self.__config['voice_channel']) >= 0 and
                        c.type is ChannelType.voice,
                server.channels
            )
            if channel is not None:
                break

        if channel is None:
            return None

        voice_client = await self.__client.join_voice_channel(channel)  # type: discord.VoiceClient
        assert isinstance(voice_client, VoiceClient)

        filename = '{}/bgm/stream.raw'.format(data_path)

        try:
            blksize = stat(filename).st_blksize
        except AttributeError:
            blksize = 4096

        audio = open(filename, 'rb', 0)
        stream = MultiStream().add_stream(CircularStream(audio, 1000 * blksize))
        player = voice_client.create_stream_player(stream)  # type: discord.voice_client.StreamPlayer
        assert isinstance(player, StreamPlayer)
        player.start()

        return channel, stream

    def run(self):
        self.__client.run(self.__config['discord_token'])
