import base64
import json
import os
import re

import pytest
import requests

from system_tests.sys_test_util import TESTDATA_DIR, request_parse


@pytest.mark.skip()
@pytest.mark.golden_test("testdata/format_*.golden.yml")
def test_format(golden):
    # Given
    with open(os.path.join(TESTDATA_DIR, golden["input"]["todo_file"]), "rb") as file:
        todo = file.read()

    optimize = "true" if golden['input']['optimize'] else "false"

    # When
    resp = requests.post(f"http://localhost:8082/format?optimize={optimize}", data=base64.b64encode(todo))
    body = resp.content.decode("utf8")

    # Then
    assert resp.status_code == 200
    assert body == golden.out["output"]
