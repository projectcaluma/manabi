from .conftest import get_config, get_server, run_server

if __name__ == "__main__":
    run_server(get_server(get_config()))
