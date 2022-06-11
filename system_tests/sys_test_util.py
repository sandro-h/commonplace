import base64
from datetime import datetime
import json
import os
import re
from functools import reduce

import requests
from commonplace.rest import EnhancedJSONEncoder
from commonplace.util import format_ymd

TESTDATA_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "testdata")
SIBYL_URL = "http://localhost:8082"
COMMONPLACE_URL = "http://127.0.0.1:5000"


def request_parse(content, target="commonplace"):
    resp = requests.post(f"{get_url(target)}/parse?fixed_time=2022-05-22", data=base64.b64encode(content.encode("utf8")))
    if target == "sibyl":
        return align_sibylgo_result(resp.json())

    return resp.json()


def request_instances(content, start: str, end: str, target="commonplace"):
    resp = requests.post(f"{get_url(target)}/instances?start={reformat_to_ymd(start)}&end={reformat_to_ymd(end)}",
                         data=base64.b64encode(content.encode("utf8")))
    if target == "sibyl":
        return align_sibylgo_result(resp.json())

    return resp.json()


def request_format(content, optimize=True, fixed_time="2022-06-05", target="commonplace"):
    resp = requests.post(f"{get_url(target)}/format?fixed_time={fixed_time}&optimize={optimize}",
                         data=base64.b64encode(content.encode("utf8")))

    return resp.content.decode("utf8")


def request_clean(todo_file, target="commonplace"):
    requests.post(f"{get_url(target)}/clean?todo_file={todo_file}")


def request_trash(todo_file, trash_file, fixed_time="2022-06-05", target="commonplace"):
    requests.post(f"{get_url(target)}/trash?fixed_time={fixed_time}&todo_file={todo_file}&trash_file={trash_file}")


def get_url(target):
    if target == "commonplace":
        return COMMONPLACE_URL
    elif target == "sibyl":
        return SIBYL_URL
    else:
        assert False, f"Invalid target {target}"


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
    indent = len(re.match(r"^(\s*)", parts[0] if parts[0] else parts[1]).group(1))
    return "\n".join([p[indent:] for p in parts])


def dataclass_to_dict(dcl):
    return json.loads(json.dumps(dcl, cls=EnhancedJSONEncoder))


def reformat_to_ymd(dmy_str):
    return format_ymd(parse_dmy(dmy_str))


def parse_dmy(dmy_str):
    return datetime.strptime(dmy_str, "%d.%m.%Y").astimezone(tz=None)
