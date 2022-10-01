# MIT license; Copyright (c) 2022 Ondrej Sienczak

from .beeper import Beeper
from .dispatch import Dispatcher
from .ledctrl import LedCtrl
from .measure import Measure
from .networking import WiFi
from .pm import PowerManagement
from .version import version
from com.color import Rgb
from com.logging import Logger
from hal.vindriktning import Vindriktning
from machine import reset_cause, PWRON_RESET
from time import sleep
from uasyncio import create_task, sleep_ms


log = Logger(__name__)


class Main:
    def __init__(self):
        log.msg('Starting version', version)
        self.version = version
        self.vindriktning = Vindriktning()
        self.pm = PowerManagement(self)
        self.measure = Measure(self)
        self.led = LedCtrl(self)
        self.beep = Beeper(self)
        self.wifi = WiFi(self)

        if reset_cause() == PWRON_RESET:
            self.vindriktning.buzzer.on()
            sleep(0.05)
            self.vindriktning.buzzer.off()

            led = self.vindriktning.led

            for c in (lambda i: Rgb(i, 0, 0), lambda i: Rgb(0, i, 0), lambda i: Rgb(0, 0, i)):
                for i in range(256):
                    led[0] = led[1] = led[2] = c(i)
                    led.write()
                for i in reversed(range(256)):
                    led[0] = led[1] = led[2] = c(i)
                    led.write()

        self.dispatcher = Dispatcher(self)

    async def __call__(self):
        create_task(self.measure.light_task())
        create_task(self.measure.co2_task())
        create_task(self.measure.dust_task())
        create_task(self.dispatcher.dispatch_task())
        create_task(self.led.animate_task())
        create_task(self.beep.beep_task())
        create_task(self.wifi.connection_task())
        create_task(self.pm.pm_task())

        while True:
            await sleep_ms(60000)
