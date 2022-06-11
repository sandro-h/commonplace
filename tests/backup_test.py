from datetime import datetime, timedelta
import os
from commonplace.backup import backup
from commonplace.util import parse_ymd_hms

DUMMY_CONTENT = "hello world"


def test_backups(tmp_path):
    # Given
    file = tmp_path / "todo.txt"
    dump(file, DUMMY_CONTENT)

    backup_dir = tmp_path / "backups"

    # When
    backup(file, backup_dir)
    backups = os.listdir(backup_dir)

    # Then
    assert len(backups) == 1
    assert load(backup_dir / backups[0]) == DUMMY_CONTENT
    assert load(file) == DUMMY_CONTENT


def test_multiple_backups(tmp_path):
    # Given
    file = tmp_path / "todo.txt"
    dump(file, DUMMY_CONTENT)

    backup_dir = tmp_path / "backups"

    # When
    now = datetime.now()
    backup(file, backup_dir, fixed_time=now)

    dump(file, DUMMY_CONTENT + "2")
    backup(file, backup_dir, fixed_time=now + timedelta(seconds=2))

    dump(file, DUMMY_CONTENT + "3")
    backup(file, backup_dir, fixed_time=now + timedelta(seconds=5))

    backups = sorted(os.listdir(backup_dir))

    # Then
    assert len(backups) == 3
    assert load(backup_dir / backups[0]) == DUMMY_CONTENT
    assert load(backup_dir / backups[1]) == DUMMY_CONTENT + "2"
    assert load(backup_dir / backups[2]) == DUMMY_CONTENT + "3"


def test_backup_pruning(tmp_path):
    # Given
    file = tmp_path / "todo.txt"
    dump(file, DUMMY_CONTENT)

    backup_dir = tmp_path / "backups"
    os.makedirs(backup_dir)
    (backup_dir / "todo.2022-06-11_15-00-30.txt").touch()
    (backup_dir / "todo.2022-06-11_15-00-31.txt").touch()
    (backup_dir / "todo.2022-06-11_15-00-32.txt").touch()
    (backup_dir / "todo.2022-06-11_15-00-33.txt").touch()
    (backup_dir / "todo-trash.2022-06-11_15-00-30.txt").touch()

    # When
    backup(file, backup_dir, max_backups=3, fixed_time=parse_ymd_hms("2022-06-11_15-05-52"))

    backups = sorted(os.listdir(backup_dir))

    # Then
    assert backups == [
        "todo-trash.2022-06-11_15-00-30.txt",
        "todo.2022-06-11_15-00-32.txt",
        "todo.2022-06-11_15-00-33.txt",
        "todo.2022-06-11_15-05-52.txt",
    ]


def dump(file, content):
    with open(file, "w", encoding="utf8") as file:
        file.write(content)


def load(file):
    with open(file, "r", encoding="utf8") as file:
        return file.read()
