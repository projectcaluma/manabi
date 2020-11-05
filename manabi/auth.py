from collections import namedtuple
from email.utils import formatdate
from functools import partial
from http.cookies import SimpleCookie

from wsgidav.middleware import BaseMiddleware

from .token import Token

CookieInfo = namedtuple("CookieInfo", ("start_response", "secure", "path", "token"))

_error_message_403 = """
<html>
    <head><title>403 Forbidden</title></head>
    <body>
        <h1>403 Forbidden</h1>
    </body>
</html>
""".strip()


def get_rfc1123_time(secs=None):
    """Return <secs> in rfc 1123 date/time format (pass secs=None for current date)."""
    # GC issue #20: time string must be locale independent
    return formatdate(timeval=secs, localtime=False, usegmt=True)


def set_cookie(info, status, headers, exc_info=None):
    path = info.path
    cookie = SimpleCookie()
    cookie[info.path] = info.token
    # TODO expire ttl_refresh * 2
    # TODO lock_refresh = ttl_refresh
    if info.secure:
        cookie[path]["secure"] = True
        cookie[path]["httponly"] = True
    headers.append(str(cookie).split(": "))
    return info.start_response(status, headers, exc_info)


class ManabiAuthenticator(BaseMiddleware):
    def manabi_secure(self):
        config = self.config
        if "manabi" not in config:
            return True
        manabi = config["manabi"]
        if "secure" not in manabi:
            return True
        return manabi["secure"]

    def access_denied(self, start_response):
        body = _error_message_403.encode("UTF-8")
        start_response(
            "403 Forbidden",
            [
                ("Content-Type", "text/html"),
                ("Content-Length", str(len(body))),
                ("Date", get_rfc1123_time()),
            ],
        )
        return [body]

    def fix_environ(self, environ, token):
        repl = f"/{token}"
        for var in ("REQUEST_URI", "PATH_INFO"):
            environ[var] = environ[var].replace(repl, "")

    def __call__(self, environ, start_response):
        path_info = environ["PATH_INFO"]
        token, _, path = path_info.strip("/").partition("/")
        cookie = None
        if "HTTP_COOKIE" in environ:
            cookie = SimpleCookie(environ["HTTP_COOKIE"])
        if not path:
            path = token.strip("/")
            if cookie:
                token = cookie.get(path)

        if not (token and path):
            return self.access_denied(start_response)

        t = Token(environ["wsgidav.config"])

        check = t.check(token, path)
        if not check:
            if cookie:
                token = cookie.get(path)
                check = t.refresh_check(token, path)

        if not check:
            return self.access_denied(start_response)

        self.fix_environ(environ, token)
        token = t.make(path)
        info = CookieInfo(start_response, self.manabi_secure(), path, token)
        return self.next_app(environ, partial(set_cookie, info))
