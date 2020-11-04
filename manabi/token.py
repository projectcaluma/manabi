import time

from branca import Branca

from .util import fromstring, short_hash


def make_token(key, path, now=None):
    f = Branca(fromstring(key))
    p = path.encode("UTF-8")
    ph = short_hash(p)
    if not now:
        now = int(time.time())
    ct = f.encode(ph, now)
    return ct


def check_token(key, data, path, ttl=None):
    f = Branca(fromstring(key))
    p = path.encode("UTF-8")
    ph = short_hash(p)
    return f.decode(data, ttl) == ph
