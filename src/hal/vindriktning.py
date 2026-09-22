# MIT license; Copyright (c) 2022 Ondrej Sienczak
from __future__ import annotations

from .scd4x import SCD4X
from .sht4x import SHT4X

from com.logging import Logger
from config import Cfg

from asyncio import sleep_ms
from dht import DHT22
from machine import ADC, PWM, Pin, SoftI2C, UART, deepsleep
from micropython import const
from neopixel import NeoPixel


log = Logger(__name__)
class config:
    hardware = Cfg(
        "hardware",
        {
            "buzzer": {
                "pin": 13,
                "inverted": False,
                "active": False,
            },
            "led": {
                "pin": 25,
            },
            "fan": {
                "pin": 12,
            },
            "light": {
                "pin": 4,
            },
            "dht22": {
                "pin": 5,
            },
            "i2c": {
                "sda": 21,
                "scl": 22,
            },
        }
    )
    measure = Cfg(
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
                "temp_shift": -1.67,
                "humi_shift": -10,
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

_LIGHTS_HIGH = const(48011)
_LIGHTS_REST = const(65535 - _LIGHTS_HIGH)


class Buzzer:
    def __init__(self) -> None:
        self._pin = Pin(config.hardware["buzzer"]["pin"], Pin.OUT)
        self._p0 = config.hardware["buzzer"]["inverted"]
        self._pin.value(self._p0)
        if config.hardware["buzzer"]["active"]:
            self.on = self._on_pin
            self.off = self._off_pin
        else:
            self.on = self._on_pwm
            self.off = self._off_pwm

    def _on_pwm(self, freq) -> None:
        self._pwm = PWM(self._pin, freq=freq, duty=512)

    def _off_pwm(self) -> None:
        self._pwm.deinit()
        self._pin.value(self._p0)

    def _on_pin(self, freq) -> None:
        self._pin.value(not self._p0)

    def _off_pin(self) -> None:
        self._pin.value(self._p0)


class Vindriktning:
    class Led(NeoPixel):
        def __init__(self) -> None:
            super().__init__(Pin(config.hardware["led"]["pin"], Pin.OUT), 3)
            for i in range(3):
                self[i] = b"\x00\x00\x00"
            self.write()

    def __init__(self) -> None:
        self.led = self.Led()
        self.fan = Pin(config.hardware["fan"]["pin"], Pin.OUT)
        self.buzzer = Buzzer()
        self._i2c = SoftI2C(
            scl=Pin(config.hardware["i2c"]["scl"]), sda=Pin(config.hardware["i2c"]["sda"]), freq=400000
        )  # SHT40 does not work with HW I2C
        self._sdc41 = SCD4X(self._i2c)
        self._sht40 = SHT4X(self._i2c)
        self._dht = DHT22(Pin(config.hardware["dht22"]["pin"]))
        self._uart = _uart
        self._dcmd = _cmd
        self._buff = bytearray(20)
        self._light_restore = 0
        self._sdc41.start_periodic_measurement()

        try:
            self._light = ADC(Pin(config.hardware["light"]["pin"]), atten=ADC.ATTN_11DB)
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

    async def data_refresh(self) -> None:
        while not self._sdc41.data_ready:
            await sleep_ms(250)

        temperature_dgc, humidity_pc, self.co2_ppm = self._sdc41.measure()

        if self._sht40 is not None:
            temperature_dgc, humidity_pc = self._sht40.measure()
            temperature_dgc += config.measure.sht40["temp_shift"]
            humidity_pc += config.measure.sht40["humi_shift"]
        elif self._dht is not None:
            self._dht.measure()
            temperature_dgc = self._dht.temperature() + config.measure.dht22["temp_shift"]
            humidity_pc = self._dht.humidity() + config.measure.dht22["humi_shift"]
        else:
            temperature_dgc += config.measure.scd41["temp_shift"]
            humidity_pc += config.measure.scd41["humi_shift"]

        self.temperature_dgc = round(temperature_dgc, 2)
        self.humidity_pc = round(min(max(humidity_pc, 0), 100), 2)

    @property
    def dust_ugpm3(self) -> int:
        rx = self._buff

        while True:
            self._uart.write(self._dcmd)
            self._uart.readinto(rx)

            data = bytes(rx)
            if data.startswith(b"\x16\x11\x0B"):
                return data[5] * 256 + data[6]

    @property
    def temperature_sdc41(self) -> bool:
        return self._dht is None

    @property
    def light(self) -> int:
        if self.light_adc:
            try:
                adc = self._light.read_u16()
                if adc != 0:
                    self._light_restore = (
                        (_LIGHTS_REST - max(adc - _LIGHTS_HIGH, 0))
                        * 255
                        // _LIGHTS_REST
                    )
                return self._light_restore
            except OSError:
                if config.measure.light_restore:
                    return self._light_restore
                else:
                    log.wrn("Reconfiguring light sensor to be used with WiFi")
                    self._light = Pin(config.hardware["light"]["pin"], Pin.IN)
                    return self.light
        else:
            return 0 if self._light.value() else 255

    @property
    def light_adc(self) -> bool:
        return isinstance(self._light, ADC)

    def light_reinit(self) -> None:
        self._light = ADC(Pin(config.hardware["light"]["pin"]), atten=ADC.ATTN_11DB)


__all__ = (
    "Buzzer",
    "Vindriktning",
    "config",
    "log",
)
