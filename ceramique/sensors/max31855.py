"""MAX31855 thermocouple-to-digital converter SPI driver.

Reads 14-bit thermocouple temperature (0.25 °C resolution) and
12-bit cold-junction reference temperature (0.0625 °C resolution).
Detects open-circuit, short-to-VCC, and short-to-GND faults.

Datasheet: https://datasheets.maximintegrated.com/en/ds/MAX31855.pdf
"""

from typing import Dict, Optional

import spidev


class MAX31855:
    """SPI driver for the MAX31855 thermocouple-to-digital converter."""

    FAULT_OPEN_CIRCUIT = 0x01
    FAULT_SHORT_TO_GND = 0x02
    FAULT_SHORT_TO_VCC = 0x04

    FAULT_MESSAGES: Dict[int, str] = {
        FAULT_OPEN_CIRCUIT: "Thermocouple not connected (open circuit)",
        FAULT_SHORT_TO_GND: "Thermocouple shorted to GND",
        FAULT_SHORT_TO_VCC: "Thermocouple shorted to VCC",
    }

    def __init__(
        self,
        bus: int = 0,
        device: int = 1,
        speed_hz: int = 5_000_000,
        corrections: Optional[Dict[int, float]] = None,
    ):
        """Initialize the MAX31855 on the given SPI bus.

        Args:
            bus: SPI bus number (typically 0 on Raspberry Pi).
            device: SPI chip-select line (CE0=0, CE1=1).
            speed_hz: SPI clock frequency. MAX31855 supports up to 5 MHz.
            corrections: Temperature correction offsets keyed by threshold
                in °C.  The highest threshold below the reading is applied.
        """
        self._corrections = corrections or {}
        self._last_valid: Optional[float] = None

        self._spi = spidev.SpiDev()
        self._spi.open(bus, device)
        self._spi.max_speed_hz = speed_hz

    def _read_raw(self) -> int:
        """Read 32 raw bits from the MAX31855."""
        raw = self._spi.xfer2([0x00, 0x00, 0x00, 0x00])
        return (raw[0] << 24) | (raw[1] << 16) | (raw[2] << 8) | raw[3]

    @property
    def temperature(self) -> Optional[float]:
        """Thermocouple temperature in °C.

        Returns the last valid reading when a fault is detected, or
        *None* if no valid reading has ever been obtained.
        """
        raw = self._read_raw()

        if raw & 0x07:  # fault bits D0–D2
            return self._last_valid

        # Bits [31:18] — 14-bit signed thermocouple value
        tc_raw = (raw >> 18) & 0x3FFF
        if tc_raw & 0x2000:
            tc_raw -= 0x4000

        temp = tc_raw * 0.25

        for threshold in sorted(self._corrections, reverse=True):
            if temp > threshold:
                temp += self._corrections[threshold]
                break

        self._last_valid = temp
        return temp

    @property
    def cold_junction(self) -> float:
        """Internal cold-junction (reference) temperature in °C."""
        raw = self._read_raw()

        # Bits [15:4] — 12-bit signed cold-junction value
        cj_raw = (raw >> 4) & 0x0FFF
        if cj_raw & 0x0800:
            cj_raw -= 0x1000

        return cj_raw * 0.0625

    @property
    def fault(self) -> Optional[str]:
        """Human-readable fault description, or *None* if healthy."""
        raw = self._read_raw()
        fault_bits = raw & 0x07
        return self.FAULT_MESSAGES.get(fault_bits)

    def close(self) -> None:
        """Release the SPI device."""
        self._spi.close()
