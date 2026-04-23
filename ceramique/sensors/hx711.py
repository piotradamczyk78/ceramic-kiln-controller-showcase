"""HX711 24-bit ADC driver for load cell weight measurement.

Communicates with the HX711 via bit-banged GPIO (no SPI/I2C).
Supports 128×/64× gain on channel A and 32× gain on channel B,
tare zeroing, and weight calibration against a known reference.

Datasheet: https://cdn.sparkfun.com/datasheets/Sensors/ForceFlex/hx711_english.pdf
"""

import time
from typing import Optional

import RPi.GPIO as GPIO


class HX711:
    """Bit-banged GPIO driver for the HX711 load cell ADC."""

    GAIN_PULSES = {128: 1, 64: 3, 32: 2}

    def __init__(self, dout_pin: int, pd_sck_pin: int, gain: int = 128):
        """Initialize the HX711 on the given GPIO pins.

        Args:
            dout_pin: BCM pin number connected to HX711 DOUT.
            pd_sck_pin: BCM pin number connected to HX711 PD_SCK.
            gain: Amplifier gain — 128 or 64 for channel A, 32 for channel B.

        Raises:
            ValueError: If *gain* is not 128, 64, or 32.
        """
        if gain not in self.GAIN_PULSES:
            raise ValueError(f"Gain must be 128, 64, or 32 — got {gain}")

        self._dout = dout_pin
        self._sck = pd_sck_pin
        self._gain = gain
        self._offset: float = 0.0
        self._scale: float = 1.0

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self._sck, GPIO.OUT)
        GPIO.setup(self._dout, GPIO.IN)

        self.reset()

    # -- Low-level I/O -------------------------------------------------------

    def reset(self) -> None:
        """Reset the HX711 by cycling PD_SCK."""
        GPIO.output(self._sck, False)
        self._wait_ready()

    def _wait_ready(self, timeout: float = 1.0) -> bool:
        """Block until DOUT goes low (data ready) or *timeout* expires."""
        deadline = time.time() + timeout
        while GPIO.input(self._dout):
            if time.time() > deadline:
                return False
            time.sleep(0.001)
        return True

    def read_raw(self) -> Optional[int]:
        """Read a raw 24-bit signed value from the ADC.

        Returns:
            Signed integer in the range −8 388 608 … +8 388 607,
            or *None* if the chip did not become ready in time.
        """
        if not self._wait_ready():
            return None

        # Clock out 24 data bits (MSB first)
        data = 0
        for _ in range(24):
            GPIO.output(self._sck, True)
            GPIO.output(self._sck, False)
            data = (data << 1) | GPIO.input(self._dout)

        # Extra pulses to set gain for the *next* conversion
        for _ in range(self.GAIN_PULSES[self._gain]):
            GPIO.output(self._sck, True)
            GPIO.output(self._sck, False)

        # Two's complement conversion (24-bit)
        if data & 0x800000:
            data -= 0x1000000

        return data

    # -- High-level readings -------------------------------------------------

    @property
    def value(self) -> Optional[float]:
        """Raw reading minus tare offset."""
        raw = self.read_raw()
        return None if raw is None else raw - self._offset

    @property
    def weight(self) -> Optional[float]:
        """Weight in the units established by :meth:`calibrate`."""
        val = self.value
        return None if val is None else val / self._scale

    # -- Calibration ---------------------------------------------------------

    def tare(self, samples: int = 10) -> bool:
        """Set the current reading as the zero point.

        Args:
            samples: Number of readings to average for the tare offset.

        Returns:
            *True* if taring succeeded (all samples were valid).
        """
        readings = []
        for _ in range(samples):
            raw = self.read_raw()
            if raw is None:
                return False
            readings.append(raw)
            time.sleep(0.05)

        self._offset = sum(readings) / len(readings)
        return True

    def calibrate(self, known_weight: float, samples: int = 10) -> bool:
        """Calibrate scale factor using a known reference weight.

        Call :meth:`tare` first with an empty load cell, then place the
        reference weight and call this method.

        Args:
            known_weight: Mass of the reference weight (in desired units).
            samples: Number of readings to average.

        Returns:
            *True* if calibration succeeded.
        """
        values = []
        for _ in range(samples):
            val = self.value
            if val is None:
                return False
            values.append(val)
            time.sleep(0.05)

        avg = sum(values) / len(values)
        if avg == 0:
            return False

        self._scale = avg / known_weight
        return True

    # -- Power management ----------------------------------------------------

    def power_down(self) -> None:
        """Enter low-power mode (PD_SCK held high for >60 µs)."""
        GPIO.output(self._sck, False)
        GPIO.output(self._sck, True)
        time.sleep(0.0001)

    def power_up(self) -> None:
        """Wake the chip from low-power mode."""
        GPIO.output(self._sck, False)
        self._wait_ready()

    def close(self) -> None:
        """Release the GPIO pins used by this driver."""
        GPIO.cleanup([self._sck, self._dout])
