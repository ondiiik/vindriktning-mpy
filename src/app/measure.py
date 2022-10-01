# MIT license; Copyright (c) 2022 Ondrej Sienczak

from com.logging import Logger
from micropython import const
from uasyncio import sleep, Event
import config.measure as config


log = Logger(__name__)


class Measure:
    def __init__(self, app):
        self.app = app
        self.dust_ugpm3 = None
        self.co2_ppm = None
        self.temperature_dgc = None
        self.humidity_pc = None
        self.temperature_method = 'SDC41' if app.vindriktning.temperature_sdc41 else 'DHT'
        self.light_pc = 100
        self.light_method = 'ADC'
        self._new_data = Event()

    async def light_task(self):
        vindriktning = self.app.vindriktning

        while True:
            self.light_pc = min(vindriktning.light * 0.392156863, 100)
            self.light_method = 'ADC' if vindriktning.light_adc else 'IO'
            await sleep(2)

    async def co2_task(self):
        vindriktning = self.app.vindriktning
        pm = self.app.pm

        while True:
            with pm.disabled:
                await vindriktning.data_refresh()

            self.co2_ppm = vindriktning.co2_ppm
            self.temperature_dgc = vindriktning.temperature_dgc
            self.humidity_pc = vindriktning.humidity_pc
            self._new_data.set()

            await sleep(config.period)

    async def dust_task(self):
        vindriktning = self.app.vindriktning
        vindriktning.fan.on()
        await sleep(2)

        while True:
            if config.dust_in_night or vindriktning.light:
                with self.app.pm.disabled:
                    vindriktning.fan.on()
                    await self._blink(7)

                    acc = 0
                    avg_cnt = const(4)
                    log.dbg(f'Averaging measured values (measure {avg_cnt} times)')

                    for _ in range(avg_cnt):
                        dust_ugpm3 = vindriktning.dust_ugpm3
                        while 128 < dust_ugpm3:
                            dust_ugpm3 = vindriktning.dust_ugpm3
                        log.dbg('\tSample', dust_ugpm3, 'ug/m3')
                        acc += dust_ugpm3
                        await self._blink(6)

                    vindriktning.fan.off()
                self.dust_ugpm3 = acc / avg_cnt
                self._new_data.set()

                await sleep(config.dust_period)
            else:
                vindriktning.fan.off()
                await sleep(120)

    async def _blink(self, cnt):
        led = self.app.led

        for _ in range(cnt):
            led[1] = led.BLACK
            await sleep(1)
            led[1] = (led[0] + led[2]) // 2
            await sleep(1)
