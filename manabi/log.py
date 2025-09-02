from functools import partial
from typing import Any, Callable, Dict, List, Tuple

from wsgidav.mw.base_mw import BaseMiddleware
from wsgidav.util import SubAppStartResponse, get_module_logger, init_logging

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
                "lock_storage",
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


class ResponseLogger(BaseMiddleware):
    def __init__(self, application, next_app, config):
        self.__application = application
        self.next_app = next_app

    def __call__(self, environ, start_response):
        sub_app_start_response = SubAppStartResponse()
        first_yield = True
        app_iter = self.next_app(environ, sub_app_start_response)

        for v in app_iter:
            # Start response (the first time)
            if first_yield:
                # Success!
                start_response(
                    sub_app_start_response.status,
                    sub_app_start_response.response_headers,
                    sub_app_start_response.exc_info,
                )

            if environ["REQUEST_METHOD"] == "LOCK":
                _logger.debug(f"LOCK Response: {v.decode('utf-8')}")
            first_yield = False
            yield v

        if hasattr(app_iter, "close"):
            app_iter.close()

        # Start response (if it hasn't been done yet)
        if first_yield:
            # Success!
            start_response(
                sub_app_start_response.status,
                sub_app_start_response.response_headers,
                sub_app_start_response.exc_info,
            )
