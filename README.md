# Manabi

## Install

Make sure libsodium exists on the system, for example execute:

```bash
apk add --no-cache libsodium
apt-get install -y libsodium23
```

# Dev

Enable dev-env:

```bash
pyenv install 3.10.2
poetry env use $HOME/.pyenv/versions/3.10.2/bin/python3.10
poetry install
poetry shell
docker-compose up -d db
(cd manabi_django && ./manage.py migrate manabi_migrations)
```

## Config

Call `manabi-keygen` and add the key to `config["manabi"]["key"]`. The key is
shared between the caluma/alexandria backend and the WebDAV server.

`mount_path`

Prefix that gets passed to wsgidav, if URL rewrites remove any prefixes use `"/"`

`lock_storage`

The ManabiLockLockStorage forces the WebDav log-timeout to `token-refresh-time / 2`

`provider_mapping`

Extends the FilesystemProvider any will only serve files if the token is valid

`middleware_stack`

Based on the default middleware_stack but HTTPAuthenticator is replace by
ManabiAuthenticator, which validates the tokens.

`manabi.key`

Shared-key between the server that creates tokens to grant access and wsgi-dav

`manabi.refresh`

How often tokens are refreshed in seconds, we recommend 10 minutes: `600`

`manabi.initial`

The time from the token being generated till it has to be refreshed the first
time, we recommend 1 minues: `60`. In case tokens leak, for example via cache on
a computer, tokens should be expired by the time an adversary gets them.

```python
from manabi import ManabiDAVApp

postgres_dsn = "dbname=manabi user=manabi host=localhost password=manabi"
config = {
    "mount_path": "/dav",
    "lock_storage": ManabiDbLockStorage(refresh, postgres_dsn),
    "provider_mapping": {
        "/": ManabiProvider(settings.MEDIA_ROOT),
    },
    "middleware_stack": [
        WsgiDavDebugFilter,
        ErrorPrinter,
        ManabiAuthenticator,
        WsgiDavDirBrowser,
        RequestResolver,
    ],
    "manabi": {
        "key": key,
        "refresh": refresh,
        "initial": settings.MANABI_TOKEN_ACTIVATE_TIMEOUT,
    },
}
dav_app = ManabiDAVApp(config)
```
