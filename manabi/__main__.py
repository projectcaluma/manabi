from .conftest import get_config, get_server, get_server_dir

if __name__ == "__main__":
    server = get_server(get_config(get_server_dir()))
    server.serve()
