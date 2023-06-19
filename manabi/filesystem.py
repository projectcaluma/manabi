from pathlib import Path
from typing import Any, Dict

from wsgidav.dav_error import HTTP_FORBIDDEN, DAVError
from wsgidav.fs_dav_provider import FileResource, FilesystemProvider, FolderResource

from .token import Token
from .util import requests_session


class ManabiFolderResource(FolderResource):
    def get_member_names(self):
        token: Token = self.environ["manabi.token"]
        # type manually checked
        token_path: Path = token.path  # type: ignore
        if not token_path:
            return []
        path = Path(self._file_path, token_path)
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
    def __init__(self, path, environ, file_path, pre_write_hook=None):
        self._pre_write_hook = pre_write_hook
        self._token = environ["manabi.token"]
        super().__init__(path, environ, file_path)

    def delete(self):
        raise DAVError(HTTP_FORBIDDEN)

    def copy_move_single(self, dest_path, is_move):
        raise DAVError(HTTP_FORBIDDEN)

    def support_recursive_move(self, dest_path):
        return False

    def move_recursive(self, dest_path):
        raise DAVError(HTTP_FORBIDDEN)

    def begin_write(self, *, content_type):
        pre = self._pre_write_hook
        token = self._token
        if pre and token:
            session = requests_session()
            session.post(pre, data=token.encode())
        # The webhhook returned and hopefully created a new version.
        # Now we can save.
        return super().begin_write(content_type=content_type)


class ManabiProvider(FilesystemProvider):
    def __init__(
        self, root_folder, *, readonly=False, shadow=None, pre_write_hook=None
    ):
        self._pre_write_hook = pre_write_hook
        super().__init__(root_folder, readonly=readonly, shadow=shadow)

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
                return ManabiFileResource(
                    path,
                    environ,
                    fp,
                    self._pre_write_hook,
                )
            else:
                return None
