from functools import partial
from http.cookies import SimpleCookie
from typing import Any, Callable, Dict, List
from unittest.mock import MagicMock

from wsgidav.middleware import BaseMiddleware  # type: ignore

from .token import Config, State, Token
from .util import AppInfo, get_rfc1123_time, set_cookie

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

    def refresh(self, id_, info, token):
        new = Token.from_token(token)
        return self.next_app(info.environ, partial(set_cookie, info, id_, new.encode()))

    def __call__(
        self, environ: Dict[str, Any], start_response: Callable
    ) -> List[bytes]:
        info = AppInfo(start_response, environ, self.manabi_secure())
        config = Config.from_dictionary(environ["wsgidav.config"])
        path_info = environ["PATH_INFO"]
        id_, _, _ = path_info.strip("/").partition("/")
        initial = Token.from_ciphertext(config.key, id_)

        if initial == State.invalid:
            return self.access_denied(start_response)

        cookie = environ.get("HTTP_COOKIE")
        if cookie:
            cookie = SimpleCookie(cookie)
            refresh = cookie.get(initial.ciphertext)
            if refresh and refresh.refresh(config.ttl) == State.valid:
                return self.refresh(id_, info, refresh)

        if initial.initial(config.ttl) == State.valid:
            return self.refresh(id_, info, initial)
        return self.access_denied(start_response)
