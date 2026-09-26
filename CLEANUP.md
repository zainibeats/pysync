# Cleanup Checklist

## MVP Direction

- **Interactive only** — the y/n confirmation prompt stays central; cron/unattended mode (lock file, `--yes` flag) is post-MVP.
- **Allowlist for `extra_flags`** — replace the blocklist with a list of approved flags (see Critical #9).
- **Dry-run preview for `--delete` jobs** — run `rsync --dry-run` first and show the deletion summary before the real run (see Critical #1).

## 1. Simplification Opportunities

- [ ] **1. Source and destination validation are near-identical (`validators.py:34-119`)**
  The source validation block and destination validation block are almost copy-pasted. A shared helper function that validates a list of entries (given a label like "source"/"destination") would cut the duplication roughly in half and make it easier to add new required fields later.

---

## 2. Critical — Data Integrity

These issues could cause data loss or corruption in production. They should be addressed before this tool is used on critical data.

- [ ] **1. No validation that source and destination are different or non-overlapping paths (`main.py:33-47`, `helpers.py:54-85`)**
  The tool never checks whether the resolved source and destination point to the same directory, or whether one path is inside the other. Same-path jobs are at best useless and at worst dangerous. Nested paths are more serious: for example, backing up `/home/user` into `/home/user/backup` can cause recursive backup growth, and using `--delete` with overlapping paths can delete or reshape data the user did not intend to touch.

  *Test note (2026-09-25):* implemented on `dev` in `f86f4f8` (`validate_path_overlap()`). Tests confirmed it catches identical paths (including via trailing slash, symlink, `~` and `..`) and nesting in both directions. Check off once `dev` is merged.

- [ ] **2. Mounted filesystems are not checked deeply enough (`helpers.py:6-15`, `validators.py:182-196`)**
  For NFS, `is_path_ready()` only checks whether the configured `mount_point` is a mount. It does not verify that the actual source/destination path exists, is a directory, is readable/writable as needed, or that the mount is responsive. A stale NFS mount may still look mounted to the kernel and then hang or fail during rsync.

  For `filesystem: "external"`, the check only uses `os.path.isdir(path)`. If the mount point or backup directory exists on the local filesystem while the external drive is disconnected, the job can run against the wrong storage location. With `--delete`, this can mirror an unexpectedly empty or wrong source/destination state.

  The readiness check should verify both the mount point and the actual target path, and should perform a lightweight read/write responsiveness check with a timeout.

  *Confirmed in testing (2026-09-25):*
  - An `external` destination whose drive was unplugged, but whose folder existed on the local disk, was treated as ready. The backup was written to the local disk.
  - An unplugged `external` source holding a stale file, with `--delete`: only the deletion prompt stopped the destination from being wiped.
  - NFS share mounted but the backup folder on it missing: rsync quietly created the folder instead of the job being reported as "Destination not ready".

- [ ] **3. No single-instance enforcement** *(post-MVP — interactive-only for now)*
  If the user accidentally launches PySync twice simultaneously targeting the same destination, both instances will run rsync concurrently against the same paths. With `--delete`, this can cause unpredictable results. A lock file (e.g., `flock` or a PID file) would prevent concurrent execution. Deferred since the MVP is interactive-only; required before any cron/unattended mode.

- [ ] **4. Duplicate names are not rejected (`validators.py:34-119`, `helpers.py:62-76`)**
  Jobs refer to sources and destinations by name, but validation does not enforce unique names. `resolve_job_paths()` silently uses the first matching entry. A duplicate name can make a job run against the wrong source or destination, which is especially dangerous when `--delete` is enabled. Duplicate *job* names should also be rejected — they make logs ambiguous about which job failed.

  *Confirmed in testing (2026-09-25):* duplicate source, destination and job names are all accepted.

- [ ] **5. Dangerous path checks should use canonical paths, not raw strings (`helpers.py:41-85`)**
  Any future same-path or nested-path validation should compare normalized/canonical paths, not the raw config strings. Paths like `~/Pictures`, `/home/user/Pictures`, paths with trailing slashes, and symlinks can refer to the same location while looking different as strings. Use tools such as `os.path.abspath()`, `os.path.realpath()`, and `os.path.commonpath()` after expanding `~`.

  *Test note (2026-09-25):* the overlap check on `dev` uses `realpath()` as recommended here and passed all canonical-path tests.

- [ ] **6. Trailing-slash semantics on source paths are not normalized (`validators.py:8-14`, `helpers.py:62-68`)**
  rsync treats `src` and `src/` completely differently: `src` creates a `dst/src/` subdirectory while `src/` syncs the directory's contents into `dst`. Config paths pass through to the command unmodified. If a user adds or drops a trailing slash between runs of a `--delete` job, rsync restructures the destination and deletes the previous layout. Normalize source paths to one convention (and document it), or warn when the convention changes the meaning of an existing destination.

- [ ] **7. Nothing is re-checked after the deletion prompt (`main.py:83-91`)** *(found in testing)*
  Readiness and the empty-source guard are re-checked after the main "You are about to run" prompt, but not after the `--delete` deletion prompt, which can stay open for any length of time. In testing, the NFS source (a mount root with a trailing slash) was unmounted while the deletion prompt was open. The preview listed one file, the user answered "y", and rsync then deleted **every** file in the destination and reported "Syncing complete!". An external source drive unplugged at that moment would do the same. Re-run `validate_rsync_command()` right before the real rsync run, after the deletion prompt.

- [ ] **8. An `nfs` path is not checked to be inside its `mount_point` (`helpers.py:11-16`)** *(found in testing)*
  `is_path_ready()` only checks that `mount_point` is mounted. If `path` is not under `mount_point` (e.g. a typo), the job still runs and writes to the local disk. Check that the resolved `path` is inside the resolved `mount_point`.

- [ ] **9. Empty folders get past the `--delete` empty-source guard (`validators.py:223-233`)** *(found in testing)*
  The guard only checks that `os.listdir()` of the source isn't empty. A source containing only empty folders (e.g. a stale mount directory with an empty subfolder) passes, and the job would delete everything else in the destination; only the deletion prompt stops it. Consider requiring at least one file somewhere in the source tree for `--delete` jobs.

## 3. Important — Robustness

These won't directly corrupt data but affect reliability and safe operation in production.

- [ ] **1. `KeyboardInterrupt` during rsync leaves no warning about partial state (`main.py:75-79`)**
  If the user hits Ctrl+C while rsync is running, the handler logs "Ctrl+C pressed" and exits, but doesn't warn that the destination may be in a partially-synced state. Since this is a backup tool for critical data, the exit message should tell the user that the last job may be incomplete and should be re-run.

  *Confirmed in testing (2026-09-25):* Ctrl+C during rsync exits cleanly with code 1 and stops the rsync process, but prints no partial-state warning.

- [ ] **2. Config collection types are not validated (`validators.py:34-179`)**
  `validate_config()` checks for required keys, but it assumes `sources`, `destinations`, and `jobs` are iterable collections of dictionaries. If a config accidentally uses the wrong type, validation can crash or behave strangely instead of reporting a clean config error. Add explicit type checks before iterating each collection.

  *Confirmed in testing (2026-09-25):* these all crash with a traceback: `sources`/`destinations`/`jobs` given as a dict, string or number, or as a list of strings or `null`s; a top-level JSON array; a number in `path` or `mount_point`.

- [ ] **3. Missing `rsync` binary crashes with a raw traceback (`executor.py:13-18`)**
  `subprocess.run` raises `FileNotFoundError` if rsync is not installed; only `CalledProcessError` is caught, so the user gets an unhandled exception instead of a clean "rsync not found" error.

  *Confirmed in testing (2026-09-25).*

- [ ] **4. `capture_output=True` buffers all rsync output until the job ends (`executor.py:13-18`)**
  With `--verbose` hardcoded, a long sync shows zero progress until it finishes, and the full file list is held in memory. Stream output line-by-line (e.g. `Popen` with a read loop) or at least log incrementally so the user can see the job is alive.

- [ ] **5. `~otheruser/...` paths break under sudo (`helpers.py:46-52`)** *(found in testing)*
  `expand_path()` replaces the leading `~` with `~$SUDO_USER`, so `~bob/Music` becomes `~alicebob/Music` when Alice runs with sudo. That path doesn't exist, so the job is skipped as "not ready". Only rewrite a bare `~` or `~/...`.

- [ ] **6. After one `sudo` run, normal runs crash (`logger.py:4-8`)** *(found in testing)*
  Running with sudo creates `logs/` and `logs/pysync.log` owned by root. The next run as a normal user fails on startup with a `PermissionError` traceback. Catch the error and fall back to console-only logging with a warning, or fix the ownership when `SUDO_USER` is set.

- [ ] **7. Ctrl+D (or no stdin) at a prompt crashes (`helpers.py:28-31`)** *(found in testing)*
  `input()` raises `EOFError`, which isn't caught, so the user gets a traceback. Nothing runs, so no data is at risk. Treat EOF as "n".

- [ ] **8. The 1-hour rsync timeout can stop long backups (`executor.py:18`)** *(from reading the code; not tested)*
  `timeout=3600` kills rsync after an hour and marks the job failed. A large first-time backup to a NAS can take longer than that. Re-running picks up where it left off, but the timeout should be configurable or much longer.

## 4. Minor

- [ ] **1. Declining the deletion prompt still reports "Syncing complete!" (`main.py:87-88`, `main.py:105`)** *(found in testing)*
  The declined job is skipped without a message, so the run ends with "Syncing complete!" and exit code 0. Log that the job was skipped.

- [ ] **2. A symlinked `mount_point` is reported as not mounted (`helpers.py:14`)** *(found in testing)*
  `os.path.ismount()` doesn't follow symlinks, so a mounted share reached through a symlink (e.g. `~/nas -> /mnt/nas`) is skipped. Safe, but confusing. Resolve the path with `realpath()` first, or document it.

- [ ] **3. Unused variable `e` (`validators.py:234`)**
  Reported by pyflakes.

## 5. Test Run — 2026-09-25

Tested `dev` at `f86f4f8`. Line numbers in items marked *(found in testing)* refer to that commit.

- **Setup:** 136 end-to-end tests running `src/main.py` against generated `config.json` files with real rsync 3.2.7 (Ubuntu 24.04, Python 3.11). tmpfs mounts stood in for NFS shares and external drives, mounted and unmounted. A non-root user was used for permission tests, and a fake `SUDO_USER` for sudo tests. The tests were kept outside the repo.
- **Result:** 111 passed, 25 failed. The failures are covered by items 2.2, 2.4, 2.7–2.9, 3.1–3.3, 3.5–3.7, 4.1 and 4.2 above.
- **Worked as expected:** missing-key and invalid-value checks; the `extra_flags` allowlist (13 bad flags rejected, including `--rsh`) and every allowed flag; `exclude_from`; overlap detection (on `dev`); NFS mounted/unmounted detection, including `~` and trailing slashes; a share dropping at the first prompt is caught by re-validation; the deletion preview matched the actual deletions exactly (including names with spaces and newlines); the empty-source guard; exit codes when some of several jobs fail; permission errors as a non-root user; sudo `~` expansion; unicode paths; a 3,000-file sync.
- **Not tested:** real kernel NFS/SMB mounts (not available in the test container), so hung mounts, stale file handles and user-ID mapping on the NAS are untested; the 1-hour timeout (3.8); running two instances at once (2.3, post-MVP). A final run on real hardware is still recommended.
