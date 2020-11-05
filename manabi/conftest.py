import shutil
from functools import partial
from subprocess import run
from threading import Thread

import pytest

from . import mock


@pytest.fixture()
def server_dir():
    return mock.get_server_dir()


@pytest.fixture()
def config(server_dir):
    return mock.get_config(server_dir)


@pytest.fixture()
def server(config):
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
