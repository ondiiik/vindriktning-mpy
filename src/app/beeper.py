# MIT license; Copyright (c) 2022 Ondrej Sienczak

from uasyncio import sleep_ms, Event
from collections import deque


class Beeper:
    def __init__(self, app):
        self.app = app
        self.beeps = deque(tuple(), 16)
        self.event = Event()

    def beep(self, duration, gap, cnt=1):
        self.beeps.append((duration, gap, cnt))
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
                    for _ in range(beep[2]):
                        buzzer.on()
                        await sleep_ms(beep[0])
                        buzzer.off()
                        await sleep_ms(beep[1])

            event.clear()
