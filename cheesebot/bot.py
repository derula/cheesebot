import asyncio
from os import stat

from discord import Channel, ChannelType, VoiceClient, utils
from discord.ext import commands
from discord.voice_client import StreamPlayer
from tinydb import TinyDB, Query

from . import CircularStream, Config, PhrasePicker, MentionCog, SEPicker, SEPlayer, MultiStream

class CheeseBot(commands.Bot):
    def __init__(self, data_path: str):
        db = TinyDB('{}/storage.json'.format(data_path))
        self.__config = Config(db.table('config'))
        self.__data_path = data_path
        super().__init__('🧀')
        self.add_cog(MentionCog, PhrasePicker(db.table('phrases')))

    def add_cog(self, cog_type: type, *args, **kwargs) -> None:
        return super().add_cog(cog_type(self, *args, **kwargs))

    async def on_ready(self):
        print('Logged in as {} (ID {})'.format(self.user, self.user.id))
        channel, stream = await self.__setup_bgm()
        if channel is not None:
            print('Now playing spoopy music in {}'.format(channel.name))
            SEPlayer(stream, SEPicker('{}/se'.format(self.__data_path))).start()
        else:
            print('Voice channel "{}" not found.'.format(self.__config['voice_channel']))

    async def __setup_bgm(self) -> (Channel, MultiStream):
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

        filename = '{}/bgm/stream.raw'.format(self.__data_path)

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
        super().run(self.__config['discord_token'])
