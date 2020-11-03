import zlib

import base62


def tostring(data):
    return base62.encodebytes(data)


def fromstring(data):
    return base62.decodebytes(data)
