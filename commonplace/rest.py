import base64
import dataclasses
import json
from contextlib import contextmanager
from datetime import datetime, time

from flask import Blueprint, current_app, request
from commonplace.backup import backup

from commonplace.clean import clean_done_moments, trash_done_moments
from commonplace.format import fold_todos, format_todos, TODO_FORMAT, outline_todos
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
    format_type = request.args.get("type", TODO_FORMAT)

    with measure_time("parse"):
        todos = parse_moments_string(content, ParseConfig())

    with measure_time("format"):
        return format_todos(todos, content, format_type=format_type, fixed_time=fixed_time)


@root.route("/folding", methods=["POST"])
def do_fold_todos():
    with measure_time("b64decode"):
        content = base64.b64decode(request.data).decode("utf8")

    with measure_time("parse"):
        todos = parse_moments_string(content, ParseConfig())

    with measure_time("fold"):
        return fold_todos(todos)


@root.route("/outline", methods=["POST"])
def do_outline_todos():
    with measure_time("b64decode"):
        content = base64.b64decode(request.data).decode("utf8")

    format_type = request.args.get("type", TODO_FORMAT)

    with measure_time("parse"):
        todos = parse_moments_string(content, ParseConfig())

    with measure_time("outline"):
        return {"outline": outline_todos(todos, content, format_type)}


@root.route("/all", methods=["POST"])
def do_all():
    with measure_time("b64decode"):
        content = base64.b64decode(request.data).decode("utf8")

    fixed_time = parse_ymd(request.args.get("fixed_time"))
    format_type = request.args.get("type", TODO_FORMAT)

    with measure_time("parse"):
        todos = parse_moments_string(content, ParseConfig())

    result = {}
    with measure_time("format"):
        result["format"] = format_todos(todos, content, format_type=format_type, fixed_time=fixed_time)

    with measure_time("fold"):
        result["fold"] = fold_todos(todos)

    with measure_time("outline"):
        result["outline"] = outline_todos(todos, content, format_type)

    # Not implemented yet:
    result["preview"] = {}

    return result


@root.route("/clean", methods=["POST"])
def clean_todos():
    backup(config().todo_file, config().backup_dir)

    with measure_time("clean"):
        clean_done_moments(config().todo_file, ParseConfig())

    return ("", 204)


@root.route("/trash", methods=["POST"])
def trash_todos():
    fixed_time = parse_ymd(request.args.get("fixed_time"))

    backup(config().todo_file, config().backup_dir)
    if config().trash_file.exists():
        backup(config().trash_file, config().backup_dir)

    with measure_time("clean"):
        trash_done_moments(config().todo_file, config().trash_file, ParseConfig(), fixed_time=fixed_time)

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
