#!/usr/bin/env python3

import os
import logging
from pathlib import Path
from typing import Optional
from .. import settings, connections

import toml
import typer

from . import account, group

app = typer.Typer()
app.add_typer(account.app)
app.add_typer(group.app)


@app.callback()
def main(
    config: Optional[Path] = typer.Option(None, "-c", "--config"),
    database: Optional[Path] = typer.Option(None, "-d", "--database"),
    verbose: bool = typer.Option(False, "-v", "--verbose"),
):
    if config:
        settings.config = toml.load(config)

    if not settings.config:
        raise FileNotFoundError(
            "Could not find configuration file! Specify one with `-c/--config`."
        )

    if database:
        sqlite_file = database
        settings.config["sqlite"]["path"] = database
    else:
        sqlite_file = settings.config["sqlite"]["path"]

    if not os.path.exists(sqlite_file):
        Path(sqlite_file).touch()

    if not os.path.getsize(sqlite_file):
        connections.init_db()

    # FIXME: basicConfig not valid for logger object
    if verbose:
        logging.basicConfig(format="%(levelname)s   %(message)s", level=logging.DEBUG)


if __name__ == "__main__":
    app()
