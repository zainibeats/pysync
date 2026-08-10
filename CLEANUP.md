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

- [ ] **1. `--delete` empty-source guard has a TOCTOU gap and doesn't cover partial data loss (`validators.py:197-212`, `main.py:63-66`)**
  The `--delete` safety check only catches a *completely* empty source directory at validation time. Two problems:
  1. **Time-of-check to time-of-use (TOCTOU):** The source could become empty (or lose files) between the re-validation at `main.py:64` and the actual rsync execution at `main.py:66`. The window is small but real.
  2. **Partial data loss is not caught:** If a source loses *most* of its files (e.g., an NFS mount goes stale and shows a subset, or a process clears part of the directory), the source isn't empty so the guard passes, and `--delete` mirrors the loss to the destination — destroying the only remaining copy.

  **Decided:** run `rsync --dry-run` first for `--delete` jobs and present the deletion summary for confirmation before the real run. A file-count/size sanity check can supplement this later.

- [ ] **2. No validation that source and destination are different or non-overlapping paths (`main.py:33-47`, `helpers.py:54-85`)**
  The tool never checks whether the resolved source and destination point to the same directory, or whether one path is inside the other. Same-path jobs are at best useless and at worst dangerous. Nested paths are more serious: for example, backing up `/home/user` into `/home/user/backup` can cause recursive backup growth, and using `--delete` with overlapping paths can delete or reshape data the user did not intend to touch.

- [ ] **3. Mounted filesystems are not checked deeply enough (`helpers.py:6-15`, `validators.py:182-196`)**
  For NFS, `is_path_ready()` only checks whether the configured `mount_point` is a mount. It does not verify that the actual source/destination path exists, is a directory, is readable/writable as needed, or that the mount is responsive. A stale NFS mount may still look mounted to the kernel and then hang or fail during rsync.

  For `filesystem: "external"`, the check only uses `os.path.isdir(path)`. If the mount point or backup directory exists on the local filesystem while the external drive is disconnected, the job can run against the wrong storage location. With `--delete`, this can mirror an unexpectedly empty or wrong source/destination state.

  The readiness check should verify both the mount point and the actual target path, and should perform a lightweight read/write responsiveness check with a timeout.

- [ ] **4. No single-instance enforcement** *(post-MVP — interactive-only for now)*
  If the user accidentally launches PySync twice simultaneously targeting the same destination, both instances will run rsync concurrently against the same paths. With `--delete`, this can cause unpredictable results. A lock file (e.g., `flock` or a PID file) would prevent concurrent execution. Deferred since the MVP is interactive-only; required before any cron/unattended mode.

- [ ] **5. Duplicate names are not rejected (`validators.py:34-119`, `helpers.py:62-76`)**
  Jobs refer to sources and destinations by name, but validation does not enforce unique names. `resolve_job_paths()` silently uses the first matching entry. A duplicate name can make a job run against the wrong source or destination, which is especially dangerous when `--delete` is enabled. Duplicate *job* names should also be rejected — they make logs ambiguous about which job failed.

- [ ] **6. Rsync failures are logged but not propagated (`executor.py:21-26`, `main.py:63-68`)**
  `run_rsync_job()` catches `subprocess.CalledProcessError` and logs the failure, but it does not return a success/failure value or re-raise the exception. `main.py` then continues and logs "Syncing complete!" before exiting with code 0. For a backup tool, this is a data-integrity risk because users can believe a backup succeeded when rsync actually failed. The same applies when a job is silently dropped by the re-validation at `main.py:64-65` — the run still ends with "Syncing complete!" and exit 0.

- [ ] **7. Dangerous path checks should use canonical paths, not raw strings (`helpers.py:41-85`)**
  Any future same-path or nested-path validation should compare normalized/canonical paths, not the raw config strings. Paths like `~/Pictures`, `/home/user/Pictures`, paths with trailing slashes, and symlinks can refer to the same location while looking different as strings. Use tools such as `os.path.abspath()`, `os.path.realpath()`, and `os.path.commonpath()` after expanding `~`.

- [ ] **8. Replace the `extra_flags` blocklist with an allowlist (`validators.py:20-32`, `150-169`)**
  The blocklist is bypassable: combined short flags like `-az`, `-avz`, or `-aP` are not caught even though `-a`/`-v` are blocked, and `-P` expands to the blocked `--partial` (plus `--progress`). It also misses dangerous flags such as `--delete-excluded`, `--force`, and `-e`/`--rsh` — the last of which lets a config file specify an arbitrary command for rsync to execute. **Decided:** switch to an allowlist of approved flags (e.g. `--delete`, `--dry-run`, `--compress`, `--exclude=...`) and reject everything else.

- [ ] **9. Trailing-slash semantics on source paths are not normalized (`validators.py:8-14`, `helpers.py:62-68`)**
  rsync treats `src` and `src/` completely differently: `src` creates a `dst/src/` subdirectory while `src/` syncs the directory's contents into `dst`. Config paths pass through to the command unmodified. If a user adds or drops a trailing slash between runs of a `--delete` job, rsync restructures the destination and deletes the previous layout. Normalize source paths to one convention (and document it), or warn when the convention changes the meaning of an existing destination.

## 3. Important — Robustness

These won't directly corrupt data but affect reliability and safe operation in production.

- [ ] **1. `KeyboardInterrupt` during rsync leaves no warning about partial state (`main.py:75-79`)**
  If the user hits Ctrl+C while rsync is running, the handler logs "Ctrl+C pressed" and exits, but doesn't warn that the destination may be in a partially-synced state. Since this is a backup tool for critical data, the exit message should tell the user that the last job may be incomplete and should be re-run.

- [ ] **2. Config collection types are not validated (`validators.py:34-179`)**
  `validate_config()` checks for required keys, but it assumes `sources`, `destinations`, and `jobs` are iterable collections of dictionaries. If a config accidentally uses the wrong type, validation can crash or behave strangely instead of reporting a clean config error. Add explicit type checks before iterating each collection.

- [ ] **3. Missing `rsync` binary crashes with a raw traceback (`executor.py:13-18`)**
  `subprocess.run` raises `FileNotFoundError` if rsync is not installed; only `CalledProcessError` is caught, so the user gets an unhandled exception instead of a clean "rsync not found" error.

- [ ] **4. `capture_output=True` buffers all rsync output until the job ends (`executor.py:13-18`)**
  With `--verbose` hardcoded, a long sync shows zero progress until it finishes, and the full file list is held in memory. Stream output line-by-line (e.g. `Popen` with a read loop) or at least log incrementally so the user can see the job is alive.
