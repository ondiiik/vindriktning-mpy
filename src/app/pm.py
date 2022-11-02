# MIT license; Copyright (c) 2022 Ondrej Sienczak

from com.logging import Logger
from uasyncio import sleep_ms
from machine import lightsleep, WDT, freq
from config.sys import pm_enabled, wdt_time

log = Logger(__name__)


class PowerManagement:
    class Users:
        def __init__(self):
            self.users = 0

        def __enter__(self):
            self.users += 1
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.users -= 1

    def __init__(self, app):
        self.app = app
        self.disabled = self.Users()

    async def pm_task(self):
        log.msg('Power management', 'enabled' if pm_enabled else 'disabled')

        wdt = WDT(timeout=wdt_time * 1000)
        log.msg('Watchdog activated - window', wdt_time, 'secons')

        def non_pm():
            return self.disabled.users or not pm_enabled

        while True:
            freq(80000000)
            log.dbg('CPU-FREQ', 80, 'MHz, light sleep', 'disabled')

            while non_pm():
                wdt.feed()
                await sleep_ms(100)

            freq(240000000)
            log.dbg('CPU-FREQ', 240, 'MHz, light sleep', 'enabled')

            while not non_pm():
                wdt.feed()
                lightsleep(50)
                await sleep_ms(0)
