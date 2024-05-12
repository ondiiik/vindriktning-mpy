# MIT license; Copyright (c) 2022 Ondrej Sienczak
from __future__ import annotations

from .plugins import Plugin, co2_alert, sensor_to_led, sensor_to_mqtt

from com.logging import Logger
from gc import collect
from os import ilistdir, mkdir
from uasyncio import create_task


log = Logger(__name__)


class Dispatcher:
    def __init__(self, app) -> None:
        self.app = app
        self.plugins = dict()

        # Create list of built-in plugins
        plugins = [co2_alert, sensor_to_led, sensor_to_mqtt]

        # Append also plugins from plugins folder
        plugins += [
            getattr(
                __import__(f"plugins.{file[0].split('.')[0]}"), file[0].split(".")[0]
            )
            for file in ilistdir("/plugins")
        ]

        # Iterate through all plugins
        for module in plugins:
            name = module.__name__.split(".")[-1]
            for attr_name in dir(module):
                plugin = getattr(module, attr_name)
                try:
                    if Plugin in plugin.__bases__:
                        p = plugin(app)
                        if p.cfg.enabled:
                            self.plugins[name] = p
                            log.msg("Using plugin", name)
                        else:
                            log.dbg("Skipped plugin", name)
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

                log.dbg("+-------------------------------------------------------")
                log.dbg("| CO2         -", measure.co2_ppm, "ppm")
                log.dbg("| Dust        -", measure.dust_ugpm3, "ug/m3")
                log.dbg(
                    "| Temperature -",
                    measure.temperature_dgc,
                    "°C",
                    measure.sensors,
                )
                log.dbg("| Humidity    -", measure.humidity_pc, "%")
                log.dbg("| Light       -", measure.light_pc, "%", measure.light_method)
                log.dbg("+-------------------------------------------------------")

                for plugin in plugins:
                    plugin.event.set()

                collect()


try:
    mkdir("plugins")
except:
    ...


__all__ = (
    "Dispatcher",
    "log",
)
