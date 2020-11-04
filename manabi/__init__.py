from functools import partial
from http.cookies import SimpleCookie

# from cryptography.fernet import Fernet
from wsgidav.middleware import BaseMiddleware

from .util import tostring


def set_cookie(start_response, secure, status, headers, exc_info=None):
    cookie = SimpleCookie()
    cookie["session"] = "this_session"
    if secure:
        cookie["session"]["secure"] = True
        cookie["session"]["httponly"] = True
    headers.append(str(cookie).split(": "))
    return start_response(status, headers, exc_info)


class ManabiAuthenticator(BaseMiddleware):
    def manabi_secure(self):
        config = self.config
        if "manabi" not in config:
            return True
        manabi = config["manabi"]
        if "secure" not in manabi:
            return True
        return manabi["secure"]

    def __call__(self, environ, start_response):
        print("hello middleware")

        if "HTTP_COOKIE" in environ:
            cookie = SimpleCookie(environ["HTTP_COOKIE"])
            if "session" in cookie:
                print("Sucess, cookie was stored")
                return self.next_app(environ, start_response)
        return self.next_app(
            environ, partial(set_cookie, start_response, self.manabi_secure())
        )


def keygen():
    with open("/dev/random", "rb") as f:
        print(tostring(f.read(32)))
