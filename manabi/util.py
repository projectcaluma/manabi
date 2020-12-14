import calendar
from datetime import datetime
from email.utils import formatdate
from http.cookies import SimpleCookie
from inspect import getsource
from typing import Any, Callable, Dict, List, Optional, Tuple, cast

import base62  # type: ignore
from attr import attrib, dataclass


def cattrib(
    attrib_type: Optional[type] = None,
    check: Optional[Callable] = None,
    optional: bool = False,
    **kwargs,
):
    if "default" in kwargs and kwargs["default"] is None:
        optional = True

    def handler(object, attribute, value):
        if value is None and optional:
            return value
        if attrib_type is not None and not isinstance(value, attrib_type):
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


@dataclass
class AppInfo:
    start_response: Callable = cattrib(check=lambda x: callable(x))
    environ: Dict[str, Any] = cattrib(dict)
    secure: bool = cattrib(bool, default=True)


def set_cookie(
    info: AppInfo,
    key: str,
    value: str,
    ttl: int,
    status: int,
    headers: List[Tuple[str, str]],
    exc_info=None,
):
    cookie: SimpleCookie = SimpleCookie()
    cookie[key] = value
    date = datetime.utcnow()
    unixtime = calendar.timegm(date.utctimetuple())
    cookie[key]["expires"] = get_rfc1123_time(unixtime + ttl)
    if info.secure:
        cookie[key]["secure"] = True
        cookie[key]["httponly"] = True
    headers.append(cast(Tuple[str, str], tuple(str(cookie).split(": "))))
    info.start_response(status, headers, exc_info)
