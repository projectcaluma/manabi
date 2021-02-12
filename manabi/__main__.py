if __name__ == "__main__":
    # This needs dev-requirements
    from .log import verbose_logging
    from .mock import get_server, with_config

    with with_config() as config:
        config["manabi"]["secure"] = False
        verbose_logging()
        server = get_server(config)
        server.serve()
