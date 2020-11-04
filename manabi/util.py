from hashlib import shake_128

import base62


def tostring(data):
    return base62.encodebytes(data)


def fromstring(data):
    return base62.decodebytes(data)


def short_hash(data):
    h = shake_128()
    h.update(data)
    return h.digest(16)
