import shutil
from pathlib import Path
from subprocess import run
from typing import Any, Dict, Generator
from unittest import mock as unitmock

import pytest  # type: ignore
from psycopg2 import connect

from . import mock
from .log import verbose_logging


@pytest.fixture(scope="session", autouse=True)
def enable_verbose_logging() -> None:
    verbose_logging()


def clean_db_exec():
    storage = connect(mock._postgres_dsn)
    storage.cursor().execute("DELETE FROM manabi_lock")
    storage.commit()
    storage.close()


@pytest.fixture(scope="session", autouse=True)
def clean_db() -> Generator[None, None, None]:
    clean_db_exec()
    yield
    clean_db_exec()


@pytest.fixture()
def postgres_dsn():
    return mock._postgres_dsn


@pytest.fixture(params=[True, False])
def lock_storage(request, postgres_dsn):
    if request.param:
        yield postgres_dsn
    else:
        with mock.lock_storage() as storage:
            yield storage


@pytest.fixture()
def server_dir() -> Path:
    return mock.get_server_dir()


@pytest.fixture()
def config(server_dir, lock_storage) -> Dict[str, Any]:
    return mock.get_config(server_dir, lock_storage)


@pytest.fixture()
def server(config: Dict[str, Any]) -> Generator:
    with mock.run_server(config):
        yield


@pytest.fixture()
def mock_now_invalid_past() -> Generator[unitmock.MagicMock, None, None]:
    with mock.shift_now(-1200) as m:
        yield m


@pytest.fixture()
def mock_now_invalid_future() -> Generator[unitmock.MagicMock, None, None]:
    with mock.shift_now(1200) as m:
        yield m


@pytest.fixture(scope="module")
def cargo():
    if shutil.which("cargo"):
        with mock.branca_impl():
            run(["cargo", "run", "x", "y"])
