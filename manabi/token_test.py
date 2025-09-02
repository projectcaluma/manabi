import shutil
from os import environ
from pathlib import Path
from string import printable
from subprocess import PIPE, run

import pytest
from branca import Branca  # type: ignore
from hypothesis import assume, given, strategies as st

from . import mock
from .token import TTL, Config, DecodingError, Key, State, Token, _decode, _encode, now
from .type_alias import OptionalProp
from .util import from_string

_old_token = "1Ui3IS5xxIedbhSdPFPoGQRnTUtPVTmleMGJe1KyvWsVU704wk68k3YC70txTn5ZEJ4Ms3bh5Esy0OD4mZM0TnumUymWglgp3wq0CHo3W89DyW0"
_old_key = "bNEZsIjvxDAiLhDA1chvF9zL9OJYPNlCqNPlm7KbhmU"

_key = b"\xef\xc5\x07\xee}\x7f6\x11L\xb0\xc3155x\x11\xce.\x8e\xb96\xba\xce\x8b\x17-\xfc\x96]\xf8%\xd8"

msgpack = st.recursive(
    st.none()
    | st.booleans()
    | st.floats(allow_nan=False)
    | st.text(printable, max_size=32),
    lambda children: st.lists(children) | st.dictionaries(st.text(printable), children),
    max_leaves=8,
)


def test_old_token():
    key = Key(from_string(_old_key))
    token = Token.from_ciphertext(key, _old_token)
    assert token.check(0) == State.invalid


def test_key_validator(config):
    key = Key.from_dictionary(config)
    assert len(key.data) == 32
    with pytest.raises(TypeError):
        # well we want to test what happens if it is not correctly typed
        key.data = "huhu"  # type: ignore
    with pytest.raises(ValueError):  # noqa: PT011
        # well we want to test what happens if it is not correctly typed
        key.data = b"huhu"  # type: ignore


def test_ttl_validator(config):
    ttl = TTL.from_dictionary(config)
    assert ttl.initial == 600
    with pytest.raises(TypeError):
        # well we want to test what happens if it is not correctly typed
        ttl.initial = "huhu"  # type: ignore
    assert ttl.initial == 600


def test_config_validator(config):
    cfg = Config.from_dictionary(config)
    assert cfg.key.data == _key
    assert cfg.ttl.initial == 600
    assert cfg.ttl.refresh == 600
    with pytest.raises(TypeError):
        # well we want to test what happens if it is not correctly typed
        cfg.key = "huhu"  # type: ignore


def test_token_invalid_past(config):
    cfg = Config.from_dictionary(config)
    path = Path("asdf.docx")
    with mock.shift_now(-1200):
        token = Token(cfg.key, path)
    assert token.check(10) == State.expired


def test_token_invalid_future(config):
    cfg = Config.from_dictionary(config)
    path = Path("asdf.docx")
    with mock.shift_now(1200):
        token = Token(cfg.key, path)
    assert token.check(10) == State.not_valid_yet


def test_token_creation(config):
    cfg = Config.from_dictionary(config)
    path = Path("asdf.docx")
    token = Token(cfg.key, path)

    assert token.key.data == _key
    assert token.check() == State.valid
    assert token.check(10) == State.valid
    assert token.check(-10) == State.expired

    # Is it still
    ct = token.encode()
    assert token.check(10) == State.valid
    assert token.check(-10) == State.expired

    token2 = Token.from_ciphertext(cfg.key, ct)
    assert token2.check() == State.valid
    assert token2.check(10) == State.valid
    assert token2.check(-10) == State.expired
    assert token2.timestamp < now() + 10  # type: ignore
    assert token2.timestamp > now() - 10  # type: ignore
    assert token2.initial(cfg.ttl) == State.valid
    assert token2.refresh(cfg.ttl) == State.valid

    # Testing refresh
    token = Token.from_token(token2)
    ct2 = token.encode()
    assert ct != ct2
    token = Token.from_ciphertext(cfg.key, ct2)
    assert token.check() == State.valid
    assert token.check(10) == State.valid
    assert token.check(-10) == State.expired
    assert token.timestamp < now() + 10  # type: ignore
    assert token.timestamp > now() - 10  # type: ignore

    token = Token(cfg.key)
    assert token.check() == State.invalid
    assert token.check(10) == State.invalid
    assert token.check(-10) == State.invalid
    assert token.check(None) == State.invalid
    return

    if ct[3] == "f":
        ct = ct[0:3] + "g" + ct[4:]
    else:
        ct = ct[0:3] + "f" + ct[4:]

    token = Token.from_ciphertext(cfg.key, ct)
    assert token.check() == State.invalid
    assert token.check(10) == State.invalid
    assert token.check(-10) == State.invalid


def token_roundtrip(tamper: bool, expire: bool, path: str, payload: OptionalProp):
    with mock.with_config() as config:
        key = Config.from_dictionary(config).key.data
    ttl = None
    if expire:
        ttl = 1
        data = _encode(key, path, payload, 1)
    else:
        data = _encode(key, path, payload)
    if tamper:
        if data[3] == "f":
            data = data[0:3] + "g" + data[4:]
        else:
            data = data[0:3] + "f" + data[4:]

    if tamper or expire:
        with pytest.raises(DecodingError):
            _decode(key, data, ttl)
    else:
        assert _decode(key, data, ttl) == (Path(path), payload)


@pytest.mark.parametrize("tamper", [True, False])
@pytest.mark.parametrize("expire", [True, False])
@pytest.mark.parametrize("path", ["hello", "asdf.docx"])
@pytest.mark.parametrize("payload", ["hello", 3, [3, 3], None])
def test_token_roundtrip(tamper: bool, expire: bool, path: str, payload: OptionalProp):
    token_roundtrip(tamper, expire, path, payload)


@given(st.booleans(), st.booleans(), st.text(min_size=1, max_size=32), msgpack)
def test_token_roundtrip_hyp(
    tamper: bool,
    expire: bool,
    path: str,
    payload: OptionalProp,
):
    token_roundtrip(tamper, expire, path, payload)


@given(st.binary(min_size=1, max_size=32))
def test_branca_roundtrip(string: bytes):
    with mock.with_config() as config:
        key = config["manabi"]["key"]
    f = Branca(from_string(key))
    res = f.decode(f.encode(string))
    assert res == string


def other_impl_decode(string: bytes):
    with mock.branca_impl():
        with mock.with_config() as config:
            key = config["manabi"]["key"]
        f = Branca(from_string(key))
        ct = f.encode(string)
        proc = run(["cargo", "run", "decode", key, ct], stdout=PIPE, check=True)
        assert from_string(proc.stdout.decode("UTF-8")) == string


def cargo_build():
    return not shutil.which("cargo") or "GITHUB_WORKFLOW" in environ


@pytest.mark.skipif(cargo_build(), reason="needs rustc and cargo")
def test_other_impl_decode(cargo):
    other_impl_decode(b"hello world")


# TODO test binary data when branca-rust supports binary data:
# https://github.com/return/branca/issues/10
# hypothesis doesn't like fixtures anymore
@pytest.mark.skipif(cargo_build(), reason="needs rustc and cargo")
@given(st.text(min_size=1))
def test_other_impl_decode_hyp(cargo, string: str):
    bstr = string.encode("UTF-8")
    assume(not bstr.startswith(b"\x00"))
    other_impl_decode(bstr)
