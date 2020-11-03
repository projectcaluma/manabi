from functools import partial
from pathlib import Path
from threading import Thread

import pytest
from cheroot import wsgi
from wsgidav.debug_filter import WsgiDavDebugFilter
from wsgidav.dir_browser import WsgiDavDirBrowser
from wsgidav.error_printer import ErrorPrinter
from wsgidav.request_resolver import RequestResolver
from wsgidav.wsgidav_app import WsgiDAVApp

from . import CamacAuthenticator

_server = None
_server_dir = Path("/tmp/296fe33fcca")
module_dir = Path(__file__).parent


def get_server_dir():
    if not _server_dir.exists():
        _server_dir.mkdir()

    return _server_dir


def get_config(server_dir):
    return {
        "host": "0.0.0.0",
        "port": 8080,
        "provider_mapping": {
            "/": str(server_dir),
        },
        "verbose": 1,
        "middleware_stack": [
            WsgiDavDebugFilter,
            ErrorPrinter,
            CamacAuthenticator,
            WsgiDavDirBrowser,
            RequestResolver,
        ],
        "salt": "dc97559ff0199fe4b69bc1612296fe33fccaea04c27e9014250b726348eb197d",
    }


def get_server(config):
    global _server
    if not _server:
        dav_app = WsgiDAVApp(config)

        path_map = {
            "/mock": dav_app,
            "/dav": dav_app,
        }
        dispatch = wsgi.PathInfoDispatcher(path_map)
        server_args = {
            "bind_addr": (config["host"], config["port"]),
            "wsgi_app": dispatch,
        }

        _server = wsgi.Server(**server_args)
    return _server


def run_server(server):
    try:
        server.start()
    finally:
        server.stop()


@pytest.fixture()
def server_dir():
    return get_server_dir()


@pytest.fixture()
def config(server_dir):
    return get_config(server_dir)


@pytest.fixture()
def server(config):
    server = get_server(config)
    server.prepare()
    Thread(target=partial(server, run_server)).run()
    yield
    _server.interrupt = True
