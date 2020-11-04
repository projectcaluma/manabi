import pytest

from .token import check_token, make_token


@pytest.mark.parametrize("tamper", (True, False))
@pytest.mark.parametrize("expire", (True, False))
@pytest.mark.parametrize("path", (True, False))
def test_make_token(tamper, expire, path, config):
    key = config["manabi"]["key"]
    ttl = None
    path = "asdf.docx"
    check = True
    if expire:
        ttl = 1
        check = False
        data = make_token(key, path, 1)
    else:
        data = make_token(key, path)
    if tamper:
        data = data[0:3] + "f" + data[4:]
    if tamper or expire:
        with pytest.raises(RuntimeError):
            check_token(key, data, path, ttl)
    else:
        assert check_token(key, data, path, ttl) == check
