from cheroot import wsgi
from wsgidav.debug_filter import WsgiDavDebugFilter
from wsgidav.dir_browser import WsgiDavDirBrowser
from wsgidav.error_printer import ErrorPrinter
from wsgidav.http_authenticator import HTTPAuthenticator
from wsgidav.request_resolver import RequestResolver
from wsgidav.wsgidav_app import WsgiDAVApp

from . import CamacAuthenticator

# TODO remove
_use = HTTPAuthenticator


config = {
    "host": "0.0.0.0",
    "port": 8080,
    "provider_mapping": {
        "/": "/home/sonder",
    },
    "verbose": 1,
    "middleware_stack": [
        WsgiDavDebugFilter,
        ErrorPrinter,
        CamacAuthenticator,
        WsgiDavDirBrowser,
        RequestResolver,
    ],
}

app = WsgiDAVApp(config)

server_args = {
    "bind_addr": (config["host"], config["port"]),
    "wsgi_app": app,
}
server = wsgi.Server(**server_args)
server.start()
