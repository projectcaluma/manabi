import random
import threading
import time
import xml.etree.ElementTree as ET
from enum import Enum
from multiprocessing.pool import ThreadPool
from typing import Any, Dict
from urllib import request
from urllib.error import HTTPError

import requests
from wsgidav.util import get_module_logger

from manabi import lock as mlock

from . import mock
from .mock import run_server

_logger = get_module_logger(__name__)

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
    try:
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
        req.get_method = lambda: method  # type: ignore
        res = opener.open(req)
        try:
            return res, res.read()
        finally:
            _logger.debug(f"xhttp-test-method {method}: {res.status}")
            res.close()
    except HTTPError as e:
        _logger.debug(f"xhttp-test-mathod {method}: {e.status}")
        raise e


def get_lock_token(xml):
    root = ET.fromstring(xml)
    res = root[0][0][5][0].text
    _logger.debug(f"xtoken {res}")
    return res


def test_connection(server_dir, postgres_dsn):
    config = mock.get_config(server_dir, postgres_dsn)
    lock_storage = config["lock_storage"]
    assert isinstance(lock_storage, mlock.ManabiDbLockStorage)
    lock_storage.cleanup()


def test_lock(config: Dict[str, Any], server):
    expect = str(time.time()).encode("UTF-8")
    req = mock.make_req(config)
    assert requests.get(req).status_code == 200
    try:
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
    finally:
        res, xml = http("UNLOCK", req, token=token)


def test_lock_two_server(server_dir, lock_storage):
    storage = lock_storage
    config = mock.get_config(server_dir, storage)
    config2 = mock.get_config(server_dir, storage)
    config2["port"] = 8082
    with run_server(config), run_server(config2):
        expect = str(time.time()).encode("UTF-8")
        req = req2 = mock.make_req(config)
        req2 = req.replace("http://localhost:8081/dav/", "http://localhost:8082/dav/")
        assert requests.get(req).status_code == 200
        assert requests.get(req2).status_code == 200
        assert requests.get(req).status_code == 200
        try:
            res, xml = http("LOCK", req)
            token = get_lock_token(xml)
            assert res.status == 200

            try:
                # Now the other server should fail without token
                res, xml = http("LOCK", req2)
            except HTTPError as e:
                assert e.status == 423

            # Switch server
            res, xml = http("LOCK", req2, token=token)
            assert res.status == 200
            res, _ = http("PUT", req2, token=token, data=expect)
            assert res.status == 204
            res, data = http("GET", req2, token=token)
            assert res.status == 200
            assert data == expect
        finally:
            res, xml = http("UNLOCK", req, token=token)


class Results(Enum):
    LOCKED_AND_UNLOCKED = 1
    LOCKED_UNLOCK_FAILED = 2
    FIRST_LOCK_FAILED = 3
    UNKNOWN_ERROR = 4
    SERVER_ERROR = 5
    SUCCESS = 6


def run_concurrent_test(server_dir, lock_storage, test, eval_func, nopool=False):
    storage = lock_storage
    config = mock.get_config(server_dir, storage)
    config2 = mock.get_config(server_dir, storage)
    config2["port"] = 8082
    with run_server(config), run_server(config2):
        req = req2 = mock.make_req(config)
        req2 = req.replace("http://localhost:8081/dav/", "http://localhost:8082/dav/")
        reqs = [req] * 50 + [req2] * 50
        random.shuffle(reqs)
        overall_success = None
        if nopool:
            for res, msg in map(test, reqs):
                overall_success = eval_func(overall_success, res, msg)
        else:
            with ThreadPool(8) as pool:
                for res, msg in pool.imap(test, reqs):
                    overall_success = eval_func(overall_success, res, msg)
        assert overall_success


def run_req_test(req):
    try:
        code = requests.get(req).status_code
        return (Results.SUCCESS, code)
    except HTTPError as e:
        if e.status == 500:
            return (Results.SERVER_ERROR, e)
        return (Results.UNKNOWN_ERROR, e)


