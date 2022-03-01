Manabi
======

Install
-------

Make sure libsodium exists on the system, for example execute:

```bash
apk add --no-cache libsodium
apt-get install -y libsodium23
```

Dev
===

Currently wsgidav is broken for python 3.8+.

Enable dev-env:

```bash
pyenv install 3.7.10
poetry env use $HOME/.pyenv/versions/3.7.10/bin/python3.7
poetry install
poetry shell
```

Config
------

Call `manabi-keygen` and add the key to `config["manabi"]["key"]`. The key is
shared between the caluma/alexandria backend and the WebDAV server.

mount_path
: prefix that gets passed to wsgidav, if URL rewrites remove any prefixes use
`"/"`

lock_manager
: The ManabiLockLockStorage forces the WebDav log-timeout to 
`token-refresh-time / 2`

provider_mapping
: Extends the FilesystemProvider any will only serve files if the token is valid

middleware_stack
: based on the default middleware_stack but HTTPAuthenticator is replace by
ManabiAuthenticator, which validates the tokens.

manabi.key
: shared-key between the server that creates tokens to grant access and wsgi-dav

manabi.refresh
: how often tokens are refreshed in seconds, we recommend 10 minutes: `600`

manabi.initial
: the time from the token being generated till it has to be refreshed the first
time, we recommend 1 minues: `60`. In case tokens leak, for example via cache on
a computer, tokens should be expired by the time an adversary gets them.

```python
config = {
    "mount_path": "/dav",
    "lock_manager": ManabiLockLockStorage(refresh),
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
```
