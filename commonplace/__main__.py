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

    # bla = {"content": "\tinr ep-reh ende rit involup tatevel :/", "doc_pos": {"length": 39, "line_num": 329, "offset": 10196}}
    # match bla:
    #     #
    #     case {"doc_pos": {"length": 40}}:
    #         print("jiiii")
    # print("hi")


if __name__ == "__main__":
    main()
