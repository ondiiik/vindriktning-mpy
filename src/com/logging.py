# MIT license; Copyright (c) 2022 Ondrej Sienczak
from __future__ import annotations

from config import Cfg


config = Cfg(
    "logging",
    {
        "verbose": {
            "value": False,
            "description": "Set this to true to have more verbose log",
        },
    },
)


class Logger:
    def __init__(self, name) -> None:
        name = f'[{name.split(".")[-1]}]'
        self.name = f"{name:<16}"

    def err(self, *args, **kwargs) -> None:
        print("!!", self.name, *args, **kwargs)

    def wrn(self, *args, **kwargs) -> None:
        print("??", self.name, *args, **kwargs)

    def msg(self, *args, **kwargs) -> None:
        print("..", self.name, *args, **kwargs)

    if config.verbose:

        def dbg(self, *args, **kwargs) -> None:
            print("  ", self.name, *args, **kwargs)

    else:

        def dbg(self, *args, **kwargs) -> None:
            pass


__all__ = (
    "Logger",
    "config",
)
