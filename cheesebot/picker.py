from math import ceil
from random import choice

class Picker():
    def __init__(self, all_items):
        self.__last_used = []
        self.__all_items = all_items

    def pick(self):
        all_items = set(self.__all_items())

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