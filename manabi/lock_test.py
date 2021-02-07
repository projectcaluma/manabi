import time
import xml.etree.ElementTree as ET
from typing import Any, Dict
from urllib import request

import requests

from . import mock
from .mock import run_server

lock_req = b"""
<?xml version="1.0" encoding="utf-8" ?>
<d:lockinfo xmlns:d="DAV:">
  <d:lockscope><d:exclusive/></d:lockscope>
        <d:locktype><d:write/></d:locktype>
          <d:owner>
          <d:href>http://www.contoso.com/~user/contact.htm</d:href>
        </d:owner>
</d:lockinfo>
""".strip()


def http(method, url, token=None, data=None):
    opener = request.build_opener(request.HTTPHandler)
    req = request.Request(url)
    if data:
        req.data = data
    if method == "LOCK":
        req.add_header("Content-type", "application/xml")
        # Lock refresh path
        if not token:
            req.data = lock_req
    if token:
        req.add_header("Lock-Token", token)
        ifstr = f"<{url}> (<{token}>)"
        req.add_header("If", ifstr)
    req.get_method = lambda: method
    res = opener.open(req)
    try:
        return res, res.read()
    finally:
        res.close()


def get_lock_token(xml):
    root = ET.fromstring(xml)
    return root[0][0][5][0].text


def test_lock(config: Dict[str, Any], server):
    expect = str(time.time()).encode("UTF-8")
    req = mock.make_req(config)
    assert requests.get(req).status_code == 200
    res, xml = http("LOCK", req)
    token = get_lock_token(xml)
    assert res.status == 200
    res, xml = http("LOCK", req, token=token)
    assert res.status == 200
    res, _ = http("PUT", req, token=token, data=expect)
    assert res.status == 204
    res, data = http("GET", req, token=token)
    assert res.status == 200
    assert data == expect


def test_lock_two_server(server_dir):
    with mock.lock_storage() as storage:
        config = mock.get_config(server_dir, storage)
        config2 = mock.get_config(server_dir, storage)
        config2["port"] = 8081
        with run_server(config), run_server(config2):
            expect = str(time.time()).encode("UTF-8")
            req = mock.make_req(config)
            req2 = req.replace(
                "http://localhost:8080/dav/", "http://localhost:8081/dav/"
            )
            assert requests.get(req).status_code == 200
            assert requests.get(req2).status_code == 200
            assert requests.get(req).status_code == 200
            res, xml = http("LOCK", req)
            token = get_lock_token(xml)
            assert res.status == 200

            # Switch server
            res, xml = http("LOCK", req2, token=token)
            assert res.status == 200
            res, _ = http("PUT", req2, token=token, data=expect)
            assert res.status == 204
            res, data = http("GET", req2, token=token)
            assert res.status == 200
            assert data == expect
