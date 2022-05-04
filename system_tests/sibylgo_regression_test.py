import base64
import os

import pytest
import requests

TESTDATA_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "testdata")
SIBYL_URL = "http://localhost:8082"
COMMONPLACE_URL = "http://localhost:5000"
BASE_URL = SIBYL_URL
FORMAT_ENDPOINT = f"{BASE_URL}/format"


@pytest.mark.golden_test("testdata/format_*.golden.yml")
def test_format_optimized(golden):
    # Given
    with open(os.path.join(TESTDATA_DIR, golden["input"]["todo_file"]), "rb") as file:
        todo = file.read()

    optimize = "true" if golden['input']['optimize'] else "false"

    # When
    resp = requests.post(f"{FORMAT_ENDPOINT}?optimize={optimize}", data=base64.b64encode(todo))
    body = resp.content.decode("utf8")

    # Then
    assert resp.status_code == 200
    assert body == golden.out["output"]
