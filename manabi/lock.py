import fcntl
import json
import shelve
import threading
import traceback
import weakref
from abc import ABC, abstractmethod
from collections.abc import MutableMapping
from pathlib import Path
from typing import Callable

from psycopg import (
    Connection as PsycopgConnection,
    InterfaceError,
    IsolationLevel,
    OperationalError,
    connect,
)
from wsgidav.lock_man.lock_storage import LockStorageDict
from wsgidav.util import get_module_logger

_logger = get_module_logger(__name__)


class ManabiTimeoutMixin:
    _max_timeout: float = 0

    @property
    def max_timeout(self) -> float:
        return self._max_timeout

    @max_timeout.setter
    def max_timeout(self, value: float) -> None:
        if value <= 0:
            raise ValueError("max_timeout must be a positive integer.")
        self._max_timeout = value

    def set_timeout(self, lock):
        max_timeout = self.max_timeout
        timeout = lock.get("timeout")

        if not timeout or timeout > max_timeout:
            lock["timeout"] = max_timeout


class ManabiContextLockMixin(ABC):
    @abstractmethod
    def acquire(self):
        pass

    def __init__(self):
        self._id = -1

    @abstractmethod
    def release(self):
        pass

    def __enter__(self):
        self.acquire()

    def __exit__(self, exc_type, exc_value, traceback):
        self.release()

    def _check_and_set_tid(self):
        tid: int = threading.get_ident()
        tid_is_set = self._id != -1
        if tid_is_set and self._id != tid:
            _logger.error("Do not use from multiple threads")
        self._id = tid


class ManabiShelfLock(ManabiContextLockMixin):
    _storage_object: Callable[[], "ManabiShelfLockLockStorage"]

    def __init__(self, storage_path, storage_object: "ManabiShelfLockLockStorage"):
        self._storage_path = storage_path
        # type manually checked
        self._storage_object = weakref.ref(storage_object)  # type: ignore
        self._semaphore = 0
        self._lock_file = open(f"{storage_path}.lock", "wb+")
        self._fd = self._lock_file.fileno()
        self.acquire_write = self.acquire_read = self.acquire
        super().__init__()

    def acquire(self):
        self._check_and_set_tid()
        if self._semaphore == 0:
            fcntl.flock(self._fd, fcntl.LOCK_EX)
            self._storage_object()._dict = shelve.open(str(self._storage_path))
        self._semaphore += 1

    def release(self):
        if self._semaphore == 0:
            _logger.error(
                f"Inconsistent use of lock. {''.join(traceback.format_stack())}"
            )

        self._check_and_set_tid()
        self._semaphore -= 1
        if self._semaphore == 0:
            storage_object = self._storage_object()
            if storage_object._dict is not None:
                storage_object._dict.close()
                storage_object._dict = None
            fcntl.flock(self._fd, fcntl.LOCK_UN)


class ManabiShelfLockLockStorage(LockStorageDict, ManabiTimeoutMixin):
    def __init__(self, refresh: float, storage: Path):
        super().__init__()
        self.max_timeout = refresh / 2
        self._storage = storage
        # this is a cast
        self._lock: ManabiShelfLock = ManabiShelfLock(storage, self)  # type:ignore

    def open(self):
        pass

    def close(self):
        pass

    def create(self, path, lock):
        with self._lock:
            self.set_timeout(lock)
            super().create(path, lock)

    def clear(self):
        if self._dict:
            with self._lock:
                self._dict.clear()

    def refresh(self, token, *, timeout):
        with self._lock:
            return super().refresh(token, timeout=timeout)

    def get(self, token):
        with self._lock:
            return super().get(token)

    def delete(self, token):
        with self._lock:
            return super().delete(token)

    def get_lock_list(self, path, *, include_root, include_children, token_only):
        with self._lock:
            return super().get_lock_list(
                path,
                include_root=include_root,
                include_children=include_children,
                token_only=token_only,
            )


