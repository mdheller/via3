from contextlib import contextmanager
from datetime import datetime


@contextmanager
def timeit(message):
    start = datetime.utcnow()
    yield
    diff = datetime.utcnow() - start
    diff = diff.seconds * 1000 + diff.microseconds / 1000

    print(f"{diff}ms {message}")
