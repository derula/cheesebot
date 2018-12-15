from audioop import mul, add
from io import BufferedReader

class CircularStream(BufferedReader):
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

            sample = mul(sample, 2, min(0.5, 1 / len(self.__streams)))
            data = add(data, sample, 2)

        return data
