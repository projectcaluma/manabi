from .util import fromstring, tostring


def test_hello_world():
    hw = b"hello world"
    assert hw == fromstring(tostring(hw))
