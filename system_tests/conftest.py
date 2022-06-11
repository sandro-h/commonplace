import os
import shutil
import typing
from pathlib import Path

import pytest

__TEST_APP_TODO_DIR = Path("c:\\temp\\commonplace_system_test")


@pytest.fixture(scope="module")
def test_app_todo_dir() -> typing.Generator[Path, None, None]:
    shutil.rmtree(__TEST_APP_TODO_DIR, ignore_errors=True)
    os.makedirs(__TEST_APP_TODO_DIR)
    yield __TEST_APP_TODO_DIR
