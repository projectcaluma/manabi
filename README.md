Manabi
======


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
