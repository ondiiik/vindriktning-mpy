# MIT license; Copyright (c) 2022 Ondrej Sienczak

from app import Main
from com.logging import Logger
from com.exception import print_exc
from sys import exit
from time import sleep
from uasyncio import run, get_event_loop


log = Logger(__name__)


def reset():
    from machine import deepsleep
    log.msg('5 seconds to reboot ...')
    sleep(5)
    deepsleep(1)


async def launcher():
    try:
        log.msg('Initializing coroutines scheduler')

        def handle_exception(loop, context):
            exception = context['exception']
            print_exc(exception)
            if isinstance(exception, KeyboardInterrupt):
                exit()
            else:
                reset()

        loop = get_event_loop()
        loop.set_exception_handler(handle_exception)

        log.msg('Launching application')
        await Main()()
    except Exception as exception:
        print_exc(exception)
        reset()


run(launcher())
reset()
