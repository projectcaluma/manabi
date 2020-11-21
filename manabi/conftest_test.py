from pathlib import Path
from typing import Any, Dict, Optional

import requests

from .token import Key, Token


def make_req(config: Dict[str, Any], override_path: Optional[str] = None) -> str:
    path = Path("asdf.docx")
    if override_path:
        path = override_path
    key = Key.from_dictionary(config)
    t = Token(key, path)
    return f"http://localhost:8080/dav/{t.as_url()}"


def test_server_failure(server, config: Dict[str, Any]):
    res = requests.get(make_req(config, Path("blabla.pdf")))
    assert res.status_code == 404


def test_server_file(config: Dict[str, Any], server, server_dir: Path):
    with open(Path(server_dir, "asdf.docx"), "rb") as f:
        exp = f.read()
        res = requests.get(make_req(config))
        assert exp == res.content
