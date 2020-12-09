from wsgidav import http_authenticator  # type: ignore

from .auth import ManabiAuthenticator

# Workaround an ugly hack in wsgidav
http_authenticator.HTTPAuthenticator = ManabiAuthenticator


def keygen() -> None:
    from .util import to_string

    with open("/dev/random", "rb") as f:
        print(to_string(f.read(32)))
