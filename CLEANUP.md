# Cleanup Checklist

## 1. Simplification Opportunities

- [ ] **1. `load_config` return value is awkward (`main.py:42-51`, `56-67`)**
  It returns a tuple that gets unpacked by index (`current_config[0]`, `current_config[1]`). Since `backup_jobs` shouldn't be extracted before validation anyway (see Critical #3), `load_config` could just return the config dict (or `None` on failure), and `backup_jobs` can be pulled from `config['jobs']` after validation passes.

- [ ] **2. Source and destination validation are near-identical (`validators.py:5-60`)**
  The source validation block and destination validation block are almost copy-pasted. A shared helper function that validates a list of entries (given a label like "source"/"destination") would cut the duplication roughly in half and make it easier to add new required fields later.

- [ ] **3. `validate_config` doesn't validate `flags` type (`validators.py:130-132`)**
  It checks that `flags` exists but not that it's a list. If someone writes `"flags": "-av --delete"` (a string instead of a list), `["rsync"] + job['flags']` at `validators.py:9` will raise a `TypeError` at runtime — after the user has already confirmed the job. Validation should catch this early.

---

## 2. Critical — Data Integrity

These issues could cause data loss or corruption in production. They should be addressed before this tool is used on critical data.

- [ ] **4. `--delete` empty-source guard has a TOCTOU gap and doesn't cover partial data loss (`validators.py:167-181`, `main.py:63-66`)**
  The `--delete` safety check only catches a *completely* empty source directory at validation time. Two problems:
  1. **Time-of-check to time-of-use (TOCTOU):** The source could become empty (or lose files) between the re-validation at `main.py:64` and the actual rsync execution at `main.py:66`. The window is small but real.
  2. **Partial data loss is not caught:** If a source loses *most* of its files (e.g., an NFS mount goes stale and shows a subset, or a process clears part of the directory), the source isn't empty so the guard passes, and `--delete` mirrors the loss to the destination — destroying the only remaining copy.

  Consider adding a file-count or size sanity check (e.g., warn if the source has significantly fewer files than the destination), or at minimum pass `--dry-run` first and present a deletion summary when `--delete` is used.

- [ ] **5. No protection against dangerous rsync flags (`validators.py:130-132`)**
  The `flags` field is passed directly to rsync with no filtering. A user could accidentally include `--remove-source-files`, which deletes source files after transfer. For a backup tool handling critical data, there should be a blocklist of flags that are incompatible with the tool's purpose, or at least a warning when dangerous flags are detected.

- [ ] **6. No validation that source and destination are different or non-overlapping paths (`main.py:33-47`, `helpers.py:54-85`)**
  The tool never checks whether the resolved source and destination point to the same directory, or whether one path is inside the other. Same-path jobs are at best useless and at worst dangerous. Nested paths are more serious: for example, backing up `/home/user` into `/home/user/backup` can cause recursive backup growth, and using `--delete` with overlapping paths can delete or reshape data the user did not intend to touch.

- [ ] **7. Dangerous overwrite-related rsync flags are not blocked (`validators.py:130-132`, `executor.py:13-18`)**
  The earlier concern that rsync always overwrites a good destination file with a partial file on interruption is not accurate for default rsync behavior: by default, rsync writes to a temporary file and renames it after a successful transfer. The real risk is that the tool lets users pass flags that change that safety behavior, such as `--inplace`, `--append`, `--append-verify`, or `--partial` without a safe `--partial-dir`. For a backup tool, these should be blocked or require an explicit high-risk confirmation. Adding a safe default like `--partial-dir=.rsync-partial` is still worth considering, but the critical issue is unrestricted unsafe flags.

- [ ] **8. Mounted filesystems are not checked deeply enough (`helpers.py:6-15`, `validators.py:151-165`)**
  For NFS, `is_path_ready()` only checks whether the configured `mount_point` is a mount. It does not verify that the actual source/destination path exists, is a directory, is readable/writable as needed, or that the mount is responsive. A stale NFS mount may still look mounted to the kernel and then hang or fail during rsync.

  For `filesystem: "external"`, the check only uses `os.path.isdir(path)`. If the mount point or backup directory exists on the local filesystem while the external drive is disconnected, the job can run against the wrong storage location. With `--delete`, this can mirror an unexpectedly empty or wrong source/destination state.

  The readiness check should verify both the mount point and the actual target path, and should perform a lightweight read/write responsiveness check with a timeout.

- [ ] **9. `subprocess.run` has no timeout (`executor.py:13-18`)**
  If rsync hangs (stale NFS, unresponsive remote), the process blocks forever with no way to recover. `subprocess.run` accepts a `timeout` parameter — a configurable timeout (or a generous default) would prevent the tool from hanging indefinitely. This is especially dangerous combined with issue #8 (stale NFS).

- [ ] **10. No single-instance enforcement**
  If the user (or a cron job) accidentally launches PySync twice simultaneously targeting the same destination, both instances will run rsync concurrently against the same paths. With `--delete`, this can cause unpredictable results. A lock file (e.g., `flock` or a PID file) would prevent concurrent execution.

- [ ] **11. Duplicate source/destination names are not rejected (`validators.py:22-108`, `helpers.py:62-76`)**
  Jobs refer to sources and destinations by name, but validation does not enforce unique names. `resolve_job_paths()` silently uses the first matching entry. A duplicate name can make a job run against the wrong source or destination, which is especially dangerous when `--delete` is enabled.

## 3. Important — Robustness

These won't directly corrupt data but affect reliability and safe operation in production.

- [ ] **12. `KeyboardInterrupt` during rsync leaves no warning about partial state (`main.py:75-79`)**
  If the user hits Ctrl+C while rsync is running, the handler logs "Ctrl+C pressed" and exits, but doesn't warn that the destination may be in a partially-synced state. Since this is a backup tool for critical data, the exit message should tell the user that the last job may be incomplete and should be re-run.

- [ ] **13. Failed jobs don't prevent exit code 0 (`main.py:62-68`)**
  If some jobs fail inside the execution loop (lines 63-66), the tool still logs "Syncing complete!" and exits with code 0. Callers (scripts, cron) will think everything succeeded. The exit code should reflect whether all jobs actually completed successfully.
