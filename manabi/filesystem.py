from pathlib import Path
from typing import Any, Dict

from wsgidav.dav_error import HTTP_FORBIDDEN, DAVError  # type: ignore
from wsgidav.fs_dav_provider import FilesystemProvider, FolderResource  # type: ignore

from .token import Token


# TODO maybe for security we should inherit from DAVCollection so it is not possible to
# leak information, if the implementation of FolderResource changes
#
# Attack by authenticated user
class ManabiFolderResource(FolderResource):
    def get_member_names(self):
        token: Token = self.environ["manabi.token"]
        path = token.path
        names = super().get_member_names()
        return list(filter(lambda x: Path(x) == path, names))

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


# TODO maybe for security we should inherit from DAVProvider so it is not possible to
# leak information, if the implementation of FilesystemProvider changes
#
# Attack by authenticated user
class ManabiProvider(FilesystemProvider):
    def get_resource_inst(self, path: str, environ: Dict[str, Any]):
        token: Token = environ["manabi.token"]
        dir_access = environ["manabi.dir_access"]
        if dir_access:
            assert token.path
            path = f"/{str(token.path.parent)}"
            fp = self._loc_to_file_path(path, environ)
            return ManabiFolderResource(path, environ, fp)
        else:
            path = token.path_as_url()
            return super().get_resource_inst(path, environ)
