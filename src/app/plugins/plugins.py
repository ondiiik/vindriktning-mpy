# MIT license; Copyright (c) 2022 Ondrej Sienczak
from __future__ import annotations

# from .app import App

from config import Cfg
from uasyncio import Event


class Plugin:
    def __init__(self, app: "App", name: str, dfl_cfg: dict[str, any]) -> None:
        self.event = Event()
        self.app = app
        dfl_cfg.setdefault(
            "enabled",
            {
                "value": False,
                "description": "Set True here to enable this plug-in",
            },
        )
        self.cfg = Cfg(f"plugins/{name.split('.')[-1]}", dfl_cfg)

    async def task(self) -> None:
        while True:
            await self.event.wait()
            self.event.clear()
            await self.cycle()

    async def cycle(self) -> None:
        raise NotImplementedError("Missing plugin body")


__all__ = ("Plugin",)
