"""Mock HX711 driver for development on non-RPi platforms.

Returns random values centered around the 24-bit midpoint to simulate
a load cell with realistic noise characteristics.
"""

import random
import time
from typing import Optional


class HX711:
    """Drop-in HX711 stub with simulated noise and calibration support."""

    GAIN_PULSES = {128: 1, 64: 3, 32: 2}
    _BASE_VALUE = 8_388_608  # 24-bit midpoint

    def __init__(self, dout_pin: int, pd_sck_pin: int, gain: int = 128):
        if gain not in self.GAIN_PULSES:
            raise ValueError(f"Gain must be 128, 64, or 32 — got {gain}")

        self._gain = gain
        self._offset: float = 0.0
        self._scale: float = 1.0
        self._ready = True

    def reset(self) -> None:
        self._ready = True

    def _wait_ready(self, timeout: float = 1.0) -> bool:
        time.sleep(0.001)
        return self._ready

    def read_raw(self) -> Optional[int]:
        if not self._ready:
            return None
        return self._BASE_VALUE + random.randint(-1000, 1000)

    @property
    def value(self) -> Optional[float]:
        raw = self.read_raw()
        return None if raw is None else raw - self._offset

    @property
    def weight(self) -> Optional[float]:
        val = self.value
        return None if val is None else val / self._scale

    def tare(self, samples: int = 10) -> bool:
        readings = [self.read_raw() for _ in range(samples)]
        if None in readings:
            return False
        self._offset = sum(readings) / len(readings)
        return True

    def calibrate(self, known_weight: float, samples: int = 10) -> bool:
        values = [self.value for _ in range(samples)]
        if None in values:
            return False
        avg = sum(values) / len(values)
        if avg == 0:
            return False
        self._scale = avg / known_weight
        return True

    def power_down(self) -> None:
        self._ready = False

    def power_up(self) -> None:
        self._ready = True

    def close(self) -> None:
        pass
