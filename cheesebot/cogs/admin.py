from collections import defaultdict
import re
from typing import Optional

from discord.ext.commands import command, Context
from tinydb import Query, operations

from . import CheeseCog
from .. import DB

q = Query()
_dict_parse_error = {'__error': RuntimeError}
_value = r'(str|int|list)\(([^)]*)\)'
_config_unset = RuntimeError

def _split_key_value(value):
    pair = value.split('=', 2)
    return pair[0], Value(pair[1]).value

class Value():
    __re_value = re.compile(_value)
    __re_guess_list = re.compile(r'\w+(,\w+)+')
    __re_guess_int = re.compile(r'\d+')

    def __init__(self, string: str) -> None:
        match = Value.__re_value.fullmatch(string)
        match = match and (match.group(1), match.group(2)) or (self.guess_type(string), string)
        callback = {'str': str, 'int': int, 'list': self.listify}[match[0]]
        self.value = callback(match[1])

    def guess_type(self, string: str) -> str:
        if Value.__re_guess_list.fullmatch(string):
            return 'list'
        elif Value.__re_guess_int.fullmatch(string):
            return 'int'
        return 'str'

    def listify(self, string: str) -> list:
        return string.split(',')

    def __str__(self):
        return str(self.value)

class StrDict(dict):
    __scanner = re.Scanner([(r'\w+=(?:[^ ]*|{})(?: +|$)'.format(_value), lambda a, v: _split_key_value(v))])

    def __init__(self, string: str) -> None:
        try:
            scan = StrDict.__scanner.scan(string)
            if scan[1]:
                raise RuntimeError()
            res = scan[0]
            super().__init__(res)
        except:
            super().__init__(_dict_parse_error)

class AdminCog(CheeseCog):
    __meta = {
        'config': {
            'required': ['level_min'],
            'unique': ['level_min'],
        },
        'phrases': {
            'required': ['content', 'set'],
            'unique': ['content']
        }
    }

    @command()
    async def db_inspect(self, table: str = None, *, where: StrDict = StrDict('')) -> None:
        query = await self.__get_query(table, where)
        if query is None:
            return
        rows = self.bot.db.table(table).search(query)
        footer = ''
        if len(rows) > 5:
            footer = '\n(Showing top 5 results out of {})'.format(len(rows))
            rows = rows[:5]
        if not len(rows):
            await self.bot.say('No matches found in table `{}`'.format(table))
            return
        await self.bot.say('```{}```{}'.format('\n\n'.join(
            '\n'.join('{}:\n    {}'.format(k, v) for k, v in row.items()) for row in rows
        ), footer))

    @command()
    async def db_update(self, table: str, operation: str, column: str, value: Value = None, *, where: StrDict = StrDict('')) -> None:
        query = await self.__get_query(table, where)
        if query is None:
            return
        try:
            assert operation[0] != '_'
            operation = getattr(operations, operation)
        except:
            all_ops = filter(lambda op: op[0] != '_', dir(operations))
            await self.bot.say('Invalid operation `{}`. Expected:\n`{}`'.format(operation, '`, `'.join(all_ops)))
            return

        args = value and (column, value.value) or (column,)
        try:
            ids = self.bot.db.table(table).update(operation(*args), query)
        except:
            await self.bot.say('Oops! Something went wrong!\nNote that some operations don\'t expect a value.')
            return
        await self.bot.say('{} records in `{}` have been updated.'.format(len(ids), table))

    @command()
    async def config_get(self, key: str, level: int = 0) -> None:
        value = self.bot.config.at_level(level).get(key, _config_unset)
        if value is _config_unset:
            await self.bot.say('Config `{}` not defined for level {} or below.'.format(key, level))
            return

        await self.bot.say('Effective value for config `{}` at level {}: `{}`'.format(key, level, value))

    @command()
    async def config_set(self, key: str, value: Value, level: int = 0) -> None:
        try:
            self.bot.config.at_level(level)[key] = value.value
        except:
            await self.bot.say('Failed setting config `{}` to `{}` for level {} and up.'.format(key, value, level))
            return

        await self.bot.say('Effective value for config `{}` at level {} set to: `{}`'.format(key, level, value))

    async def __get_query(self, table: str, where: StrDict) -> Optional[list]:
        all_tables = filter(lambda s: s[0] != '_', self.bot.db.tables())
        if table is None:
            await self.bot.say('The following tables are available:\n`{}`'.format('`, `'.join(all_tables)))
            return
        if table not in all_tables:
            await self.bot.say('Table `{}` doesn\'t exist.'.format(table))
            return
        if where == _dict_parse_error:
            await self.bot.say(
                'Invalid where condition. Expected:\n```{}db_* ̇{} key1=value1 key2=value2 ...```'
                .format(self.bot.command_prefix, table)
            )
            return
        query = q
        for k, v in where.items():
            query &= q[k] == v
        return query
