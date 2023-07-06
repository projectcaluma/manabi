from pathlib import Path
from typing import Any, Dict, Optional

from attr import dataclass
from wsgidav.dav_error import HTTP_FORBIDDEN, DAVError
from wsgidav.fs_dav_provider import FileResource, FilesystemProvider, FolderResource

from .token import Token
from .type_alias import WriteType
from .util import cattrib, requests_session


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


@dataclass
class CallbackHookConfig:
    pre_write_hook: Optional[str] = cattrib(Optional[str], default=None)
    pre_write_callback: Optional[WriteType] = cattrib(Optional[WriteType], default=None)
    post_write_hook: Optional[str] = cattrib(Optional[str], default=None)
    post_write_callback: Optional[WriteType] = cattrib(
        Optional[WriteType], default=None
    )


class ManabiFileResource(FileResource):
    def __init__(
        self,
        path,
        environ,
        file_path,
        *,
        cb_hook_config: Optional[CallbackHookConfig] = None,
    ):
        self._cb_config = cb_hook_config
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

    def get_token_and_config(self):
        token = self._token
        config = self._cb_config
        return token and config, token, config

    def process_post_write_hooks(self):
        ok, token, config = self.get_token_and_config()
        if not ok:
            return
        post_hook = config.post_write_hook
        post_callback = config.post_write_callback

        if post_hook:
            session = requests_session()
            session.post(post_hook, data=token.encode())
        if post_callback:
            post_callback(token)

    def end_write(self, *, with_errors):
        if not with_errors:
            self.process_post_write_hooks()

    def process_pre_write_hooks(self):
        ok, token, config = self.get_token_and_config()
        if not ok:
            return
        pre_hook = config.pre_write_hook
        pre_callback = config.pre_write_callback

        if pre_hook:
            session = requests_session()
            res = session.post(pre_hook, data=token.encode())
            if res.status_code != 200:
                raise DAVError(HTTP_FORBIDDEN)
        if pre_callback:
            if not pre_callback(token):
                raise DAVError(HTTP_FORBIDDEN)

    def begin_write(self, *, content_type):
        self.process_pre_write_hooks()
        return super().begin_write(content_type=content_type)


class ManabiProvider(FilesystemProvider):
    def __init__(
        self,
        root_folder,
        *,
        readonly=False,
        shadow=None,
        cb_hook_config: Optional[CallbackHookConfig] = None,
    ):
        self._cb_hook_config = cb_hook_config
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
                    cb_hook_config=self._cb_hook_config,
                )
            else:
                return None
