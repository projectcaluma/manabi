from wsgidav.lock_storage import LockStorageDict


# Actually we'd like to extend LockManager not LockStorage, but the config only allows
# to set LockStorage. It is possible to mock our LockManager into wsgidav, but I prefer
# not to do that.
class ManabiLockLockStorage(LockStorageDict):
    def __init__(self, refresh: float):
        self.max_timeout = refresh / 2
        super().__init__()

    def create(self, path, lock):
        max_timeout = self.max_timeout
        timeout = lock.get("timeout")
        if not timeout:
            lock["timeout"] = max_timeout
        else:
            if timeout > max_timeout:
                lock["timeout"] = max_timeout
        return super().create(path, lock)
