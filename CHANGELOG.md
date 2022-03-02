# Changelog

<!--next-version-placeholder-->

## 0.2

- ManabiLockLockStorage takes `storage: Path` as argument, pointing to the
  shared lock-storage. ManabiLockLockStorage will store the locks as
  sqlite-database. In the future we might use memcache or some other method.

- Users should add

```python
    "hotfixes": {
        "re_encode_path_info": False,
    },
```

to their config, as this workaround is not correct on webservers that work
correctly. I we have tested this extensively with cherrypy.
