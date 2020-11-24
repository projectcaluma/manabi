from typing import Generator

import pytest
import requests
from hypothesis import assume, given  # type: ignore
from hypothesis.strategies import binary, booleans, lists, text  # type: ignore

from . import mock


def get_config() -> dict:
    return mock.get_config(mock.get_server_dir())


@pytest.fixture(scope="module")
def mod_server() -> Generator:
    with mock.run_server(get_config()):
        yield


@given(text())
def test_dumb_force(mod_server, url):
    req = f"http://localhost:8080/dav/{url}"
    res = requests.get(req)
    # No access or crash
    assert res.status_code != 200
    assert res.status_code != 500


@given(lists(text()))
def test_structured_force(mod_server, url):
    url = "/".join(url)
    req = f"http://localhost:8080/dav/{url}"
    res = requests.get(req)
    # No access or crash
    assert res.status_code != 200
    assert res.status_code != 500
