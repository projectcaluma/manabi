from wsgidav.util import init_logging  # type: ignore

from .mock import get_config, get_server_dir


def verbose_logging() -> None:
    config = get_config(get_server_dir())
    init_logging(config)
