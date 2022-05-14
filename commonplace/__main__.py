import dataclasses
from datetime import datetime
import json
import sys
from commonplace.models import ParseConfig
# from flask import Flask

from commonplace.parse import parse_moments_file

VERSION = "0.1.0.0"

# APP = Flask(__name__)

# @APP.route("/")
# def hello_world():
#     return "<p>Hello, World!</p>"

# @APP.route("/format", methods=["POST"])
# def format_todos():
#     return "Not implemented"


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

    # APP.run()

    now = datetime.now()
    todos = parse_moments_file("system_tests/testdata/test_todo.txt", ParseConfig())
    print((datetime.now() - now).total_seconds() * 1000)
    with open("commonplace_parse.json", "w", encoding="utf8") as file:
        json.dump(todos, file, indent=2, sort_keys=True, cls=EnhancedJSONEncoder)


if __name__ == "__main__":
    main()
