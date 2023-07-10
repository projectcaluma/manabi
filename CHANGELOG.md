# Changelog

<!--next-version-placeholder-->

### Feature
* Add post-write-hook/callback ([`80cbf38`](https://github.com/projectcaluma/manabi/commit/80cbf387a775e1a417e3a44bcfb884e926d5bf08))

### Fix
* **token:** Handle errors from msgpack by creating a invalid token ([`81a5ccf`](https://github.com/projectcaluma/manabi/commit/81a5ccff740112947c8fb67b97d17d6e640eedfb))

## v1.1.0 (2023-07-03)

### Feature
* Add pre_write_callback and hook/callback approve write ([`08b6a6f`](https://github.com/projectcaluma/manabi/commit/08b6a6fe2ea76e006de17cc0a7f0be35f2b1e1f6))

## v1.0.0 (2023-06-20)

### Feature
* feat(hook): add pre_write_hook ([`4de0ad6`](https://github.com/projectcaluma/manabi/commit/4de0ad65b95bbd0be5fa19ed986660233fcd6b6c))

### Fix
* fix: fuzzying found relative urls like '..' ([`e74b263`](https://github.com/projectcaluma/manabi/commit/e74b2638f9413b339988dea52eb2b8747262a2dc))

### Feature
* feat(hook): add payload to token ([`7679f9d`](https://github.com/projectcaluma/manabi/commit/7679f9d2d1a87fd933c5af109bfb1ec244a0c480))

## v0.7.1 (2022-12-02)

### Fix
* **postgres:** Reconnect on OperationalError too ([`c6f587f`](https://github.com/projectcaluma/manabi/commit/c6f587f6b855d8053536f99a6cc6afe654e44eb9))

## v0.7.0 (2022-11-11)

### Fix
* **postgres:** Reconnect ([`b5fac12`](https://github.com/projectcaluma/manabi/commit/b5fac12089ef96e775959ef9597f8dfa86050609))

## v0.6.7 (2022-09-29)

### Fix
* **postgres:** Make sure connection to postgresql is closed ([`df0b35d`](https://github.com/projectcaluma/manabi/commit/df0b35d04729071115b77d54fb6b3f34d4b99cad))

## v0.6.6 (2022-08-15)

### Feature
* Postgres-based lock-storage ([`715ff71`](https://github.com/projectcaluma/manabi/commit/715ff716a8556c4edd5c7d3b18dffdf21cc2175b))

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
