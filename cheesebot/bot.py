from discord.ext.commands import Bot
from tinydb import TinyDB, Query

from . import Config
from .cogs import PhrasePicker, MentionCog, SEPicker, AudioCog

class CheeseBot(Bot):
    def __init__(self, data_path: str):
        db = TinyDB('{}/storage.json'.format(data_path))
        self.__config = Config(db.table('config'))
        super().__init__('🧀')
        self.add_cog(MentionCog, PhrasePicker(db.table('phrases')))
        self.add_cog(
            AudioCog,
            voice_channel=self.__config['voice_channel'],
            bgm='{}/bgm/stream.raw'.format(data_path),
            se_picker=SEPicker('{}/se'.format(data_path))
        )

    def add_cog(self, cog_type: type, *args, **kwargs) -> None:
        return super().add_cog(cog_type(self, *args, **kwargs))

    def run(self):
        super().run(self.__config['discord_token'])
