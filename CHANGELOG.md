# Changelog

<!--next-version-placeholder-->

## v0.5.2 (2022-03-02)
### Fix
* **build:** Exclude mock from build ([`f6df578`](https://github.com/projectcaluma/manabi/commit/f6df5787432870239ddecc8075718694023866e3))

## v0.5.1 (2022-03-02)

### Fix
* **build:** Remove obsolete files from build ([`ffa82e9`](https://github.com/projectcaluma/manabi/commit/ffa82e9b57ebbb097bcc4498be8feb4eeec5d3a3))

## v0.5.0 (2022-03-02)

### Breaking
* Renamed option `lock_manager` to `lock_storage`, removed support for python 3.6 and added support for python 3.8, 3.9 and 3.10. ([`92fed81`](https://github.com/projectcaluma/manabi/commit/92fed817353d28b02f64a9ec84dca0cc4e418037))

### Documentation
* **changelog:** Move changelog to separate file ([`aaa80ea`](https://github.com/projectcaluma/manabi/commit/aaa80eac7165ed78be2e7783e0717bb9423891cf))

## v0.2.0 (2021-03-18)

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