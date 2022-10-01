# MIT license; Copyright (c) 2022 Ondrej Sienczak

from app.plugins import Plugin
from com.logging import Logger
from machine import unique_id
from uasyncio import sleep
from ubinascii import hexlify
from ujson import dumps
from umqtt.simple import MQTTClient
import config.plugins.sensor_to_mqtt as config


log = Logger(__name__)


class Sensor2Mqtt(Plugin):
    async def task(self):
        log.dbg('')
        log.dbg('When you want to see you sensors in Home Assistant, please add following to configuration.yaml')
        log.dbg('')
        log.dbg('mqtt:')
        log.dbg('  sensor:')
        log.dbg('    - name: "My own CO2 sensor name (please fill in)"')
        log.dbg(f'      unique_id: "{config.topic.replace("/","_")}_co2"')
        log.dbg('      icon: "mdi:molecule-co2"')
        log.dbg(f'      state_topic: "{config.topic}"')
        log.dbg('      unit_of_measurement: "ppm"')
        log.dbg('      value_template: "{{ value_json.co2 }}"')
        log.dbg('    - name: "My own dust sensor name (please fill in)"')
        log.dbg(f'      unique_id: "{config.topic.replace("/","_")}_dust"')
        log.dbg('      icon: "mdi:weather-dust"')
        log.dbg(f'      state_topic: "{config.topic}"')
        log.dbg('      unit_of_measurement: "ug/m3"')
        log.dbg('      value_template: "{{ value_json.dust }}"')
        log.dbg('    - name: "My own temperature sensor name (please fill in)"')
        log.dbg(f'      unique_id: "{config.topic.replace("/","_")}_temp"')
        log.dbg('      icon: "mdi:thermometer"')
        log.dbg(f'      state_topic: "{config.topic}"')
        log.dbg('      unit_of_measurement: "°C"')
        log.dbg('      value_template: "{{ value_json.temp }}"')
        log.dbg('    - name: "My own temperature sensor name (please fill in)"')
        log.dbg(f'      unique_id: "{config.topic.replace("/","_")}_humi"')
        log.dbg('      icon: "mdi:water-percent"')
        log.dbg(f'      state_topic: "{config.topic}"')
        log.dbg('      unit_of_measurement: "%"')
        log.dbg('      value_template: "{{ value_json.humi }}"')
        log.dbg('    - name: "My own light sensor name (please fill in)"')
        log.dbg(f'      unique_id: "{config.topic.replace("/","_")}_light"')
        log.dbg('      icon: "mdi:theme-light-dark"')
        log.dbg(f'      state_topic: "{config.topic}"')
        log.dbg('      unit_of_measurement: "%"')
        log.dbg('      value_template: "{{ value_json.light }}"')
        log.dbg('')

        version = str(self.app.version)
        measure = self.app.measure
        mqtt = MQTTClient(hexlify(unique_id()),
                          config.server,
                          port=config.port,
                          user=config.user,
                          password=config.password,
                          ssl=config.ssl)

        while True:
            await self.event.wait()
            self.event.clear()

            try:
                async with self.app.wifi:
                    log.dbg('Connecting ...')
                    mqtt.connect()
                    log.msg('Connected')

                    msg = dumps({'version': version,
                                 'co2': measure.co2_ppm,
                                 'dust': measure.dust_ugpm3,
                                 'temp': measure.temperature_dgc,
                                 'temp_method': measure.temperature_method,
                                 'humi': measure.humidity_pc,
                                 'light': measure.light_pc,
                                 'light_method': measure.light_method})
                    log.dbg('Publish', msg)
                    mqtt.publish(config.topic, msg)
                    mqtt.disconnect()

                await sleep(config.period)

            except OSError as e:
                log.err('MQTT connection reported', e)
                log.dbg('Retry in', config.retry_time, 'seconds')
                await sleep(config.retry_time)
