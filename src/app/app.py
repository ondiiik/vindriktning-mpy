# MIT license; Copyright (c) 2022 Ondrej Sienczak
from __future__ import annotations

from .beeper import Beeper
from .dispatch import Dispatcher
from .ledctrl import LedCtrl
from .measure import Measure
from .networking import WiFi
from .pm import PowerManagement
from .version import version

from com.color import Rgb
from com.exception import print_exc
from com.logging import Logger
from hal.vindriktning import Vindriktning

from asyncio import create_task, gather, get_event_loop, run, sleep_ms
from machine import PWRON_RESET, deepsleep, reset_cause
from time import sleep


_log = Logger(__name__)


class App:
    def __init__(self) -> None:
        _log.msg("Starting version", version)
        self.version = version
        self.vindriktning = Vindriktning()
        self.pm = PowerManagement(self)
        self.measure = Measure(self)
        self.led = LedCtrl(self)
        self.beep = Beeper(self)
        self.wifi = WiFi(self)

        if reset_cause() == PWRON_RESET:
            for i in (262, 294, 330, 349, 392, 440, 494, 523):
                self.vindriktning.buzzer.on(i)
                sleep(0.05)
            self.vindriktning.buzzer.off()

            led = self.vindriktning.led

            for c in (
                lambda i: Rgb(i, 0, 0),
                lambda i: Rgb(0, i, 0),
                lambda i: Rgb(0, 0, i),
            ):
                for i in range(256):
                    led[0] = led[1] = led[2] = c(i)
                    led.write()
                for i in reversed(range(256)):
                    led[0] = led[1] = led[2] = c(i)
                    led.write()

        self.dispatcher = Dispatcher(self)

    def __call__(self) -> None:
        run(self._run())

    async def _run(self) -> None:
        try:
            _log.msg("Initializing coroutines scheduler")

            def handle_exception(loop, context):
                exception = context["exception"]
                print_exc(exception)
                if isinstance(exception, KeyboardInterrupt):
                    exit()
                else:
                    self._reset()

            loop = get_event_loop()
            loop.set_exception_handler(handle_exception)

            _log.msg("Launching application")
            await gather(
                self.measure.light_task(),
                self.measure.co2_task(),
                self.measure.dust_task(),
                self.dispatcher.dispatch_task(),
                self.led.animate_task(),
                self.beep.beep_task(),
                self.wifi.connection_task(),
                self.pm.pm_task(),
            )
        except Exception as exception:
            print_exc(exception)
            self._reset()

    @staticmethod
    def _reset() -> None:
        _log.msg("5 seconds to reboot ...")
        sleep(5)
        deepsleep(1)


__all__ = ("App",)
