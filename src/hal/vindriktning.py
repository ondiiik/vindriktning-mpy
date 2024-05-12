# MIT license; Copyright (c) 2022 Ondrej Sienczak
from __future__ import annotations

from .scd4x import SCD4X
from .sht4x import HIGH_PRECISION, SHT4X

from com.color import Rgb
from com.logging import Logger
from config import Cfg

from dht import DHT22
from machine import ADC, PWM, Pin, SoftI2C, UART, deepsleep
from micropython import const
from neopixel import NeoPixel
from uasyncio import sleep_ms


log = Logger(__name__)
config = Cfg(
    "measure",
    {
        "period": {
            "value": {
                "main": 15,
                "dust": 900,
            },
            "description": "Period of measuring of sensors in seconds",
        },
        "dust_in_night": {
            "value": True,
            "description": "Says if dust sensor shall operate in night (in low light conditions)",
        },
        "scd41": {
            "value": {
                "temp_shift": -4,
                "humi_shift": 12.03,
            },
            "description": "Values shift (calibration because of ESP32 heating)",
        },
        "sht40": {
            "value": {
                "temp_shift": 0,
                "humi_shift": 0,
            },
            "description": "Values shift (calibration because of ESP32 heating)",
        },
        "dht22": {
            "value": {
                "temp_shift": -3.18,
                "humi_shift": 8.81,
            },
            "description": "Values shift (calibration because of ESP32 heating)",
        },
        "light_restore": {
            "value": True,
            "description": "Sets light restore mode to be active (useful when WiFi connect to peak strategy is used)",
        },
    },
)


# Following code is required in order to do early handshake with PM1006 sensor
_cmd = b"\x11\x02\x0B\x01\xE1"
_uart = UART(2, baudrate=9600)
_uart.read()
_uart.write(_cmd)

_LIGHTS_HIGH = const(3000)
_LIGHTS_REST = const(4095 - _LIGHTS_HIGH)


class Buzzer:
    def __init__(self) -> None:
        self._pin = Pin(13, Pin.OUT)
        self._pin.off()

    def on(self, freq) -> None:
        self._pwm = PWM(self._pin, freq=freq, duty=512)

    def off(self) -> None:
        self._pwm.deinit()
        self._pin.off()


class Vindriktning:
    class Led(NeoPixel):
        def __init__(self) -> None:
            super().__init__(Pin(25, Pin.OUT), 3)
            for i in range(3):
                self[i] = b"\x00\x00\x00"
            self.write()

    def __init__(self) -> None:
        self.led = self.Led()
        self.fan = Pin(12, Pin.OUT)
        self.buzzer = Buzzer()
        self._i2c = SoftI2C(
            scl=Pin(22), sda=Pin(21), freq=400000
        )  # SHT40 does not work with HW I2C
        self._sdc41 = SCD4X(self._i2c)
        self._sht40 = SHT4X(self._i2c)
        self._dht = DHT22(Pin(5))
        self._uart = _uart
        self._dcmd = _cmd
        self._buff = bytearray(20)
        self._light_restore = 0
        self._sdc41.start_periodic_measurement()

        try:
            self._light = ADC(Pin(4), atten=ADC.ATTN_11DB)
        except ValueError:
            log.msg("ADC occupied by WiFi - rebooting")
            deepsleep(1)

        self.sensors = ("SDC41",)

        try:
            self._dht.measure()
            self._dht.temperature()
            self._dht.humidity()
            self.sensors = "SDC41", "DHT22"
        except Exception:
            log.dbg("DHT22 not found - skipping")
            self._dht = None

        try:
            self._sht40.reset()
            self._sht40.measure()
            self.sensors = "SDC41", "SHT40"
        except Exception:
            log.dbg("SHT40 not found - skipping")
            self._sht40 = None

    async def data_refresh(self):
        while not self._sdc41.data_ready:
            await sleep_ms(250)

        temperature_dgc, humidity_pc, self.co2_ppm = self._sdc41.measure()

        if self._sht40 is not None:
            temperature_dgc, humidity_pc = self._sht40.measure()
            temperature_dgc += config.sht40["temp_shift"]
            humidity_pc += config.sht40["humi_shift"]
        elif self._dht is not None:
            self._dht.measure()
            temperature_dgc = self._dht.temperature() + config.dht22["temp_shift"]
            humidity_pc = self._dht.humidity() + config.dht22["humi_shift"]
        else:
            temperature_dgc += config.scd41["temp_shift"]
            humidity_pc += config.scd41["humi_shift"]

        self.temperature_dgc = round(temperature_dgc, 2)
        self.humidity_pc = round(min(max(humidity_pc, 0), 100), 2)

    @property
    def dust_ugpm3(self) -> None:
        rx = self._buff

        while True:
            self._uart.write(self._dcmd)
            self._uart.readinto(rx)

            data = bytes(rx)
            if data.startswith(b"\x16\x11\x0B"):
                return data[5] * 256 + data[6]

    @property
    def temperature_sdc41(self) -> None:
        return self._dht is None

    @property
    def light(self) -> None:
        if self.light_adc:
            try:
                self._light_restore = (
                    (_LIGHTS_REST - max(self._light.read() - _LIGHTS_HIGH, 0))
                    * 255
                    // _LIGHTS_REST
                )
                return self._light_restore
            except OSError:
                if config.light_restore:
                    return self._light_restore
                else:
                    log.wrn("Reconfiguring light sensor to be used with WiFi")
                    self._light = Pin(4, Pin.IN)
                    return self.light
        else:
            return 0 if self._light.value() else 255

    @property
    def light_adc(self) -> None:
        return isinstance(self._light, ADC)

    def light_reinit(self) -> None:
        self._light = ADC(Pin(4), atten=ADC.ATTN_11DB)


__all__ = (
    "Buzzer",
    "Vindriktning",
    "config",
    "log",
)
