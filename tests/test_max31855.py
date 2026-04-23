"""Tests for the MAX31855 thermocouple SPI driver.

Mocks the SPI bus to verify bit-parsing logic with known raw bytes.
"""

import sys
from types import ModuleType
from unittest.mock import MagicMock

import pytest

# Provide a mock spidev module before importing the driver
_spidev_mock = ModuleType("spidev")


class _MockSpiDev:
    def __init__(self):
        self.max_speed_hz = 0
        self._data = [0x00, 0x00, 0x00, 0x00]

    def open(self, bus, device):
        pass

    def xfer2(self, data):
        return list(self._data)

    def close(self):
        pass


_spidev_mock.SpiDev = _MockSpiDev
sys.modules["spidev"] = _spidev_mock

from ceramique.sensors.max31855 import MAX31855  # noqa: E402


class TestMAX31855:
    """Verify raw-byte parsing for the MAX31855 thermocouple converter."""

    def _make_sensor(self, raw_bytes: list[int]) -> MAX31855:
        """Create a MAX31855 that returns fixed raw bytes."""
        sensor = MAX31855()
        sensor._spi._data = raw_bytes
        return sensor

    def test_positive_temperature(self):
        """25.0 °C → raw 14-bit value = 100 (0x0064), shifted left by 18."""
        # 25.0 °C = 100 * 0.25
        # 14-bit value: 0b00000001100100 = 100
        # In 32-bit frame: 100 << 18 = 0x01900000
        raw = 0x01900000
        raw_bytes = [
            (raw >> 24) & 0xFF,
            (raw >> 16) & 0xFF,
            (raw >> 8) & 0xFF,
            raw & 0xFF,
        ]
        sensor = self._make_sensor(raw_bytes)
        assert sensor.temperature == 25.0

    def test_high_temperature(self):
        """850.0 °C → raw 14-bit value = 3400."""
        # 850.0 °C = 3400 * 0.25
        raw_14bit = 3400  # 0x0D48
        raw = raw_14bit << 18
        raw_bytes = [
            (raw >> 24) & 0xFF,
            (raw >> 16) & 0xFF,
            (raw >> 8) & 0xFF,
            raw & 0xFF,
        ]
        sensor = self._make_sensor(raw_bytes)
        assert sensor.temperature == 850.0

    def test_negative_temperature(self):
        """-1.0 °C → raw 14-bit value = 0x3FFC (two's complement of -4)."""
        # -1.0 °C = -4 * 0.25
        # 14-bit two's complement of -4: 0x3FFC
        raw_14bit = 0x3FFC
        raw = raw_14bit << 18
        raw_bytes = [
            (raw >> 24) & 0xFF,
            (raw >> 16) & 0xFF,
            (raw >> 8) & 0xFF,
            raw & 0xFF,
        ]
        sensor = self._make_sensor(raw_bytes)
        assert sensor.temperature == -1.0

    def test_fault_returns_last_valid(self):
        """When fault bits are set, the last valid reading is returned."""
        # First, get a valid reading
        raw_14bit = 400  # 100.0 °C
        raw = raw_14bit << 18
        raw_bytes = [
            (raw >> 24) & 0xFF,
            (raw >> 16) & 0xFF,
            (raw >> 8) & 0xFF,
            raw & 0xFF,
        ]
        sensor = self._make_sensor(raw_bytes)
        assert sensor.temperature == 100.0

        # Now simulate an open-circuit fault (bit 0 set)
        sensor._spi._data = [0x00, 0x00, 0x00, 0x01]
        assert sensor.temperature == 100.0  # returns last valid

    def test_fault_with_no_prior_reading(self):
        """Fault on first read returns None (no prior valid reading)."""
        sensor = self._make_sensor([0x00, 0x00, 0x00, 0x01])
        assert sensor.temperature is None

    def test_cold_junction(self):
        """Verify cold-junction temperature parsing from bits [15:4]."""
        # 25.0 °C cold junction = 400 * 0.0625
        cj_raw = 400  # 12-bit value
        raw = cj_raw << 4  # shift into bits [15:4]
        raw_bytes = [0x00, 0x00, (raw >> 8) & 0xFF, raw & 0xFF]
        sensor = self._make_sensor(raw_bytes)
        assert sensor.cold_junction == 25.0

    def test_fault_detection(self):
        """Verify human-readable fault messages."""
        sensor = self._make_sensor([0x00, 0x00, 0x00, 0x01])
        assert sensor.fault == "Thermocouple not connected (open circuit)"

        sensor._spi._data = [0x00, 0x00, 0x00, 0x02]
        assert sensor.fault == "Thermocouple shorted to GND"

        sensor._spi._data = [0x00, 0x00, 0x00, 0x00]
        assert sensor.fault is None

    def test_calibration_corrections(self):
        """Corrections are applied at the highest matching threshold."""
        sensor = self._make_sensor([0x00, 0x00, 0x00, 0x00])
        sensor._corrections = {300: 10.0, 500: 20.0}

        # 400 °C → correction for threshold 300 = +10
        raw_14bit = 1600  # 400.0 °C
        raw = raw_14bit << 18
        sensor._spi._data = [
            (raw >> 24) & 0xFF,
            (raw >> 16) & 0xFF,
            (raw >> 8) & 0xFF,
            raw & 0xFF,
        ]
        assert sensor.temperature == 410.0

        # 600 °C → correction for threshold 500 = +20
        raw_14bit = 2400  # 600.0 °C
        raw = raw_14bit << 18
        sensor._spi._data = [
            (raw >> 24) & 0xFF,
            (raw >> 16) & 0xFF,
            (raw >> 8) & 0xFF,
            raw & 0xFF,
        ]
        assert sensor.temperature == 620.0
