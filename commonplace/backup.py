from datetime import datetime
import os
from pathlib import Path
import re
import shutil


def backup(file: Path, backup_dir: Path, max_backups=3, fixed_time=None):
    if not backup_dir.exists():
        os.makedirs(backup_dir)

    file_stem = file.stem
    now = fixed_time if fixed_time else datetime.now()
    timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
    new_backup = backup_dir / f"{file_stem}.{timestamp}{file.suffix}"

    shutil.copyfile(file, new_backup)
    prune_backups(file_stem, backup_dir, max_backups)


def prune_backups(file_stem: str, backup_dir: Path, max_backups):
    all_backups = [backup_dir.joinpath(f) for f in os.listdir(backup_dir)]
    all_backups = sorted((f for f in all_backups if backup_stem(f) == file_stem), reverse=True)
    for old_backup in all_backups[max_backups:]:
        os.remove(old_backup)


def backup_stem(file: Path):
    return re.sub(r"\.[^.]+$", "", file.stem)
