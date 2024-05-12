# MIT license; Copyright (c) 2022 Ondrej Sienczak
from __future__ import annotations

from com.logging import Logger
from config import Cfg

from machine import WDT, freq, lightsleep
from time import sleep_ms as ssleep_ms
from uasyncio import sleep_ms


log = Logger(__name__)
config = Cfg(
    "sys",
    {
        "pm_enabled": {
            "value": True,
            "description": "Set this true to enable power management and prevent from ESP32 heating",
        },
        "wdt_time": {
            "value": 90,
            "description": "Watchdog time in seconds",
        },
    },
)


class PowerManagement:
    class Users:
        def __init__(self) -> None:
            self.users = 0

        def __enter__(self) -> None:
            self.users += 1
            return self

        def __exit__(self, exc_type, exc_val, exc_tb) -> None:
            self.users -= 1

    def __init__(self, app) -> None:
        self.app = app
        self.disabled = self.Users()

    async def pm_task(self):
        log.msg("Power management", "enabled" if config.pm_enabled else "disabled")

        wdt = WDT(timeout=config.wdt_time * 1000)
        log.msg("Watchdog activated - window", config.wdt_time, "secons")

        def non_pm():
            return self.disabled.users or not config.pm_enabled

        while True:
            freq(80000000)
            log.dbg("CPU-FREQ", 80, "MHz, light sleep", "disabled")

            while non_pm():
                wdt.feed()
                await sleep_ms(100)

            freq(240000000)
            log.dbg("CPU-FREQ", 240, "MHz, light sleep", "enabled")

            while not non_pm():
                wdt.feed()
                ssleep_ms(10)
                lightsleep(50)
                await sleep_ms(0)


__all__ = (
    "PowerManagement",
    "config",
    "log",
)
