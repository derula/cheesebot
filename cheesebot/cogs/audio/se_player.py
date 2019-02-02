from random import randint
from threading import Thread, Event, Timer

from . import SEPicker
from .streams import MultiStream

class SEPlayer(Thread):
    def __init__(self, stream: MultiStream, picker: SEPicker):
        super().__init__()
        self.__stream = stream
        self.__resume = Event()
        self.__dying = Event()
        self.__picker = picker

    def run(self):
        while not self.__dying.is_set():
            self.__do_run()

    def shutdown(self, signal: int) -> None:
        self.__dying.set()
        self.__resume.set()

    def __do_run(self):
        Timer(randint(10, 60), self.__resume.set).start()
        if not self.__wait():
            return

        se = self.__picker.pick()

        # If no sound effects found, try again next time.
        if se is None:
            return

        with open(se, 'rb') as stream:
            self.__stream.add_stream(stream, self.__resume.set)
            if not self.__wait():
                return

    def __wait(self):
        self.__resume.wait()
        self.__resume.clear()
        return not self.__dying.is_set()
