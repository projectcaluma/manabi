from wsgidav import http_authenticator  # type: ignore
from wsgidav.http_authenticator import HTTPAuthenticator  # type: ignore

from .auth import ManabiAuthenticator


class MetaFakeHTTPAuthenticator(type):
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
http_authenticator.HTTPAuthenticator = FakeHTTPAuthenticator


def keygen() -> None:
    from .util import to_string

    with open("/dev/random", "rb") as f:
        print(to_string(f.read(32)))
