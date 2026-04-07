# Cleanup Checklist

## 1. Logic & Behavior

- [ ] **1. `load_config()` doesn't catch `json.JSONDecodeError` (`main.py:44-48`)**
  Only `FileNotFoundError` is caught. Malformed JSON (trailing comma, missing quote, etc.) will produce a raw traceback instead of a user-friendly error message.

- [ ] **2. `validate_config` doesn't check `filesystem` values (`validators.py`)**
  A typo like `"filesystem": "loccal"` passes validation silently and only fails later in `is_path_ready` with a generic "Unknown 'filesystem' value" error. Validation should reject unknown filesystem types early with a clear message.

- [ ] **3. `expand_path` replaces all `~` characters, not just the leading one (`helpers.py:43`)**
  `path.replace("~", sudo_user_home_prefix)` replaces every `~` in the string. A path like `/data/~archive/files` would get mangled. Should only replace a leading `~`.

- [ ] **4. `config.json` is tracked in git despite being in `.gitignore`**
  `.gitignore` only prevents *untracked* files from being staged. Since `config.json` was committed before the gitignore rule was added, it's still tracked. Run `git rm --cached config.json` to untrack it without deleting the local file.

---

## 2. Minor Issues

- [ ] **1. `local` and `external` are identical in code (`helpers.py:8-11`)**
  Both branches do `os.path.isdir()`. If they're supposed to behave differently (per the README), the code should reflect that. If they're not different, question whether both types are needed.

- [ ] **2. README project structure doesn't mention `validators.py`**
  The tree in the README still shows the old structure without `validators.py`.

---

## 3. Simplification Opportunities

- [ ] **1. `load_config` return value is awkward (`main.py:42-51`, `56-67`)**
  It returns a tuple that gets unpacked by index (`current_config[0]`, `current_config[1]`). Since `backup_jobs` shouldn't be extracted before validation anyway (see Critical #3), `load_config` could just return the config dict (or `None` on failure), and `backup_jobs` can be pulled from `config['jobs']` after validation passes.

- [ ] **2. Source and destination validation are near-identical (`validators.py:5-60`)**
  The source validation block and destination validation block are almost copy-pasted. A shared helper function that validates a list of entries (given a label like "source"/"destination") would cut the duplication roughly in half and make it easier to add new required fields later.

- [ ] **3. `validate_config` doesn't validate `flags` type (`validators.py:84-86`)**
  It checks that `flags` exists but not that it's a list. If someone writes `"flags": "-av --delete"` (a string instead of a list), `rsync_args = ["rsync"] + job['flags']` at `main.py:13` would concatenate individual characters instead of flags.
