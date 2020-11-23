from typing import Any, Dict

from wsgidav.fs_dav_provider import FilesystemProvider  # type: ignore

from .token import Token


class ManabiProvider(FilesystemProvider):
    def get_resource_inst(self, path: str, environ: Dict[str, Any]):
        token: Token = environ["manabi.token"]
        dir_access = environ["manabi.dir_access"]
        if dir_access:
            path = "/"
        else:
            path = token.path_as_url()
        inst = super().get_resource_inst(path, environ)
        return inst
