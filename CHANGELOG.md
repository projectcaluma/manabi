# Changelog

## v2.0.1

### Fix

* **deps:** Update to psycopg v3 ([`64183fe`](https://github.com/projectcaluma/manabi/commit/64183fe880f79778e7e240ca28080de4f5767d46))

## v2.0.0

### Feature

* **deps:** Update dependencies ([`edd2fb0`](https://github.com/projectcaluma/manabi/commit/edd2fb02eafbbdc0401cd7fc3f226f2e2aa10927))

### Breaking

* This removes support for Python < 3.12 ([`edd2fb0`](https://github.com/projectcaluma/manabi/commit/edd2fb02eafbbdc0401cd7fc3f226f2e2aa10927))

## v1.5.0

### Feature

* Widen token column a bit ([`fcb0a2f`](https://github.com/projectcaluma/manabi/commit/fcb0a2f0b458f5918d76654b4c2d5aaf135329a5))

## v1.4.1

### Fix

* fix: do not crash if expected lock entry is not in db ([`2920c64`](https://github.com/projectcaluma/manabi/commit/2920c64e31eba99f2f30f913b235595478c56e7e))
* fix: do not log stacktrace on db reconnect ([`8f0d753`](https://github.com/projectcaluma/manabi/commit/8f0d75365fd8afb16924f616d5c02d14d75e9839))

## v1.4.0

### Chore

* update to django 4.x ([`3e9084b`](https://github.com/projectcaluma/manabi/commit/3e9084b0774bfa06c6229311ae927f86d426a6ed))

## v1.3.3
### Fix

* Move methods from `ManabiFileResource` to `ManabiFileResourceMixin` ([`acc3193`](https://github.com/projectcaluma/manabi/commit/acc31932047bd75bc75ef9681fe84308fb98ad7c))

## v1.3.2
### Fix

* Fix inheritance order with `ManabiFileResourceMixin` ([`c751b69`](https://github.com/projectcaluma/manabi/commit/c751b6946aff4a75d180e6c7e9f0da4bdd9b45c3))

## v1.3.1

### Fix
* fix: fix path handling difference between MinIO and S3 ([`dab81ec`](https://github.com/projectcaluma/manabi/commit/dab81ec35d2a6a7fe8f237976b253fdf15ab5963))

## v1.3.0

### Feature
* Add ManabiS3Provider ([`a90e373`](https://github.com/projectcaluma/manabi/commit/a90e3735253da1adce8dc8dcdbe3462bce6e5e84))

## v1.2.0

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
