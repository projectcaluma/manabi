from .conftest import get_config, get_server, get_server_dir

if __name__ == "__main__":
    config = get_config(get_server_dir())
    config["manabi"]["secure"] = False
    server = get_server(config)
    server.serve()
