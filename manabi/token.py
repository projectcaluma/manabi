from branca import Branca

from .util import fromstring, short_hash


class Token:
    def __init__(self, config):
        self.key = config["manabi"]["key"]
        self.ttl_init = config["manabi"]["ttl_init"]
        self.ttl_refresh = config["manabi"]["ttl_refresh"]

    def make(self, path):
        return make_token(self.key, path)

    def check_ttl(self, data, path=None, ttl=None):
        try:
            if path is None:
                check_token(self.key, data, "", ttl)
                return True
            else:
                return check_token(self.key, data, path, ttl)
        except (RuntimeError, ValueError):
            return False

    def check(self, data, path=None):
        return self.check_ttl(data, path, self.ttl_init)

    def refresh_check(self, data, path=None):
        return self.check_ttl(data, path, self.ttl_refresh)


def make_token(key, path, now=None):
    f = Branca(fromstring(key))
    p = path.encode("UTF-8")
    ph = short_hash(p)
    ct = f.encode(ph, now)
    return ct


def check_token(key, data, path, ttl=None):
    f = Branca(fromstring(key))
    p = path.encode("UTF-8")
    ph = short_hash(p)
    return f.decode(data, ttl) == ph
