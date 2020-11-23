import os
import shutil
from contextlib import contextmanager
from functools import partial
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from cheroot import wsgi  # type: ignore
from wsgidav.debug_filter import WsgiDavDebugFilter  # type: ignore
from wsgidav.dir_browser import WsgiDavDirBrowser  # type: ignore
from wsgidav.error_printer import ErrorPrinter  # type: ignore
from wsgidav.request_resolver import RequestResolver  # type: ignore
from wsgidav.wsgidav_app import WsgiDAVApp  # type: ignore

from .auth import ManabiAuthenticator
from .filesystem import ManabiProvider
from .token import Key, Token
from .util import get_rfc1123_time

_server: Optional[wsgi.Server] = None
_server_dir = Path("/tmp/296fe33fcca")
_module_dir = Path(__file__).parent
_test_file1 = Path(_module_dir, "data", "asdf.docx")
_test_file2 = Path(_module_dir, "data", "qwert.docx")


def get_server_dir():
    if not _server_dir.exists():
        _server_dir.mkdir()
        shutil.copy(_test_file1, _server_dir)
        shutil.copy(_test_file2, _server_dir)

    return _server_dir


def get_config(server_dir: Path):
    return {
        "host": "0.0.0.0",
        "port": 8080,
        "mount_path": "/dav",
        "provider_mapping": {
            "/": ManabiProvider(server_dir),
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
            "refresh": 600,
            "initial": 600,
            "base_url": "localhost:8080",
        },
    }


def serve_document(
    config: Dict[str, Any], environ: Dict[str, Any], start_response: Callable
):
    key = Key.from_dictionary(config)
    path1 = Path("asdf.docx")
    url1 = Token(key, path1).as_url()
    path2 = Path("nope.docx")
    url2 = Token(key, path2).as_url()
    base = config["manabi"]["base_url"]
    body = f"""
<!doctype html>

<html lang="en">
<head>
  <meta charset="utf-8">

  <title>WebDAV test page</title>
</head>

<body>
    <h1>existing</h1>
    <h2>word link</h2>
    <a href="ms-word:ofe|u|http://{base}/dav/{url1}">{path1}</a>
    <h2>webdav link</h2>
    <a href="webdav://{base}/dav/{url1}">{path1}</a>
    <h2>http link</h2>
    <a href="http://{base}/dav/{url1}">{path1}</a>
    <h1>non-existing</h1>
    <h2>word link</h2>
    <a href="ms-word:ofe|u|http://{base}/dav/{url2}">{path2}</a>
    <h2>webdav link</h2>
    <a href="webdav://{base}/dav/{url2}">{path2}</a>
    <h2>http link</h2>
    <a href="http://{base}/dav/{url2}">{path2}</a>
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


def get_server(config: Dict[str, Any]):
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
