# MIT license; Copyright (c) 2022 Ondrej Sienczak
from __future__ import annotations

from app.plugins import Plugin
from com.logging import Logger


log = Logger(__name__)


class Co2Alert(Plugin):
    def __init__(self, app: "App") -> None:
        super().__init__(
            app,
            __name__,
            {
                "levels_high": {
                    "value": 1200,
                    "description": "Levels of CO2 in ppm when alert beeps",
                },
                "levels_low": {
                    "value": 600,
                    "description": "Levels of CO2 in ppm when alert consider save CO2 level",
                },
                "night_silent": {
                    "value": True,
                    "description": "Set this on True when you want to switch alert off in night",
                },
            },
        )

    async def task(self):
        measure = self.app.measure
        beep = self.app.beep

        while True:
            while True:
                await self.event.wait()
                self.event.clear()

                if measure.co2_ppm > self.cfg.levels_high:
                    if measure.light_pc > 0:
                        log.msg(
                            "!!! Too much CO2 - ALERT !!!",
                            measure.co2_ppm,
                            "ppm",
                            "(day)",
                        )
                        for _ in range(6):
                            beep(3136, 20, 20, 7)
                            beep(3136, 20, 100)
                            beep(2093, 20, 20, 7)
                            beep(2093, 20, 800)
                    elif not self.cfg.night_silent:
                        log.msg(
                            "!!! Too much CO2 - ALERT !!!",
                            measure.co2_ppm,
                            "ppm",
                            "(night)",
                        )
                        beep(20, 5, 195, 16)
                        beep(20, 5, 1095)
                    else:
                        log.msg(
                            "!!! Too much CO2 - ALERT !!!",
                            measure.co2_ppm,
                            "ppm",
                            "(silent)",
                        )
                        continue
                    break

            while True:
                await self.event.wait()
                self.event.clear()

                if measure.co2_ppm < self.cfg.levels_low:
                    log.msg("Relaxed ...")
                    if measure.light_pc > 0:
                        for i in (262, 294, 330, 349, 392, 440, 494, 523):
                            beep(i, 100)
                    elif not self.cfg.night_silent:
                        for i in (262, 294, 330, 349, 392, 440, 494, 523):
                            beep(i, 5, 95)
                    break


__all__ = (
    "Co2Alert",
    "log",
)
