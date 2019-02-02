from collections import defaultdict
from typing import Union

from tinydb import Query
from tinydb.database import Table

ConfigQuery = Query()
ConfigEntry = Union[str, int, float, bool]

def _has_handlers(cls):
    for method in cls.__dict__.values():
        for key in getattr(method, 'handles', []):
            cls._handlers[key].append(method)
    return cls

def _handles(key: str) -> callable:
    def decorator(func: callable) -> callable:
        if not hasattr(func, 'handles'):
            func.handles = []
        func.handles.append(key)
        return func
    return decorator
@_has_handlers
class Config(dict):
    _handlers = defaultdict(list)

    def __init__(self, bot: 'CheeseBot', level: int=0) -> None:
        super().__init__()
        self.__bot = bot
        self.__table = bot.db.table('config')
        self._handlers = {k: [m.__get__(self) for m in v] for k, v in self._handlers.items()}
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
        self.__handle(key, value)

    @property
    def level(self) -> int:
        return self.__level

    @level.setter
    def level(self, value: int) -> None:
        self.__level = value

        entries = self.__table.search(ConfigQuery.level_min <= value)

        # Collect config in new dict to avoid reaching an inconsistent state
        old_config = self.copy()
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

        # Call all handlers for now-current values
        for key in old_config.keys():
            new_value = self.get(key)
            if old_config[key] != new_value:
                self.__handle(key, new_value)

    def __handle(self, key: str, value: ConfigEntry):
        for meth in self._handlers.get(key, []):
            meth(value)
