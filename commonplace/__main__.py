import logging
import os
import sys
from pathlib import Path

import yaml
from dacite import from_dict
from flask import Flask

from commonplace.models import Config, YamlConfig
from commonplace.rest import root

# Will be set to contents of version.txt by Makefile:
VERSION = "0.1.0.0"


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--version":
        print(VERSION)
        return

    create_app().run(host="127.0.0.1", port=load_config().port)


def create_app():
    log = logging.getLogger("werkzeug")
    log.setLevel(logging.ERROR)

    app = Flask(__name__)
    app.register_blueprint(root)
    app.config["commonplace"] = load_config()

    return app


def load_config() -> Config:
    yaml_config = load_yaml_config()
    todo_file = Path(yaml_config.todo_file).absolute()
    todo_dir = todo_file.parent.absolute()
    return Config(
        port=yaml_config.port,
        todo_dir=todo_dir,
        todo_file=todo_file,
        trash_file=todo_dir / f"{todo_file.stem}-trash.txt",
        backup_dir=todo_dir / "backup",
        parse_config=yaml_config.parse_config,
    )


def load_yaml_config() -> YamlConfig:
    config_file = Path("config.yaml")
    if "COMMONPLACE_CONFIG" in os.environ:
        config_file = Path(os.environ["COMMONPLACE_CONFIG"])
        print(config_file)
        # if passed explicitly and doesn't exist, throw an error:
        if not config_file.exists():
            raise CliException(f"COMMONPLACE_CONFIG {config_file.absolute()} does not exist.")

    if not config_file.exists():
        return YamlConfig()

    with open(config_file, "r", encoding="utf8") as file:
        data = yaml.safe_load(file)

    return from_dict(data_class=YamlConfig, data=data)


class CliException(Exception):
    pass


if __name__ == "__main__":
    main()
