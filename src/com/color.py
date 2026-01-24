# MIT license; Copyright (c) 2022 Ondrej Sienczak
from __future__ import annotations

from typing import List


class Rgb(list):
    def __init__(self, r=0, g=0, b=0) -> None:
        super().__init__((r, g, b))

    def __add__(self, other) -> Rgb:
        return Rgb(self[0] + other[0], self[1] + other[1], self[2] + other[2])

    def __sub__(self, other) -> Rgb:
        return Rgb(self[0] - other[0], self[1] - other[1], self[2] - other[2])

    def __mul__(self, num) -> Rgb:
        return Rgb(self[0] * num, self[1] * num, self[2] * num)

    def __floordiv__(self, num) -> Rgb:
        return Rgb(self[0] // num, self[1] // num, self[2] // num)

    def __truediv__(self, num) -> Rgb:
        return Rgb(self[0] / num, self[1] / num, self[2] / num)

    def binary(self, val) -> Rgb:
        return Rgb(
            val[0] if self[0] else 0, val[1] if self[1] else 0, val[2] if self[2] else 0
        )

    def max(self, val) -> bytes:
        m = max(*self)
        return bytes([int(m == self[i]) * val[i] for i in range(3)])

    @property
    def bytes(self) -> bytes:
        return bytes(self._crop)

    @property
    def round(self) -> Rgb:
        return Rgb(*self._crop)

    @property
    def _crop(self) -> List[int]:
        return [max(0, min(255, round(i))) for i in self]


__all__ = ("Rgb",)
