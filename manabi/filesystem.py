import time
from pathlib import Path
from typing import Any, Dict, Optional

from attr import dataclass
from botocore.exceptions import ClientError
from smart_open import open as s3_open
from wsgidav.dav_error import HTTP_FORBIDDEN, DAVError
from wsgidav.dav_provider import DAVCollection, DAVNonCollection
from wsgidav.fs_dav_provider import FileResource, FilesystemProvider
from wsgidav.util import join_uri

from .token import Token
from .type_alias import WriteType
from .util import cattrib, get_boto_client, requests_session


class ManabiFolderResource(DAVCollection):
    def __init__(self, path: str, environ: dict):
        super().__init__(path, environ)
        self.token_path: Path = self.environ["manabi.token"].path

    def get_member_names(self):
        # type manually checked
        return [str(self.token_path)] if self.token_path else []

    def get_member(self, name):
        if Path(name) != self.token_path:
            raise DAVError(HTTP_FORBIDDEN)
        return self.provider.get_resource_inst(join_uri(self.path, name), self.environ)

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


class ManabiFileResourceMixin:
    _token: Token
    _cb_config: Optional[CallbackHookConfig]

    def delete(self):
        raise DAVError(HTTP_FORBIDDEN)

    def copy_move_single(self, dest_path, is_move):
        raise DAVError(HTTP_FORBIDDEN)

    def support_recursive_move(self, dest_path):
        return False

    def move_recursive(self, dest_path):
        raise DAVError(HTTP_FORBIDDEN)

    def _get_token_and_config(self):
        token = self._token
        config = self._cb_config
        return token and config, token, config

    def process_post_write_hooks(self):
        ok, token, config = self._get_token_and_config()
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
        ok, token, config = self._get_token_and_config()
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


class ManabiFileResource(ManabiFileResourceMixin, FileResource):
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

    def begin_write(self, *, content_type=None):
        self.process_pre_write_hooks()
        return super().begin_write(content_type=content_type)


class ManabiProvider(FilesystemProvider):
    def __init__(
        self,
        root_folder,
        *,
        readonly=False,
        fs_opts=None,
        cb_hook_config: Optional[CallbackHookConfig] = None,
    ):
        self._cb_hook_config = cb_hook_config
        super().__init__(root_folder, readonly=readonly, fs_opts=fs_opts)

    def get_file_resource(self, path, environ, fp):
        if Path(fp).exists():
            return ManabiFileResource(
                path,
                environ,
                fp,
                cb_hook_config=self._cb_hook_config,
            )

    def get_resource_inst(self, path: str, environ: Dict[str, Any]):
        token: Token = environ["manabi.token"]
        if path.lstrip("/") != str(token.path):
            return ManabiFolderResource(path, environ)

        path = token.path_as_url()
        fp = self._loc_to_file_path(path, environ)
        return self.get_file_resource(path, environ, fp)


class ManabiS3FileResource(ManabiFileResourceMixin, DAVNonCollection):
    def __init__(
        self,
        s3,
        bucket_name,
        path,
        environ,
        file_path,
        *,
        cb_hook_config: Optional[CallbackHookConfig] = None,
    ):
        self.provider: ManabiS3Provider
        super().__init__(path, environ)
        self.s3 = s3
        self.bucket_name = bucket_name
        self._cb_config = cb_hook_config
        self._token = environ["manabi.token"]
        self.path = path

        # if the files reside in the buckets top-level directory, there is a difference
        # between MinIO and S3. MinIO doesn't use a database as opposed to S3. That's
        # the reason, why leading slashes are not preserved. For S3 on the other hand,
        # we need to manually strip them.
        # -> https://github.com/minio/minio/issues/17356#issuecomment-1578787168
        if self.provider.root_folder_path == "/":
            file_path = file_path.lstrip("/")

        self.file_path = file_path
        self.file_obj = self.s3.get_object(Bucket=self.bucket_name, Key=self.file_path)
        self.name = Path(self.path).name

    def support_etag(self):
        return True

    def get_content_length(self):
        return self.file_obj["ContentLength"]

    def get_content_type(self):
        return self.file_obj["ContentType"]

    def get_creation_date(self):
        # Amazon S3 maintains only the last modified date for each object.
        return self.get_last_modified()

    def get_etag(self):
        return self.file_obj["ETag"].strip('"')

    def get_last_modified(self):
        return time.mktime(self.file_obj["LastModified"].timetuple())

    def get_content(self):
        """Open content as a stream for reading.

        We can't call `super()` here, because we need to use `open` from `smart_open`.
        """
        assert not self.is_collection
        return s3_open(
            f"s3://{self.bucket_name}/{self.file_path}",
            "rb",
            transport_params={"client": self.s3},
        )

    def begin_write(self, *, content_type=None):
        """Open content as a stream for writing.

        We can't call `super()` here, because we need to use `open` from `smart_open`.
        """
        self.process_pre_write_hooks()
        assert not self.is_collection
        if self.provider.readonly:
            raise DAVError(HTTP_FORBIDDEN)
        return s3_open(
            f"s3://{self.bucket_name}/{self.file_path}",
            "wb",
            transport_params={"client": self.s3},
        )


class ManabiS3Provider(ManabiProvider):
    def __init__(
        self,
        root_folder,
        endpoint_url,
        aws_access_key_id,
        aws_secret_access_key,
        region_name,
        bucket_name,
        readonly=False,
        shadow=None,
        cb_hook_config: Optional[CallbackHookConfig] = None,
    ):
        super(FilesystemProvider, self).__init__()

        if not root_folder:
            raise ValueError(f"Invalid root path: {root_folder}")

        self.root_folder_path = str(root_folder)
        self.readonly = readonly
        if shadow:
            self.shadow = {k.lower(): v for k, v in shadow.items()}
        else:
            self.shadow = {}

        self.fs_opts: Dict[str, Any] = {}
        # Get shadow map and convert keys to lower case
        self.shadow_map = self.fs_opts.get("shadow_map") or {}
        if self.shadow_map:
            self.shadow_map = {k.lower(): v for k, v in self.shadow_map.items()}

        self._cb_hook_config = cb_hook_config

        self.endpoint_url = endpoint_url
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.region_name = region_name
        self.bucket_name = bucket_name
        self.s3 = get_boto_client(
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            region_name=self.region_name,
        )
        self._file_resource = None

    def get_file_resource(self, path, environ, fp):
        try:
            return ManabiS3FileResource(
                self.s3,
                self.bucket_name,
                path,
                environ,
                fp,
                cb_hook_config=self._cb_hook_config,
            )
        except ClientError as ex:
            if ex.response["Error"]["Code"] == "NoSuchKey":
                # File does not exist
                return None
