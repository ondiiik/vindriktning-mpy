# MIT license; Copyright (c) 2022 Ondrej Sienczak

from .plugins import Plugin
from com.logging import Logger
from gc import collect
from os import ilistdir
from uasyncio import create_task


log = Logger(__name__)


class Dispatcher:
    def __init__(self, app):
        self.app = app
        self.plugins = dict()

        for file in ilistdir('/plugins'):
            name = file[0].split('.')[0]

            if name.startswith('_'):
                continue

            try:
                config = getattr(getattr(__import__(f'config.plugins.{name}'), 'plugins'), name)
            except AttributeError:
                log.dbg('Skipped plugin', name, '(missing config)')
                continue

            try:
                if not config.enabled:
                    log.dbg('Skipped plugin', name, '(disabled)')
                    continue
            except AttributeError:
                log.dbg('Skipped plugin', name, '(default)')
                continue

            module = getattr(__import__(f'plugins.{name}'), name)

            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                try:
                    if Plugin in attr.__bases__:
                        log.msg('Using plugin', name, attr)
                        self.plugins[name] = attr(app)
                except AttributeError:
                    pass

    async def dispatch_task(self):
        plugins = self.plugins.values()

        if plugins:
            for plugin in plugins:
                create_task(plugin.task())

            measure = self.app.measure

            while True:
                await measure._new_data.wait()
                measure._new_data.clear()

                log.dbg('+-------------------------------------------------------')
                log.dbg('| CO2         -', measure.co2_ppm, 'ppm')
                log.dbg('| Dust        -', measure.dust_ugpm3, 'ug/m3')
                log.dbg('| Temperature -', measure.temperature_dgc, '°C', measure.temperature_method)
                log.dbg('| Humidity    -', measure.humidity_pc, '%')
                log.dbg('| Light       -', measure.light_pc, '%', measure.light_method)
                log.dbg('+-------------------------------------------------------')

                for plugin in plugins:
                    plugin.event.set()

                collect()
