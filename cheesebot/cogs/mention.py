from tinydb import Query
from tinydb.database import Table

from . import CheeseCog
from .. import Picker

Phrase = Query()

class PhrasePicker(Picker):
    def __init__(self, table: Table) -> None:
        self.__table = table
        super().__init__()

    def _all_items(self):
        return map(lambda row: row['content'], self.__table.search(Phrase.language == 'odan'))

class MentionCog(CheeseCog):
    def __init__(self, bot: 'cheesebot.CheeseBot', phrase_picker: PhrasePicker):
        super().__init__(bot)
        self.__phrase_picker = phrase_picker

    async def on_message(self, message):
        if message.content.find(self.bot.user.mention) >= 0:
            await self.bot.send_message(message.channel, self.__phrase_picker.pick())
