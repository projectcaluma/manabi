from pathlib import Path
from typing import Any, Dict

import requests

from .mock import make_req


def test_server_not_found(server, config: Dict[str, Any]):
    res = requests.get(make_req(config, Path("blabla.pdf")))
    assert res.status_code == 404


def test_server_denied(server, config: Dict[str, Any]):
    f = "http://localhost:8080/dav/bla.pdf"
    res = requests.get(f)
    assert res.status_code == 403


def test_server_file(config: Dict[str, Any], server, server_dir: Path):
    with open(Path(server_dir, "asdf.docx"), "rb") as f:
        exp = f.read()
        res = requests.get(make_req(config))
        assert res.status_code == 200
        assert exp == res.content
