import argparse
import sys
from pathlib import Path

from manabi.util import get_boto_client

# This needs dev-requirements
from .log import verbose_logging
from .mock import get_server, make_req, upload_file_to_s3, with_config


def parse_args(argv):
    parser = argparse.ArgumentParser(description="Manabi")
    parser.add_argument("--s3", help="Use s3", default=False, action="store_true")
    parser.add_argument(
        "-l",
        "--link",
        help="Print a link on startup",
        default=False,
        action="store_true",
    )
    return parser.parse_args(argv)


if __name__ == "__main__":
    args = parse_args(sys.argv[1:])

    with with_config(args.s3) as config:
        config["manabi"]["secure"] = False
        verbose_logging()
        if args.link:
            link = make_req(
                config,
                override_path=Path("asdf-s3.docx") if args.s3 else Path("asdf.docx"),
            )
            print(link)
        if args.s3:
            s3 = get_boto_client()
            upload_file_to_s3(s3)
        server = get_server(config)
        server.serve()
