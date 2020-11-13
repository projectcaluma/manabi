from email.utils import formatdate
from inspect import getsource

import base62  # type: ignore
from attr import attrib


def cattrib(attrib_type, check=None, **kwargs):
    none_is_ok = False
    if "default" in kwargs and kwargs["default"] is None:
        none_is_ok = True

    def handler(object, attribute, value):
        if not (value is None and none_is_ok):
            if not isinstance(value, attrib_type):
                raise TypeError(
                    f"{attribute.name} ({type(value)}) is not of type {attrib_type}"
                )
            if check and not check(value):
                source = getsource(check).strip()
                raise ValueError(f"check failed: {source}")
        return value

    return attrib(validator=handler, on_setattr=handler, **kwargs)


def get_rfc1123_time(secs: float = None) -> str:
    """Return <secs> in rfc 1123 date/time format (pass secs=None for current date)."""
    return formatdate(timeval=secs, localtime=False, usegmt=True)


def to_string(data: bytes) -> str:
    return base62.encodebytes(data)


def from_string(data: str) -> bytes:
    return base62.decodebytes(data)
