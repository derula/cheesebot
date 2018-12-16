from .. import CheeseBot, Picker
from .audio import SEPicker, AudioCog
from .mention import PhrasePicker, MentionCog

class CheeseCog():
    def __init__(self, bot: CheeseBot) -> None:
        self.__bot = bot

    @property
    def bot(self):
        return self.__bot
