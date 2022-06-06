import base64
from contextlib import contextmanager
import dataclasses
import json
import sys
from datetime import datetime, time

from flask import Flask, request
from commonplace.clean import clean_done_moments, trash_done_moments
from commonplace.format import format_todos
from commonplace.instantiate import generate_instances

from commonplace.models import ParseConfig
from commonplace.parse import parse_moments_string
from commonplace.util import parse_ymd

VERSION = "0.1.0.0"

APP = Flask(__name__)


@contextmanager
def measure_time(label):
    if APP.config["ENV"] != "development":
        yield
    else:
        start = datetime.now()
        try:
            yield
        finally:
            print(f"{label}: {(datetime.now() - start).total_seconds() * 1000}ms")


@APP.route("/parse", methods=["POST"])
def parse_todos():
    with measure_time("b64decode"):
        content = base64.b64decode(request.data).decode("utf8")

    fixed_time = None
    if "fixed_time" in request.args:
        fixed_time = parse_ymd(request.args["fixed_time"])

    with measure_time("parse"):
        todos = parse_moments_string(content, ParseConfig(fixed_time=fixed_time))

    with measure_time("json.dumps"):
        data = json.dumps(todos, cls=EnhancedJSONEncoder)

    return data


@APP.route("/instances", methods=["POST"])
def generate_moment_instances():
    with measure_time("b64decode"):
        content = base64.b64decode(request.data).decode("utf8")

    start = parse_ymd(request.args["start"]).astimezone(tz=None)
    end = parse_ymd(request.args["end"]).astimezone(tz=None)

    with measure_time("parse"):
        todos = parse_moments_string(content, ParseConfig())

    with measure_time("instantiate"):
        instances = generate_instances(todos.moments, start, end)

    with measure_time("json.dumps"):
        data = json.dumps(instances, cls=EnhancedJSONEncoder)

    return data


@APP.route("/format", methods=["POST"])
def do_format_todos():
    with measure_time("b64decode"):
        content = base64.b64decode(request.data).decode("utf8")

    fixed_time = None
    if "fixed_time" in request.args:
        fixed_time = parse_ymd(request.args["fixed_time"])

    with measure_time("parse"):
        todos = parse_moments_string(content, ParseConfig())

    with measure_time("format"):
        return format_todos(todos, content, fixed_time=fixed_time)


@APP.route("/clean", methods=["POST"])
def clean_todos():
    # TODO: if no todo_file/trash_file arg, use the configured files
    todo_file = request.args["todo_file"]

    with measure_time("clean"):
        clean_done_moments(todo_file, ParseConfig())

    return ("", 204)


@APP.route("/trash", methods=["POST"])
def trash_todos():
    # TODO: if no todo_file/trash_file arg, use the configured files
    todo_file = request.args["todo_file"]
    trash_file = request.args["trash_file"]

    fixed_time = None
    if "fixed_time" in request.args:
        fixed_time = parse_ymd(request.args["fixed_time"])

    with measure_time("clean"):
        trash_done_moments(todo_file, trash_file, ParseConfig(), fixed_time=fixed_time)

    return ("", 204)


class EnhancedJSONEncoder(json.JSONEncoder):

    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        if isinstance(o, datetime):
            return o.isoformat()
        if isinstance(o, time):
            return o.isoformat()
        return super().default(o)


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--version":
        print(VERSION)
        return

    APP.run()


if __name__ == "__main__":
    main()
