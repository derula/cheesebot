from glob import glob
from math import ceil
from random import choice
from typing import Any

from tinydb import Query
from tinydb.database import Table

class Picker():
    def __init__(self) -> None:
        self.__last_used = []

    def _all_items(self) -> list:
        raise NotImplementedError('Don\'t use Picker directly, use subclasses.')

    def pick(self) -> Any:
        all_items = set(self._all_items())

        # No sound effect found :(
        if len(all_items) == 0:
            return None

        # Make sure that at most half of the sound effects are blocked from playing next.
        # In particular:
        # - If there is only 1 sound effect, ceil(1 - 0.5) = 1 will always be removed.
        # - If there are two SEs, only one item will be disabled (they will be played in turn).
        # - If there are three SEs, only direct repetition will be prevented.
        to_remove = ceil(len(self.__last_used) - len(all_items) / 2)
        if to_remove > 0:
            self.__last_used = self.__last_used[to_remove:]

        item = choice(list(all_items.difference(self.__last_used)))

        # Don't play this sound effect again next time.
        self.__last_used.append(item)

        return item

Phrase = Query()

class PhrasePicker(Picker):
    def __init__(self, table: Table) -> None:
        self.__table = table
        super().__init__()

    def _all_items(self):
        return map(lambda row: row['content'], self.__table.search(Phrase.language == 'odan'))

class SEPicker(Picker):
    def __init__(self, path: str) -> None:
        self.__path = path
        super().__init__()

    def _all_items(self):
        return glob('{}/*.raw'.format(self.__path))
