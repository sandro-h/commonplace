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


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--version":
        print(VERSION)
        return

    # APP.run()

    todos = parse_moments_file("system_tests/testdata/test_todo.txt", ParseConfig())
    print(todos)


if __name__ == "__main__":
    main()
