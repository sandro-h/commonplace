import base64
import dataclasses
from datetime import datetime
import json
import os
import re
from functools import reduce
from time import time

import requests

TESTDATA_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "testdata")
SIBYL_URL = "http://localhost:8082"
COMMONPLACE_URL = "http://127.0.0.1:5000"
COMMONPLACE_JS_URL = "http://127.0.0.1:3000"


def request_parse(content, target="commonplace_js"):
    resp = requests.post(f"{get_url(target)}/parse?fixed_time=2022-05-22&localTime=true",
                         data=base64.b64encode(content.encode("utf8")),
                         headers={"Content-Type": "application/text"})
    if target == "sibyl":
        return align_sibylgo_result(resp.json())
    if target == "commonplace_js":
        return align_commonplace_js_result(resp.json())

    return resp.json()


def request_instances(content, start: str, end: str, target="commonplace_js"):
    resp = requests.post(f"{get_url(target)}/instances?start={reformat_to_ymd(start)}&end={reformat_to_ymd(end)}&localTime=true",
                         data=base64.b64encode(content.encode("utf8")),
                         headers={"Content-Type": "application/text"})

    if target == "sibyl":
        return align_sibylgo_result(resp.json())
    if target == "commonplace_js":
        res = align_commonplace_js_result(resp.json())
        add_null_categories(res)
        return res
    return resp.json()


def request_format(content, format_type="todo", fixed_time="2022-06-05", target="commonplace_js"):
    resp = requests.post(f"{get_url(target)}/format?fixed_time={fixed_time}&type={format_type}",
                         data=base64.b64encode(content.encode("utf8")),
                         headers={"Content-Type": "application/text"})

    return resp.content.decode("utf8")


def request_fold(content, target="commonplace_js"):
    resp = requests.post(f"{get_url(target)}/folding",
                         data=base64.b64encode(content.encode("utf8")),
                         headers={"Content-Type": "application/text"})

    return resp.content.decode("utf8")


def request_outline(content, format_type="todo", target="commonplace_js"):
    resp = requests.post(f"{get_url(target)}/outline?type={format_type}",
                         data=base64.b64encode(content.encode("utf8")),
                         headers={"Content-Type": "application/text"})

    return resp.json()


def request_preview(content, target="commonplace_js", fixed_time="2021-04-17"):
    resp = requests.post(f"{get_url(target)}/preview?fixed_time={fixed_time}&localTime=true",
                         data=base64.b64encode(content.encode("utf8")),
                         headers={"Content-Type": "application/text"})

    return resp.json()


def request_clean(target="commonplace_js"):
    requests.post(f"{get_url(target)}/clean")


def request_trash(fixed_time="2022-06-05", target="commonplace_js"):
    requests.post(f"{get_url(target)}/trash?fixed_time={fixed_time}")


def get_url(target):
    if target == "commonplace":
        return COMMONPLACE_URL
    elif target == "sibyl":
        return SIBYL_URL
    elif target == "commonplace_js":
        print("ja")
        return COMMONPLACE_JS_URL
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


def align_commonplace_js_result(data):
    repls = [
        ('"docPos"', '"doc_pos"'),
        ('"lineNum"', '"line_num"'),
        ('"timeOfDay"', '"time_of_day"'),
        ('"workState"', '"work_state"'),
        ('"subMoments"', '"sub_moments"'),
        ('"sub_moments": null', '"sub_moments": []'),
        ('"comments": null', '"comments": []'),
        (".000", ""),
        (".999", ".999999"),
        ('"recurrence": {', '"recurrence": {'),
        ('"recurrence": "', '"recurrence_type": "'),
        ("refDate", "ref_date"),
        ("inProgress", "in_progress"),
        ("recurrenceType", "recurrence_type"),
        ("originDocPos", "origin_doc_pos"),
        ("subInstances", "sub_instances"),
        ("endsInRange", "ends_in_range"),
    ]

    j = json.dumps(data, indent=2, sort_keys=True)
    aligned = reduce(lambda c, r: c.replace(r[0], r[1]), repls, j)
    return json.loads(aligned)


def add_null_categories(instances):
    for i in instances:
        if "category" not in i:
            i["category"] = None

        add_null_categories(i.get("sub_instances", []))


def dedent(content):
    """Removes the base indentation from a multi-line string.
    Allows to properly indent multiline strings in these tests for better readability."""
    if not content:
        return content
    parts = content.split("\n")
    indent = len(re.match(r"^(\s*)", parts[0] if parts[0] else parts[1]).group(1))
    return "\n".join([p[indent:] for p in parts])


def dataclass_to_dict(dcl):
    return json.loads(json.dumps(dcl, cls=EnhancedJSONEncoder))


def reformat_to_ymd(dmy_str):
    return format_ymd(parse_dmy(dmy_str))


def parse_dmy(dmy_str):
    return datetime.strptime(dmy_str, "%d.%m.%Y").astimezone(tz=None)


def format_ymd(date: datetime) -> str:
    return date.strftime("%Y-%m-%d")


class EnhancedJSONEncoder(json.JSONEncoder):

    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        if isinstance(o, datetime):
            return o.isoformat()
        if isinstance(o, time):
            return o.isoformat()
        return super().default(o)
