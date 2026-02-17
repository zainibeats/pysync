# pysync

A Python script that runs rsync backup commands automatically. You set up your backup jobs in a config file and the script takes care of the rest.

## What It Does

- **Backups from a config file**:  All your backup jobs are set up in `config.json`
- **Checks if drives are mounted**: Skips a job if the source or destination drive isn't available
- **Logs everything**: Shows errors on the console and writes to `logs/pysync.log` with timestamps

## Project Structure

```
pysync/
├── src/
│   ├── main.py        # Starts the script and runs the jobs
│   ├── helpers.py     # Checks if paths are ready to use
│   └── logger.py      # Sets up logging
├── config.json        # Where you define your backup jobs
├── logs/
│   └── pysync.log     # Log file output
└── .gitignore
```

## Configuration

Everything is set up in `config.json`. There are three sections:


### Sources

These are the folders you want to back up:

```json
"sources": [
    {
        "name": "my-documents",
        "path": "/home/user/Documents",
        "external": false
    }
]
```

### Destinations

These are where the backups get saved to:

```json
"destinations": [
    {
        "name": "backup-drive",
        "path": "/media/user/Backup/backups",
        "external": true
    }
]
```

### Jobs

Each job connects a source to a destination using their names:

```json
"jobs": [
    {
        "name": "Documents backup",
        "source": "my-documents",
        "destination": "backup-drive",
        "exclude_from": null,
        "flags": ["-av", "--delete"]
    }
]
```

- **name**:  A label so you can tell jobs apart in the logs 
- **source**: The name of one of your sources 
- **destination**: The name of one of your destinations 
- **exclude_from**: Path to a file listing things to skip, or `null` if you don't need one 
- **flags**: The rsync flags you want to use (e.g. "-av", "--delete") 

## Usage

```bash
cd /path/to/pysync
python src/main.py 
```

## How It Works

1. `main.py` reads the job list from `config.json`
2. For each job, it looks up the source and destination paths
3. `is_path_ready()` checks that each path exists and the drive is actually mounted
4. If both paths are good, it puts together the rsync command and runs it
5. It logs whether the job passed or failed

