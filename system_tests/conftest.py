import os
import platform
import shutil
import typing
from pathlib import Path

import pytest


@pytest.fixture(scope="module")
def test_app_todo_dir() -> typing.Generator[Path, None, None]:
    tmp_dir = Path("c:\\temp\\commonplace_system_test") if platform.system() == "Windows" else Path(
        "/tmp/commonplace_system_test")
    shutil.rmtree(tmp_dir, ignore_errors=True)
    os.makedirs(tmp_dir)
    yield tmp_dir
