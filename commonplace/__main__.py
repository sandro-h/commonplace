import sys
from flask import Flask

VERSION = "0.1.0.0"

APP = Flask(__name__)


@APP.route("/")
def hello_world():
    return "<p>Hello, World!</p>"


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--version":
        print(VERSION)
        return

    APP.run()


if __name__ == "__main__":
    main()
