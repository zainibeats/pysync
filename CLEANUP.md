# Cleanup Checklist

## 1. Minor Issues

- [ ] **1. `local` and `external` are identical in code (`helpers.py:8-11`)**
  Both branches do `os.path.isdir()`. If they're supposed to behave differently (per the README), the code should reflect that. If they're not different, question whether both types are needed.

- [ ] **2. README project structure doesn't mention `validators.py`**
  The tree in the README still shows the old structure without `validators.py`.

---

## 2. Simplification Opportunities

- [ ] **1. `load_config` return value is awkward (`main.py:42-51`, `56-67`)**
  It returns a tuple that gets unpacked by index (`current_config[0]`, `current_config[1]`). Since `backup_jobs` shouldn't be extracted before validation anyway (see Critical #3), `load_config` could just return the config dict (or `None` on failure), and `backup_jobs` can be pulled from `config['jobs']` after validation passes.

- [ ] **2. Source and destination validation are near-identical (`validators.py:5-60`)**
  The source validation block and destination validation block are almost copy-pasted. A shared helper function that validates a list of entries (given a label like "source"/"destination") would cut the duplication roughly in half and make it easier to add new required fields later.

- [ ] **3. `validate_config` doesn't validate `flags` type (`validators.py:84-86`)**
  It checks that `flags` exists but not that it's a list. If someone writes `"flags": "-av --delete"` (a string instead of a list), `rsync_args = ["rsync"] + job['flags']` at `main.py:13` would concatenate individual characters instead of flags.
