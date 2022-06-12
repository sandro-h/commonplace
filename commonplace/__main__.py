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

    cfg = load_config()
    print(f"Starting server at 127.0.0.1:{cfg.port}")
    create_app().run(host="127.0.0.1", port=cfg.port)


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
    config_file = get_my_path() / "config.yml"
    print(config_file)
    if "COMMONPLACE_CONFIG" in os.environ:
        config_file = Path(os.environ["COMMONPLACE_CONFIG"])
        # if passed explicitly and doesn't exist, throw an error:
        if not config_file.exists():
            raise CliException(f"COMMONPLACE_CONFIG {config_file.absolute()} does not exist.")

    if not config_file.exists():
        print("Using default config")
        return YamlConfig()

    print(f"Loading config from {config_file.absolute()}")
    with open(config_file, "r", encoding="utf8") as file:
        data = yaml.safe_load(file)

    return from_dict(data_class=YamlConfig, data=data)


def get_my_path() -> Path:
    if getattr(sys, 'frozen', False):
        # Note: the real directory where PyInstaller extracts and runs the code from is sys._MEIPASS
        # But we want the path of the executable so we can access neighboring files like the config.
        return Path(sys.executable).parent

    return Path(os.path.dirname(os.path.abspath(__file__)))


class CliException(Exception):
    pass


if __name__ == "__main__":
    main()
