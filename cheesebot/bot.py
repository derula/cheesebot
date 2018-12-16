from discord.ext.commands import Bot

from . import Config, DB
from .cogs import CogFactory

class CheeseBot(Bot):
    def __init__(self, data_path: str):
        self.__db = DB('{}/storage.json'.format(data_path))
        self.__config = Config(self.__db.table('config'))
        self.__data_path = data_path
        super().__init__('🧀')
        self.__cog_factory = CogFactory(self)

    @property
    def db(self) -> DB:
        return self.__db

    @property
    def config(self) -> Config:
        return self.__config

    @property
    def data_path(self) -> str:
        return self.__data_path

    def add_cog(self, cog_type: type) -> None:
        super().add_cog(self.__cog_factory(cog_type))

    def run(self):
        super().run(self.__config['discord_token'])
