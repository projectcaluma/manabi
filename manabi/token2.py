from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional

from attr import dataclass
from branca import Branca  # type: ignore

from .util import cattrib, from_string


@dataclass
class TTL:
    initial: int = cattrib(int)
    refresh: int = cattrib(int)

    @classmethod
    def from_config(cls, config: dict):
        initial = config["manabi"]["initial"]
        refresh = config["manabi"]["refresh"]
        return cls(initial, refresh)


@dataclass
class Key:
    data: bytes = cattrib(bytes, lambda x: len(x) == 32)

    @classmethod
    def from_config(cls, config: dict):
        return cls(from_string(config["manabi"]["key"]))


@dataclass
class Config:
    key: Key = cattrib(Key)
    ttl: TTL = cattrib(TTL)

    @classmethod
    def from_config(cls, config: dict):
        return cls(Key.from_config(config), TTL.from_config(config))


class State(Enum):
    valid = 1
    expired = 2
    invalid = 3


@dataclass
class Token:
    config: Config = cattrib(Config)
    path: Path = cattrib(Path)
    ttl: Optional[TTL] = cattrib(TTL, default=None)

    def encode(self):
        return _encode(self.config.key.data, str(self.path))

    @classmethod
    def from_cipher_text(cls, config: Config, ct: str):
        return cls(config, Path(_decode(config.key.data, ct)))


def _encode(key: bytes, path: str, now: Optional[int] = None) -> str:
    f = Branca(key)
    p = path.encode("UTF-8")
    ct = f.encode(p, now)
    return ct


def _decode(key: bytes, data: str, ttl=None) -> str:
    f = Branca(key)
    return f.decode(data, ttl).decode("UTF-8")
