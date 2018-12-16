from tinydb import TinyDB
from tinydb.storages import JSONStorage
from tinydb.middlewares import CachingMiddleware

class DB(TinyDB):
    def __init__(self, path: str) -> None:
        super().__init__(path, storage=CachingMiddleware(JSONStorage))