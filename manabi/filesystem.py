from typing import Any, Dict

from wsgidav.fs_dav_provider import FilesystemProvider  # type: ignore


class ManabiProvider(FilesystemProvider):
    def get_resource_inst(self, path: str, environ: Dict[str, Any]):
        return super().get_resource_inst(environ["manabi.path"], environ)
