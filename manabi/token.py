from branca import Branca

from .util import fromstring


class Token:
    def __init__(self, config):
        self.key = config["manabi"]["key"]
        self.ttl_init = config["manabi"]["ttl_init"]
        self.ttl_refresh = config["manabi"]["ttl_refresh"]

    def make(self, path):
        return make_token(self.key, path)

    def check_ttl(self, data, ttl=None):
        try:
            return check_token(self.key, data, ttl)
        except (RuntimeError, ValueError):
            return False

    def check(self, data):
        return self.check_ttl(data, self.ttl_init)

    def refresh_check(self, data):
        return self.check_ttl(data, self.ttl_refresh)


def make_token(key, path, now=None):
    f = Branca(fromstring(key))
    p = path.encode("UTF-8")
    ct = f.encode(p, now)
    return ct


def check_token(key, data, ttl=None):
    f = Branca(fromstring(key))
    return f.decode(data, ttl).decode("UTF-8")
