if __name__ == "__main__":
    # This needs dev-requirements
    from .log import verbose_logging
    from .mock import get_config, get_server, get_server_dir

    config = get_config(get_server_dir())
    config["manabi"]["secure"] = False
    verbose_logging()
    server = get_server(config)
    server.serve()
