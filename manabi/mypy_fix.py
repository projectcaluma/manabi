from pathlib import Path

import boto3
import botocore
import smart_open
import wsgidav


def fix():
    # Workaround for https://github.com/python/mypy/issues/8545
    for module in [wsgidav, boto3, botocore, smart_open]:
        try:
            file = module.__file__
            if file:
                (Path(file).absolute().parent / "py.typed").touch()
        except Exception as e:
            print(e)


if __name__ == "__main__":
    fix()
