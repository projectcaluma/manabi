import fcntl
from contextlib import contextmanager
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

    @contextmanager
    def lock_file(self):
        fd = self._lock_file.fileno()
        try:
            fcntl.flock(fd, fcntl.LOCK_EX)
            yield
        finally:
            fcntl.flock(fd, fcntl.LOCK_UN)

    def open(self):
        _logger.debug(f"open({self._storage})")
        self._dict = SqliteDict(self._storage, autocommit=True)
        self._lock_file = open(f"{self._storage}.lock", "wb+")

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
            lock = self._lock_file
            self._lock_file = None
            if con:
                con.close()
                lock.close()
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
        with self.lock_file():
            return super().create(path, lock)

    def refresh(self, token, timeout):
        with self.lock_file():
            return super().refresh(token, timeout)

    def delete(self, token):
        with self.lock_file():
            return super().delete(token)
