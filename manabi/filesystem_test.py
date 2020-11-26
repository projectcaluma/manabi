from typing import Any, Dict

import requests

from . import mock


def test_get_and_put(config: Dict[str, Any], server):
    req = mock.make_req(config)
    res = requests.get(req)
    assert res.status_code == 200
    res = requests.put(req, data=res.content)
    assert res.status_code == 204
