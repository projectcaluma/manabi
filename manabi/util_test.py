from typing import Callable

import pytest
from attr import dataclass

from .util import cattrib, from_string, to_string


def test_hello_world():
    hw = b"hello world"
    assert hw == from_string(to_string(hw))


@dataclass
class CallableClass:
    attr: Callable = cattrib(check=lambda x: callable(x))


def test_callable():
    with pytest.raises(ValueError):
        CallableClass(True)
    CallableClass(test_callable)
