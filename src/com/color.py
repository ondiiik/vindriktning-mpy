# MIT license; Copyright (c) 2022 Ondrej Sienczak
from __future__ import annotations


class Rgb(list):
    def __init__(self, r=0, g=0, b=0) -> None:
        super().__init__((r, g, b))

    def __add__(self, other) -> None:
        return Rgb(self[0] + other[0], self[1] + other[1], self[2] + other[2])

    def __sub__(self, other) -> None:
        return Rgb(self[0] - other[0], self[1] - other[1], self[2] - other[2])

    def __mul__(self, num) -> None:
        return Rgb(self[0] * num, self[1] * num, self[2] * num)

    def __floordiv__(self, num) -> None:
        return Rgb(self[0] // num, self[1] // num, self[2] // num)

    def __truediv__(self, num) -> None:
        return Rgb(self[0] / num, self[1] / num, self[2] / num)

    def binary(self, val) -> None:
        return Rgb(
            val[0] if self[0] else 0, val[1] if self[1] else 0, val[2] if self[2] else 0
        )

    def max(self, val) -> None:
        m = max(*self)
        return bytes([int(m == self[i]) * val[i] for i in range(3)])

    @property
    def bytes(self) -> None:
        return bytes(self._crop)

    @property
    def round(self) -> None:
        return Rgb(*self._crop)

    @property
    def _crop(self) -> None:
        return [max(0, min(255, round(i))) for i in self]


__all__ = ("Rgb",)
