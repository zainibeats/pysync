# PySync Issue Tracker

## Phase 1: Critical — Must Fix Before Testing on Real Data

### 1. `--delete` flag + empty/missing source = data loss
- **File:** `config.json`, `src/helpers.py`
- **Problem:** `is_path_ready` only checks if the NFS mount point is mounted, not whether the actual data path exists or has contents. If the mount is active but the source directory is empty, `rsync --delete` will wipe the destination.
- **Status:** [ ] Not started

### 2. `~` expansion under `sudo`
- **File:** `config.json`, `src/main.py:24`
- **Problem:** All config paths use `~`. If the script is run with `sudo`, `os.path.expanduser("~")` resolves to `/root` instead of the intended user's home directory.
- **Status:** [ ] Not started

### 3. Rsync trailing slash inconsistency
- **File:** `config.json`
- **Problem:** Source paths have trailing slashes, destination paths don't. Rsync treats these differently — a trailing slash on the source means "copy the contents of this directory" vs "copy the directory itself." Need to verify this is intentional and consistent.
- **Status:** [ ] Not started

### 4. `build_rsync_command` called twice — state can change
- **File:** `src/main.py:86-102`
- **Problem:** Commands are built once for preview and again for execution. A mount could go down (or come up) between the two passes, meaning the user confirms one set of commands but a different set actually runs.
- **Status:** [ ] Not started

### 5. Return type mismatch on `build_rsync_command`
- **File:** `src/main.py:18,38,41,46,48`
- **Problem:** Type hint says `-> list` but multiple code paths return `None` via bare `return` statements. The caller handles this, but the type hint is dishonest and could mislead future callers.
- **Status:** [ ] Not started

---

## Phase 2: Medium — Confusing Failures

### 6. Silent failure when NFS `mount_point` is `None`
- **File:** `src/helpers.py:13-16`
- **Problem:** If an NFS entry is missing `mount_point`, `os.path.expanduser(None)` raises `TypeError`, which is caught silently. The user sees "Source not ready" with no explanation of *why*.
- **Status:** [ ] Not started

### 7. No config validation
- **File:** `src/main.py:13-15`
- **Problem:** No validation of config structure. Missing or misspelled keys (e.g., `"filesytem"` instead of `"filesystem"`) would cause confusing KeyErrors with no helpful context.
- **Status:** [ ] Not started

### 8. `exclude_from` file not checked for existence
- **File:** `src/main.py:54-55`
- **Problem:** If `exclude_from` is set but the file doesn't exist on disk, rsync will fail with its own error rather than a clear message from the application.
- **Status:** [ ] Not started

---

## Phase 3: Polish — Improvements

### 9. Exit codes are all 0
- **File:** `src/main.py:105,108`
- **Problem:** Both success and user-cancellation exit with code 0. Wrapper scripts, cron, or systemd can't distinguish outcomes.
- **Status:** [ ] Not started

### 10. Double `expanduser` call
- **File:** `src/main.py:24`, `src/helpers.py:7`
- **Problem:** Path is expanded in `build_rsync_command`, then expanded again inside `is_path_ready`. Harmless but redundant.
- **Status:** [ ] Not started

### 11. `logging.basicConfig` at import time
- **File:** `src/logger.py:8`
- **Problem:** Configures the root logger. If any imported library also calls `basicConfig`, only the first call wins. A named logger with explicit handlers would be more robust.
- **Status:** [ ] Not started

### 12. `if user_confirmed == True` style
- **File:** `src/main.py:96`
- **Problem:** Pythonic style is `if user_confirmed:`. Minor.
- **Status:** [ ] Not started
