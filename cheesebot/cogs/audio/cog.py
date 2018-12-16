from glob import glob
from os import stat

from discord import Channel, ChannelType, VoiceClient, utils
from discord.voice_client import StreamPlayer

from .. import CheeseBot, CheeseCog
from ... import Picker
from .se_player import SEPlayer
from .streams import CircularStream, MultiStream

class SEPicker(Picker):
    def __init__(self, path: str) -> None:
        self.__path = path
        super().__init__()

    def _all_items(self):
        return glob('{}/*.raw'.format(self.__path))

class AudioCog(CheeseCog):
    def __init__(self, bot: CheeseBot, voice_channel: str, bgm: str, se_picker: SEPicker):
        super().__init__(bot)
        self.__voice_channel = voice_channel
        self.__bgm = bgm
        self.__se_picker = se_picker

    async def on_ready(self):
        print('Logged in as {} (ID {})'.format(self.bot.user, self.bot.user.id))
        channel, stream = await self.__setup_bgm()
        if channel is not None:
            print('Now playing spoopy music in {}'.format(channel.name))
            SEPlayer(stream, self.__se_picker).start()
        else:
            print('Voice channel "{}" not found.'.format(self.__voice_channel))

    async def __setup_bgm(self) -> (Channel, MultiStream):
        channel = None  # type: discord.Channel

        for server in self.bot.servers:
            channel = utils.find(
                lambda c: c.name.find(self.__voice_channel) >= 0 and
                        c.type is ChannelType.voice,
                server.channels
            )
            if channel is not None:
                break

        if channel is None:
            return None

        voice_client = await self.bot.join_voice_channel(channel)  # type: discord.VoiceClient
        assert isinstance(voice_client, VoiceClient)

        try:
            blksize = stat(self.__bgm).st_blksize
        except AttributeError:
            blksize = 4096

        audio = open(self.__bgm, 'rb', 0)
        stream = MultiStream().add_stream(CircularStream(audio, 1000 * blksize))
        player = voice_client.create_stream_player(stream)  # type: discord.voice_client.StreamPlayer
        assert isinstance(player, StreamPlayer)
        player.start()

        return channel, stream
