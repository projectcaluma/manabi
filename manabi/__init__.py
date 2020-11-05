from wsgidav import http_authenticator

from .auth import ManabiAuthenticator

# Workaround an ugly hack in wsgidav
http_authenticator.HTTPAuthenticator = ManabiAuthenticator


def keygen():
    from .util import tostring

    with open("/dev/random", "rb") as f:
        print(tostring(f.read(32)))


def setup_log():
    from wsgidav.util import init_logging

    from .mock import get_config, get_server_dir

    config = get_config(get_server_dir())
    init_logging(config)


setup_log()
