from collections import defaultdict
import re
from typing import Optional

from discord.ext.commands import Command, command, Context
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

class AdminCommand(Command):
    @property
    def cog_name(self) -> str:
        for cls in self.instance.__class__.__mro__[1:]:
            if hasattr(cls, self.callback.__name__):
                return cls.__name__

        return super().cog_name()

def _admin_command(func):
    return command(cls=AdminCommand)(func)

class Maintenance(CheeseCog):
    @_admin_command
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

    @_admin_command
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

class Configuration(CheeseCog):
    @_admin_command
    async def config_get(self, key: str, level: int = 0) -> None:
        value = self.bot.config.at_level(level).get(key, _config_unset)
        if value is _config_unset:
            await self.bot.say('Config `{}` not defined for level {} or below.'.format(key, level))
            return

        await self.bot.say('Effective value for config `{}` at level {}: `{}`'.format(key, level, value))

    @_admin_command
    async def config_set(self, key: str, value: Value, level: int = 0) -> None:
        try:
            self.bot.config.at_level(level)[key] = value.value
        except:
            await self.bot.say('Failed setting config `{}` to `{}` for level {} and up.'.format(key, value, level))
            return

        await self.bot.say('Effective value for config `{}` at level {} set to: `{}`'.format(key, level, value))

class Phrases(CheeseCog):
    @_admin_command
    async def phrase_add(self, set_name: str, content: str, notes: str = None) -> None:
        table = self.bot.db.table('phrases')
        existing = table.get(q.content == content)
        if existing:
            await self.bot.say('Phrase already exists in set `{}`! Be a little more creative :)'.format(existing['set']))
            return

        table.insert({'set': set_name, 'content': content, 'notes': notes})
        await self.bot.say('Added the phrase to set `{}`.'.format(set_name))

    @_admin_command
    async def phrase_move(self, content: str, set_name: str) -> None:
        if not self.bot.db.table('phrases').update({'set': set_name}, q.content == content):
            await self.bot.say('Phrase could _not_ be moved to set `{}`.'.format(set_name))
            return

        await self.bot.say('Phrase was successfully moved to set `{}`.'.format(set_name))

    @_admin_command
    async def phrase_annotate(self, content: str, notes: str) -> None:
        if not self.bot.db.table('phrases').update({'notes': notes}, q.content == content):
            await self.bot.say('Notes could _not_ be set for the given phrase.')
            return

        await self.bot.say('Notes were successfully set for the given phrase.')

    @_admin_command
    async def phrase_remove(self, content: str) -> None:
        if not self.bot.db.table('phrases').remove(q.content == content):
            await self.bot.say('Phrase could _not_ be removed.')
            return

        await self.bot.say('Phrase was successfully removed.')

    @_admin_command
    async def phrase_info(self, content: str) -> None:
        info = self.bot.db.table('phrases').get(q.content == content)
        if not info:
            await self.bot.say('The given phrase doesn\'t exist in any phrase set.')
            return

        await self.bot.say('The given phrase is part of the phrase set `{}`.{}'.format(
            info['set'], info['notes'] and '\nThe following notes were provided:\n```̇{}```'.format(info['notes']) or ''
        ))

    @_admin_command
    async def phrase_set_move(self, old_name: str, new_name: str) -> None:
        ids = self.bot.db.table('phrases').update({'set': new_name}, q.set == old_name)

        await self.bot.say('{} phrases were moved from step `{}` to step `{}`.'.format(len(ids), old_name, new_name))

    @_admin_command
    async def phrase_set_remove(self, set_name: str) -> None:
        ids = self.bot.db.table('phrases').remove(q.set == set_name)

        await self.bot.say('{} phrase were removed from step `{}`.'.format(len(ids), set_name))

class AdminCog(Maintenance, Configuration, Phrases):
    pass
