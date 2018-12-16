import os

from cheesebot import CheeseBot

CheeseBot('{}/data'.format(os.path.realpath(os.path.dirname(__file__)))).run()
