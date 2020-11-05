from pathlib import Path

import requests

from .token import Token
from .util import short_hash, tostring


def make_req(config):
    t = Token(config)
    path = "asdf.docx"
    token = t.make(path)
    return f"http://localhost:8080/dav/{token}/{path}"


def test_server_hash(server, config):
    res = requests.get(make_req(config))
    assert "3n843L6rn6Gi6gcpjcOBD2" == tostring(short_hash(res.content))


def test_server_file(config, server, server_dir):
    with open(Path(server_dir, "asdf.docx"), "rb") as f:
        exp = f.read()
        res = requests.get(make_req(config))
        assert exp == res.content
