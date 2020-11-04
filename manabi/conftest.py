import shutil
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

from . import ManabiAuthenticator

_server = None
_server_dir = Path("/tmp/296fe33fcca")
_module_dir = Path(__file__).parent
_test_file = Path(_module_dir, "data", "asdf.docx")


def get_server_dir():
    if not _server_dir.exists():
        _server_dir.mkdir()
        shutil.copy(_test_file, _server_dir)

    return _server_dir


def get_config(server_dir):
    return {
        "host": "0.0.0.0",
        "port": 8080,
        "mount_path": "/dav",
        "provider_mapping": {
            "/": str(server_dir),
        },
        "verbose": 1,
        "middleware_stack": [
            WsgiDavDebugFilter,
            ErrorPrinter,
            ManabiAuthenticator,
            WsgiDavDirBrowser,
            RequestResolver,
        ],
        "manabi": {"key": "4BOzP21QBk7PrKsT0AGyAdNqrICDmw8NNDZknw3wqZv"},
    }


def get_server(config):
    global _server
    if not _server:
        dav_app = WsgiDAVApp(config)

        path_map = {
            # "/test": test_app,  # TODO web-server for test with a office-software
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


@pytest.fixture()
def server_dir():
    return get_server_dir()


@pytest.fixture()
def config(server_dir):
    return get_config(server_dir)


@pytest.fixture()
def server(config):
    global _server
    server = get_server(config)
    thread = Thread(target=partial(server.serve))
    thread.start()
    yield
    server.stop()
    thread.join()
    _server = None
