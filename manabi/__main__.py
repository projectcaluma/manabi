if __name__ == "__main__":
    # This needs dev-requirements
    from .mock import get_config, get_server, get_server_dir

    config = get_config(get_server_dir())
    config["manabi"]["secure"] = False
    server = get_server(config)
    server.serve()
