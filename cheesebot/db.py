from functools import wraps
from threading import Lock
from typing import Union

from tinydb import TinyDB
from tinydb.middlewares import Middleware, CachingMiddleware
from tinydb.storages import Storage

class LockingMiddleware(Middleware):
    def __init__(self, storage_cls: Union[Middleware, Storage]=TinyDB.DEFAULT_STORAGE) -> None:
        super().__init__(storage_cls)
        self.__lock = Lock()

    def __getattr__(self, name: str):
        attr = super().__getattr__(name)
        if callable(attr):
            attr = self.__wrap(attr)
        return attr

    def __wrap(self, func: callable) -> callable:
        @wraps(func)
        def locking_func(*args, **kwargs):
            with self.__lock:
                return func(*args, *kwargs)
        return locking_func

class DB(TinyDB):
    def __init__(self, path: str) -> None:
        super().__init__(path, storage=LockingMiddleware(CachingMiddleware(TinyDB.DEFAULT_STORAGE)))
