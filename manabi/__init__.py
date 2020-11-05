from .util import tostring


def keygen():
    with open("/dev/random", "rb") as f:
        print(tostring(f.read(32)))
