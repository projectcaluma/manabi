Manabi
======

Install
-------

Make sure libsodium exists on the system, for example execute:

```bash
apk add --no-cache libsodium
apt-get install -y libsodium23
```

Config
------

Call `manabi-keygen` and add the key to `config["manabi"]["key"]`. The key is
shared between the caluma/alexandria backend and the WebDAV server.

Dev
===

When changing dependencies or the build image, ie any of these files:

* c/install
* c/pipinstall
* Dockerfile
* Pipfile
* Pipfile.lock
* setup.cfg
* setup.py
* MANIFEST.in

You need to merge the changes to master first, because the container can only be
published by a master build.

!! Do not forget to increment MANABI_IMAGE_VERSION in ./c/config


TODO later
----------

* use has_a instead of is_a to harden against implementation changes

Some ways to plug into wsgidav
------------------------------

Python code:

```python
from wsgidav.dc.simple_dc import SimpleDomainController
from wsgidav.fs_dav_provider import FilesystemProvider
from wsgidav.middleware import BaseMiddleware


class ManabiAuthenticator(BaseMiddleware):
    def __call__(self, environ, start_response):
        print("hello middleware")
        return self.next_app(environ, start_response)


class ManabiDomainCotroller(SimpleDomainController):
    def require_authentication(self, realm, environ):
        print("hello controller")
        return False


class ManabiProvider(FilesystemProvider):
    def get_resource_inst(self, path, environ):
        print("hello provider")
        return super().get_resource_inst(path, environ)
```

Config:

```python
config = {
    "host": "0.0.0.0",
    "port": 8080,
    "provider_mapping": {
        "/": ManabiProvider("/home/sonder"),
    },
    "verbose": 1,
    "middleware_stack": [
        WsgiDavDebugFilter,
        ErrorPrinter,
        ManabiAuthenticator,
        WsgiDavDirBrowser,
        RequestResolver,
    ],
    "http_authenticator": {"domain_controller": ManabiDomainCotroller},
}
```
