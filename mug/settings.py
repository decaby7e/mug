import logging
import os

import toml

BASE_DIR = os.path.dirname(
    os.path.realpath(os.path.join(os.getcwd(), os.path.expanduser(__file__)))
)

APP_NAME = "MUG"


def get_config():
    config = None
    search_paths = ["./config.toml", "/etc/mug.toml"]

    for path in search_paths:
        if os.path.exists(path):
            config = toml.load(path)
            break

    return config


# Generated variables
config = get_config()
logger = logging.getLogger(APP_NAME)
