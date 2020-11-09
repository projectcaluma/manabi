import shutil
from subprocess import PIPE, run

import pytest  # type: ignore
from branca import Branca  # type: ignore
from hypothesis import assume, given  # type: ignore
from hypothesis.strategies import binary, booleans, text  # type: ignore

from . import mock
from .token import check_token, make_token
from .util import fromstring


def get_config() -> dict:
    return mock.get_config(mock.get_server_dir())


def token_roundtrip(tamper: bool, expire: bool, path: str):
    config = get_config()
    key = config["manabi"]["key"]
    ttl = None
    if expire:
        ttl = 1
        data = make_token(key, path, 1)
    else:
        data = make_token(key, path)
    if tamper:
        if data[3] == "f":
            data = data[0:3] + "g" + data[4:]
        else:
            data = data[0:3] + "f" + data[4:]
    if tamper or expire:
        with pytest.raises(RuntimeError):
            check_token(key, data, ttl)
    else:
        assert check_token(key, data, ttl) == path


@pytest.mark.parametrize("tamper", (True, False))
@pytest.mark.parametrize("expire", (True, False))
@pytest.mark.parametrize("path", ("hello", "asdf.docx"))
def test_token_roundtrip(tamper: bool, expire: bool, path: str):
    token_roundtrip(tamper, expire, path)


@given(booleans(), booleans(), text(min_size=1, max_size=32))
def test_token_roundtrip_hyp(tamper: bool, expire: bool, path: str):
    token_roundtrip(tamper, expire, path)


@given(binary(min_size=1, max_size=32))
def test_branca_roundtrip(string: bytes):
    config = get_config()
    key = config["manabi"]["key"]
    f = Branca(fromstring(key))
    res = f.decode(f.encode(string))
    assert res == string


def other_impl_decode(string: bytes):
    with mock.branca_impl():
        config = get_config()
        key = config["manabi"]["key"]
        f = Branca(fromstring(key))
        ct = f.encode(string)
        proc = run(["cargo", "run", "decode", key, ct], stdout=PIPE, check=True)
        assert fromstring(proc.stdout.decode("UTF-8")) == string


@pytest.mark.skipif(not shutil.which("cargo"), reason="needs rustc and cargo")
def test_other_impl_decode(cargo):
    other_impl_decode("hello world".encode("UTF-8"))


# TODO test binary data when branca-rust supports binary data:
# https://github.com/return/branca/issues/10
# hypothesis doesn't like fixtures anymore
@pytest.mark.skipif(not shutil.which("cargo"), reason="needs rustc and cargo")
@given(text(min_size=1))
def test_other_impl_decode_hyp(cargo, string: str):
    bstr = string.encode("UTF-8")
    assume(not bstr.startswith(b"\x00"))
    other_impl_decode(bstr)
