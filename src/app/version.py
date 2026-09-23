# MIT license; Copyright (c) 2022 Ondrej Sienczak
from __future__ import annotations


class Version(tuple):
    def __init__(self, major: int, minor: int) -> None:
        super().__init__((major, minor))

    def __repr__(self) -> str:
        return f"v{self[0]}.{self[1]}"

    def __str__(self) -> str:
        return repr(self)


version = Version(2, 6)


__all__ = (
    "Version",
    "version",
)
