import shutil
from pathlib import Path
from subprocess import PIPE, run
from time import sleep

import pytest
from branca import Branca  # type: ignore
from hypothesis import assume, given  # type: ignore
from hypothesis.strategies import binary, booleans, text  # type: ignore

from . import mock
from .token import TTL, Config, Key, State, Token, _decode, _encode, now
from .util import from_string

_key = b"\xef\xc5\x07\xee}\x7f6\x11L\xb0\xc3155x\x11\xce.\x8e\xb96\xba\xce\x8b\x17-\xfc\x96]\xf8%\xd8"


def test_key_validator(config):
    key = Key.from_dictionary(config)
    assert len(key.data) == 32
    with pytest.raises(TypeError):
        key.data = "huhu"
    with pytest.raises(ValueError):
        key.data = b"huhu"


def test_ttl_validator(config):
    ttl = TTL.from_dictionary(config)
    assert ttl.initial == 600
    with pytest.raises(TypeError):
        ttl.initial = "huhu"
    assert ttl.initial == 600


def test_config_validator(config):
    cfg = Config.from_dictionary(config)
    assert cfg.key.data == _key
    assert cfg.ttl.initial == 600
    assert cfg.ttl.refresh == 600
    with pytest.raises(TypeError):
        cfg.key = "huhu"


def test_token_creation(config):
    cfg = Config.from_dictionary(config)
    path = Path("asdf.docx")
    token = Token(cfg.key, path)

    assert token.key.data == _key
    assert token.check(path) == State.valid
    assert token.check(path, 10) == State.valid
    assert token.check(path, -10) == State.expired

    # Is it still
    ct = token.encode()
    assert token.check(path, 10) == State.valid
    assert token.check(path, -10) == State.expired
    assert token.check(path) == State.valid

    token2 = Token.from_ciphertext(cfg.key, ct)
    assert token2.check(path) == State.valid
    assert token2.check("huh") == State.intact
    assert token2.check(path, 10) == State.valid
    assert token2.check("huh", 10) == State.intact
    assert token2.check(path, -10) == State.expired
    assert token2.check("huh", -10) == State.intact
    assert token2.timestamp < now() + 10
    assert token2.timestamp > now() - 10
    assert token2.initial(path, cfg.ttl) == State.valid
    assert token2.refresh(path, cfg.ttl) == State.valid

    # Testing refresh
    tokenN = Token.from_token(token2)
    ct2 = tokenN.encode()
    assert ct != ct2
    token22 = Token.from_ciphertext(cfg.key, ct2)
    assert token22.check(path) == State.valid
    assert token22.check("huh") == State.intact
    assert token22.check(path, 10) == State.valid
    assert token22.check("huh", 10) == State.intact
    assert token22.check(path, -10) == State.expired
    assert token22.check("huh", -10) == State.intact
    assert token22.timestamp < now() + 10
    assert token22.timestamp > now() - 10

    token3 = Token(cfg.key)
    assert token3.check(path) == State.invalid
    assert token3.check("huh") == State.invalid
    assert token3.check(path, 10) == State.invalid
    assert token3.check("huh", 10) == State.invalid
    assert token3.check(path, -10) == State.invalid
    assert token3.check("huh", -10) == State.invalid
    assert token3.check(None) == State.invalid

    path = Path("")
    token4 = Token(cfg.key, Path(""))
    assert token4.check(path) == State.valid
    assert token4.check("huh") == State.intact
    assert token4.check(path, 10) == State.valid
    assert token4.check("huh", 10) == State.intact
    assert token4.check(path, -10) == State.expired
    assert token4.check("huh", -10) == State.intact

    if ct[3] == "f":
        ct = ct[0:3] + "g" + ct[4:]
    else:
        ct = ct[0:3] + "f" + ct[4:]

    token5 = Token.from_ciphertext(cfg.key, ct)
    assert token5.check(path) == State.invalid
    assert token5.check("huh") == State.invalid
    assert token5.check(path, 10) == State.invalid
    assert token5.check("huh", 10) == State.invalid
    assert token5.check(path, -10) == State.invalid
    assert token5.check("huh", -10) == State.invalid


def get_config() -> dict:
    return mock.get_config(mock.get_server_dir())


def token_roundtrip(tamper: bool, expire: bool, path: str):
    key = Config.from_dictionary(get_config()).key.data
    ttl = None
    if expire:
        ttl = 1
        data = _encode(key, path, 1)
    else:
        data = _encode(key, path)
    if tamper:
        if data[3] == "f":
            data = data[0:3] + "g" + data[4:]
        else:
            data = data[0:3] + "f" + data[4:]

    if tamper or expire:
        with pytest.raises(RuntimeError):
            _decode(key, data, ttl)
    else:
        assert _decode(key, data, ttl) == path


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
    key = get_config()["manabi"]["key"]
    f = Branca(from_string(key))
    res = f.decode(f.encode(string))
    assert res == string


def other_impl_decode(string: bytes):
    with mock.branca_impl():
        key = get_config()["manabi"]["key"]
        f = Branca(from_string(key))
        ct = f.encode(string)
        proc = run(["cargo", "run", "decode", key, ct], stdout=PIPE, check=True)
        assert from_string(proc.stdout.decode("UTF-8")) == string


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
