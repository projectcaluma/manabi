import calendar
import os
import threading
from datetime import UTC, datetime
from email.utils import formatdate
from http.cookies import SimpleCookie
from inspect import getsource
from typing import Any, Callable, Dict, List, Optional, Tuple, cast

import base62  # type: ignore
import boto3
import requests
from attr import attrib, dataclass

from .type_alias import TypeType

_local_session = threading.local()


def requests_session() -> requests.Session:
    """Wsgidav uses threading, lets get a session per thread."""
    local_dict = _local_session.__dict__
    session = local_dict.get("session")
    if not session:
        local_dict["session"] = session = requests.Session()
    return session


def cattrib(
    attrib_type: Optional[TypeType] = None,
    check: Optional[Callable] = None,
    optional: bool = False,
    **kwargs,
):
    if "default" in kwargs and kwargs["default"] is None:
        optional = True

    def handler(object, attribute, value):
        if value is None and optional:
            return value
        # Some python versions cannot do the check assume True
        is_inst = True
        try:
            if attrib_type is not None:
                is_inst = isinstance(value, attrib_type)
        except TypeError:
            pass
        if not is_inst:
            raise TypeError(
                f"{attribute.name} ({type(value)}) is not of type {attrib_type}"
            )
        if check and not check(value):
            source = getsource(check).strip()
            raise ValueError(f"check failed: {source}")
        return value

    return attrib(validator=handler, on_setattr=handler, **kwargs)


def get_rfc1123_time(secs: Optional[float] = None) -> str:
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
    date = datetime.now(UTC)
    unixtime = calendar.timegm(date.utctimetuple())
    cookie[key]["expires"] = get_rfc1123_time(unixtime + ttl)
    if info.secure:
        cookie[key]["secure"] = True
        cookie[key]["httponly"] = True
    headers.append(cast("Tuple[str, str]", tuple(str(cookie).split(": "))))
    info.start_response(status, headers, exc_info)


def get_boto_client(
    endpoint_url=None,
    aws_access_key_id=None,
    aws_secret_access_key=None,
    region_name=None,
):
    return boto3.client(
        "s3",
        endpoint_url=endpoint_url
        or os.environ.get("S3_ENDPOINT", "http://127.0.0.1:9000"),
        aws_access_key_id=aws_access_key_id
        or os.environ.get("S3_ACCESS_KEY_ID", "veryvery"),
        aws_secret_access_key=aws_secret_access_key
        or os.environ.get("S3_SECRET_ACCESS_KEY", "secretsecret"),
        region_name=region_name or os.environ.get("S3_REGION", "us-east-1"),
    )
