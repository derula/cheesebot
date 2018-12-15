import discord
import asyncio
import audioop
import glob
import logging
import math
import random
import inspect
import io
import os
import signal
import threading

class CircularStream(io.BufferedReader):
    def read(self, size=-1):
        data = super().read(size)
        while len(data) < size:
            self.seek(0)
            data += super().read(size - len(data))
        return data

class MultiStream():
    def __init__(self):
        self.__streams = []

    def add_stream(self, stream, after: callable = None):
        self.__streams.append((stream, after))
        return self

    def read(self, size=-1):
        data = b'\x00' * size
        for item in self.__streams:
            stream, after = item
            sample = stream.read(size)

            # Close streams that have ended.
            if len(sample) < size:
                sample += b'\x00' * (size - len(sample))
                self.__streams.remove(item)
                if callable(after):
                    after()

            sample = audioop.mul(sample, 2, min(0.5, 1 / len(self.__streams)))
            data = audioop.add(data, sample, 2)

        return data

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
        to_remove = math.ceil(len(self.__last_used) - len(all_items) / 2)
        if to_remove > 0:
            self.__last_used = self.__last_used[to_remove:]

        item = random.choice(list(all_items.difference(self.__last_used)))

        # Don't play this sound effect again next time.
        self.__last_used.append(item)

        return item

class SEPlayer(threading.Thread):
    def __init__(self, stream: MultiStream, **kwargs):
        super().__init__(**kwargs)
        self.__stream = stream
        self.__resume = threading.Event()
        self.__dying = threading.Event()
        self.__picker = Picker(lambda: glob.glob('se/*.raw'))

        for sig in (signal.SIGTERM, signal.SIGHUP, signal.SIGINT):
            old_handler = signal.getsignal(sig)

            def stop(signo, _frame):
                self.__dying.set()
                self.__resume.set()
                if callable(old_handler):
                    old_handler()

            signal.signal(sig, stop)

    def __wait(self):
        self.__resume.wait()
        self.__resume.clear()
        return not self.__dying.is_set()

    def run(self):
        while not self.__dying.is_set():
            self.__do_run()

    def __do_run(self):
        threading.Timer(random.randint(10, 60), self.__resume.set).start()
        if not self.__wait():
            return

        se = self.__picker.pick()

        # If no sound effects found, try again next time.
        if se is None:
            return

        print('Playing {}'.format(se))
        with open(se, 'rb') as stream:
            self.__stream.add_stream(stream, self.__resume.set)
            if not self.__wait():
                return

async def setup_bgm() -> (discord.Channel, MultiStream):
    channel = None  # type: discord.Channel

    for server in client.servers:
        channel = discord.utils.find(
            lambda c: c.name.find('Ch\'sebur\'gah') >= 0 and
                      c.type is discord.ChannelType.voice,
            server.channels
        )
        if channel is not None:
            break

    if channel is None:
        return None

    voice_client = await client.join_voice_channel(channel)  # type: discord.VoiceClient
    assert isinstance(voice_client, discord.VoiceClient)

    try:
        blksize = os.stat('stream.raw').st_blksize
    except AttributeError:
        blksize = 4096

    audio = open('stream.raw', 'rb', 0)
    stream = MultiStream().add_stream(CircularStream(audio, 1000 * blksize))
    player = voice_client.create_stream_player(stream)  # type: discord.voice_client.StreamPlayer
    assert isinstance(player, discord.voice_client.StreamPlayer)
    player.start()

    return channel, stream

def load_phrases():
    phrases = []
    with open('phrases.txt', 'r') as f:
        for line in f:
            line = line.lstrip('\ufeff').strip()
            if len(line) > 0 and not line.startswith('#'):
                phrases.append(line)
    return phrases

client = discord.Client()

@client.event
async def on_ready():
    print('Logged in as {} (ID {})'.format(client.user, client.user.id))
    channel, stream = await setup_bgm()
    if channel is not None:
        print('Now playing spoopy music in {}'.format(channel.name))
        SEPlayer(stream).start()
    else:
        print('Ch\'sebur\'gah voice room not found.')

phrase_picker = Picker(load_phrases)

@client.event
async def on_message(message):
    if message.content.find(client.user.mention) >= 0:
        await client.send_message(message.channel, phrase_picker.pick())

client.run(os.environ.get('CHSEBURGAH_SECRET'))
