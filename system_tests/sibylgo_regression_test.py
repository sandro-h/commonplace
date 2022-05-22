import base64
from datetime import datetime
from functools import reduce
import json
import os
import re
import sys

import pytest
import requests

TESTDATA_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "testdata")
SIBYL_URL = "http://localhost:8082"
COMMONPLACE_URL = "http://127.0.0.1:5000"
BASE_URL = COMMONPLACE_URL


@pytest.mark.golden_test("testdata/parse.golden.yml")
def test_parse(golden):
    # Given
    with open(os.path.join(TESTDATA_DIR, golden["input"]["todo_file"]), "rb") as file:
        todo = file.read()

    # When
    resp = requests.post(f"{BASE_URL}/parse?fixed_time=2022-05-22", data=base64.b64encode(todo))

    # Then
    if BASE_URL == SIBYL_URL:
        result = align_sibylgo_result(resp)
        with open("sibyl_parse.json", "w", encoding="utf8") as file:
            file.write(result)
    else:
        data = resp.json()
        result = json.dumps(data, indent=2, sort_keys=True)

    assert remove_timezone_offset(result) == golden.out["output"]


def remove_timezone_offset(result):
    return re.sub(r"\+\d{2}:\d{2}", "", result)


def align_sibylgo_result(resp):
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
        ("999+02:00", "+02:00"),
        ("999+01:00", "+01:00"),
        ('"Recurrence": {', '"recurrence": {'),
        ('"Recurrence": "', '"recurrence_type": "'),
        ("RefDate", "ref_date"),
    ]

    data = resp.json()
    del data["MomentsByID"]
    j = json.dumps(data, indent=2, sort_keys=True)
    return reduce(lambda c, r: c.replace(r[0], r[1]), repls, j)


@pytest.mark.skip()
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
