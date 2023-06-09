from pathlib import Path

import wsgidav


def fix():
    # Workaround for https://github.com/python/mypy/issues/8545
    try:
        (Path(wsgidav.__file__).absolute().parent / "py.typed").touch()
    except Exception:
        pass


if __name__ == "__main__":
    fix()
