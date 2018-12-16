from typing import Union

from tinydb import Query
from tinydb.database import Table

ConfigQuery = Query()
ConfigEntry = Union[str, int, float, bool]

class Config(dict):
    def __init__(self, table: Table, level: int=0) -> None:
        super().__init__()
        self.__table = table
        self.level = level

    def at_level(self, level: int) -> 'Config':
        if level == self.level:
            return self
        return Config(self.__table, level)

    def __getitem__(self, key: str) -> ConfigEntry:
        return super().__getitem__(key)

    def __setitem__(self, key: str, value: ConfigEntry) -> None:
        super().__setitem__(key, value)
        doc = {key: value, 'level_min': self.level}
        self.__table.upsert(doc, ConfigQuery.level_min == self.level)

    @property
    def level(self) -> int:
        return self.__level

    @level.setter
    def level(self, value: int) -> None:
        self.__level = value

        entries = self.__table.search(ConfigQuery.level_min <= value)

        # Collect config in new dict to avoid reaching an inconsistent state
        new_config = {}
        for entry in sorted(entries, key=lambda entry: entry['level_min']):
            new_config.update(entry)
        del new_config['level_min']

        # Update as atomically as possible (doing a clear(); update() would mean we're losing
        # all configuration for a split second. Not good for a threaded application.)
        keys_to_delete = set(self.keys()).difference(new_config.keys())
        self.update(new_config)
        for key in keys_to_delete:
            del self[key]


