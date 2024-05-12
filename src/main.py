# MIT license; Copyright (c) 2022 Ondrej Sienczak
from __future__ import annotations

from app import App
from com.exception import print_exc
from com.logging import Logger

from machine import deepsleep
from sys import exit
from time import sleep
from uasyncio import get_event_loop, run


log = Logger(__name__)


def reset() -> None:
    log.msg("5 seconds to reboot ...")
    sleep(5)
    deepsleep(1)


async def launcher():
    try:
        log.msg("Initializing coroutines scheduler")

        def handle_exception(loop, context):
            exception = context["exception"]
            print_exc(exception)
            if isinstance(exception, KeyboardInterrupt):
                exit()
            else:
                reset()

        loop = get_event_loop()
        loop.set_exception_handler(handle_exception)

        log.msg("Launching application")
        await App()()
    except Exception as exception:
        print_exc(exception)
        reset()


run(launcher())
reset()


__all__ = (
    "log",
    "reset",
)
