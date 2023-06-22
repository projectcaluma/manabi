from typing import Any, Dict

import pytest
import requests

from . import mock


@pytest.mark.parametrize("tamper, expect_status", [(True, 403), (False, 204)])
def test_get_and_put(tamper, expect_status, config: Dict[str, Any], server):
    req = mock.make_req(config)
    res = requests.get(req)
    assert res.status_code == 200
    if tamper:
        i = 58
        if req[i] == "f":
            req = req[0:i] + "g" + req[i + 1 :]
        else:
            req = req[0:i] + "f" + req[i + 1 :]
    res = requests.put(req, data=res.content)
    assert res.status_code == expect_status


@pytest.mark.parametrize(
    "hook_status, expect_status",
    [
        (None, 204),
        (403, 403),
        (200, 204),
    ],
)
def test_get_and_put_hooked(
    hook_status, expect_status, pre_write_hook, config: Dict[str, Any], server
):
    assert config["pre_write_hook"] == "http://127.0.0.1/pre_write_hook"
    with mock.with_pre_write_hook(config, hook_status):
        req = mock.make_req(config)
        res = requests.get(req)
        assert res.status_code == 200
        res = requests.put(req, data=res.content)
        assert res.status_code == expect_status


@pytest.mark.parametrize("callback_return, expect_status", [(False, 403), (True, 204)])
def test_get_and_put_called(
    callback_return,
    expect_status,
    pre_write_callback,
    config: Dict[str, Any],
    server,
):
    assert config["pre_write_callback"] == pre_write_callback
    req = mock.make_req(config)
    res = requests.get(req)
    assert res.status_code == 200
    try:
        mock._check_token_return = callback_return
        res = requests.put(req, data=res.content)
        assert res.status_code == expect_status
    finally:
        mock._check_token_return = True
