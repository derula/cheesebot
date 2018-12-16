from random import randint
from signal import getsignal, signal, SIGTERM, SIGINT
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

        for sig in (SIGTERM, SIGINT):
            old_handler = getsignal(sig)

            def stop(signo, _frame):
                self.__dying.set()
                self.__resume.set()
                if callable(old_handler):
                    old_handler()

            signal(sig, stop)

    def __wait(self):
        self.__resume.wait()
        self.__resume.clear()
        return not self.__dying.is_set()

    def run(self):
        while not self.__dying.is_set():
            self.__do_run()

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
