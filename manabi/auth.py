import calendar
from datetime import datetime
from functools import partial
from http.cookies import SimpleCookie
from typing import Any, Callable, Dict, List, Tuple, cast
from unittest.mock import MagicMock

from attr import dataclass
from wsgidav.middleware import BaseMiddleware  # type: ignore

from .token import Token
from .util import get_rfc1123_time


@dataclass
class CookieInfo:
    start_response: Callable
    secure: bool
    path: str
    token: str
    ttl: int


_error_message_403 = """
<html>
    <head><title>403 Forbidden</title></head>
    <body>
        <h1>403 Forbidden</h1>
    </body>
</html>
""".strip().encode(
    "UTF-8"
)


def set_cookie(
    info: CookieInfo, status: int, headers: List[Tuple[str, str]], exc_info=None
) -> None:
    path = info.path
    cookie: SimpleCookie = SimpleCookie()
    cookie[path] = info.token
    date = datetime.utcnow()
    unixtime = calendar.timegm(date.utctimetuple())
    cookie[path]["expires"] = get_rfc1123_time(unixtime + info.ttl)
    # TODO set locktimeout
    if info.secure:
        cookie[path]["secure"] = True
        cookie[path]["httponly"] = True
    entry = cast(Tuple[str, str], str(cookie).split(": "))
    headers.append(entry)
    info.start_response(status, headers, exc_info)


class ManabiAuthenticator(BaseMiddleware):
    def get_domain_controller(self) -> Any:
        return MagicMock()

    def manabi_secure(self) -> bool:
        config = self.config
        if "manabi" not in config:
            return True
        manabi = config["manabi"]
        if "secure" not in manabi:
            return True
        return manabi["secure"]

    def access_denied(self, start_response: Callable) -> List[bytes]:
        body = _error_message_403
        start_response(
            "403 Forbidden",
            [
                ("Content-Type", "text/html"),
                ("Content-Length", str(len(body))),
                ("Date", get_rfc1123_time()),
            ],
        )
        return [body]

    def fix_environ(self, environ: Dict[str, Any], token: str, path: str) -> None:
        environ["wsgidav.auth.user_name"] = f"{path}|{token[10:14]}"
        repl = f"/{token}"
        for var in ("REQUEST_URI", "PATH_INFO"):
            environ[var] = environ[var].replace(repl, "")

    def __call__(
        self, environ: Dict[str, Any], start_response: Callable
    ) -> List[bytes]:
        path_info = environ["PATH_INFO"]
        token, _, path = path_info.strip("/").partition("/")

        cookie = None
        if "HTTP_COOKIE" in environ:
            cookie = SimpleCookie(environ["HTTP_COOKIE"])

        if not path:
            return self.access_denied(start_response)
        else:
            config = environ["wsgidav.config"]
            t = Token(config)
            # A file-access
            check_path = t.check(token)
            if check_path != path and cookie:
                check_path = t.refresh_check(token)

            if check_path != path:
                return self.access_denied(start_response)
            self.fix_environ(environ, token, path)
            token = t.make(path)
            info = CookieInfo(
                start_response,
                self.manabi_secure(),
                path,
                token,
                int(config["manabi"]["ttl_refresh"]),
            )
            return self.next_app(environ, partial(set_cookie, info))
