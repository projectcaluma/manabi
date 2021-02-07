from pathlib import Path

from sqlitedict import SqliteDict  # type: ignore
from wsgidav.lock_storage import LockStorageDict  # type: ignore
from wsgidav.util import get_module_logger  # type: ignore

_logger = get_module_logger(__name__)


class ManabiLockLockStorage(LockStorageDict):
    def __init__(self, refresh: float, storage: Path):
        super().__init__()
        self.max_timeout = refresh / 2
        self._storage = storage

    def open(self):
        _logger.debug(f"open({self._storage})")
        self._dict = SqliteDict(self._storage, autocommit=True)

    def clear(self):
        _logger.debug("clear()")
        self._lock.acquire_write()
        try:
            self.close()
            self._storage.unlink()
            self.open()
        finally:
            self._lock.release()

    def close(self):
        _logger.debug("close()")
        self._lock.acquire_write()
        try:
            con = self._dict
            self._dict = None
            if con:
                con.close()
        finally:
            self._lock.release()

    def create(self, path, lock):
        max_timeout = self.max_timeout
        timeout = lock.get("timeout")

        if not timeout:
            lock["timeout"] = max_timeout
        else:
            if timeout > max_timeout:
                lock["timeout"] = max_timeout
        return super().create(path, lock)

    def get(self, token):
        res = super().get(token)
        return res
