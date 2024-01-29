from pathlib import Path
from typing import Any, Dict

import pytest
import requests
from moto import mock_aws

from . import mock
from .conftest import TEST_FILES_DIR


@pytest.mark.parametrize(
    "config,use_s3,file_name",
    [(True, True, "asdf-s3.docx"), (False, False, "asdf.docx")],
    indirect=["config"],
)
@pytest.mark.parametrize(
    "tamper, exists, expect_status",
    [(True, True, 403), (False, True, 204), (True, False, 403), (False, False, 403)],
)
def test_get_and_put(
    use_s3,
    file_name,
    tamper,
    exists,
    expect_status,
    config: Dict[str, Any],
    s3_file,
    server,
):
    if not exists:
        file_name = "nonexistent.docx"
    req = mock.make_req(config, override_path=Path(file_name))
    with mock_aws():
        res = requests.get(req)
    assert res.status_code == 200 if exists else 404
    if tamper:
        i = 58
        if req[i] == "f":
            req = req[0:i] + "g" + req[i + 1 :]
        else:
            req = req[0:i] + "f" + req[i + 1 :]
    with mock_aws():
        res = requests.put(req, data=res.content)

    assert res.status_code == expect_status


@pytest.mark.parametrize(
    "config,use_s3,file_name",
    [(True, True, "asdf-s3.docx"), (False, False, "asdf.docx")],
    indirect=["config"],
)
@pytest.mark.parametrize(
    "url_addition",
    ["", "/", "foobarbaz", "foo/", "/foo/", "/foo/bar/baz/"],
)
def test_collection_propfind(
    config: Dict[str, Any], use_s3, file_name, url_addition, s3_file, server, snapshot
):
    propfind_request = """<?xml version="1.0"?>
        <a:propfind
            xmlns:a="DAV:">
            <a:prop>
                <a:resourcetype/>
            </a:prop>
        </a:propfind>"""

    req = (
        f"{mock.make_req(config, override_path=Path(file_name)).rstrip(file_name)}"
        f"{url_addition}"
    )
    session = requests.Session()
    with mock_aws():
        res = session.request(
            method="PROPFIND",
            url=req,
            data=propfind_request,
            headers={"Depth": "1"},
        )
    assert res.status_code == 207
    assert res.content == snapshot


@pytest.mark.skip(reason="Integration test. Useful in dev with minIO")
@pytest.mark.parametrize("config", [True], indirect=["config"])  # use S3
@pytest.mark.parametrize("expect_status", [204])
def test_get_and_put_s3_integration(
    expect_status, config: Dict[str, Any], server, s3_file
):
    with (TEST_FILES_DIR / "asdf.docx").open("rb") as f:
        asdf_bytes = f.read()
    with (TEST_FILES_DIR / "qwert.docx").open("rb") as f:
        qwert_bytes = f.read()
    req = mock.make_req(config, override_path=Path("asdf-s3.docx"))
    res = requests.get(req)
    assert res.status_code == 200
    assert res.content == asdf_bytes
    res = requests.put(req, data=qwert_bytes)
    assert res.status_code == expect_status
    res = requests.get(req)
    assert res.status_code == 200
    assert res.content == qwert_bytes


@pytest.mark.parametrize(
    "hook_status, expect_status",
    [
        (None, 204),
        (403, 403),
        (200, 204),
    ],
)
def test_get_and_put_hooked(
    hook_status, expect_status, write_hooks, config: Dict[str, Any], server
):
    cb_hook_config = config["cb_hook_config"]
    assert cb_hook_config.pre_write_hook == "http://127.0.0.1/pre_write_hook"
    assert cb_hook_config.post_write_hook == "http://127.0.0.1/post_write_hook"
    with mock.with_write_hooks(config, hook_status):
        req = mock.make_req(config)
        res = requests.get(req)
        assert res.status_code == 200
        res = requests.put(req, data=res.content)
        assert res.status_code == expect_status


@pytest.mark.parametrize("callback_return, expect_status", [(False, 403), (True, 204)])
def test_get_and_put_called(
    callback_return,
    expect_status,
    write_callback,
    config: Dict[str, Any],
    server,
):
    assert config["cb_hook_config"].pre_write_callback == write_callback
    assert config["cb_hook_config"].post_write_callback == write_callback
    req = mock.make_req(config)
    res = requests.get(req)
    assert res.status_code == 200
    try:
        mock._check_token_return = callback_return
        res = requests.put(req, data=res.content)
        assert res.status_code == expect_status
    finally:
        mock._check_token_return = True