class ManabiPostgresLock(ManabiContextLockMixin):
    _storage_object: Callable[[], "ManabiDbLockStorage"]

    def __init__(self, storage_object: "ManabiDbLockStorage"):
        # type manually checked
        self._storage_object = weakref.ref(storage_object)  # type: ignore
        self.acquire_write = self.acquire_read = self.acquire
        self._semaphore = 0
        super().__init__()

    def acquire(self):
        tid = threading.get_ident()
        self._check_and_set_tid()
        if self._semaphore == 0:
            _logger.info(f"{tid} acquire")
            self._storage_object().execute(
                "LOCK TABLE manabi_lock IN ACCESS EXCLUSIVE MODE"
            )
        self._semaphore += 1

    def release(self):
        tid = threading.get_ident()
        if self._semaphore == 0:
            _logger.error(
                f"Inconsistent use of lock. {''.join(traceback.format_stack())}"
            )
        self._check_and_set_tid()
        self._semaphore -= 1
        if self._semaphore == 0:
            _logger.info(f"{tid} release")
            self._storage_object()._connection.commit()


class ManabiPostgresDict(MutableMapping):
    _storage_object: Callable[[], "ManabiDbLockStorage"]

    def __init__(self, storage_object: "ManabiDbLockStorage", lock):
        # type manually checked
        self._storage_object = weakref.ref(storage_object)  # type: ignore
        self._lock = lock

    @staticmethod
    def decode_lock(lock):
        if "owner" in lock:
            owner = lock["owner"]
            if isinstance(owner, bytes):
                lock["owner"] = {"manabi_was_bytes": owner.decode("UTF-8")}

    @staticmethod
    def encode_lock(lock):
        if "owner" in lock:
            owner = lock["owner"]
            if "manabi_was_bytes" in owner:
                lock["owner"] = owner["manabi_was_bytes"].encode("UTF-8")

    def cleanup(self):
        with self._lock:
            self._storage_object().execute("DELETE FROM manabi_lock;")

    def __len__(self):
        with self._lock:
            cursor = self._storage_object().execute("SELECT count(*) FROM manabi_lock")
            return int(cursor.fetchone()[0])

    def __iter__(self):
        with self._lock:
            cursor = self._storage_object().execute("SELECT token FROM manabi_lock")
            for token in cursor.fetchall():
                yield token[0]

    def __delitem__(self, token):
        with self._lock:
            self._storage_object().execute(
                "DELETE FROM manabi_lock WHERE token = %s", (str(token),)
            )

    def __contains__(self, token):
        with self._lock:
            cursor = self._storage_object().execute(
                "SELECT 1 FROM manabi_lock WHERE token = %s", (str(token),)
            )
            return cursor.fetchone() is not None

    def __setitem__(self, token, lock):
        with self._lock:
            self.decode_lock(lock)
            json_lock = json.dumps(lock)
            self._storage_object().execute(
                """
                    INSERT INTO manabi_lock(token, data) VALUES (%(token)s, %(data)s)
                        ON CONFLICT(token) DO
                        UPDATE SET data = %(data)s WHERE manabi_lock.token = %(token)s
                """,
                {
                    "token": token,
                    "data": json_lock,
                },
            )

    def __getitem__(self, token):
        with self._lock:
            cursor = self._storage_object().execute(
                "SELECT data FROM manabi_lock WHERE token = %s", (str(token),)
            )
            locks = cursor.fetchmany(1)
            if not len(locks):
                raise KeyError(f"{token} not found")

            lock = locks[0][0]  # first row, first col
            self.encode_lock(lock)
            return lock


class ManabiDbLockStorage(LockStorageDict, ManabiTimeoutMixin):
    _connection: PsycopgConnection

    def __init__(self, refresh: float, postgres_dsn: str):
        super().__init__()
        self._postgres_dsn = postgres_dsn
        self.max_timeout = refresh / 2
        self.connect()
        # this is a cast
        self._lock: ManabiPostgresLock = ManabiPostgresLock(self)  # type: ignore
        self._dict = ManabiPostgresDict(self, self._lock)

    def connect(self):
        try:
            if self._connection:
                # it the connecton failed, this might cause an exception, we do not care.
                self._connection.close()
        except Exception:
            pass
        self._connection = connect(self._postgres_dsn)
        self._connection.commit()
        self._connection.autocommit = False
        self._connection.isolation_level = IsolationLevel.SERIALIZABLE
        self._cursor = self._connection.cursor()

    def open(self):
        pass

    def execute(self, *args, **kwargs):
        try:
            self._cursor.execute(*args, **kwargs)
        except (InterfaceError, OperationalError):
            _logger.warning("Postgres connection lost, reconnecting")

            self.connect()
            self._cursor.execute(*args, **kwargs)
        return self._cursor

    def close(self):
        pass

    def create(self, path, lock):
        with self._lock:
            self.set_timeout(lock)
            super().create(path, lock)
