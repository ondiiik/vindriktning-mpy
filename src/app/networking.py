# MIT license; Copyright (c) 2022 Ondrej Sienczak
from __future__ import annotations

from com.logging import Logger
from config import Cfg

from asyncio import Event, sleep_ms
from gc import collect
from machine import lightsleep
from network import STA_IF, WLAN
from typing import Type


log = Logger(__name__)
config = Cfg(
    "wifi",
    {
        "ssid": {
            "value": "Please fill in",
            "description": "SSID (name) of WiFi network where to be connected.",
        },
        "passwd": {
            "value": "Please fill in",
            "description": "WiFi connection password.",
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

    async def __aenter__(self) -> Type[WiFi]:
        cls = type(self)
        cls.users += 1

        if cls.users == 1:
            cls.ev_change.set()

        await cls.ev_running.wait()

        return cls

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        cls = type(self)
        cls.users -= 1

        if cls.users == 0:
            cls.ev_change.set()

    async def connection_task(self) -> None:
        log.msg("Start service ...")
        cls = type(self)

        while True:
            await cls.ev_change.wait()

            with self.app.pm.disabled:
                log.dbg("Connecting ...")
                cls.sta_if.active(True)
                await cls._connect()
                collect()

                while not cls.sta_if.isconnected():
                    await sleep_ms(500)

                log.msg("Connected:", cls.sta_if.ifconfig())
                cls.ev_running.set()
                cls.ev_change.clear()

                await cls.ev_change.wait()
                log.dbg("Disconnecting ...")

                cls.sta_if.disconnect()
                cls.sta_if.config(
                    pm=0
                )  # Prevent from "E (114888) wifi:mac deinit fail, txing can't stop, exit!"
                await sleep_ms(1000)
                cls.sta_if.active(False)

            lightsleep(1)
            self.app.vindriktning.light_reinit()

            cls.ev_change.clear()
            cls.ev_running.clear()
            log.msg("Disconnected")

    @classmethod
    async def _connect(cls) -> None:
        for _ in range(8):
            try:
                cls.sta_if.connect(config.ssid, config.passwd)
                return
            except OSError:
                await sleep_ms(1000)
        cls.sta_if.connect(config.ssid, config.passwd)


__all__ = (
    "WiFi",
    "config",
    "log",
)
