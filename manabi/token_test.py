from subprocess import PIPE, run

import pytest
from branca import Branca
from hypothesis import given
from hypothesis.strategies import text

from .conftest import branca_impl
from .token import check_token, make_token
from .util import fromstring


@pytest.mark.parametrize("tamper", (True, False))
@pytest.mark.parametrize("expire", (True, False))
@pytest.mark.parametrize("path", (True, False))
def test_make_token(tamper, expire, path, config):
    key = config["manabi"]["key"]
    ttl = None
    path = "asdf.docx"
    check = True
    if expire:
        ttl = 1
        check = False
        data = make_token(key, path, 1)
    else:
        data = make_token(key, path)
    if tamper:
        data = data[0:3] + "f" + data[4:]
    if tamper or expire:
        with pytest.raises(RuntimeError):
            check_token(key, data, path, ttl)
    else:
        assert check_token(key, data, path, ttl) == check


@given(text(min_size=1, max_size=32))
def test_other_impl_decode(config, string):
    with branca_impl():
        string = string.encode("UTF-8")
        key = config["manabi"]["key"]
        f = Branca(fromstring(key))
        ct = f.encode(string)
        proc = run(["cargo", "run", "decode", key, ct], stdout=PIPE, check=True)
        assert proc.stdout == string
