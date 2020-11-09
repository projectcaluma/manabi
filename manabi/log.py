from wsgidav.util import init_logging

from .mock import get_config, get_server_dir

config = get_config(get_server_dir())
init_logging(config)
