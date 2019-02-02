from signal import getsignal, signal, SIGTERM, SIGINT

from discord.ext.commands import Bot

from . import Config, DB
from .cogs import CogFactory

class CheeseBot(Bot):
    def __init__(self, data_path: str):
        self.__db = DB('{}/storage.json'.format(data_path))
        self.__config = Config(self)
        self.__data_path = data_path
        super().__init__('🧀')
        self.__cog_factory = CogFactory(self)

        for sig in (SIGTERM, SIGINT):
            old_handler = getsignal(sig)

            def stop(signo, _frame):
                for cog in self.cogs.values():
                    cog.shutdown(signo)
                self.db.close()
                if callable(old_handler):
                    old_handler(signo, _frame)

            signal(sig, stop)

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
