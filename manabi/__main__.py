if __name__ == "__main__":
    # This needs dev-requirements
    from wsgidav import http_authenticator
    from wsgidav.util import init_logging

    from .auth import ManabiAuthenticator

    # Workaround an ugly hack in wsgidav
    http_authenticator.HTTPAuthenticator = ManabiAuthenticator

    from .mock import get_config, get_server, get_server_dir

    config = get_config(get_server_dir())
    init_logging(config)
    config["manabi"]["secure"] = False
    server = get_server(config)
    server.serve()
