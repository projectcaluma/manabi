import os
import random
import shutil
from collections.abc import Generator
from contextlib import contextmanager
from functools import partial
from glob import glob
from pathlib import Path
from threading import Thread
from typing import Any, Callable, Dict, Optional, Tuple, Union
from unittest import mock as unitmock

import requests_mock
from cheroot import wsgi  # type: ignore
from wsgidav.dir_browser import WsgiDavDirBrowser
from wsgidav.error_printer import ErrorPrinter
from wsgidav.mw.debug_filter import WsgiDavDebugFilter
from wsgidav.request_resolver import RequestResolver

from . import ManabiDAVApp, lock as mlock
from .auth import ManabiAuthenticator
from .filesystem import CallbackHookConfig, ManabiProvider, ManabiS3Provider
from .lock import ManabiDbLockStorage as ManabiDbLockStorageOrig
from .log import HeaderLogger, ResponseLogger
from .token import Config, Key, Token, now
from .type_alias import WriteType
from .util import get_rfc1123_time

_servers: Dict[Tuple[str, int], wsgi.Server] = dict()
_server_dir = Path("/tmp/296fe33fcca.dir")
_lock_storage = Path("/tmp/296fe33fcca.lock")
_module_dir = Path(__file__).parent
_test_file1 = Path(_module_dir, "data", "asdf.docx")
_test_file2 = Path(_module_dir, "data", "qwert.docx")
_postgres_dsn = "dbname=manabi user=manabi host=localhost password=manabi"

TEST_FILES_DIR = Path(__file__).parent.resolve() / "data"


@contextmanager
def with_config(use_s3=False) -> Generator[dict, None, None]:
    with lock_storage() as storage:
        yield get_config(get_server_dir(), storage, use_s3=use_s3)


def get_server_dir():
    if not _server_dir.exists():
        _server_dir.mkdir()
    shutil.copy(_test_file1, _server_dir)
    shutil.copy(_test_file2, _server_dir)

    return _server_dir


_check_token_return = True


def check_token(token: Token) -> bool:
    assert token.check()
    return _check_token_return


_pre_write_hook: Optional[str] = None
_post_write_hook: Optional[str] = None


@contextmanager
def with_write_hooks(config: Dict[str, Any], status_code=None):
    if not (_pre_write_hook and _post_write_hook):
        return

    cfg = Config.from_dictionary(config)

    def check_token(request, context):
        if status_code:
            context.status_code = status_code
            return
        token = Token.from_ciphertext(cfg.key, request.text)
        if token.check():
            context.status_code = 200
        else:
            context.status_code = 403

    with requests_mock.Mocker(real_http=True) as m:
        m.post(_pre_write_hook, text=check_token)
        m.post(_post_write_hook, text=check_token)
        yield


_pre_write_callback: Optional[WriteType] = None
_post_write_callback: Optional[WriteType] = None


def get_config(server_dir: Path, lock_storage: Union[Path, str], use_s3: bool = False):
    refresh = 600
    base_url = os.environ.get("MANABI_BASE_URL") or "localhost:8081"
    lock_obj: Union[mlock.ManabiShelfLockLockStorage, mlock.ManabiDbLockStorage]
    if isinstance(lock_storage, Path):
        lock_obj = mlock.ManabiShelfLockLockStorage(refresh, lock_storage)
    else:
        lock_obj = mlock.ManabiDbLockStorage(refresh, lock_storage)
    cb_hook_config = CallbackHookConfig(
        pre_write_hook=_pre_write_hook,
        pre_write_callback=_pre_write_callback,
        post_write_hook=_post_write_hook,
        post_write_callback=_post_write_callback,
    )
    provider_class: type[Union[ManabiProvider, ManabiS3Provider]] = ManabiProvider
    provider_kwargs: dict[str, str] = {}
    if use_s3:
        provider_class = ManabiS3Provider
        provider_kwargs = {
            "endpoint_url": os.environ.get("S3_ENDPOINT", "http://127.0.0.1:9000"),
            "aws_access_key_id": os.environ.get("S3_ACCESS_KEY_ID", "veryvery"),
            "aws_secret_access_key": os.environ.get(
                "S3_SECRET_ACCESS_KEY", "secretsecret"
            ),
            "region_name": os.environ.get("S3_REGION", "us-east-1"),
            "bucket_name": os.environ.get("S3_BUCKET_NAME", "manabi-media"),
        }

    return {
        "cb_hook_config": cb_hook_config,
        "host": "0.0.0.0",
        "port": 8081,
        "mount_path": "/dav",
        "lock_storage": lock_obj,
        "provider_mapping": {
            "/": provider_class(
                server_dir, cb_hook_config=cb_hook_config, **provider_kwargs
            ),
        },
        "middleware_stack": [
            HeaderLogger,
            ResponseLogger,
            WsgiDavDebugFilter,
            ErrorPrinter,
            ManabiAuthenticator,
            WsgiDavDirBrowser,
            RequestResolver,
        ],
        "manabi": {
            "key": "ur7Q80cCgjDsrciXbuRKLF83xqWDdzGhXaPwpwz7boG",
            "refresh": refresh,
            "initial": 600,
            "base_url": base_url,
        },
        "hotfixes": {
            "re_encode_path_info": False,
        },
    }


