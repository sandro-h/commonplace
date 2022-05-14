import base64
from functools import reduce
import json
import os

import pytest
import requests

TESTDATA_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "testdata")
SIBYL_URL = "http://localhost:8082"
COMMONPLACE_URL = "http://localhost:5000"
BASE_URL = SIBYL_URL


@pytest.mark.golden_test("testdata/parse.golden.yml")
def test_parse(golden):
    # Given
    with open(os.path.join(TESTDATA_DIR, golden["input"]["todo_file"]), "rb") as file:
        todo = file.read()

    # When
    resp = requests.post(f"{BASE_URL}/parse", data=base64.b64encode(todo))

    # Then
    with open("sibyl_parse.json", "w") as file:
        repls = [
            ('"Categories"', '"categories"'),
            ('"Name"', '"name"'),
            ('"DocPos"', '"doc_pos"'),
            ('"Priority"', '"priority"'),
            ('"Color"', '"color"'),
            ('"lineNumber"', '"line_num"'),
            ('"Comments"', '"comments"'),
            ('"Category"', '"category"'),
            ('"Content"', '"content"'),
            ('"Moments"', '"moments"'),
            ('"TimeOfDay"', '"time_of_day"'),
            ('"Start"', '"start"'),
            ('"End"', '"end"'),
            ('"WorkState"', '"work_state"'),
            ('"Time"', '"dt"'),
            ('"SubMoments"', '"sub_moments"'),
            ('"sub_moments": null', '"sub_moments": []'),
            ('"comments": null', '"comments": []'),
            ("999+02:00", ""),
            ("999+01:00", ""),
            ("+02:00", ""),
        ]
        data = resp.json()
        del data["MomentsByID"]
        j = json.dumps(data, indent=2, sort_keys=True)
        file.write(reduce(lambda c, r: c.replace(r[0], r[1]), repls, j))
    assert json.dumps(resp.json(), indent=2, sort_keys=True) == golden.out["output"]


@pytest.mark.golden_test("testdata/format_*.golden.yml")
def test_format(golden):
    # Given
    with open(os.path.join(TESTDATA_DIR, golden["input"]["todo_file"]), "rb") as file:
        todo = file.read()

    optimize = "true" if golden['input']['optimize'] else "false"

    # When
    resp = requests.post(f"{BASE_URL}/format?optimize={optimize}", data=base64.b64encode(todo))
    body = resp.content.decode("utf8")

    # Then
    assert resp.status_code == 200
    assert body == golden.out["output"]
