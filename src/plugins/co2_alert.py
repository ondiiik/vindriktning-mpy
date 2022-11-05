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
                        log.msg('!!! Too much CO2 - ALERT !!!', measure.co2_ppm, 'ppm', '(day)')
                        for _ in range(6):
                            beep(3136, 20, 20, 7)
                            beep(3136, 20, 100)
                            beep(2093, 20, 20, 7)
                            beep(2093, 20, 800)
                    elif not config.night_silent:
                        log.msg('!!! Too much CO2 - ALERT !!!', measure.co2_ppm, 'ppm', '(night)')
                        beep(20, 5, 195, 16)
                        beep(20, 5, 1095)
                    else:
                        log.msg('!!! Too much CO2 - ALERT !!!', measure.co2_ppm, 'ppm', '(silent)')
                        continue
                    break

            while True:
                await self.event.wait()
                self.event.clear()

                if measure.co2_ppm < config.levels_low:
                    log.msg('Relaxed ...')
                    if measure.light_pc > 0:
                        for i in (262, 294, 330, 349, 392, 440, 494, 523):
                            beep(i, 100)
                    elif not config.night_silent:
                        for i in (262, 294, 330, 349, 392, 440, 494, 523):
                            beep(i, 5, 95)
                    break
