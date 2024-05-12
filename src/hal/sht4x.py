# SPDX-FileCopyrightText: Copyright (c) 2023 Jose D. Montoya
#
# SPDX-License-Identifier: MIT
#
# Modified by Ondrej Sienczak
from __future__ import annotations

from micropython import const
import struct
import time


_RESET = const(0x94)

HIGH_PRECISION = const(0xFD)
MEDIUM_PRECISION = const(0xF6)
LOW_PRECISION = const(0xE0)
_p2s = {
    HIGH_PRECISION: "HIGH_PRECISION",
    MEDIUM_PRECISION: "MEDIUM_PRECISION",
    LOW_PRECISION: "LOW_PRECISION",
}

HEATER_200mW = b"\0x39\0x32"
HEATER_110mW = b"\0x2F\0x24"
HEATER_20mW = b"\0x1E\0x15"
_h2s = {
    HEATER_200mW: "HEATER_200mW",
    HEATER_110mW: "HEATER_110mW",
    HEATER_20mW: "HEATER_20mW",
}

TEMP_1 = const(0)
TEMP_0_1 = const(1)
_t2s = {
    TEMP_1: "TEMP_1",
    TEMP_0_1: "TEMP_0_1",
}


class SHT4X:
    def __init__(self, i2c, address: int = 0x44) -> None:
        self._i2c = i2c
        self._addr = address
        self._data = bytearray(6)

        self._command = 0xFD
        self._temperature_precision = HIGH_PRECISION
        self._heater_power = HEATER_20mW
        self._heat_time = TEMP_0_1

    @property
    def temperature_precision(self) -> str:
        return _p2s[self._temperature_precision]

    @temperature_precision.setter
    def temperature_precision(self, value: int) -> None:
        if value not in _p2s.keys():
            raise ValueError("Invalid value")
        self._temperature_precision = self._command = value

    def measure(self) -> tuple[float, float]:  # Temperature, Humidity
        self._i2c.writeto(self._addr, bytes([self._command]), False)
        if self._command in (0x39, 0x2F, 0x1E):
            time.sleep(1.2)
        elif self._command in (0x32, 0x24, 0x15):
            time.sleep(0.2)
        time.sleep(0.2)
        self._i2c.readfrom_into(self._addr, self._data)

        temperature, temp_crc, humidity, humidity_crc = struct.unpack_from(
            ">HBHB", self._data
        )

        if temp_crc != self._crc(
            memoryview(self._data[0:2])
        ) or humidity_crc != self._crc(memoryview(self._data[3:5])):
            raise RuntimeError("Invalid CRC calculated")

        temperature = -45.0 + 175.0 * temperature / 65535.0

        humidity = -6.0 + 125.0 * humidity / 65535.0
        humidity = max(min(humidity, 100), 0)

        return temperature, min(max(humidity, 0), 100)

    @property
    def heater_power(self) -> str:
        return _h2s[self._heater_power]

    @heater_power.setter
    def heater_power(self, value: bytes) -> None:
        if value not in _h2s.keys():
            raise ValueError("Invalid value")
        self._heater_power = value
        self._command = value[self._heat_time]

    @property
    def heat_time(self) -> str:
        return _t2s[self._heat_time]

    @heat_time.setter
    def heat_time(self, value: int) -> None:
        if value not in _t2s.keys():
            raise ValueError("Invalid value")
        self._heat_time = value
        self._command = self._heater_power[value]

    def reset(self) -> None:
        self._i2c.writeto(self._addr, bytes([_RESET]), False)
        time.sleep(0.1)

    @staticmethod
    def _crc(buffer) -> int:
        crc = 0xFF
        for byte in buffer:
            crc ^= byte
            for _ in range(8):
                if crc & 0x80:
                    crc = (crc << 1) ^ 0x31
                else:
                    crc = crc << 1
        return crc & 0xFF


__all__ = (
    "HEATER_110mW",
    "HEATER_200mW",
    "HEATER_20mW",
    "HIGH_PRECISION",
    "LOW_PRECISION",
    "MEDIUM_PRECISION",
    "SHT4X",
    "TEMP_0_1",
    "TEMP_1",
)
