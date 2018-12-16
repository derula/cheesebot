import os

from cheesebot import CheeseBot
from cheesebot.cogs import MentionCog, AudioCog

bot = CheeseBot('{}/data'.format(os.path.realpath(os.path.dirname(__file__))))
bot.add_cog(MentionCog)
bot.add_cog(AudioCog)
bot.run()
