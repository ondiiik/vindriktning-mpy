# MIT license; Copyright (c) 2022 Ondrej Sienczak

from app.plugins import Plugin
from com.logging import Logger
import config.plugins.co2_alert as config


log = Logger(__name__)


class Sensor2Led(Plugin):
    async def task(self):
        measure = self.app.measure
        beep = self.app.beep

        while True:
            while True:
                await self.event.wait()
                self.event.clear()

                if measure.co2_ppm > config.levels_high:
                    if measure.light_pc > 0:
                        for _ in range(3):
                            log.msg('!!! Too much CO2 - ALERT !!!', measure.co2_ppm, 'ppm', '(day)')
                            beep.beep(100, 100, 5)
                            beep.beep(100, 1000)
                    elif not config.night_silent:
                        log.msg('!!! Too much CO2 - ALERT !!!', measure.co2_ppm, 'ppm', '(night)')
                        beep.beep(5, 195, 5)
                        beep.beep(5, 1095)
                    else:
                        log.msg('!!! Too much CO2 - ALERT !!!', measure.co2_ppm, 'ppm', '(silent)')
                    break

            while True:
                await self.event.wait()
                self.event.clear()

                if measure.co2_ppm < config.levels_low:
                    log.msg('Relaxed ...')
                    break
