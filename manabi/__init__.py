from wsgidav import http_authenticator
from wsgidav.http_authenticator import HTTPAuthenticator
from wsgidav.wsgidav_app import WsgiDAVApp

from .auth import ManabiAuthenticator


class ManabiDAVApp(WsgiDAVApp):
    def __init__(self, config):
        super().__init__(config)
        self.lock_manager._lock = config["lock_storage"]._lock  # type: ignore


class MetaFakeHTTPAuthenticator(type(http_authenticator.HTTPAuthenticator)):  # type: ignore
    def __instancecheck__(cls, instance):
        return isinstance(instance, HTTPAuthenticator) or isinstance(
            instance, ManabiAuthenticator
        )


class FakeHTTPAuthenticator(
    http_authenticator.HTTPAuthenticator, metaclass=MetaFakeHTTPAuthenticator
):
    pass


# Instead of accepting an override for HTTPAuthenticator as for everything else, wsgidav
# just expects a class extending HTTPAuthenticator in the middleware_stack.
# wsgidav grabs that class out of the middleware_stack.
#
# Using a metaclass is slightly less intrusive than just replacing HTTPAuthenticator
# with ManabiAuthenticator. If http_authenticator.HTTPAuthenticator is created it is
# still a HTTPAuthenticator.
http_authenticator.HTTPAuthenticator = FakeHTTPAuthenticator  # type: ignore


def keygen() -> None:
    from .util import to_string

    with open("/dev/random", "rb") as f:
        print(to_string(f.read(32)))
