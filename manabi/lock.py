import fcntl
import shelve
from contextlib import contextmanager
from pathlib import Path

from wsgidav.lock_storage import LockStorageDict  # type: ignore
from wsgidav.util import get_module_logger  # type: ignore

_logger = get_module_logger(__name__)


class ManabiLockLockStorage(LockStorageDict):
    def __init__(self, refresh: float, storage: Path):
        super().__init__()
        self.max_timeout = refresh / 2
        self._storage = storage

    @contextmanager
    def get_shelve(self):
        fd = self._lock_file.fileno()
        try:
            self._lock.acquire_write()
            try:
                if self._semaphore == 0:
                    fcntl.flock(fd, fcntl.LOCK_EX)
                    self._dict = shelve.open(str(self._storage))
                    _logger.debug(
                        f"get_shelve({self._storage}): {len(self._dict)} locks"
                    )
                self._semaphore += 1
                yield
            finally:
                self._semaphore -= 1
                if self._semaphore == 0:
                    self._dict.close()
                    self._dict = None
                    fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            self._lock.release()

    def open(self):
        _logger.debug(f"open({self._storage})")
        self._lock_file = open(f"{self._storage}.lock", "wb+")
        self._semaphore = 0

    def close(self):
        _logger.debug("close()")
        self._lock.acquire_write()
        try:
            lock = self._lock_file
            self._lock_file = None
            lock.close()
            self._semaphore = 0
        finally:
            self._lock.release()

    def clear(self):
        _logger.debug("clear()")
        self._lock.acquire_write()
        try:
            self._storage.unlink()
        finally:
            self._lock.release()

    def get(self, token):
        with self.get_shelve():
            return super().get(token)

    def create(self, path, lock):
        max_timeout = self.max_timeout
        timeout = lock.get("timeout")

        if not timeout:
            lock["timeout"] = max_timeout
        else:
            if timeout > max_timeout:
                lock["timeout"] = max_timeout
        with self.get_shelve():
            return super().create(path, lock)

    def refresh(self, token, timeout):
        with self.get_shelve():
            return super().refresh(token, timeout)

    def delete(self, token):
        with self.get_shelve():
            return super().delete(token)

    def get_lock_list(self, path, include_root, include_children, token_only):
        with self.get_shelve():
            return super().get_lock_list(
                path, include_root, include_children, token_only
            )
