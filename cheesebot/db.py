from functools import wraps
from threading import Lock, Timer
from typing import Union

from tinydb import TinyDB
from tinydb.middlewares import Middleware
from tinydb.storages import Storage

class LockingCachingMiddleware(Middleware):
    def __init__(self, storage_cls: Union[Middleware, Storage]=TinyDB.DEFAULT_STORAGE) -> None:
        super().__init__(storage_cls)
        self.__lock = Lock()
        self.__cache = None
        self.__flush_timer = None

    def read(self) -> dict:
        with self.__lock:
            if self.__cache is None:
                self.__cache = self.storage.read()
            return self.__cache

    def write(self, data: dict) -> None:
        old_data = self.__cache.copy()
        with self.__lock:
            # Poor man's deadlock detection
            assert old_data == self.__cache, 'Locking error, please retry.'
            self.__cache = data
            if not self.__flush_timer:
                self.__flush_timer = Timer(300, self.__flush)
                self.__flush_timer.start()

    def close(self) -> None:
        if self.__flush_timer:
            self.__flush_timer.cancel()
        self.__flush()
        with self.__lock:
            self.storage.close()

    def __flush(self) -> None:
        with self.__lock:
            self.storage.write(self.__cache)
            self.__flush_timer = None

class DB(TinyDB):
    def __init__(self, path: str) -> None:
        super().__init__(path, storage=LockingCachingMiddleware(TinyDB.DEFAULT_STORAGE))
