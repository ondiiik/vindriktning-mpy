# MIT license; Copyright (c) 2022 Ondrej Sienczak

from .scd4x import SCD4X
from com.color import Rgb
from com.logging import Logger
from dht import DHT22
from machine import Pin, PWM, UART, I2C, ADC, deepsleep
from micropython import const
from neopixel import NeoPixel
from uasyncio import sleep_ms
import config.measure as config


log = Logger(__name__)


# Following code is required in order to do early handshake with PM1006 sensor
_cmd = b'\x11\x02\x0B\x01\xE1'
_uart = UART(2, baudrate=9600)
_uart.read()
_uart.write(_cmd)

_LIGHTS_HIGH = const(3000)
_LIGHTS_REST = const(4095 - _LIGHTS_HIGH)


class Buzzer:
    def __init__(self):
        self._pin = Pin(13, Pin.OUT)
        self._pin.off()

    def on(self, freq):
        self._pwm = PWM(self._pin, freq=freq, duty=512)

    def off(self):
        self._pwm.deinit()
        self._pin.off()


class Vindriktning:
    class Led(NeoPixel):
        def __init__(self):
            super().__init__(Pin(25, Pin.OUT), 3)
            for i in range(3):
                self[i] = b'\x00\x00\x00'
            self.write()

    def __init__(self):
        self.led = self.Led()
        self.fan = Pin(12, Pin.OUT)
        self.buzzer = Buzzer()
        self._sdc41 = SCD4X(I2C(0, scl=Pin(22), sda=Pin(21), freq=400000))
        self._dht = DHT22(Pin(5))
        self._uart = _uart
        self._dcmd = _cmd
        self._buff = bytearray(20)
        self._light_restore = 0
        self._sdc41.start_periodic_measurement()

        try:
            self._light = ADC(Pin(4), atten=ADC.ATTN_11DB)
        except ValueError:
            log.msg('ADC occupied by WiFi - rebooting')
            deepsleep(1)

        try:
            self._dht.measure()
            self._dht.temperature()
            self._dht.humidity()
        except OSError:
            self._dht = None

    async def data_refresh(self):
        while not self._sdc41.data_ready:
            await sleep_ms(250)

        self.co2_ppm = self._sdc41.co2_ppm

        if self._dht is None:
            self.temperature_dgc = round(self._sdc41.temperature + config.csd41_temp_shift, 2)
            humidity_pc = round(self._sdc41.relative_humidity + config.scd41_humi_shift, 2)
        else:
            self._dht.measure()
            self.temperature_dgc = self._dht.temperature() + config.dht22_temp_shift
            humidity_pc = self._dht.humidity() + config.dht22_humi_shift

        self.humidity_pc = min(max(humidity_pc, 0), 100)

    @property
    def dust_ugpm3(self):
        rx = self._buff

        while True:
            self._uart.write(self._dcmd)
            self._uart.readinto(rx)

            data = bytes(rx)
            if data.startswith(b'\x16\x11\x0B'):
                return data[5] * 256 + data[6]

    @property
    def temperature_sdc41(self):
        return self._dht is None

    @property
    def light(self):
        if self.light_adc:
            try:
                self._light_restore = (_LIGHTS_REST - max(self._light.read() - _LIGHTS_HIGH, 0)) * 255 // _LIGHTS_REST
                return self._light_restore
            except OSError:
                if config.light_restore:
                    return self._light_restore
                else:
                    log.wrn('Reconfiguring light sensor to be used with WiFi')
                    self._light = Pin(4, Pin.IN)
                    return self.light
        else:
            return 0 if self._light.value() else 255

    @property
    def light_adc(self):
        return isinstance(self._light, ADC)

    def light_reinit(self):
        self._light = ADC(Pin(4), atten=ADC.ATTN_11DB)
