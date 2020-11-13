import calendar
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional

from attr import Factory, dataclass
from branca import Branca  # type: ignore

from .util import cattrib, from_string


def now() -> int:
    return calendar.timegm(datetime.utcnow().timetuple())


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
    intact = 3
    invalid = 4


@dataclass
class Token:
    config: Config = cattrib(Config)
    path: Optional[Path] = cattrib(Path, default=None)
    timestamp: int = cattrib(int, default=Factory(now))
    _ciphertext: str = cattrib(str, default=None)

    def encode(self):
        if self.path is None:
            raise ValueError("path may not be None")
        if self.timestamp is None:
            self.timestamp = self.now()
        self._ciphertext = _encode(self.config.key.data, str(self.path), self.timestamp)
        return self._ciphertext

    @classmethod
    def from_ciphertext(cls, config: Config, ciphertext: str):
        assert ciphertext
        branca = Branca(config.key.data)
        timestamp = branca.timestamp(ciphertext)
        try:
            token_path = Path(branca.decode(ciphertext).decode("UTF-8"))
        except RuntimeError:
            return cls(config, None, timestamp)
        return cls(config, token_path, timestamp, ciphertext)

    def check(self, path: Path, ttl: Optional[int] = None) -> State:
        if self.path is None:
            return State.invalid
        if self.path != path:
            return State.intact
        if ttl is not None:
            future = self.timestamp + ttl
            if now() > future:
                return State.expired
        return State.valid

    def refresh(self, path: Path) -> State:
        return self.check(path, self.config.ttl.refresh)

    def initial(self, path: Path) -> State:
        return self.check(path, self.config.ttl.initial)


def _encode(key: bytes, path: str, now: Optional[int] = None) -> str:
    f = Branca(key)
    p = path.encode("UTF-8")
    ciphertext = f.encode(p, now)
    return ciphertext


def _decode(key: bytes, ciphertext: str, ttl=None) -> str:
    f = Branca(key)
    return f.decode(ciphertext, ttl).decode("UTF-8")
