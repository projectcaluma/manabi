from pathlib import Path
from typing import Any, Dict

from wsgidav.dav_error import HTTP_FORBIDDEN, DAVError  # type: ignore
from wsgidav.fs_dav_provider import (  # type: ignore
    FileResource,
    FilesystemProvider,
    FolderResource,
)

from .token import Token


class ManabiFolderResource(FolderResource):
    def get_member_names(self):
        token: Token = self.environ["manabi.token"]
        path = Path(self._file_path, token.path)
        if path.exists():
            return [str(token.path)]
        else:
            return []

    def get_member(self, name):
        token: Token = self.environ["manabi.token"]
        path = token.path
        if Path(name) != path:
            raise DAVError(HTTP_FORBIDDEN)
        return super().get_member(name)

    def create_empty_resource(self, name):
        raise DAVError(HTTP_FORBIDDEN)

    def create_collection(self, name):
        raise DAVError(HTTP_FORBIDDEN)

    def delete(self):
        raise DAVError(HTTP_FORBIDDEN)

    def copy_move_single(self, dest_path, is_move):
        raise DAVError(HTTP_FORBIDDEN)

    def support_recursive_move(self, dest_path):
        return False

    def move_recursive(self, dest_path):
        raise DAVError(HTTP_FORBIDDEN)

    def set_last_modified(self, dest_path, time_stamp, dry_run):
        raise DAVError(HTTP_FORBIDDEN)


class ManabiFileResource(FileResource):
    def delete(self):
        raise DAVError(HTTP_FORBIDDEN)

    def copy_move_single(self, dest_path, is_move):
        raise DAVError(HTTP_FORBIDDEN)

    def support_recursive_move(self, dest_path):
        return False

    def move_recursive(self, dest_path):
        raise DAVError(HTTP_FORBIDDEN)


class ManabiProvider(FilesystemProvider):
    def get_resource_inst(self, path: str, environ: Dict[str, Any]):
        token: Token = environ["manabi.token"]
        dir_access = environ["manabi.dir_access"]
        if dir_access:
            assert token.path
            path = f"/{str(token.path.parent)}"
        fp = self._loc_to_file_path(path, environ)
        if dir_access or Path(fp).is_dir():
            return ManabiFolderResource(path, environ, fp)
        else:
            path = token.path_as_url()
            fp = self._loc_to_file_path(path, environ)
            if Path(fp).exists():
                return ManabiFileResource(path, environ, fp)
            else:
                return None
