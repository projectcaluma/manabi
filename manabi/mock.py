import os
import shutil
from contextlib import contextmanager
from functools import partial
from pathlib import Path
from typing import Any, Callable, Dict

from cheroot import wsgi  # type: ignore
from wsgidav.debug_filter import WsgiDavDebugFilter  # type: ignore
from wsgidav.dir_browser import WsgiDavDirBrowser  # type: ignore
from wsgidav.error_printer import ErrorPrinter  # type: ignore
from wsgidav.request_resolver import RequestResolver  # type: ignore
from wsgidav.wsgidav_app import WsgiDAVApp  # type: ignore

from .auth import ManabiAuthenticator
from .token import Token
from .util import get_rfc1123_time

_server = None
_server_dir = Path("/tmp/296fe33fcca")
_module_dir = Path(__file__).parent
_test_file = Path(_module_dir, "data", "asdf.docx")


def get_server_dir():
    if not _server_dir.exists():
        _server_dir.mkdir()
        shutil.copy(_test_file, _server_dir)

    return _server_dir


def get_config(server_dir: Path):
    return {
        "host": "0.0.0.0",
        "port": 8080,
        "mount_path": "/dav",
        "provider_mapping": {
            "/": str(server_dir),
        },
        "verbose": 5,
        "middleware_stack": [
            WsgiDavDebugFilter,
            ErrorPrinter,
            ManabiAuthenticator,
            WsgiDavDirBrowser,
            RequestResolver,
        ],
        "enable_loggers": ["lock_manager", "request_resolver"],
        "manabi": {
            "key": "ur7Q80cCgjDsrciXbuRKLF83xqWDdzGhXaPwpwz7boG",
            "ttl_refresh": 600,
            "ttl_init": 600,
        },
    }


def serve_document(config: dict, environ: Dict[str, Any], start_response: Callable):
    path = "asdf.docx"
    token = Token.from_config(config).make(path)
    body = f"""
<!doctype html>

<html lang="en">
<head>
  <meta charset="utf-8">

  <title>WebDAV test page</title>
</head>

<body>
    <a href="ms-word:ofe|u|http://192.168.1.11:8080/dav/{token}/{path}">asdf.docx</a>
</body>
</html>
""".strip().encode(
        "UTF-8"
    )

    start_response(
        "200 Ok",
        [
            ("Content-Type", "text/html"),
            ("Content-Length", str(len(body))),
            ("Date", get_rfc1123_time()),
        ],
    )
    return [body]


def get_server(config):
    global _server
    if not _server:
        dav_app = WsgiDAVApp(config)

        path_map = {
            "/test": partial(serve_document, config),
            "/dav": dav_app,
        }
        dispatch = wsgi.PathInfoDispatcher(path_map)
        server_args = {
            "bind_addr": (config["host"], config["port"]),
            "wsgi_app": dispatch,
        }

        _server = wsgi.Server(**server_args)
        _server.prepare()
    return _server


@contextmanager
def branca_impl():
    cwd = Path().cwd()
    os.chdir(Path(_module_dir.parent, "branca-test"))
    yield
    os.chdir(cwd)
