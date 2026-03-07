# PySync Issue Tracker

## Phase 1: Critical — Must Fix Before Testing on Real Data

### 1. Rsync trailing slash inconsistency
- **File:** `config.json`
- **Problem:** Source paths have trailing slashes, destination paths don't. Rsync treats these differently — a trailing slash on the source means "copy the contents of this directory" vs "copy the directory itself." Need to verify this is intentional and consistent.
- **Status:** [ ] Not started

### 2. `build_rsync_command` called twice — preview can diverge from execution
- **File:** `src/main.py:88-108`
- **Problem:** Commands are built once for preview and again for execution. Although `build_rsync_command` re-checks path readiness on both passes, state can change between them. A path that was up during preview could go down (command silently skipped — user expected it to run), or a path that was down could come up (command runs without the user ever seeing it in the preview). The fix is to build once, store the results, preview those stored commands, and execute exactly those — so what the user confirms is what actually runs.
- **Status:** [ ] Not started

---

## Phase 2: Medium — Confusing Failures

### 1. Silent failure when NFS `mount_point` is `None`
- **File:** `src/helpers.py:13-16`
- **Problem:** If an NFS entry is missing `mount_point`, `os.path.expanduser(None)` raises `TypeError`, which is caught silently. The user sees "Source not ready" with no explanation of *why*.
- **Status:** [ ] Not started

### 2. No config validation
- **File:** `src/main.py:13-15`
- **Problem:** No validation of config structure. Missing or misspelled keys (e.g., `"filesytem"` instead of `"filesystem"`) would cause confusing KeyErrors with no helpful context.
- **Status:** [ ] Not started

### 3. `exclude_from` file not checked for existence
- **File:** `src/main.py:54-55`
- **Problem:** If `exclude_from` is set but the file doesn't exist on disk, rsync will fail with its own error rather than a clear message from the application.
- **Status:** [ ] Not started

---

## Phase 3: Polish — Improvements

### 1. Exit codes are all 0
- **File:** `src/main.py:105,108`
- **Problem:** Both success and user-cancellation exit with code 0. Wrapper scripts, cron, or systemd can't distinguish outcomes.
- **Status:** [ ] Not started

### 2. Double `expanduser` call
- **File:** `src/main.py:24`, `src/helpers.py:7`
- **Problem:** Path is expanded in `build_rsync_command`, then expanded again inside `is_path_ready`. Harmless but redundant.
- **Status:** [ ] Not started

### 3. `logging.basicConfig` at import time
- **File:** `src/logger.py:8`
- **Problem:** Configures the root logger. If any imported library also calls `basicConfig`, only the first call wins. A named logger with explicit handlers would be more robust.
- **Status:** [ ] Not started

### 4. `if user_confirmed == True` style
- **File:** `src/main.py:96`
- **Problem:** Pythonic style is `if user_confirmed:`. Minor.
- **Status:** [ ] Not started


---

# Important Context

The reason we specify the mountpoint in the config.json is so we can address issues related to doing an rsync command on a subdirectory of an nfs share -- we can check the ACTUAL mountpoint rather than check the subdirectory (if NFS share is mounted, it should return that true and false if not).
                                                                      
### Mount Point Behaviors                                             
| Path | Type | When Unmounted | Check Method |                       
|------|------|----------------|--------------|                       
| `/media/cheyenne/4TBEvo` | `external` | Directory does not exist | `os.path.isdir()` |                                                   
| `/media/cheyenne/Backup` | `external` | Directory does not exist | `os.path.isdir()` |                                                   
| `/home/cheyenne/remote_mount/ubuntu_mount` | `nfs` | Directory exists but empty | `os.path.ismount()` on declared mount point |      
| `/home/cheyenne/Dropbox` | `local` | Always locally available | No check needed |                                                        

### Path Type Definitions
- **`external`** — External drive. Directory does not exist when unmounted. Check with `os.path.isdir()`.                              
- **`nfs`** — Network mount. Directory always exists even when unmounted. Requires a declared `mount_point` field in config. Check with `os.path.ismount()` on that mount point.                         
- **`local`** — Always locally available (e.g. Dropbox). No mount check needed, skip directly to rsync. 