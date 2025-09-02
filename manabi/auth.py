from functools import partial
from http.cookies import SimpleCookie
from pathlib import Path
from typing import Any, Callable, Dict, List
from unittest.mock import MagicMock

from wsgidav.mw.base_mw import BaseMiddleware

from .token import Config, State, Token
from .util import AppInfo, get_rfc1123_time, set_cookie

_error_message_403 = """
<html>
    <head><title>403 Forbidden</title></head>
    <body>
        <h1>403 Forbidden</h1>
        {0}
    </body>
</html>
""".strip()


class ManabiAuthenticator(BaseMiddleware):
    # Instead of accepting an override for HTTPAuthenticator as for everything else,
    # wsgidav just expects a class extending HTTPAuthenticator in the middleware_stack.
    # In it also accesses the domain_controller with out check if it exists in some debug code.
    # https://github.com/mar10/wsgidav/pull/204
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

    def access_denied(self, start_response: Callable, reason: str = "") -> List[bytes]:
        body = _error_message_403
        content = body.format(reason).encode("UTF-8")
        start_response(
            "403 Forbidden",
            [
                ("Content-Type", "text/html"),
                ("Content-Length", str(len(content))),
                ("Date", get_rfc1123_time()),
            ],
        )
        return [content]

    def update_env(self, info: AppInfo, token: Token, id_: str, dir_access: bool):
        environ = info.environ
        # Update the path for security, so we can't ever be tricked into serving a
        # path not authenticated by the token.
        path = token.path_as_url()
        environ["PATH_INFO"] = str(Path(path).parent) if dir_access else path
        environ["REQUEST_URI"] = path
        environ["manabi.path"] = path

        environ["wsgidav.auth.user_name"] = f"{path.strip('/')}|{id_[10:18]}"
        environ["manabi.token"] = token

    def refresh(
        self, id_: str, info: AppInfo, token: Token, ttl: int, dir_access: bool
    ):
        new = Token.from_token(token)
        self.update_env(info, token, id_, dir_access)
        return self.next_app(
            info.environ,
            partial(set_cookie, info, id_, new.encode(), ttl),
        )

    def __call__(
        self, environ: Dict[str, Any], start_response: Callable
    ) -> List[bytes]:
        """__call__ is the entry-point of a wsgi-middleware.

        The method checks if the token is valid, so wsgi-dav can serve the document.
        It also refreshes the token by setting a new token in a cookie.

        Middlewares and wsgi-handlers are identical. Middlewares need to wrap
        start_response with a closure, if they want to add headers.
        https://www.python.org/dev/peps/pep-3333/
        """
        info = AppInfo(start_response, environ, self.manabi_secure())
        config = Config.from_dictionary(environ["wsgidav.config"])
        path_info = environ["PATH_INFO"]
        id_, _, suffix = path_info.strip("/").partition("/")
        suffix = suffix.strip("/")
        # We need this in order to correctly set environ["PATH_INFO"]
        dir_access = suffix == ""
        if not id_:
            return self.access_denied(start_response, "no token supplied")
        initial = Token.from_ciphertext(config.key, id_)
        check = initial.check()

        if check == State.invalid:
            return self.access_denied(start_response, check.value[1])

        cookie = environ.get("HTTP_COOKIE")
        ttl = config.ttl.refresh
        if cookie:
            cookie = SimpleCookie(cookie)
            refresh_cookie = cookie.get(initial.ciphertext)
            if refresh_cookie and refresh_cookie.value:
                refresh = Token.from_ciphertext(config.key, refresh_cookie.value)
                if refresh.refresh(config.ttl) == State.valid:
                    return self.refresh(id_, info, refresh, ttl, dir_access)

        check = initial.initial(config.ttl)
        if initial.initial(config.ttl) == State.valid:
            return self.refresh(id_, info, initial, ttl, dir_access)
        return self.access_denied(start_response, check.value[1])
