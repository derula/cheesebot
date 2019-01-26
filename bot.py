import os

from cheesebot import CheeseBot
from cheesebot.cogs import MentionCog, AudioCog, AdminCog

bot = CheeseBot('{}/data'.format(os.path.realpath(os.path.dirname(__file__))))
bot.add_cog(MentionCog)
bot.add_cog(AudioCog)
bot.add_cog(AdminCog)
bot.run()
