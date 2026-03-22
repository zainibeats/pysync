# PySync

A Python script that runs rsync backup commands automatically. You set up your backup jobs in a config file and the script takes care of the rest.

## Features

- **Config-based backups**: Define all your backup jobs in `config.json`
- **Mount point checking**: Automatically skips jobs if the source or destination drives aren't available
- **Command preview**: Shows you the exact rsync commands before executing so you can confirm
- **Comprehensive logging**: Shows errors on the console and writes to `logs/pysync.log` with timestamps
- **Sudo-compatible paths**: Correctly expands `~` paths even when running with `sudo`

## Project Structure

```
pysync/
├── src/
│   ├── main.py        # Starts the script and runs the jobs
│   ├── helpers.py     # Checks if paths are ready, prompts user, expands paths
│   └── logger.py      # Sets up logging
├── config.example.json  # Template — copy to config.json and edit
├── config.json          # Your local config
├── logs/
│   └── pysync.log     # Log file output
└── .gitignore
```

## Usage

```bash
git clone https://github.com/zainibeats/pysync
cd pysync
cp config.example.json config.json
# Edit config.json with your own paths and backup jobs
python src/main.py
```

## Configuration

Everything is set up in the [config.json](./config.example.json) file. There are three sections:

### Sources

These are the folders you want to back up:

```json
"sources": [
    {
        "name": "john-music",
        "path": "/home/john/Music/",
        "filesystem": "local",
        "mount_point": null
    },
    {
        "name": "john-pictures",
        "path": "~/Pictures",
        "filesystem": "local",
        "mount_point": null
    }
]
```

### Destinations

These are where the backups get saved to:

```json
"destinations": [
    {
        "name": "external-ssd",
        "path": "/media/john/external-ssd/backup",
        "filesystem": "external",
        "mount_point": null
    },
    {
        "name": "truenas-backup",
        "path": "~/remote-mount/truenas/backup",
        "filesystem": "nfs",
        "mount_point": "~/remote-mount/truenas"
    }
]
```

### Source and Destination Fields

- **name**: A label used to connect sources and destinations to jobs
- **path**: The directory to back up from (source) or to (destination)
- **filesystem**: One of `"local"`, `"external"`, or `"nfs"` — determines how the script checks if the path is available (see [Filesystem Types](#filesystem-types))
- **mount_point**: Only needed for `"nfs"` paths. Set to the actual NFS mount point so the script can check if the share is mounted. Set to `null` for everything else

### Trailing Slashes on Source Paths

Rsync treats trailing slashes on source paths differently, and it's up to you to set them correctly for your use case:

- **With trailing slash** (`/home/$USER/Music/`) — rsync copies the *contents* of the directory into the destination
- **Without trailing slash** (`/home/$USER/Music`) — rsync copies the *directory itself* into the destination

For example, say you have two users who each want to back up their music to a shared destination `/backup/songs`:

```
# With trailing slash — contents get poured into the destination:
rsync /home/alice/Music/ /backup/songs
rsync /home/bob/Music/   /backup/songs
# Result: /backup/songs/song1.mp3, song2.mp3, ...

# Without trailing slash — the directory itself gets copied:
rsync /home/alice/Music /backup/songs
# Result: /backup/songs/Music/song1.mp3, ...
```

If you're backing up a directory like `/home/$USER/Pictures` to a destination that already has the same folder structure (e.g. `/backup`), leaving off the trailing slash is fine — the whole `Pictures` directory gets synced over as-is.

Pick whichever matches your intent. Just know that getting it wrong means files end up in the wrong place.

Destination paths do not need trailing slashes.

### Jobs

Each job connects a source to a destination using their names:

```json
"jobs": [
    {
        "name": "Music to external SSD",
        "source": "john-music",
        "destination": "external-ssd",
        "exclude_from": null,
        "flags": ["-av", "--delete"]
    },
    {
        "name": "Pictures to TrueNAS",
        "source": "john-pictures",
        "destination": "truenas-backup",
        "exclude_from": null,
        "flags": ["-av", "--delete"]
    }
]
```

- **name**:  A label so you can tell jobs apart in the logs
- **source**: The name of one of your sources
- **destination**: The name of one of your destinations
- **exclude_from**: Path to a file listing things to skip, or `null` if you don't need one
- **flags**: The rsync flags you want to use (e.g. `"-av"`, `"--delete"`)

### Filesystem Types

The `filesystem` field tells the script how to check if a path is available before running rsync:

| Type | When to use | How it checks |
|------|-------------|---------------|
| `local` | Paths that are always available (e.g. `~/Dropbox`) | No check — always considered ready |
| `external` | External drives that disappear when unplugged | `os.path.isdir()` — the directory won't exist when unmounted |
| `nfs` | Network mounts where the directory still exists when unmounted | `os.path.ismount()` on the declared `mount_point` |

For `nfs` paths, the mount point in the config should point to the actual NFS mount point, not a subdirectory of it. This is because NFS mount directories still exist when the share is unmounted (they're just empty), so checking the subdirectory with `isdir()` would give a false positive.