def evaluate_req(overall_success, res, msg):
    assert res == Results.SUCCESS, msg
    return True


def test_req_spam_server(server_dir, lock_storage):
    run_concurrent_test(server_dir, lock_storage, run_req_test, evaluate_req)


def run_lock_test(req):
    locked = False
    try:
        requests.get(req)
        res, xml = http("LOCK", req)
        # Test condition: If we can lock the file, we should also be able to unlock the file
        if res.status in (200, 204):
            locked = True
            time.sleep(random.random() / 4)
            token = get_lock_token(xml)
            res, xml = http("UNLOCK", req, token=token)
            if res.status in (200, 204):
                return (Results.LOCKED_AND_UNLOCKED, f"status: {res.status}")
            else:
                return (Results.LOCKED_UNLOCK_FAILED, f"status: {res.status}")
        return (Results.FIRST_LOCK_FAILED, f"status: {res.status}")
    except HTTPError as e:
        if e.status == 500:
            return (Results.SERVER_ERROR, e)
        if locked:
            return (Results.LOCKED_UNLOCK_FAILED, e)
        else:
            if e.status == 423:
                return (Results.FIRST_LOCK_FAILED, e)
            else:
                return (Results.UNKNOWN_ERROR, e)
    except Exception as e:
        return (False, e)


# Currently not used, since double locks of the same file are possible, but this is good
# enough for our purposes
def evaluate_result_strict(overall_success, res, msg):
    if overall_success is None:
        overall_success = False
    msg = str(msg)
    if res == Results.LOCKED_AND_UNLOCKED:
        overall_success = True
    elif res == Results.LOCKED_UNLOCK_FAILED:
        raise AssertionError(f"File locked, but unlock failed: {msg}")
    elif res == Results.FIRST_LOCK_FAILED:
        pass
    elif res == Results.UNKNOWN_ERROR:
        raise AssertionError(f"Locking failed with a unknown error: {msg}")
    return overall_success


# Only SERVER_ERROR (500) is a failure, this happens when dict becomes inconsistent
def evaluate_result_loose(overall_success, res, msg):
    if overall_success is None:
        overall_success = False
    msg = str(msg)
    if res == Results.LOCKED_AND_UNLOCKED:
        overall_success = True
    elif res == Results.SERVER_ERROR:
        raise AssertionError(f"wsgidav has thrown a server error (500): {msg}")
    elif res == Results.UNKNOWN_ERROR:
        raise AssertionError(f"Locking failed with a unknown error: {msg}")
    return overall_success


def test_lock_spam_server(server_dir, lock_storage):
    run_concurrent_test(server_dir, lock_storage, run_lock_test, evaluate_result_strict)


def test_lock_chaos_spam_server(chaos, server_dir, postgres_dsn):
    run_concurrent_test(server_dir, postgres_dsn, run_lock_test, evaluate_result_strict)


_thread_count = 0
_local = threading.local()


def run_postgres_lock_test(dsn):
    global _thread_count
    if not hasattr(_local, "lock"):
        storage = mlock.ManabiDbLockStorage(600, dsn)
        storage.open()
        # We don't care about cyclic dependencies in pytest, let gc handle it
        storage._lock._keep_alive = storage  # type: ignore
        _local.lock = storage._lock
    lock = _local.lock
    try:
        lock.acquire()
        _thread_count += 1
        assert _thread_count == 1
        time.sleep(random.random() / 8)
        assert _thread_count == 1
        time.sleep(random.random() / 8)
        assert _thread_count == 1
    except Exception as e:
        return e
    finally:
        _thread_count -= 1
        lock.release()
    return None


def test_postgres_lock(chaos, postgres_dsn):
    global _thread_count

    _thread_count = 0
    reqs = [postgres_dsn] * 50
    with ThreadPool(8) as pool:
        for res in pool.imap(run_postgres_lock_test, reqs):
            if res:
                raise res
