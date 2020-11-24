from typing import Generator

import pytest
import requests
from hypothesis import assume, given  # type: ignore
from hypothesis.strategies import binary, booleans, text  # type: ignore

from . import mock


def get_config() -> dict:
    return mock.get_config(mock.get_server_dir())


@pytest.fixture(scope="module")
def mod_server() -> Generator:
    with mock.run_server(get_config()):
        yield


@given(text())
def test_dump_force(mod_server, url):
    req = f"http://localhost:8080/dav/{url}"
    res = requests.get(req)
    # No access or crash
    assert res.status_code != 200
    assert res.status_code != 500
