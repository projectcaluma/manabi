import os
import shutil
from collections.abc import Generator
from pathlib import Path
from subprocess import run
from typing import Any, Dict
from unittest import mock as unitmock

import pytest
from hypothesis import settings
from moto import mock_aws
from psycopg2 import connect

from . import mock
from .log import verbose_logging
from .mock import MockManabiDbLockStorage, upload_file_to_s3
from .util import get_boto_client

TEST_FILES_DIR = Path(__file__).parent.resolve() / "data"


def configure_hypothesis():
    settings.register_profile("ci", print_blob=True, deadline=None)
    settings.register_profile(
        "fuzzing", print_blob=True, max_examples=10000, deadline=None
    )
    settings.register_profile("basic", print_blob=True)
    settings.load_profile(os.getenv("HYPOTHESIS_PROFILE", "basic"))


configure_hypothesis()


@pytest.fixture
def chaos():
    with unitmock.patch("manabi.lock.ManabiDbLockStorage", MockManabiDbLockStorage):
        yield


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


@pytest.fixture
def postgres_dsn():
    return mock._postgres_dsn


@pytest.fixture(params=[True, False])
def lock_storage(request, postgres_dsn):
    if request.param:
        yield postgres_dsn
    else:
        with mock.lock_storage() as storage:
            yield storage


@pytest.fixture
def write_hooks():
    try:
        mock._pre_write_hook = "http://127.0.0.1/pre_write_hook"
        mock._post_write_hook = "http://127.0.0.1/post_write_hook"
        yield
    finally:
        mock._pre_write_hook = None
        mock._post_write_hook = None


@pytest.fixture
def write_callback():
    try:
        mock._pre_write_callback = mock.check_token
        mock._post_write_callback = mock.check_token
        yield mock.check_token
    finally:
        mock._pre_write_callback = None
        mock._post_write_callback = None


@pytest.fixture
def server_dir(s3_file) -> Path:
    return mock.get_server_dir()


@pytest.fixture(params=[False])
def config(server_dir, lock_storage, request) -> Dict[str, Any]:
    return mock.get_config(server_dir, lock_storage, request.param)


@pytest.fixture
def server(config: Dict[str, Any]) -> Generator:
    with mock.run_server(config):
        yield


@pytest.fixture
def mock_now_invalid_past() -> Generator[unitmock.MagicMock, None, None]:
    with mock.shift_now(-1200) as m:
        yield m


@pytest.fixture
def mock_now_invalid_future() -> Generator[unitmock.MagicMock, None, None]:
    with mock.shift_now(1200) as m:
        yield m


@pytest.fixture(scope="module")
def cargo():
    if shutil.which("cargo"):
        with mock.branca_impl():
            run(["cargo", "run", "x", "y"], check=False)


@pytest.fixture
def s3():
    with mock_aws():
        s3 = get_boto_client()
        s3.create_bucket(Bucket=os.environ.get("S3_BUCKET_NAME", "manabi-media"))
        yield s3


@pytest.fixture
def s3_file(s3):
    return upload_file_to_s3(s3)
