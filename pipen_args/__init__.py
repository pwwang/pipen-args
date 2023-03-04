"""Command line argument parser for pipen"""
from __future__ import annotations

import sys
from typing import Any

from diot import Diot
from simpleconf import Config

from .version import __version__
from .parser import Parser  # noqa: F401
from .procgroup import ProcGroup  # noqa: F401


def __getattr__(name: str) -> Any:
    """Instantiate the instance only on import"""
    # to avoid this function to be called twice
    if name == "__path__":  # pragma: no cover
        raise AttributeError

    if name == "config":
        # Allow
        # from pipen_args import config
        # to load the config from the file and use it separately
        for arg in sys.argv:
            if arg.startswith("@"):
                return Config.load(arg[1:])
        return Diot()

    raise AttributeError  # pragma: no cover
