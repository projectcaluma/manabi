from .conftest import get_config, get_server, get_server_dir, run_server

if __name__ == "__main__":
    run_server(get_server(get_config(get_server_dir())))
