from functools import partial
from typing import Any, Callable, Dict, List, Tuple

from wsgidav.middleware import BaseMiddleware  # type: ignore
from wsgidav.util import get_module_logger, init_logging  # type: ignore

_logger = get_module_logger(__name__)


class HeaderLogger(BaseMiddleware):
    def logger(
        self,
        environ: Dict[str, Any],
        start_response: Callable,
        status: int,
        headers: List[Tuple[str, str]],
        exc_info=None,
    ):
        _logger.debug(f"Request environ: {environ}")
        _logger.debug(f"Response headers: {dict(headers)}")
        return start_response(status, headers, exc_info)

    def __call__(
        self, environ: Dict[str, Any], start_response: Callable
    ) -> List[bytes]:
        return self.next_app(environ, partial(self.logger, environ, start_response))


def verbose_logging() -> None:
    # Enable everything that seems like module that could have logging
    init_logging(
        {
            "verbose": 5,
            "enable_loggers": [
                "manabi.log",
                "manabi.lock",
                "lock_manager",
                "lock_storage",
                "request_resolver",
                "request_server",
                "http_authenticator",
                "property_manager",
                "fs_dav_provider",
                "dir_browser",
                "server",
            ],
        }
    )
