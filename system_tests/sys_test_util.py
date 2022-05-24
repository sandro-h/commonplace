import base64
import json
import os
import re
from functools import reduce

import requests
from commonplace.__main__ import EnhancedJSONEncoder

TESTDATA_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "testdata")
SIBYL_URL = "http://localhost:8082"
COMMONPLACE_URL = "http://127.0.0.1:5000"


def request_parse(content, target="commonplace"):
    if target == "commonplace":
        url = COMMONPLACE_URL
    elif target == "sibyl":
        url = SIBYL_URL
    else:
        assert False, f"Invalid target {target}"

    resp = requests.post(f"{url}/parse?fixed_time=2022-05-22", data=base64.b64encode(content.encode("utf8")))
    if target == "sibyl":
        return align_sibylgo_result(resp.json())

    return resp.json()


def align_sibylgo_result(data):
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
        ("inProgress", "in_progress"),
    ]

    del data["MomentsByID"]
    j = json.dumps(data, indent=2, sort_keys=True)
    aligned = reduce(lambda c, r: c.replace(r[0], r[1]), repls, j)
    return json.loads(aligned)


def dedent(content):
    """Removes the base indentation from a multi-line string.
    Allows to properly indent multiline strings in these tests for better readability."""
    parts = content.split("\n")
    indent = len(re.match(r"^(\s*)", parts[0]).group(1))
    return "\n".join([p[indent:] for p in parts])


def dataclass_to_dict(dcl):
    return json.loads(json.dumps(dcl, cls=EnhancedJSONEncoder))
