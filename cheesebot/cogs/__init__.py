from .. import Picker

class CheeseCog():
    def __init__(self, bot: 'cheesebot.CheeseBot') -> None:
        self.__bot = bot

    @property
    def bot(self):
        return self.__bot

from .audio import AudioCog
from .mention import MentionCog
from .factory import CogFactory
