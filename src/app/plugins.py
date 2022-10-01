# MIT license; Copyright (c) 2022 Ondrej Sienczak

from uasyncio import Event


class Plugin:
    def __init__(self, app):
        self.event = Event()
        self.app = app

    async def task(self):
        while True:
            await self.event.wait()
            self.event.clear()
            await self.cycle()

    async def cycle(self):
        raise NotImplementedError('Missing plugin body')
