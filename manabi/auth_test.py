from typing import Generator

import pytest
import requests
from hypothesis import given  # type: ignore
from hypothesis.strategies import booleans, lists, permutations, text  # type: ignore

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
    assert res.status_code == 403


@given(lists(text()))
def test_structured_force(mod_server, url):
    url = "/".join(url)
    req = f"http://localhost:8080/dav/{url}"
    res = requests.get(req)
    assert res.status_code == 403


@given(lists(text()).flatmap(lambda x: permutations(x + [None])), booleans())
def test_force_with_token(mod_server, url, past):
    shift = 1200
    if past:
        shift = -1200
    with mock.shift_now(shift):
        t = mock.make_token(get_config())
    for i, v in enumerate(url):
        if v is None:
            url[i] = t.encode()
    url = "/".join(url)
    req = f"http://localhost:8080/dav/{url}"
    res = requests.get(req)
    assert res.status_code == 403
