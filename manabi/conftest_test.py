from pathlib import Path
from typing import Optional

import requests

from .token import Token


def make_req(config: dict, override_path: Optional[str] = None):
    t = Token(config)
    path = "asdf.docx"
    token = t.make(path)
    if override_path:
        path = override_path
    return f"http://localhost:8080/dav/{token}/{path}"


def test_server_failure(server, config: dict):
    res = requests.get(make_req(config, "blabla.pdf"))
    assert res.status_code == 403


def test_server_file(config, server: dict, server_dir: Path):
    with open(Path(server_dir, "asdf.docx"), "rb") as f:
        exp = f.read()
        res = requests.get(make_req(config))
        assert exp == res.content
