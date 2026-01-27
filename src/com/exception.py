# MIT license; Copyright (c) 2022 Ondrej Sienczak
from __future__ import annotations

from com.logging import Logger, config

from sys import exit, print_exception


def print_exc(exception) -> None:
    print_exception(exception)

    if config.exceptions:
        with open("error.log", "a") as f:
            f.write("\n")
            print_exception(exception, f)


__all__ = ("print_exc",)
