import json
import os

import pytest
from system_tests.parse_sys_test import remove_timezone_offset

from system_tests.sys_test_util import TESTDATA_DIR, request_preview


@pytest.mark.golden_test("testdata/preview.*.golden.yml")
def test_preview(golden):
    # Given
    with open(os.path.join(TESTDATA_DIR, golden["input"]["todo_file"]), "rb") as file:
        # Remove carrier returns to get same offsets on windows and linux.
        todo = file.read().decode("utf8").replace("\r", "")

    # When
    fmt = request_preview(todo)

    # Then
    assert remove_timezone_offset(json.dumps(fmt, indent=2)) == golden.out["output"]
