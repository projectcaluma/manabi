from wsgidav.util import init_logging  # type: ignore


def verbose_logging() -> None:
    # Enable everything that seems like module that could have logging
    init_logging(
        {
            "verbose": 5,
            "enable_loggers": [
                "lock_manager",
                "lock_storage",
                "request_resolver",
                "request_server",
                "http_authenticator",
                "property_manager",
                "fs_dav_provider" "dir_browser" "server",
            ],
        }
    )
