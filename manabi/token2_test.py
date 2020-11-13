from pathlib import Path

import pytest

from .token2 import TTL, Config, Key, Token

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