def serve_document(
    config: Dict[str, Any], environ: Dict[str, Any], start_response: Callable
):
    key = Key.from_dictionary(config)
    path1 = Path("asdf.docx")
    url1 = Token(key, path1).as_url()
    path2 = Path("asdf-s3.docx")
    url2 = Token(key, path2).as_url()
    path3 = Path("nope.docx")
    url3 = Token(key, path3).as_url()
    base = config["manabi"]["base_url"]
    script = """
function copy_command(input) {
  var copyText = document.getElementById(input);
  copyText.select();
  copyText.setSelectionRange(0, 99999); /*For mobile devices*/
  document.execCommand("copy");
  alert("Copied the text: " + copyText.value);
}
"""
    body = f"""
<!doctype html>

<html lang="en">
<head>
  <meta charset="utf-8">

  <title>WebDAV test page</title>
</head>
<script>
{script}
</script>
<body>
    <h1>existing</h1>
    <h2>word link</h2>
    <a href="ms-word:ofe|u|http://{base}/dav/{url1}">{path1}</a>
    <h2>webdav link</h2>
    <a href="webdav://{base}/dav/{url1}">{path1}</a>
    <h2>http link</h2>
    <a href="http://{base}/dav/{url1}">{path1}</a>
    <h2>libreoffice command</h2>
    LibreOffice does not support cookies so it is not a very good test and only LibreOffice 7+ works at all.
    <a href="https://git.libreoffice.org/core/+/58b84caca87c893ac04f0b1399aeadc839a2f075%5E%21">Bug fix.</a>
    <input type="text" value="libreoffice webdav://{base}/dav/{url1}" id="existing" size="115">
    <button onclick="copy_command('existing')">Copy command</button>
    <h1>S3</h1>
    <h2>word link</h2>
    <a href="ms-word:ofe|u|http://{base}/dav/{url2}">{path2}</a>
    <h2>webdav link</h2>
    <a href="webdav://{base}/dav/{url2}">{path2}</a>
    <h2>http link</h2>
    <a href="http://{base}/dav/{url2}">{path2}</a>
    <h2>libreoffice command</h2>
    LibreOffice does not support cookies so it is not a very good test and only LibreOffice 7+ works at all.
    <a href="https://git.libreoffice.org/core/+/58b84caca87c893ac04f0b1399aeadc839a2f075%5E%21">Bug fix.</a>
    <input type="text" value="libreoffice webdav://{base}/dav/{url2}" id="existing-s3" size="115">
    <button onclick="copy_command('existing-s3')">Copy command</button>
    <h1>non-existing</h1>
    <h2>word link</h2>
    <a href="ms-word:ofe|u|http://{base}/dav/{url3}">{path3}</a>
    <h2>webdav link</h2>
    <a href="webdav://{base}/dav/{url3}">{path3}</a>
    <h2>http link</h2>
    <a href="http://{base}/dav/{url3}">{path3}</a>
</body>
</html>
""".strip().encode("UTF-8")

    start_response(
        "200 Ok",
        [
            ("Content-Type", "text/html"),
            ("Content-Length", str(len(body))),
            ("Date", get_rfc1123_time()),
        ],
    )
    return [body]


def get_server(config: Dict[str, Any]) -> wsgi.Server:
    bind_addr = (config["host"], config["port"])
    server = _servers.get(bind_addr)
    if not server:
        dav_app = ManabiDAVApp(config)

        path_map = {
            "/test": partial(serve_document, config),
            "/dav": dav_app,
        }
        dispatch = wsgi.PathInfoDispatcher(path_map)
        server = wsgi.Server(bind_addr, dispatch, numthreads=1)
        server.prepare()
        _servers[bind_addr] = server
        server._manabi_id = bind_addr  # type: ignore
    return server


def remove_server(server: wsgi.Server):
    _servers.pop(server._manabi_id)  # type: ignore


@contextmanager
def lock_storage():
    try:
        for f in glob(f"{_lock_storage}*"):
            Path(f).unlink()
    except FileNotFoundError:
        pass
    yield Path(_lock_storage)


@contextmanager
def shift_now(offset: int) -> Generator[unitmock.MagicMock, None, None]:
    new = now() + offset
    with unitmock.patch("manabi.token.now") as m:
        m.return_value = new
        yield m


@contextmanager
def run_server(config: Dict[str, Any]) -> Generator[None, None, None]:
    server = get_server(config)
    thread = Thread(target=partial(server.serve))
    thread.start()
    try:
        yield
    finally:
        server.stop()
        thread.join()
        remove_server(server)


@contextmanager
def branca_impl() -> Generator[None, None, None]:
    cwd = Path().cwd()
    os.chdir(Path(_module_dir.parent, "branca-test"))
    yield
    os.chdir(cwd)


def make_token(config: Dict[str, Any], override_path: Optional[Path] = None) -> Token:
    path = Path("asdf.docx")
    if override_path:
        path = override_path
    key = Key.from_dictionary(config)
    return Token(key, path)


def make_req(
    config: Dict[str, Any],
    override_path: Optional[Path] = None,
) -> str:
    t = make_token(config, override_path)
    port = config["port"]
    return f"http://localhost:{port}/dav/{t.as_url()}"


def upload_file_to_s3(s3):
    with _test_file1.open("rb") as f:
        s3.put_object(
            Bucket=os.environ.get("S3_BUCKET_NAME", "manabi-media"),
            Key=str(_server_dir / "asdf-s3.docx"),
            Body=f.read(),
        )


class MockManabiDbLockStorage(ManabiDbLockStorageOrig):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def execute(self, *args, **kwargs):
        if random.random() > 0.8 and self._lock._semaphore == 0:
            self._connection.close()
        return super().execute(*args, **kwargs)
