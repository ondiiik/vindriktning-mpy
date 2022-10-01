# MIT license; Copyright (c) 2022 Ondrej Sienczak

from uasyncio import sleep_ms
from com.color import Rgb


class LedCtrl(list):
    BLACK = Rgb(0, 0, 0)
    GRAY = Rgb(96, 96, 96)

    def __init__(self, app):
        super().__init__([self.BLACK] * 3)
        self.app = app
        self.min = b'\x00\x00\x00', b'\x00\x00\x00', b'\x00\x00\x00'

    async def animate_task(self):
        led = self.app.vindriktning.led
        measure = self.app.measure
        firg = 0.0
        firc = self

        while True:
            gain = max(measure.light_pc, 0.1) / 100
            firg = firg * 0.9 + gain * 0.1
            firc = [fir * 0.9 + led * 0.1 for led, fir in zip(self, firc)]

            for i in range(3):
                clf = firc[i] * firg
                clr = clf.round
                led[i] = clr if any(clr) else clf.max(self.min[i])

            led.write()

            await sleep_ms(round(50 - 40 * gain))
