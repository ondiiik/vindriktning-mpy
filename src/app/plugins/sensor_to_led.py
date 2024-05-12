# MIT license; Copyright (c) 2022 Ondrej Sienczak
from __future__ import annotations

from app.plugins import Plugin
from com.color import Rgb
from com.logging import Logger


log = Logger(__name__)


class Sensor2Led(Plugin):
    colors = (
        Rgb(0, 96, 0),
        Rgb(0, 56, 56),
        Rgb(0, 0, 96),
        Rgb(255, 0, 160),
        Rgb(255, 0, 0),
    )

    def __init__(self, app: "App") -> None:
        super().__init__(
            app,
            __name__,
            {
                "enabled": {
                    "value": True,
                    "description": "Set True here to enable this plug-in",
                },
                "levels_co2": {
                    "value": [700, 850, 1000, 1200],
                    "description": "Levels for sensors values for GOOD, OK, BAD and WORST signalisation of CO2 in ppm",
                },
                "levels_dust": {
                    "value": [20, 40, 67, 85],
                    "description": "Levels for sensors values for GOOD, OK, BAD and WORST signalisation of dust in air in ug/m3",
                },
                "night_mode": {
                    "value": False,
                    "description": "When enabled, then LEDs are off during night, excluding case of BAD or WORST CO2 sensor conditions level",
                },
            },
        )
        app.led.min = (
            b"\x00\x00\x00",
            b"\x00\x00\x00",
            b"\x01\x00\x00" if self.cfg.night_mode else b"\x01\x01\x01",
        )

    async def cycle(self):
        measure = self.app.measure
        led = self.app.led

        self._led(led, 2, self.cfg.levels_co2, measure.co2_ppm)
        self._led(led, 0, self.cfg.levels_dust, measure.dust_ugpm3)

        led[1] = (led[0] + led[2]) // 2
        log.dbg("LED state", led[0], led[1], led[2])

    @classmethod
    def _led(cls, led, idx, levels, val) -> None:
        colors = cls.colors

        if val is None:
            led = led.BLACK
            return

        if val < levels[0]:
            led[idx] = colors[0]
            return

        for i in range(3):
            rng1 = levels[i + 1]
            if val < rng1:
                rng0 = levels[i]
                color = (colors[i] * (rng1 - val) + colors[i + 1] * (val - rng0)) / (
                    rng1 - rng0
                )
                led[idx] = color
                return

        led[idx] = colors[-1]


__all__ = (
    "Sensor2Led",
    "log",
)
