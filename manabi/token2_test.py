from pathlib import Path

import pytest

from .token2 import TTL, Config, Key, State, Token, now

_key = b"\xef\xc5\x07\xee}\x7f6\x11L\xb0\xc3155x\x11\xce.\x8e\xb96\xba\xce\x8b\x17-\xfc\x96]\xf8%\xd8"


def test_key_validator(config):
    key = Key.from_config(config)
    assert len(key.data) == 32
    with pytest.raises(TypeError):
        key.data = "huhu"
    with pytest.raises(ValueError):
        key.data = b"huhu"


def test_ttl_validator(config):
    ttl = TTL.from_config(config)
    assert ttl.initial == 600
    with pytest.raises(TypeError):
        ttl.initial = "huhu"
    assert ttl.initial == 600


def test_config_validator(config):
    cfg = Config.from_config(config)
    assert cfg.key.data == _key
    assert cfg.ttl.initial == 600
    assert cfg.ttl.refresh == 600
    with pytest.raises(TypeError):
        cfg.key = "huhu"


def test_token_creation(config):
    cfg = Config.from_config(config)
    path = Path("asdf.docx")
    token = Token(cfg, path)
    assert token.config.key.data == _key
    token.check(path) == State.valid
    token.check(path, 10) == State.valid
    token.check(path, -10) == State.expired
    ct = token.encode()
    token.check(path, 10) == State.valid
    token.check(path, -10) == State.expired
    token.check(path) == State.valid

    token2 = Token.from_ciphertext(cfg, ct)
    assert token2.check(path) == State.valid
    assert token2.check("huh") == State.intact
    assert token2.check(path, 10) == State.valid
    assert token2.check("huh", 10) == State.intact
    assert token2.check(path, -10) == State.expired
    assert token2.check("huh", -10) == State.intact
    assert token2.timestamp < now() + 10
    assert token2.timestamp > now() - 10

    if ct[3] == "f":
        ct = ct[0:3] + "g" + ct[4:]
    else:
        ct = ct[0:3] + "f" + ct[4:]

    token2 = Token.from_ciphertext(cfg, ct)
    assert token2.check(path) == State.invalid
    assert token2.check("huh") == State.invalid
    assert token2.check(path, 10) == State.invalid
    assert token2.check("huh", 10) == State.invalid
    assert token2.check(path, -10) == State.invalid
    assert token2.check("huh", -10) == State.invalid

    token3 = Token(cfg)
    assert token3.check(path) == State.invalid
    assert token3.check("huh") == State.invalid
    assert token3.check(path, 10) == State.invalid
    assert token3.check("huh", 10) == State.invalid
    assert token3.check(path, -10) == State.invalid
    assert token3.check("huh", -10) == State.invalid
    assert token3.check(None) == State.invalid

    path = Path("")
    token4 = Token(cfg, Path(""))
    assert token4.check(path) == State.valid
    assert token4.check("huh") == State.intact
    assert token4.check(path, 10) == State.valid
    assert token4.check("huh", 10) == State.intact
    assert token4.check(path, -10) == State.expired
    assert token4.check("huh", -10) == State.intact
