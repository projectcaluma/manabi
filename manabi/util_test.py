from .util import from_string, to_string


def test_hello_world():
    hw = b"hello world"
    assert hw == from_string(to_string(hw))
