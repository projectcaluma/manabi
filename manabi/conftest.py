import shutil
from functools import partial
from pathlib import Path
from subprocess import run
from threading import Thread
from typing import Any, Dict, Generator

import pytest  # type: ignore

from . import mock


@pytest.fixture()
def server_dir() -> Path:
    return mock.get_server_dir()


@pytest.fixture()
def config(server_dir) -> Dict[str, Any]:
    return mock.get_config(server_dir)


@pytest.fixture()
def server(config: Dict[str, Any]) -> Generator:
    server = mock.get_server(config)
    thread = Thread(target=partial(server.serve))
    thread.start()
    yield
    server.stop()
    thread.join()
    mock._server = None


@pytest.fixture(scope="module")
def cargo():
    if shutil.which("cargo"):
        with mock.branca_impl():
            run(["cargo", "run", "x", "y"])
