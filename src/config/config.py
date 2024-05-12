# MIT license; Copyright (c) 2022 Ondrej Sienczak
from __future__ import annotations

from json import dump, load
from os import mkdir


class Cfg(dict):
    def __init__(self, path: str, dfl_cfg: dict[str, any]) -> dict[str, any]:
        path = f"cfg/{path}.json"
        try:
            with open(path, "r") as f:
                cfg = load(f)
            super().__init__(cfg.items())
        except OSError:
            with open(path, "w") as f:
                f.write("{\n")
                for i, (k, v) in enumerate(dfl_cfg.items()):
                    f.write(f'  "{k}": ')
                    dump(v, f)
                    f.write("\n" if i == (len(dfl_cfg) - 1) else ",\n")
                f.write("}\n")
            super().__init__(dfl_cfg.items())

    def __getattr__(self, k: str) -> any:
        v = super().get(k)
        return v["value"] if isinstance(v, dict) else v

    def __setattr__(self, k: str, v: any) -> None:
        raise ValueError("Read only object")


try:
    mkdir("cfg")
except:
    ...

try:
    mkdir("cfg/plugins")
except:
    ...


__all__ = ("Cfg",)
