from email.utils import formatdate

import base62  # type: ignore


def get_rfc1123_time(secs: float = None) -> str:
    """Return <secs> in rfc 1123 date/time format (pass secs=None for current date)."""
    return formatdate(timeval=secs, localtime=False, usegmt=True)


def tostring(data: bytes) -> str:
    return base62.encodebytes(data)


def fromstring(data: str) -> bytes:
    return base62.decodebytes(data)
