# MIT license; Copyright (c) 2022 Ondrej Sienczak
from __future__ import annotations

from collections import deque, namedtuple
from time import sleep_ms
from uasyncio import Event, sleep_ms as asleep_ms


class Beeper:
    beepit = namedtuple("Beep", ("freq", "duration", "gap", "cnt"))

    def __init__(self, app) -> None:
        self.app = app
        self.beeps = deque(tuple(), 128)
        self.event = Event()

    def __call__(self, freq, duration, gap=0, cnt=1) -> None:
        self.beeps.append(self.beepit(freq, duration, gap, cnt))
        self.event.set()

    async def beep_task(self):
        buzzer = self.app.vindriktning.buzzer
        beeps = self.beeps
        event = self.event
        pm = self.app.pm

        while True:
            await event.wait()

            with pm.disabled:
                while beeps:
                    beep = beeps.popleft()
                    for _ in range(beep.cnt):
                        buzzer.on(beep.freq)
                        sleep_ms(beep.duration)
                        buzzer.off()
                        await asleep_ms(beep.gap)

            event.clear()


__all__ = ("Beeper",)
