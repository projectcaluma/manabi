from cheroot import wsgi
from wsgidav.wsgidav_app import WsgiDAVApp

config = {
    "host": "0.0.0.0",
    "port": 8080,
    "provider_mapping": {
        "/": "/home/sonder",
    },
    "verbose": 1,
    "simple_dc": {"user_mapping": {"*": True}},
}

app = WsgiDAVApp(config)

server_args = {
    "bind_addr": (config["host"], config["port"]),
    "wsgi_app": app,
}
server = wsgi.Server(**server_args)
server.start()
