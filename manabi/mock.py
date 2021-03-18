import os
import shutil
from contextlib import contextmanager
from functools import partial
from pathlib import Path
from threading import Thread
from typing import Any, Callable, Dict, Generator, Optional, Tuple
from unittest import mock as unitmock

from cheroot import wsgi  # type: ignore
from wsgidav.debug_filter import WsgiDavDebugFilter  # type: ignore
from wsgidav.dir_browser import WsgiDavDirBrowser  # type: ignore
from wsgidav.error_printer import ErrorPrinter  # type: ignore
from wsgidav.request_resolver import RequestResolver  # type: ignore
from wsgidav.wsgidav_app import WsgiDAVApp  # type: ignore

from .auth import ManabiAuthenticator
from .filesystem import ManabiProvider
from .lock import ManabiLockLockStorage
from .log import HeaderLogger, ResponseLogger
from .token import Key, Token, now
from .util import get_rfc1123_time

_servers: Dict[Tuple[str, int], wsgi.Server] = dict()
_server_dir = Path("/tmp/296fe33fcca.dir")
_lock_storage = Path("/tmp/296fe33fcca.lock")
_module_dir = Path(__file__).parent
_test_file1 = Path(_module_dir, "data", "asdf.docx")
_test_file2 = Path(_module_dir, "data", "qwert.docx")


@contextmanager
def with_config() -> Generator[dict, None, None]:
    with lock_storage() as storage:
        yield get_config(get_server_dir(), storage)


def get_server_dir():
    if not _server_dir.exists():
        _server_dir.mkdir()
    shutil.copy(_test_file1, _server_dir)
    shutil.copy(_test_file2, _server_dir)

    return _server_dir


def get_config(server_dir: Path, lock_storage: Path):
    refresh = 600
    base_url = os.environ.get("MANABI_BASE_URL") or "localhost:8080"
    return {
        "host": "0.0.0.0",
        "port": 8080,
        "mount_path": "/dav",
        "lock_manager": ManabiLockLockStorage(refresh, lock_storage),
        "provider_mapping": {
            "/": ManabiProvider(server_dir),
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
    path2 = Path("nope.docx")
    url2 = Token(key, path2).as_url()
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
    <h1>non-existing</h1>
    <h2>word link</h2>
    <a href="ms-word:ofe|u|http://{base}/dav/{url2}">{path2}</a>
    <h2>webdav link</h2>
    <a href="webdav://{base}/dav/{url2}">{path2}</a>
    <h2>http link</h2>
    <a href="http://{base}/dav/{url2}">{path2}</a>
</body>
</html>
""".strip().encode(
        "UTF-8"
    )

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
        dav_app = WsgiDAVApp(config)

        path_map = {
            "/test": partial(serve_document, config),
            "/dav": dav_app,
        }
        dispatch = wsgi.PathInfoDispatcher(path_map)
        server_args = {
            "bind_addr": bind_addr,
            "wsgi_app": dispatch,
        }

        server = wsgi.Server(**server_args)
        server.prepare()
        _servers[bind_addr] = server
        server._manabi_id = bind_addr
    return server


def remove_server(server: wsgi.Server):
    _servers.pop(server._manabi_id)


@contextmanager
def lock_storage():
    try:
        _lock_storage.unlink()
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
