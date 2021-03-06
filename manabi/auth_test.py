from typing import Generator, cast
from urllib.parse import quote

import pytest
import requests
from hypothesis import assume, example, given  # type: ignore
from hypothesis.strategies import (  # type: ignore
    binary,
    booleans,
    lists,
    permutations,
    text,
)

from . import mock


@pytest.fixture(scope="module")
def mod_server() -> Generator:
    with mock.with_config() as config:
        with mock.run_server(config):
            yield


def dumb_force(url):
    req = f"http://localhost:8080/dav/{url}"
    res = requests.get(req)
    assert res.status_code == 403


@given(text())
def test_dumb_force(mod_server, url):
    dumb_force(url)


@given(binary())
def test_dumb_binary_force(mod_server, url):
    dumb_force(url)


@given(binary())
def test_dumb_quote_force(mod_server, url):
    url = quote(url)
    dumb_force(url)


def structured_force(url, sep="/"):
    url = sep.join(url)
    req = f"http://localhost:8080/dav/{url}"
    res = requests.get(req)
    assert res.status_code == 403


@given(lists(text()))
@example(["%80"])
@example(["例え.テスト"])
@example(["これは、これを日本語のテキストです"])
def test_structured_force(mod_server, url):
    structured_force(url)


@given(lists(binary()))
def test_structured_binary_force(mod_server, url):
    structured_force(url, sep=b"/")


@given(lists(binary()))
def test_structured_quote_force(mod_server, url):
    assume(url != b"..")
    url = [quote(x) for x in url]
    structured_force(url)


def force_with_token(url, past, do_quote=False, sep="/"):
    shift = 1200
    if past:
        shift = -1200
    with mock.with_config() as config:
        with mock.shift_now(shift):
            t = mock.make_token(config)
    for i, v in enumerate(url):
        if v is None:
            if sep == "/":
                url[i] = t.encode()
            elif sep == b"/":
                url[i] = t.encode().encode("UTF-8")
            else:
                raise RuntimeError("Bad sperator")
        elif do_quote:
            url[i] = quote(url[i])
    url = sep.join(url)
    req = f"http://localhost:8080/dav/{url}"
    res = requests.get(req)
    assert res.status_code == 403


@given(lists(text()).flatmap(lambda x: permutations(x + [cast(str, None)])), booleans())
def test_force_with_token(mod_server, url, past):
    force_with_token(url, past)


@given(
    lists(binary()).flatmap(lambda x: permutations(x + [cast(bytes, None)])), booleans()
)
def test_force_quote_with_token(mod_server, url, past):
    force_with_token(url, past, do_quote=True)


@given(
    lists(binary()).flatmap(lambda x: permutations(x + [cast(bytes, None)])), booleans()
)
def test_force_binary_with_token(mod_server, url, past):
    force_with_token(url, past, do_quote=False, sep=b"/")
