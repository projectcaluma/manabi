from pathlib import Path

import requests

from .util import short_hash, tostring


def test_server_hash(server):
    res = requests.get("http://localhost:8080/dav/asdf.docx")
    assert "3n843L6rn6Gi6gcpjcOBD2" == tostring(short_hash(res.content))


def test_server_file(server, server_dir):
    with open(Path(server_dir, "asdf.docx"), "rb") as f:
        exp = f.read()
        res = requests.get("http://localhost:8080/dav/asdf.docx")
        assert exp == res.content
