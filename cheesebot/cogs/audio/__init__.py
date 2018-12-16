from glob import glob
from .. import CheeseCog, Picker

class SEPicker(Picker):
    def __init__(self, path: str) -> None:
        self.__path = path
        super().__init__()

    def _all_items(self):
        return glob('{}/*.raw'.format(self.__path))

from .cog import AudioCog
