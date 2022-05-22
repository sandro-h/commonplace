import base64
import dataclasses
import json
import sys
from datetime import datetime

from flask import Flask, request

from commonplace.models import ParseConfig
from commonplace.parse import parse_moments_string

VERSION = "0.1.0.0"

APP = Flask(__name__)


@APP.route("/")
def hello_world():
    return "<p>Hello, World!</p>"


@APP.route("/parse", methods=["POST"])
def parse_todos():
    content = base64.b64decode(request.data).decode("utf8")
    fixed_time = None
    if "fixed_time" in request.args:
        fixed_time = datetime.strptime(request.args["fixed_time"], "%Y-%m-%d")

    todos = parse_moments_string(content, ParseConfig(fixed_time=fixed_time))
    data = json.dumps(todos, cls=EnhancedJSONEncoder)
    return data


@APP.route("/format", methods=["POST"])
def format_todos():
    return "Not implemented"


class EnhancedJSONEncoder(json.JSONEncoder):

    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        if isinstance(o, datetime):
            return o.isoformat()
        return super().default(o)


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--version":
        print(VERSION)
        return

    APP.run()

    # with open("system_tests/testdata/test_todo.txt", "r") as file:
    #     data = file.read()

    # durs = []
    # for _ in range(0, 1):
    #     now = datetime.now()
    #     # todos = parse_moments_string(data, ParseConfig())
    #     todos = parse_moments_file("system_tests/testdata/test_todo.txt", ParseConfig())

    #     dur = (datetime.now() - now).total_seconds() * 1000
    #     durs.append(dur)

    # print(f"{median(durs)} ms")

    # with open("commonplace_parse.json", "w", encoding="utf8") as file:
    #     json.dump(todos, file, indent=2, sort_keys=True, cls=EnhancedJSONEncoder)


if __name__ == "__main__":
    main()
