from email.utils import formatdate
from hashlib import shake_128

import base62


def get_rfc1123_time(secs=None):
    """Return <secs> in rfc 1123 date/time format (pass secs=None for current date)."""
    # GC issue #20: time string must be locale independent
    return formatdate(timeval=secs, localtime=False, usegmt=True)


def tostring(data):
    return base62.encodebytes(data)


def fromstring(data):
    return base62.decodebytes(data)
