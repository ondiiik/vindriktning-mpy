# MIT license; Copyright (c) 2022 Ondrej Sienczak
from __future__ import annotations

from app.plugins import Plugin
from com.logging import Logger

from machine import unique_id
from uasyncio import sleep
from ubinascii import hexlify
from ujson import dumps
from umqtt.simple import MQTTClient


log = Logger(__name__)


class Sensor2Mqtt(Plugin):
    def __init__(self, app: "App") -> None:
        super().__init__(
            app,
            __name__,
            {
                "server": {
                    "value": "Please fill in",
                    "description": "IP address of MQTT broker",
                },
                "port": {
                    "value": 8883,
                    "description": "Port where MQTT broker is listening",
                },
                "user": {
                    "value": "Please fill in",
                    "description": "User-name to login to MQTT broker",
                },
                "password": {
                    "value": "Please fill in",
                    "description": "Password to login to MQTT broker",
                },
                "ssl": {
                    "value": True,
                    "description": "Say if SSL/TLS encryption will be used to communicate with MQTT broker",
                },
                "topic": {
                    "value": f"vindriktning/sensor_{hexlify(unique_id()).decode()}",
                    "description": "Period how often the data shall be refreshed on MQTT",
                },
                "period": {
                    "value": 180,
                    "description": "Topic to be used to present sensor on MQTT",
                },
                "retry_time": {
                    "value": 60,
                    "description": "Time after which system retry to connect to MQTT in the case of failure",
                },
            },
        )

    async def task(self):
        log.dbg("")
        log.dbg(
            "When you want to see you sensors in Home Assistant, please add following to configuration.yaml"
        )
        log.dbg("")
        log.dbg("mqtt:")
        log.dbg("  sensor:")
        log.dbg('    - name: "My own CO2 sensor name (please fill in)"')
        log.dbg(f'      unique_id: "{self.cfg.topic.replace("/","_")}_co2"')
        log.dbg('      icon: "mdi:molecule-co2"')
        log.dbg(f'      state_topic: "{self.cfg.topic}"')
        log.dbg('      unit_of_measurement: "ppm"')
        log.dbg('      value_template: "{{ value_json.co2 }}"')
        log.dbg('    - name: "My own dust sensor name (please fill in)"')
        log.dbg(f'      unique_id: "{self.cfg.topic.replace("/","_")}_dust"')
        log.dbg('      icon: "mdi:weather-dust"')
        log.dbg(f'      state_topic: "{self.cfg.topic}"')
        log.dbg('      unit_of_measurement: "ug/m3"')
        log.dbg('      value_template: "{{ value_json.dust }}"')
        log.dbg('    - name: "My own temperature sensor name (please fill in)"')
        log.dbg(f'      unique_id: "{self.cfg.topic.replace("/","_")}_temp"')
        log.dbg('      icon: "mdi:thermometer"')
        log.dbg(f'      state_topic: "{self.cfg.topic}"')
        log.dbg('      unit_of_measurement: "°C"')
        log.dbg('      value_template: "{{ value_json.temp }}"')
        log.dbg('    - name: "My own temperature sensor name (please fill in)"')
        log.dbg(f'      unique_id: "{self.cfg.topic.replace("/","_")}_humi"')
        log.dbg('      icon: "mdi:water-percent"')
        log.dbg(f'      state_topic: "{self.cfg.topic}"')
        log.dbg('      unit_of_measurement: "%"')
        log.dbg('      value_template: "{{ value_json.humi }}"')
        log.dbg('    - name: "My own light sensor name (please fill in)"')
        log.dbg(f'      unique_id: "{self.cfg.topic.replace("/","_")}_light"')
        log.dbg('      icon: "mdi:theme-light-dark"')
        log.dbg(f'      state_topic: "{self.cfg.topic}"')
        log.dbg('      unit_of_measurement: "%"')
        log.dbg('      value_template: "{{ value_json.light }}"')
        log.dbg("")

        version = str(self.app.version)
        measure = self.app.measure
        mqtt = MQTTClient(
            hexlify(unique_id()),
            self.cfg.server,
            port=self.cfg.port,
            user=self.cfg.user,
            password=self.cfg.password,
            ssl=self.cfg.ssl,
        )

        while True:
            await self.event.wait()
            self.event.clear()

            try:
                async with self.app.wifi:
                    log.dbg("Connecting ...")
                    mqtt.connect()
                    log.msg("Connected")

                    msg = dumps(
                        {
                            "version": version,
                            "co2": measure.co2_ppm,
                            "dust": measure.dust_ugpm3,
                            "temp": measure.temperature_dgc,
                            "sensors": measure.sensors,
                            "humi": measure.humidity_pc,
                            "light": measure.light_pc,
                            "light_method": measure.light_method,
                        }
                    )
                    log.dbg("Publish", msg)
                    mqtt.publish(self.cfg.topic, msg, retain=True)
                    mqtt.disconnect()

                await sleep(self.cfg.period)

            except OSError as e:
                log.err("MQTT connection reported", e)
                log.dbg("Retry in", self.cfg.retry_time, "seconds")
                await sleep(self.cfg.retry_time)


__all__ = (
    "Sensor2Mqtt",
    "log",
)
