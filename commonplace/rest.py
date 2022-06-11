import base64
import dataclasses
import json
from contextlib import contextmanager
from datetime import datetime, time

from flask import Blueprint, current_app, request

from commonplace.clean import clean_done_moments, trash_done_moments
from commonplace.format import format_todos
from commonplace.instantiate import generate_instances
from commonplace.models import Config, ParseConfig
from commonplace.parse import parse_moments_string
from commonplace.util import parse_ymd

root = Blueprint('root', __name__)


@root.route("/parse", methods=["POST"])
def parse_todos():
    with measure_time("b64decode"):
        content = base64.b64decode(request.data).decode("utf8")

    fixed_time = parse_ymd(request.args.get("fixed_time"))

    with measure_time("parse"):
        todos = parse_moments_string(content, ParseConfig(fixed_time=fixed_time))

    with measure_time("json.dumps"):
        data = json.dumps(todos, cls=EnhancedJSONEncoder)

    return data


@root.route("/instances", methods=["POST"])
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


@root.route("/format", methods=["POST"])
def do_format_todos():
    with measure_time("b64decode"):
        content = base64.b64decode(request.data).decode("utf8")

    fixed_time = parse_ymd(request.args.get("fixed_time"))

    with measure_time("parse"):
        todos = parse_moments_string(content, ParseConfig())

    with measure_time("format"):
        return format_todos(todos, content, fixed_time=fixed_time)


@root.route("/clean", methods=["POST"])
def clean_todos():
    todo_file = config().todo_file

    if is_development():
        todo_file = request.args.get("todo_file", todo_file)

    with measure_time("clean"):
        clean_done_moments(todo_file, ParseConfig())

    return ("", 204)


@root.route("/trash", methods=["POST"])
def trash_todos():
    todo_file = config().todo_file
    trash_file = config().trash_file
    fixed_time = parse_ymd(request.args.get("fixed_time"))

    if is_development():
        todo_file = request.args.get("todo_file", todo_file)
        trash_file = request.args.get("trash_file", trash_file)

    with measure_time("clean"):
        trash_done_moments(todo_file, trash_file, ParseConfig(), fixed_time=fixed_time)

    return ("", 204)


def config() -> Config:
    return current_app.config["commonplace"]


def is_development() -> bool:
    return current_app.config["ENV"] == "development"


@contextmanager
def measure_time(label):
    if not is_development():
        yield
    else:
        start = datetime.now()
        try:
            yield
        finally:
            print(f"{label}: {(datetime.now() - start).total_seconds() * 1000}ms")


class EnhancedJSONEncoder(json.JSONEncoder):

    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        if isinstance(o, datetime):
            return o.isoformat()
        if isinstance(o, time):
            return o.isoformat()
        return super().default(o)
