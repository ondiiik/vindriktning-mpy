# MIT license; Copyright (c) 2022 Ondrej Sienczak
from __future__ import annotations

from com.logging import Logger
from config import Cfg

from gc import collect
from machine import lightsleep
from network import STA_IF, WLAN
from uasyncio import Event, sleep_ms


log = Logger(__name__)
config = Cfg(
    "wifi",
    {
        "ssid": {
            "value": "Please fill in",
            "description": "SSID (name) of WiFi network where to be connected",
        },
        "passwd": {
            "value": "Please fill in",
            "description": "WiFi Password",
        },
    },
)


class WiFi:
    ev_change = Event()
    ev_running = Event()
    users = 0
    sta_if = WLAN(STA_IF)

    def __init__(self, app) -> None:
        self.app = app

    async def __aenter__(self):
        self.app.pm.disabled.__enter__()

        cls = type(self)
        cls.users += 1

        if cls.users == 1:
            cls.ev_change.set()

        await cls.ev_running.wait()

        return cls

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.app.pm.disabled.__exit__(exc_type, exc_val, exc_tb)

        cls = type(self)
        cls.users -= 1

        if cls.users == 0:
            cls.ev_change.set()

    async def connection_task(self):
        log.msg("Start service ...")
        cls = type(self)

        while True:
            await cls.ev_change.wait()

            log.dbg("Connecting ...")
            cls.sta_if.active(True)
            cls._connect()
            collect()

            while not cls.sta_if.isconnected():
                await sleep_ms(500)

            log.msg("Connected:", cls.sta_if.ifconfig())
            cls.ev_running.set()
            cls.ev_change.clear()

            await cls.ev_change.wait()
            log.dbg("Disconnecting ...")

            cls.sta_if.disconnect()
            cls.sta_if.active(False)
            lightsleep(1)
            self.app.vindriktning.light_reinit()

            cls.ev_change.clear()
            cls.ev_running.clear()
            log.msg("Disconnected")

    @classmethod
    def _connect(cls) -> None:
        cls.sta_if.connect(config.ssid, config.passwd)


__all__ = (
    "WiFi",
    "config",
    "log",
)
